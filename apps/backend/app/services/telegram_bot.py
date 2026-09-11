# apps/backend/app/services/telegram_bot.py
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Setup logging biar kita bisa lihat apa yang terjadi di terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dijalankan saat user mengetik /start"""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Halo! 👋\n\n"
        f"Chat ID lu adalah: `{chat_id}`\n\n"
        f"Kirim ide, catatan, atau perintah coding lu di sini. "
        f"Untuk menghubungkan akun ini dengan dashboard web lu, gunakan perintah:\n"
        f"`/link <kode_unik_dari_web>`"
    )


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dijalankan saat user mengirim pesan biasa (akan jadi input untuk AI Agent nanti)"""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    logger.info(f"Pesan diterima dari chat_id {chat_id}: {user_message}")

    # TODO: Di sini nanti kita panggil Google ADK Agent untuk memproses pesan ini
    # Untuk sekarang, kita balas dulu sebagai konfirmasi
    await update.message.reply_text(
        f"🧠 *Otak sedang memproses:* \n\n`{user_message}`\n\n*(Fitur AI Agent akan segera aktif!)*",
        parse_mode="Markdown",
    )


# Fungsi untuk menjalankan bot (akan dipanggil dari main.py)
def run_bot(application: Application):
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
