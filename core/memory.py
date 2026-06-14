"""
core/memory.py
──────────────
Per-user conversation history manager.
Keeps context window bounded and always injects the system prompt first.
"""
from typing import List, Dict
from utils.logger import logger


class MemoryManager:
    def __init__(self, max_messages: int = 20):
        self._history: Dict[str, List[Dict]] = {}
        self.max_messages = max_messages

    def _get_system_prompt(self) -> Dict:
        # Imported here to avoid circular imports
        from core.persona import load_persona
        from config.settings import BOT_PERSONA
        return {"role": "system", "content": load_persona(BOT_PERSONA)}

    def get_history(self, user_id: str) -> List[Dict]:
        if user_id not in self._history:
            self._history[user_id] = [self._get_system_prompt()]
        return self._history[user_id]

    def add_message(self, user_id: str, role: str, content: str):
        history = self.get_history(user_id)
        history.append({"role": role, "content": content})

        # Trim: always keep system prompt at index 0
        if len(history) > self.max_messages + 1:
            system = history[0]
            self._history[user_id] = [system] + history[-(self.max_messages):]

    def append_raw(self, user_id: str, message: Dict):
        """Append a raw message dict (e.g. tool call objects from Ollama)."""
        self.get_history(user_id).append(message)

    def clear(self, user_id: str):
        if user_id in self._history:
            del self._history[user_id]
        logger.info(f"Memory cleared for user {user_id}")


# Singleton instance
memory = MemoryManager()
