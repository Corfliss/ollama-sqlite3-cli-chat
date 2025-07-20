"""Export all chat sessions from the database into markdown files."""

import sqlite3
from db import DB_PATH, get_session_path, ensure_folder_exists


def fetch_sessions():
    """
    Retrieve all session metadata from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, folder, filename FROM sessions")
    sessions = c.fetchall()
    conn.close()
    return sessions


def fetch_messages(session_id):
    """
    Retrieve all messages for a given session, ordered by message ID.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content, model, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY id
    ''', (session_id,))
    messages = c.fetchall()
    conn.close()
    return messages


def export_all_sessions():
    """
    Export all sessions and their messages into markdown files.
    """
    sessions = fetch_sessions()

    for session_id, folder, filename in sessions:
        ensure_folder_exists(folder)
        path = get_session_path(folder, filename)
        messages = fetch_messages(session_id)

        with open(path, 'w') as f:
            f.write(f"# Chat: {filename}\n\n")

            for role, content, model, timestamp in messages:
                header = f"### {role.capitalize()} — {timestamp}"
                if role == "assistant" and model:
                    header += f" — {model}"
                f.write(f"{header}\n```\n{content.strip()}\n```\n\n")

        print(f"✅ Exported: {path}")


if __name__ == "__main__":
    export_all_sessions()
