"""Main CLI menu to manage chat sessions with Ollama models."""

import sys
from chat import start_chat, list_chats, continue_chat
from export import export_all_sessions
from db import delete_chat


def menu() -> None:
    """
    Print the CLI menu options.
    """
    print("\n🧠 Ollama Chat CLI")
    print("1. Start new chat")
    print("2. List existing chats")
    print("3. Continue a chat")
    print("4. Export all chats to markdown")
    print("5. Delete a chat")  # 🔥 Added
    print("6. Exit")


def main() -> None:
    """
    CLI loop for interacting with the user.
    """
    while True:
        menu()
        choice = input("Select an option (1–5): ").strip()

        if choice == '1':
            folder = input("Enter folder name (e.g., `default`): ").strip() or "default"
            name = input("Enter file name (e.g., `chat-1`): ").strip() or "chat-1"
            start_chat(folder, name)

        elif choice == '2':
            list_chats()

        elif choice == '3':
            list_chats()
            chat_id = input("Enter the session ID to continue: ").strip()
            if chat_id.isdigit():
                continue_chat(int(chat_id))
            else:
                print("❌ Invalid session ID.")

        elif choice == '4':
            export_all_sessions()

        elif choice == '5':
            list_chats()
            chat_id = input("Enter the session ID to delete: ").strip()
            if chat_id.isdigit():
                confirm = input(f"⚠️ Are you sure you want to delete chat {chat_id}? (y/N): ").strip().lower()
                if confirm == "y":
                    delete_chat(int(chat_id))
                else:
                    print("❎ Deletion cancelled.")
            else:
                print("❌ Invalid session ID.")

        elif choice == '6':
            print("👋 Exiting.")
            sys.exit(0)

        else:
            print("❌ Invalid option. Please choose 1–5.")


if __name__ == "__main__":
    main()
