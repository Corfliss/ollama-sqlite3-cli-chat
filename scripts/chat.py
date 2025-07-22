"""CLI chat interface for interacting with Ollama models and saving logs.

Features:
- Chat with different models (with ability to switch mid-chat)
- Saves chats to SQLite and markdown in real-time
"""

import json
import os
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from config import OLLAMA_MODEL, OLLAMA_HOST, DB_PATH, TZ_OFFSET
from db import (
    init_db,
    create_session,
    save_message,
    get_session_path,
    ensure_folder_exists,
    get_messages_history,
)

def query_ollama(model: str, messages: list[dict], stream: bool = True) -> str:
    """
    Send chat messages to Ollama and return the full response.
    Optionally stream output to the terminal.
    """
    response_text = ""
    try:
        res = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": stream
            },
            stream=True
        )
        for line in res.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        if stream:
                            print(content, end="", flush=True)
                        response_text += content
                except json.JSONDecodeError:
                    print("⚠️ Failed to decode line:", line)
                    continue
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return "[ERROR: Failed to connect to Ollama]"

    if stream:
        print()  # Ensure newline after stream
    return response_text.strip()

# def query_ollama(model: str, messages: list[dict]) -> str:
#     """
#     Send a chat history to Ollama's /api/chat endpoint.
#     """
#     response_text = ""
#     try:
#         res = requests.post(
#             f"{OLLAMA_HOST}/api/chat",
#             json={"model": model, "messages": messages},
#             stream=True,
#             timeout=60
#         )
#         res.raise_for_status()

#         for line in res.iter_lines():
#             if not line.strip():
#                 continue
#             try:
#                 data = json.loads(line.decode("utf-8"))
#             except json.JSONDecodeError:
#                 print("⚠️ Malformed JSON from Ollama:", line)
#                 continue

#         return response_text.strip()

#     except requests.exceptions.RequestException as e:
#         print(f"❌ Error communicating with model: {e}")
#         return "[ERROR] Could not contact model server."

def append_to_markdown(
    folder: str,
    filename: str,
    role: str,
    content: str,
    timestamp: str,
    model: str = None
) -> None:
    """
    Append a message to the markdown file with timestamp and model info.
    """
    path = get_session_path(folder, filename)
    with open(path, 'a') as f:
        if role == "assistant":
            f.write(f"### Assistant - {timestamp} - {model}\n")
        else:
            f.write(f"### User - {timestamp}\n")
        f.write(f"\n{content.strip()}\n\n")

def current_timestamp() -> str:
    """
    Return the current timestamp formatted with timezone offset.
    """
    local_offset = timedelta(hours=TZ_OFFSET)
    local_time = datetime.now(timezone(local_offset))
    return local_time.strftime('%Y.%m.%d %H:%M:%S %z')

def start_chat(folder: str = "default", filename: str = "chat-1") -> None:
    """
    Start a new chat session and log messages to DB and markdown.
    """
    init_db()
    ensure_folder_exists(folder)
    session_id = create_session(folder, filename)

    print(f"\n🧠 Starting new chat in `{folder}/{filename}.md`")
    print(f"💡 Using model: {OLLAMA_MODEL}")
    print("Type `/switch model_name` to change model, or 'exit' to stop.\n")

    # Write markdown header
    with open(get_session_path(folder, filename), 'w') as f:
        f.write(f"# Chat: {filename}\n\n")
        f.write(f"> Started: {current_timestamp()}\n\n")
        f.write(f"---\n\n")

    current_model = OLLAMA_MODEL

    while True:
        user_input = input("You:\n").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("👋 Chat ended.")
            break

        if user_input.startswith("/switch "):
            new_model = user_input.split("/switch ")[1].strip()
            if new_model:
                current_model = new_model
                print(f"🔄 Switched model to `{current_model}`\n")
            continue

        timestamp = current_timestamp()
        save_message(session_id, "user", user_input)
        append_to_markdown(folder, filename, "user", user_input, timestamp)

        # Build message history from DB
        db_messages = get_messages_history(session_id)
        history = [{"role": m["role"], "content": m["content"]} for m in db_messages]

        print(f"\n{current_model}:\n", end="")  # Add newline before model response
        response = query_ollama(current_model, history, stream=True)

        timestamp = current_timestamp()
        save_message(session_id, "assistant", response, model=current_model)
        append_to_markdown(folder, filename, "assistant", response, timestamp, model=current_model)
        print()  # Separate conversations with a blank line


