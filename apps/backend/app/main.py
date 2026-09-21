# apps/backend/app/main.py
import secrets
from .config import settings
from contextlib import asynccontextmanager


from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from telegram import Update

# PENTING: Gunakan titik (.) di depan untuk relative import
from .bot import ptb_app
from .database import engine, get_session
from .models import Note


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Nyalakan bot saat server start, matikan dengan rapi saat server stop
    async with ptb_app:
        await ptb_app.start()
        if settings.TELEGRAM_MODE == "polling":
            # drop_pending_updates=False: pesan yang dikirim saat instance mati
            # akan tetap diproses begitu backend menyala (penting untuk self-hosted
            # di perangkat pribadi yang tidak selalu aktif 24 jam).
            await ptb_app.updater.start_polling(drop_pending_updates=False)
        yield
        if settings.TELEGRAM_MODE == "polling":
            await ptb_app.updater.stop()
        await ptb_app.stop()
    await engine.dispose()


app = FastAPI(title="Second Brain API", version="0.1.0", lifespan=lifespan)

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


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.TELEGRAM_MODE != "webhook":
        raise HTTPException(
            status_code=404, detail="Webhook endpoint inactive in polling mode"
        )

    # Tolak request yang bukan dari Telegram
    secret = settings.TELEGRAM_WEBHOOK_SECRET or ""
    received = (x_telegram_bot_api_secret_token or "").encode()
    if not secrets.compare_digest(received, secret.encode()):
        raise HTTPException(status_code=403, detail="Invalid secret token")

    update = Update.de_json(await request.json(), ptb_app.bot)
    # Masukkan ke antrean lalu langsung balas 200, supaya Telegram tidak retry
    await ptb_app.update_queue.put(update)
    return {"ok": True}


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
