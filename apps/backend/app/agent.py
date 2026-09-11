# apps/backend/app/agent.py
import os
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, func, select

from .database import SessionLocal
from .models import Note, TimeLog, utcnow

load_dotenv()

APP_NAME = "second_brain"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
LOCAL_TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Jakarta"))


def _fmt(dt: datetime) -> str:
    return dt.astimezone(LOCAL_TZ).strftime("%d %b %Y %H:%M")


def _user_id(tool_context: ToolContext) -> UUID:
    # user_id datang dari backend (runner), BUKAN dari argumen yang diisi LLM.
    # Jadi agent tidak mungkin membaca/menulis data user lain.
    return UUID(tool_context.user_id)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def save_note(content: str, tags: list[str], tool_context: ToolContext) -> dict:
    """Menyimpan catatan, ide, tugas, atau informasi dari user.

    Args:
        content: Isi catatan yang sudah dirapikan, tanpa kata perintah seperti "catet:".
        tags: 1-3 tag pendek huruf kecil yang menggambarkan topik, misalnya ["vue", "belajar"].
    """
    async with SessionLocal() as session:
        note = Note(
            user_id=_user_id(tool_context),
            content=content.strip(),
            tags=[t.strip().lower() for t in tags if t.strip()][:3] or None,
            source="telegram",
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)
    return {"status": "success", "note_id": note.id, "tags": note.tags}


async def search_notes(keyword: str, tool_context: ToolContext) -> dict:
    """Mencari catatan user berdasarkan kata kunci (maksimal 10 hasil terbaru).

    Args:
        keyword: Satu kata atau frasa pendek yang dicari di isi catatan.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Note)
            .where(Note.user_id == _user_id(tool_context))
            .where(col(Note.content).ilike(f"%{keyword}%"))
            .order_by(col(Note.created_at).desc())
            .limit(10)
        )
        notes = result.scalars().all()
    return {
        "status": "success",
        "count": len(notes),
        "notes": [
            {
                "id": n.id,
                "content": n.content,
                "tags": n.tags,
                "created_at": _fmt(n.created_at),
            }
            for n in notes
        ],
    }


async def start_timer(project_name: str, tool_context: ToolContext) -> dict:
    """Memulai timer sesi deep work. Hanya boleh ada satu timer aktif per user.

    Args:
        project_name: Nama proyek atau aktivitas, misalnya "second brain backend".
    """
    user_id = _user_id(tool_context)
    async with SessionLocal() as session:
        result = await session.execute(
            select(TimeLog).where(
                TimeLog.user_id == user_id, col(TimeLog.ended_at).is_(None)
            )
        )
        running = result.scalars().first()
        if running:
            return {
                "status": "error",
                "reason": "timer_already_running",
                "running_project": running.project_name,
                "started_at": _fmt(running.started_at),
            }

        log = TimeLog(user_id=user_id, project_name=project_name.strip())
        session.add(log)
        try:
            await session.commit()
        except IntegrityError:
            # Balapan dua pesan sekaligus; unique index di DB yang menahan
            return {"status": "error", "reason": "timer_already_running"}
        await session.refresh(log)
    return {
        "status": "success",
        "project": log.project_name,
        "started_at": _fmt(log.started_at),
    }


async def stop_timer(tool_context: ToolContext) -> dict:
    """Menghentikan timer deep work yang sedang berjalan dan mencatat durasinya."""
    user_id = _user_id(tool_context)
    async with SessionLocal() as session:
        result = await session.execute(
            select(TimeLog).where(
                TimeLog.user_id == user_id, col(TimeLog.ended_at).is_(None)
            )
        )
        running = result.scalars().first()
        if running is None:
            return {"status": "error", "reason": "no_running_timer"}

        running.ended_at = utcnow()
        running.duration_minutes = int(
            (running.ended_at - running.started_at).total_seconds() // 60
        )
        project, minutes = running.project_name, running.duration_minutes
        await session.commit()
    return {"status": "success", "project": project, "duration_minutes": minutes}


async def get_summary(period: str, tool_context: ToolContext) -> dict:
    """Ringkasan deep work dan catatan user untuk periode tertentu.

    Args:
        period: "today" untuk hari ini, atau "week" untuk minggu ini (mulai Senin).
    """
    user_id = _user_id(tool_context)
    now_local = datetime.now(LOCAL_TZ)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        start_local -= timedelta(days=start_local.weekday())

    async with SessionLocal() as session:
        per_project = await session.execute(
            select(TimeLog.project_name, func.sum(TimeLog.duration_minutes))
            .where(TimeLog.user_id == user_id)
            .where(TimeLog.started_at >= start_local)
            .where(col(TimeLog.ended_at).is_not(None))
            .group_by(TimeLog.project_name)
        )
        running = (
            (
                await session.execute(
                    select(TimeLog).where(
                        TimeLog.user_id == user_id, col(TimeLog.ended_at).is_(None)
                    )
                )
            )
            .scalars()
            .first()
        )
        notes = (
            (
                await session.execute(
                    select(Note)
                    .where(Note.user_id == user_id, Note.created_at >= start_local)
                    .order_by(col(Note.created_at).desc())
                )
            )
            .scalars()
            .all()
        )

    projects = {name: int(total or 0) for name, total in per_project.all()}
    return {
        "status": "success",
        "period": period,
        "since": _fmt(start_local),
        "total_deep_work_minutes": sum(projects.values()),
        "minutes_per_project": projects,
        "running_timer": (
            {"project": running.project_name, "started_at": _fmt(running.started_at)}
            if running
            else None
        ),
        "notes_count": len(notes),
        "latest_notes": [n.content for n in notes[:10]],
    }


# ---------------------------------------------------------------------------
# Agent & Runner
# ---------------------------------------------------------------------------

INSTRUCTION = """
Kamu adalah asisten "second brain" pribadi di Telegram. Tugasmu menangkap ide
tanpa hambatan dan melacak waktu deep work.