def continue_chat(session_id: int) -> None:
    """
    Continue an existing chat session based on session ID.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT folder, filename FROM sessions WHERE id = ?", (session_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        print("❌ Session not found.")
        return

    folder, filename = result
    print(f"\n🔁 Continuing chat `{filename}` in folder `{folder}`\n"
          f"Type 'exit' to stop.\n")

    while True:
        user_input = input("You:\n").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Chat ended.")
            break

        timestamp = current_timestamp()
        save_message(session_id, "user", user_input)
        append_to_markdown(folder, filename, "user", user_input, timestamp)

        db_messages = get_messages_history(session_id)
        history = [{"role": m["role"], "content": m["content"]} for m in db_messages]

        print(f"\n{OLLAMA_MODEL}:\n", end="")  # Newline before response
        response = query_ollama(OLLAMA_MODEL, history, stream=True)

        timestamp = current_timestamp()
        save_message(session_id, "assistant", response, model=OLLAMA_MODEL)
        append_to_markdown(folder, filename, "assistant", response, timestamp, model=OLLAMA_MODEL)
        print()  # Blank line between exchanges

def list_chats():
    """
    List all chat sessions from the database.
    Returns a list of (id, folder, filename, created_at).
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, folder, filename, created_at FROM sessions ORDER BY id")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("📭 No chat sessions found.")
        return []

    print("💾 Existing Chats:")
    for row in rows:
        print(f"[{row[0]}] {row[1]}/{row[2]} — {row[3]}")
    return rows

# def list_chats() -> None:
#     """
#     Print all existing chat sessions from the database.
#     """
#     init_db()
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute(
#         "SELECT id, folder, filename, created_at "
#         "FROM sessions ORDER BY id DESC"
#     )
#     rows = c.fetchall()
#     conn.close()

#     if not rows:
#         print("📭 No chats found.")
#         return

#     print("\n💾 Existing Chats:")
#     for row in rows:
#         print(f"[{row[0]}] {row[1]}/{row[2]} - {row[3]}")

def delete_chat(session_id: int) -> bool:
    """
    Delete a chat session and its markdown file.
    Returns True if deleted, False otherwise.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT folder, filename FROM sessions WHERE id = ?", (session_id,))
    result = c.fetchone()

    if not result:
        print("❌ Session ID not found.")
        conn.close()
        return False

    folder, filename = result
    md_path = get_session_path(folder, filename)

    # Delete from DB
    c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    print(f"🧹 Deleted DB records for session {session_id}")

    # Delete markdown file
    if os.path.exists(md_path):
        os.remove(md_path)
        print(f"🗑️ Deleted markdown: {md_path}")

    # Remove folder if empty
    folder_path = os.path.dirname(md_path)
    if os.path.isdir(folder_path) and not os.listdir(folder_path):
        os.rmdir(folder_path)
        print(f"🧼 Deleted empty folder: {folder_path}")

    conn.close()
    return True

# def delete_chat(session_id: int):
#     """
#     Delete a chat session and its markdown file.
#     """
#     init_db()
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()

#     c.execute("SELECT folder, filename FROM sessions WHERE id = ?", (session_id,))
#     result = c.fetchone()

#     if not result:
#         print("❌ Session ID not found.")
#         conn.close()
#         return

#     folder, filename = result
#     md_path = get_session_path(folder, filename)

#     # Delete from DB
#     c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
#     c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
#     conn.commit()
#     print(f"🧹 Deleted DB records for session {session_id}")

#     # Delete markdown file
#     if os.path.exists(md_path):
#         os.remove(md_path)
#         print(f"🗑️ Deleted markdown: {md_path}")

#     # Remove folder if empty
#     folder_path = os.path.dirname(md_path)
#     if os.path.isdir(folder_path) and not os.listdir(folder_path):
#         os.rmdir(folder_path)
#         print(f"🧼 Deleted empty folder: {folder_path}")

#     conn.close()
