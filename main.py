"""
main.py
────────
Entry-point for the AI Agent SysAdmin Telegram Bot.
Initializes the bot, registers routers, and starts polling.
"""
import asyncio
from aiogram import Bot, Dispatcher
from config.settings import BOT_TOKEN, BOT_PERSONA, OLLAMA_MODEL
from handlers import commands, messages
from utils.logger import logger


async def main():
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("   AI Agent SysAdmin Bot — Starting")
    logger.info(f"   Model  : {OLLAMA_MODEL}")
    logger.info(f"   Persona: {BOT_PERSONA}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("BOT_TOKEN is not set. Please configure your .env file.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher()

    dp.include_router(commands.router)
    dp.include_router(messages.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
