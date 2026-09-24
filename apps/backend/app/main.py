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
from .ambient import (
    check_bedtime_status,
    check_habit_by_keyword,
    get_ambient_status,
    handle_git_commit_event,
    handle_quick_capture,
    start_ambient_timer,
    stop_ambient_timer,
)


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


# ==========================================
# AMBIENT TRACKING ENDPOINTS (OS / VS Code)
# ==========================================
from pydantic import BaseModel


class AmbientStartRequest(BaseModel):
    email: str
    project_name: str
    source: str = "vscode"
    context: str | None = None
    notify_telegram: bool = True


class AmbientStopRequest(BaseModel):
    email: str
    project_name: str | None = None
    reason: str = "window_closed"
    notify_telegram: bool = True


def verify_ambient_key(
    x_ambient_key: str | None = Header(default=None, alias="X-Ambient-Key"),
):
    expected = settings.AMBIENT_API_KEY
    if (
        not expected
        or not x_ambient_key
        or not secrets.compare_digest(x_ambient_key, expected)
    ):
        raise HTTPException(
            status_code=403,
            detail="Header X-Ambient-Key tidak valid atau tidak disertakan",
        )
    return True


@app.post("/api/v1/ambient/timer/start")
async def api_ambient_start(
    payload: AmbientStartRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Memulai timer fokus otomatis dari ambient desktop watcher."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await start_ambient_timer(
        session=session,
        email=payload.email,
        project_name=payload.project_name,
        source=payload.source,
        context=payload.context,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@app.post("/api/v1/ambient/timer/stop")
async def api_ambient_stop(
    payload: AmbientStopRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Menghentikan timer fokus otomatis saat jendela ditutup atau idle."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await stop_ambient_timer(
        session=session,
        email=payload.email,
        project_name=payload.project_name,
        reason=payload.reason,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@app.get("/api/v1/ambient/status")
async def api_ambient_status(
    email: str,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Cek status timer aktif dan konfigurasi user untuk ambient daemon."""
    result = await get_ambient_status(session=session, email=email)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@app.get("/api/v1/ambient/bedtime-status")
async def api_ambient_bedtime_status(
    email: str,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Mengecek status jam malam user untuk sinkronisasi dengan desktop watcher."""
    result = await check_bedtime_status(session=session, email=email)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


class AmbientHabitCheckRequest(BaseModel):
    email: str
    habit_keyword: str
    notify_telegram: bool = True


@app.post("/api/v1/ambient/habit/check")
async def api_ambient_habit_check(
    payload: AmbientHabitCheckRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Mencentang habit secara otomatis berdasarkan kata kunci nama habit."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await check_habit_by_keyword(
        session=session,
        email=payload.email,
        habit_keyword=payload.habit_keyword,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    elif result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


class AmbientGitCommitRequest(BaseModel):
    email: str
    commit_message: str
    repo_name: str | None = None
    branch: str | None = None
    notify_telegram: bool = True


@app.post("/api/v1/ambient/git/commit")
async def api_ambient_git_commit(
    payload: AmbientGitCommitRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Menerima event git commit untuk auto-done tasks dan habit sync."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await handle_git_commit_event(
        session=session,
        email=payload.email,
        commit_message=payload.commit_message,
        repo_name=payload.repo_name,
        branch=payload.branch,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


class QuickCaptureRequest(BaseModel):
    email: str
    text: str
    source: str = "global_hotkey"
    notify_telegram: bool = True


@app.post("/api/v1/ambient/quick-capture")
async def api_quick_capture(
    payload: QuickCaptureRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Menerima tangkapan ide/tugas cepat dari Global Desktop Quick Capture."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await handle_quick_capture(
        session=session,
        email=payload.email,
        text=payload.text,
        source=payload.source,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
