import os
from functools import wraps
from aiogram.types import Message
from utils.logger import logger

OWNER_ID: str = os.getenv("OWNER_ID", "")


def owner_only(handler):
    """Decorator: restrict handler access to the bot owner only."""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        if str(message.from_user.id) != str(OWNER_ID):
            logger.warning(f"Unauthorized access: user_id={message.from_user.id}")
            await message.answer("🚫 Unauthorized.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper
