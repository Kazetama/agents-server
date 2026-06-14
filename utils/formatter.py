"""
utils/formatter.py
───────────────────
Helper functions for formatting Telegram bot messages.
Uses Telegram's MarkdownV2 / HTML formatting.
"""

def code_block(text: str) -> str:
    """Wrap text in a monospace code block."""
    return f"<pre>{text}</pre>"

def bold(text: str) -> str:
    return f"<b>{text}</b>"

def italic(text: str) -> str:
    return f"<i>{text}</i>"
