"""Database utility functions for managing sessions and messages."""

import sqlite3
import os
from config import DB_PATH, CHATS_DIR  # <-- use values from config.yaml


def init_db() -> None:
    """
    Initialize the database with required tables: sessions and messages.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,         -- user or assistant
            content TEXT NOT NULL,
            model TEXT,                 -- model used (optional for user)
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')

    conn.commit()
    conn.close()


def create_session(folder: str, filename: str) -> int:
    """
    Create a new chat session.

    Returns:
        int: The ID of the newly created session.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT INTO sessions (folder, filename) VALUES (?, ?)',
        (folder, filename)
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def save_message(
    session_id: int,
    role: str,
    content: str,
    model: str = None
) -> None:
    """
    Save a single message to the database.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (session_id, role, content, model)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content, model))
    conn.commit()
    conn.close()


def get_session_path(folder: str, filename: str) -> str:
    """
    Construct the path to a markdown file for a given session.
    """
    return os.path.join(CHATS_DIR, folder, f"{filename}.md")


def ensure_folder_exists(folder: str) -> None:
    """
    Ensure that a chat folder exists on disk.
    """
    path = os.path.join(CHATS_DIR, folder)
    os.makedirs(path, exist_ok=True)

def get_messages_history(session_id: int) -> list[dict]:
    """
    Retrieve the full chat history for a session.
    Returns it in Ollama-compatible format.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
    ''', (session_id,))
    rows = c.fetchall()
    conn.close()

    return [{"role": role, "content": content} for role, content in rows]

# Moved the delete_chat() to chat.py. So this one is not used
# def delete_chat(session_id: int) -> None:
#     """
#     Delete a chat session and all its messages from the database.
#     Also deletes the associated markdown file if exists.
#     """
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()

#     # Get session path
#     c.execute("SELECT folder, filename FROM sessions WHERE id = ?", (session_id,))
#     result = c.fetchone()

#     if not result:
#         print("❌ Chat not found.")
#         conn.close()
#         return

#     folder, filename = result
#     markdown_path = get_session_path(folder, filename)

#     # Delete messages and session
#     c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
#     c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
#     conn.commit()
#     conn.close()

#     # Delete markdown file
#     if os.path.exists(markdown_path):
#         os.remove(markdown_path)
#         print(f"🗑️ Deleted markdown: {markdown_path}")
#     else:
#         print("⚠️ Markdown file not found.")

#     print("✅ Chat deleted successfully.")