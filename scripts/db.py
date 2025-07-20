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