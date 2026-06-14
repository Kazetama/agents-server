from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from utils.security import owner_only
from core.memory import memory
from config.settings import BOT_PERSONA

router = Router()


@router.message(CommandStart())
@owner_only
async def cmd_start(message: Message):
    memory.clear(str(message.from_user.id))
    await message.answer(
        f"⚡ <b>AI Agent Online</b>\n"
        f"Persona: <code>{BOT_PERSONA}</code>\n\n"
        f"Ketik perintahmu atau tanya apa saja tentang server. Aku siap!",
        parse_mode="HTML"
    )


@router.message(Command("clear"))
@owner_only
async def cmd_clear(message: Message):
    memory.clear(str(message.from_user.id))
    await message.answer("🧹 Memory cleared. Context reset.")


@router.message(Command("status"))
@owner_only
async def cmd_status(message: Message):
    from skills.server_monitor import get_system_status
    result = get_system_status()
    await message.answer(f"<b>Server Status</b>\n<pre>{result}</pre>", parse_mode="HTML")


@router.message(Command("help"))
@owner_only
async def cmd_help(message: Message):
    text = (
        "<b>Available Commands</b>\n\n"
        "/start — Reset conversation & greet\n"
        "/clear — Clear memory context\n"
        "/status — Quick server resource check\n"
        "/help — Show this help\n\n"
        "<b>Available Skills (auto-invoked by AI)</b>\n"
        "• Server monitor (CPU/RAM/Disk/Uptime)\n"
        "• Docker manager (list/restart/stop)\n"
        "• Package manager (apt install/upgrade)\n"
        "• Log analyzer (tail any log file)\n"
        "• Shell executor (any bash command)\n"
        "• Network checker (ping/port/IP)\n\n"
        "<b>Persona</b>\n"
        f"Active: <code>{BOT_PERSONA}</code>\n"
        "Change: edit <code>BOT_PERSONA</code> in .env and restart."
    )
    await message.answer(text, parse_mode="HTML")
