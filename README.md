# Disclosure
```txt
This is using ChatGPT to generate for almost all of the repository. Including the README.md, except this line. 
Consider booing me at my social media for the lazy AI usage, as my brain is on a lot of pain and burnout at the time of writing this after doing a lot for bachelor thesis lul.
```

# 🧠 Local Memory Ollama CLI Chat

A lightweight, terminal-based chat interface using [Ollama](https://ollama.com/) as the AI model backend, `sqlite3` for persistent chat storage, and Markdown for readable session logs.

## ✨ Features

- Chat with local LLMs via Ollama (`http://localhost:11434`)
- Chats stored in SQLite database and automatically exported to Markdown
- Organized by folder & filename (e.g. `chats/default/chat-1.md`)
- Supports switching models mid-conversation (`/switch`)
- Timezone-aware timestamps in messages
- Command-line menu interface

---

## 🛠️ Requirements

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running
- A model pulled via Ollama (e.g. `llama3`, `mistral`, etc.)

---

## 📦 Installation

```bash
git clone https://github.com/Corfliss/local-memory-ollama-cli-chat.git
cd local-memory-ollama-cli-chat
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Example of `requirements.txt`:
```txt
requests
python-dotenv
```

## ⚙️ Configuration

Create a .env file in the root directory to customize the settings:
```env
OLLAMA_MODEL=llama3
OLLAMA_HOST=http://localhost:11434
DB_PATH=database/app.db
TZ_OFFSET=7
```

* `OLLAMA_MODEL`: Default model name (e.g., mistral, llama3)
* `OLLAMA_HOST`: Ollama server URL
* `DB_PATH`: Path to SQLite DB file
* `TZ_OFFSET`: Timezone offset from GMT (e.g., 7 for GMT+7)

## 🚀 Running the Program:

Use the CLI menu to interact:
```bash
python run.py
```

### Menu Options:
```txt
1. Start new chat
2. List existing chats
3. Continue a chat
4. Export all chats to markdown
5. Exit
```

## 💬 Commands During Chat

* `/switch <model>` — switch model mid-chat. Example: `/switch mistral`
* `exit` or `quit` — end the chat

## 📁 Folder Structure
```txt
ollama-cli-chat/
├── chats/                  # Markdown logs organized by folder
│   └── default/
│       └── chat-1.md
├── database/               # SQLite DB location (default path)
│   └── app.db
├── chat.py                 # Core chat logic
├── db.py                   # Database logic
├── export.py               # Markdown export utility
├── interface.py            # CLI menu (formerly run.py)
├── .env                    # Environment configuration
├── requirements.txt
└── README.md
```

## 🧪 Example Chat Output (Markdown)

### Chat: example-chat

> Started: 2025.07.14 23:45:02 +0700

---

#### User — 2025.07.14 23:45:02 +0700
```
How do I write a recursive function in Python?
```

#### Assistant — 2025.07.14 23:45:05 +0700 — llama3
```
A recursive function is one that calls itself. Here's an example...
```

## 🧰 Dev Notes

- All messages are stored in the database and reflected in Markdown in real time
- Changing models mid-conversation updates both markdown and database with model info