Aturan:
- Jika pesan berisi ide, catatan, tugas, link, atau informasi apa pun: langsung
  panggil save_note. Jangan minta konfirmasi. Rapikan ejaan seperlunya tanpa
  mengubah makna.
- Jika user ingin mulai fokus/kerja/ngoding: panggil start_timer.
- Jika user selesai/berhenti/istirahat: panggil stop_timer.
- Jika user bertanya progres, rekap, atau ringkasan: panggil get_summary.
- Jika user mencari catatan lama: panggil search_notes.
- Jika ragu apakah pesan itu catatan atau obrolan, anggap sebagai catatan.
- Jangan pernah mengarang data. Semua angka dan isi catatan harus dari hasil tool.
- Jika tool mengembalikan status "error", jelaskan singkat ke user apa yang terjadi.

Gaya balasan: singkat (1-3 kalimat), bahasa yang sama dengan user, teks polos
tanpa format Markdown. Untuk ringkasan, boleh pakai beberapa baris.
"""

root_agent = Agent(
    name="second_brain_agent",
    model=GEMINI_MODEL,
    description="Asisten second brain untuk mencatat ide dan melacak deep work.",
    instruction=INSTRUCTION,
    tools=[save_note, search_notes, start_timer, stop_timer, get_summary],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


async def run_agent(user_id: UUID, chat_id: int, text: str) -> str:
    """Kirim satu pesan user ke agent dan kembalikan balasan akhirnya."""
    uid = str(user_id)
    # Satu sesi percakapan per chat per hari, supaya konteks tidak menumpuk tanpa batas
    session_id = f"{chat_id}-{datetime.now(LOCAL_TZ):%Y%m%d}"

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=uid, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=uid, session_id=session_id
        )

    message = types.Content(role="user", parts=[types.Part(text=text)])
    reply = ""
    async for event in runner.run_async(
        user_id=uid, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(part.text or "" for part in event.content.parts)
    return reply.strip() or "✅ Beres."
