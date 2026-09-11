# apps/backend/app/bot.py
import logging
import os

from dotenv import load_dotenv
from sqlmodel import select
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .agent import run_agent
from .database import SessionLocal
from .models import Note, Profile

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_MAX_LEN = 4096

# updater(None) = tanpa polling. Update masuk lewat webhook FastAPI.
ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).updater(None).build()

NOT_LINKED_MSG = (
    "Akun Telegram ini belum terhubung ke Second Brain.\n\n"
    "Chat ID kamu: {chat_id}\n"
    "Kirim Chat ID ini ke admin untuk dihubungkan."
)


async def get_profile_by_chat_id(chat_id: int) -> Profile | None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Profile).where(Profile.telegram_chat_id == chat_id)
        )
        return result.scalars().first()


async def save_raw_note(profile: Profile, content: str) -> int:
    """Cadangan kalau AI gagal: pesan tetap tersimpan apa adanya."""
    async with SessionLocal() as session:
        note = Note(user_id=profile.id, content=content, source="telegram")
        session.add(note)
        await session.commit()
        await session.refresh(note)
        return note.id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)

    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    name = f", {profile.full_name}" if profile.full_name else ""
    await update.effective_message.reply_text(
        f"Halo{name}! Akun kamu sudah terhubung.\n\n"
        "Contoh yang bisa kamu kirim:\n"
        "• ide: bikin fitur export notes ke markdown\n"
        "• mulai ngoding second brain\n"
        "• udahan dulu\n"
        "• rekap hari ini\n"
        "• cari catatan soal vue"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id
    text = message.text.strip()

    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await message.reply_text(NOT_LINKED_MSG.format(chat_id=chat_id))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await run_agent(profile.id, chat_id, text)
    except Exception:
        logger.exception("Agent gagal memproses pesan dari chat_id=%s", chat_id)
        note_id = await save_raw_note(profile, text)
        reply = f"⚠️ AI sedang bermasalah, tapi pesanmu sudah disimpan sebagai catatan mentah (#{note_id})."

    await message.reply_text(reply[:TELEGRAM_MAX_LEN])


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Error saat memproses update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Gagal memproses pesan. Coba lagi sebentar."
        )


private = filters.ChatType.PRIVATE
ptb_app.add_handler(CommandHandler("start", start, filters=private))
# UpdateType.MESSAGE = abaikan pesan yang di-edit (supaya tidak diproses dua kali)
ptb_app.add_handler(
    MessageHandler(
        private & filters.UpdateType.MESSAGE & filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)
ptb_app.add_error_handler(on_error)
