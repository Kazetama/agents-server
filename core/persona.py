"""
core/persona.py
───────────────
Parses config/personas.md and returns the system prompt
for the configured persona (BOT_PERSONA in .env).
"""
import os
import re
from pathlib import Path
from utils.logger import logger


_PERSONAS_FILE = Path(__file__).parent.parent / "config" / "personas.md"


def load_persona(name: str) -> str:
    """
    Load a persona system prompt by name from config/personas.md.

    Args:
        name: The persona key (e.g. "onee-chan", "cyborg", "drill-sergeant")

    Returns:
        The system prompt string for the selected persona.
    """
    if not _PERSONAS_FILE.exists():
        logger.error(f"personas.md not found at {_PERSONAS_FILE}")
        return "You are a helpful Linux server assistant."

    content = _PERSONAS_FILE.read_text(encoding="utf-8")

    # Split sections by "## persona: <name>"
    sections = re.split(r"^##\s+persona:\s+", content, flags=re.MULTILINE)

    personas: dict[str, str] = {}
    for section in sections[1:]:  # skip preamble
        lines = section.strip().splitlines()
        persona_name = lines[0].strip()
        prompt = "\n".join(lines[1:]).strip()
        personas[persona_name] = prompt

    if name not in personas:
        available = list(personas.keys())
        logger.warning(f"Persona '{name}' not found. Available: {available}. Falling back to first.")
        name = available[0] if available else None

    if name:
        logger.info(f"Loaded persona: '{name}'")
        return personas[name]

    return "You are a helpful Linux server assistant."
