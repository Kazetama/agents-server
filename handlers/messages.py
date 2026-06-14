from aiogram import Router, F
from aiogram.types import Message
from utils.security import owner_only
from core.agent import process_message
from utils.logger import logger

router = Router()


@router.message(F.text)
@owner_only
async def handle_text(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = process_message(str(message.from_user.id), message.text)
        await message.answer(response)
    except Exception as e:
        logger.error(f"Handler error: {e}")
        await message.answer(f"⚠️ Error: {e}")
