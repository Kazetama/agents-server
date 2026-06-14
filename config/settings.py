import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: str  = os.getenv("OWNER_ID", "")

# ─── Ollama ──────────────────────────────────────────────────
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# ─── Persona ─────────────────────────────────────────────────
# Must match a ## persona: <name> header in config/personas.md
BOT_PERSONA: str = os.getenv("BOT_PERSONA", "onee-chan")
