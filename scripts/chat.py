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
from config import OLLAMA_MODEL, OLLAMA_HOST, DB_PATH, CHATS_DIR, TZ_OFFSET
from db import (
    init_db,
    create_session,
    save_message,
    get_session_path,
    ensure_folder_exists,
    get_messages_for_session,
)

def query_ollama(model, messages):
    """
    Send full chat history to Ollama and get response (with memory).
    """
    res = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={"model": model, "messages": messages}
    )

    if res.status_code != 200:
        print("❌ Failed to get response:", res.text)
        return "Error: failed to fetch response."

    data = res.json()
    return data.get("message", {}).get("content", "").strip()

    return response_text.strip()


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
            f.write(f"### Assistant — {timestamp} — {model}\n")
        else:
            f.write(f"### User — {timestamp}\n")
        f.write(f"```\n{content.strip()}\n```\n\n")


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
        print("\n")

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
        db_messages = get_messages_for_session(session_id)
        history = [{"role": m[0], "content": m[1]} for m in db_messages]
        history.append({"role": "user", "content": user_input})

        response = query_ollama(current_model, history)
        print(f"{current_model}:\n{response.strip()}")
        print("\n")

        timestamp = current_timestamp()
        save_message(session_id, "assistant", response, model=current_model)
        append_to_markdown(
            folder, filename, "assistant", response, timestamp, model=current_model
        )


def continue_chat(session_id: int) -> None:
    """
    Continue an existing chat session based on session ID.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT folder, filename FROM sessions WHERE id = ?",
        (session_id,)
    )
    result = c.fetchone()
    conn.close()

    if not result:
        print("❌ Session not found.")
        return

    folder, filename = result
    print(f"\n🔁 Continuing chat `{filename}` in folder `{folder}`\n"
          f"Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Chat ended.")
            break

        timestamp = current_timestamp()
        save_message(session_id, "user", user_input)
        append_to_markdown(folder, filename, "user", user_input, timestamp)

        # Build message history from DB
        db_messages = get_messages_for_session(session_id)
        history = [{"role": m[0], "content": m[1]} for m in db_messages]
        history.append({"role": "user", "content": user_input})

        response = query_ollama(OLLAMA_MODEL, history)
        print(f"{OLLAMA_MODEL}: {response.strip()}")

        timestamp = current_timestamp()
        save_message(session_id, "assistant", response, model=OLLAMA_MODEL)
        append_to_markdown(folder, filename, "assistant", response, timestamp,
                           model=OLLAMA_MODEL)


def list_chats() -> None:
    """
    Print all existing chat sessions from the database.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, folder, filename, created_at "
        "FROM sessions ORDER BY id DESC"
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("📭 No chats found.")
        return

    print("\n💾 Existing Chats:")
    for row in rows:
        print(f"[{row[0]}] {row[1]}/{row[2]} — {row[3]}")
