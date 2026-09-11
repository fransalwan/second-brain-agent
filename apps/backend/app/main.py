from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import threading  # <-- TAMBAHKAN INI

# 1. Import Database & Models
from .database import get_session, engine
from .models import Note, Profile, TimeLog, Donation

# 2. Import Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.services.telegram_bot import start, echo_message, TOKEN

app = FastAPI(title="Second Brain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Second Brain API is running. Brain loaded."}


@app.get("/test-db")
async def test_db_connection(session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(select(Note).limit(1))
        note = result.scalars().first()
        return {
            "status": "success",
            "message": "Connected to Supabase successfully!",
            "sample_data": str(note)
            if note
            else "No notes found (this is fine for a new DB)",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Fungsi khusus untuk menjalankan bot di thread terpisah
def run_bot_in_background():
    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    # run_polling sekarang aman dijalankan di thread-nya sendiri
    tg_app.run_polling(allowed_updates=Update.ALL_TYPES)


@app.on_event("startup")
async def startup_event():
    print(">>> Starting Telegram Bot in background thread...")

    # Buat thread baru (daemon=True agar mati otomatis saat server utama mati)
    bot_thread = threading.Thread(target=run_bot_in_background, daemon=True)
    bot_thread.start()

    print(">>> Telegram Bot is running safely in background! 🤖")
