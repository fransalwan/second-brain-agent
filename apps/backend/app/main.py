# apps/backend/app/main.py
import secrets
from .config import settings
from contextlib import asynccontextmanager


from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
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
    handle_thesis_sync,
    start_ambient_timer,
    stop_ambient_timer,
)
from .mcp_server import create_mcp_sse_app


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

# Standard Anthropic MCP Server (SSE Transport at /mcp/sse and /mcp/messages/)
app.mount("/mcp", create_mcp_sse_app())


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


@app.post("/api/v1/github/webhook")
async def api_github_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_github_event: str | None = Header(default="push", alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
):
    """Menerima webhook dari GitHub untuk integrasi otomatis materi-kuliah, thesis-manuscripts, & thesis-experiments."""
    import hashlib
    import hmac

    raw_body = await request.body()

    # Verifikasi Secret jika dikonfigurasi
    secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
    if secret:
        if not x_hub_signature_256 or not x_hub_signature_256.startswith("sha256="):
            raise HTTPException(status_code=401, detail="Header X-Hub-Signature-256 tidak valid")
        expected_sig = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(x_hub_signature_256, expected_sig):
            raise HTTPException(status_code=401, detail="Tanda tangan GitHub Webhook tidak cocok")

    # Handle Ping event dari setup webhook GitHub
    if x_github_event == "ping":
        return {
            "status": "pong",
            "message": "GitHub Webhook Second Brain aktif dan terhubung!",
        }

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    repo_info = payload.get("repository", {})
    repo_name = repo_info.get("name") or "unknown-repo"
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref

    pusher = payload.get("pusher", {})
    pusher_email = pusher.get("email")

    commits = payload.get("commits")
    if not commits and payload.get("head_commit"):
        commits = [payload["head_commit"]]

    if not commits:
        return {
            "status": "ignored",
            "reason": "no_commits_found",
            "repo": repo_name,
            "event": x_github_event,
        }

    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    results = []

    for c in commits:
        commit_msg = c.get("message", "")
        author_email = (
            c.get("author", {}).get("email")
            or pusher_email
            or "fransalwanpurba@mail.ugm.ac.id"
        )
        res = await handle_git_commit_event(
            session=session,
            email=author_email,
            commit_message=commit_msg,
            repo_name=repo_name,
            branch=branch,
            notify_telegram=True,
            bot=bot,
        )
        results.append(res)

    return {
        "status": "success",
        "processed_commits": len(results),
        "repo": repo_name,
        "branch": branch,
        "details": results,
    }


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


class ThesisSyncRequest(BaseModel):
    email: str
    experiments_data: dict | None = None
    manuscripts_data: dict | None = None
    notify_telegram: bool = True


@app.post("/api/v1/ambient/thesis/sync")
async def api_thesis_sync(
    payload: ThesisSyncRequest,
    _auth: bool = Depends(verify_ambient_key),
    session: AsyncSession = Depends(get_session),
):
    """Menerima sinkronisasi otomatis dari repo thesis-experiments dan thesis-manuscripts."""
    bot = ptb_app.bot if ptb_app and ptb_app.bot else None
    result = await handle_thesis_sync(
        session=session,
        email=payload.email,
        experiments_data=payload.experiments_data,
        manuscripts_data=payload.manuscripts_data,
        notify_telegram=payload.notify_telegram,
        bot=bot,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


# ==========================================
# RAG & SEMANTIC SEARCH ENDPOINTS (AI ENGINE)
# ==========================================
class RagSearchRequest(BaseModel):
    email: str
    query: str
    top_k: int = 5


class RagAskRequest(BaseModel):
    email: str
    question: str


class RagIndexRequest(BaseModel):
    email: str
    note_id: int | None = None


@app.post("/api/v1/rag/search")
async def api_rag_search(
    payload: RagSearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """Pencarian Hibrida Semantik (BM25 + pgvector RRF) atas catatan Second Brain."""
    from .models import Profile
    from .rag import hybrid_search_notes
    prof_res = await session.execute(select(Profile).where(Profile.email == payload.email))
    profile = prof_res.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"User dengan email {payload.email} tidak ditemukan")

    results = await hybrid_search_notes(session, profile.id, payload.query, top_k=payload.top_k)
    return {"status": "success", "count": len(results), "query": payload.query, "results": results}


@app.post("/api/v1/rag/ask")
async def api_rag_ask(
    payload: RagAskRequest,
    session: AsyncSession = Depends(get_session),
):
    """Menjawab pertanyaan berbasis RAG (Retrieval-Augmented Generation) berdasar konteks catatan pribadi."""
    from .models import Profile
    from .rag import answer_with_second_brain
    prof_res = await session.execute(select(Profile).where(Profile.email == payload.email))
    profile = prof_res.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"User dengan email {payload.email} tidak ditemukan")

    return await answer_with_second_brain(session, profile.id, payload.question)


@app.post("/api/v1/rag/index")
async def api_rag_index(
    payload: RagIndexRequest,
    session: AsyncSession = Depends(get_session),
):
    """Melakukan kalkulasi dan penyimpanan embedding vektor catatan ke dalam database."""
    from .models import Profile, Note
    from .rag import index_note_embedding
    prof_res = await session.execute(select(Profile).where(Profile.email == payload.email))
    profile = prof_res.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"User dengan email {payload.email} tidak ditemukan")

    if payload.note_id:
        note = await session.get(Note, payload.note_id)
        if not note or note.user_id != profile.id:
            raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
        emb = await index_note_embedding(session, note.id, profile.id, note.content)
        return {"status": "success", "indexed_count": 1, "note_id": note.id}
    else:
        notes_res = await session.execute(select(Note).where(Note.user_id == profile.id))
        all_notes = notes_res.scalars().all()
        for n in all_notes:
            await index_note_embedding(session, n.id, profile.id, n.content)
        return {"status": "success", "indexed_count": len(all_notes)}


@app.post("/api/v1/notes/upload-visual")
async def api_upload_visual_note(
    file: UploadFile = File(...),
    email: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
):
    """Menerima berkas gambar (PNG, JPEG, WebP, PDF) untuk dianalisis oleh Gemini VLM (Vision Language Model).
    Melakukan OCR cerdas terhadap tulisan tangan / slide, mengekstrak insight grafik riset (CatBoost/loss/F1),
    dan otomatis mengindeksnya ke RAG pgvector + RAPTOR.
    """
    allowed_types = ["image/png", "image/jpeg", "image/webp", "image/jpg", "application/pdf"]
    content_type = file.content_type or "image/png"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Format file '{content_type}' tidak didukung. Harap upload format gambar (PNG, JPEG, WebP) atau PDF.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File kosong tidak dapat diproses.")

    from .models import Profile
    from .multimodal import process_and_save_visual_document
    from uuid import uuid4

    profile = None
    if email:
        prof_res = await session.execute(select(Profile).where(Profile.email == email))
        profile = prof_res.scalars().first()

    if not profile:
        prof_res = await session.execute(select(Profile).limit(1))
        profile = prof_res.scalars().first()

    if not profile:
        profile = Profile(id=uuid4(), email="student@ugm.ac.id", full_name="Student UGM")
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

    result = await process_and_save_visual_document(
        session=session,
        user_id=profile.id,
        file_bytes=file_bytes,
        filename=file.filename or "visual_document.png",
        mime_type=content_type,
    )
    return {"status": "success", "data": result}

