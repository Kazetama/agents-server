# 🤖 AI Agent SysAdmin Bot

A **production-ready, DevOps-grade Telegram Bot** powered by a local Llama 3.2 AI agent (via Ollama) and built on Python + Aiogram 3.

The bot acts as an autonomous SysAdmin AI agent — it can monitor your server, manage packages, control Docker, analyze logs, and execute shell commands, all through natural language conversations in Telegram.

---

## ✨ Features

- 🧠 **Local AI (Offline)** — Runs entirely on your own hardware via Ollama (no cloud API needed)
- 🎭 **Configurable Persona** — Switch bot personality (Cute Sister / Cyborg AI / Drill Sergeant / Hacker) via `.env`
- 🛠️ **Autonomous Tool Calling** — Agent decides which tools to use based on your request
- 🔒 **Owner-Only Access** — All commands restricted to a single authorized Telegram user
- 💾 **Conversation Memory** — Remembers context within a session
- 📦 **Modular Skills** — Easy to add new capabilities by creating a single file

---

## 📁 Project Structure

```
telegram-server-bot/
├── config/
│   ├── settings.py        # Global settings loader (.env)
│   └── personas.md        # ⭐ Persona definitions (editable!)
├── core/
│   ├── agent.py           # Main AI agent loop (tool execution)
│   ├── memory.py          # Per-user conversation history
│   └── persona.py         # Persona loader from personas.md
├── skills/
│   ├── registry.py        # Central tool auto-registry
│   ├── SKILLS.md          # Skills documentation
│   ├── server_monitor.py  # CPU / RAM / Disk / Uptime
│   ├── docker_manager.py  # Docker container management
│   ├── package_manager.py # apt install / upgrade
│   ├── log_analyzer.py    # Log file reader
│   ├── shell_executor.py  # Arbitrary shell command execution
│   └── network_checker.py # Ping / port check / public IP
├── handlers/
│   ├── commands.py        # /start /clear /status /help
│   └── messages.py        # Natural language message handler
├── utils/
│   ├── logger.py          # Structured logging
│   ├── security.py        # Owner-only access control
│   └── formatter.py       # Telegram message formatters
├── .env.example           # Environment variable template
├── main.py                # Entry-point
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo>
cd telegram-server-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Fill in:
```env
BOT_TOKEN=your_telegram_bot_token
OWNER_ID=your_telegram_user_id
OLLAMA_MODEL=llama3.2
BOT_PERSONA=onee-chan
```

### 3. Install & Run Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

### 4. Run the Bot

```bash
python main.py
```

---

## 🎭 Personas

Edit `BOT_PERSONA` in `.env` to switch the bot's personality. Available presets (defined in `config/personas.md`):

| Persona Key | Description |
|---|---|
| `onee-chan` | Cute, caring big sister who loves her little sibling 💕 |
| `cyborg` | ARIA — a cold, precise autonomous AI agent ⚡ |
| `drill-sergeant` | Sergeant Rex — brutally direct, no fluff 🎖️ |
| `hacker` | Ghost — underground, terminal-native vibes 💀 |

You can create custom personas by adding a new `## persona: <name>` section in `config/personas.md`.

---

## 🛠️ Adding New Skills

1. Create `skills/your_skill.py` with `TOOL_SCHEMA` and `TOOL_FUNCTION`
2. Import and add to `SKILL_MODULES` in `skills/registry.py`
3. Restart the bot — that's it!

See [`skills/SKILLS.md`](skills/SKILLS.md) for full documentation.

---

## 📋 Commands

| Command | Description |
|---|---|
| `/start` | Reset conversation and greet |
| `/clear` | Clear AI memory context |
| `/status` | Quick server resource snapshot |
| `/help` | Show all commands and active persona |

---

## 🔧 Tech Stack

- **Python 3.12**
- **Aiogram 3** — Telegram Bot framework
- **Ollama** — Local LLM inference
- **Llama 3.2** — AI model with native function calling
- **psutil** — System resource monitoring
- **python-dotenv** — Environment configuration

---

## 📄 License

MIT License — feel free to fork, modify, and deploy!
