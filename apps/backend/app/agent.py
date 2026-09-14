from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, func, select
from .database import SessionLocal
from .models import ChatHistory, Note, TimeLog, utcnow
from .config import settings

APP_NAME = "second_brain"
GEMINI_MODEL = settings.GEMINI_MODEL
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(LOCAL_TZ).strftime("%d %b %Y %H:%M")


def _user_id(tool_context: ToolContext) -> UUID:
    return UUID(tool_context.user_id)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
async def save_note(content: str, tags: list[str], tool_context: ToolContext) -> dict:
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
    return {"status": "success", "note_id": str(note.id), "tags": note.tags}


async def search_notes(keyword: str, tool_context: ToolContext) -> dict:
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
            {"content": n.content, "tags": n.tags, "created_at": _fmt(n.created_at)}
            for n in notes
        ],
    }


async def start_timer(project_name: str, tool_context: ToolContext) -> dict:
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
            }

        log = TimeLog(user_id=user_id, project_name=project_name.strip())
        session.add(log)
        try:
            await session.commit()
        except IntegrityError:
            return {"status": "error", "reason": "timer_already_running"}
        await session.refresh(log)
    return {
        "status": "success",
        "project": log.project_name,
        "started_at": _fmt(log.started_at),
    }


async def stop_timer(tool_context: ToolContext) -> dict:
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
    user_id = _user_id(tool_context)
    now_local = datetime.now(LOCAL_TZ)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        start_local -= timedelta(days=start_local.weekday())

    async with SessionLocal() as session:
        per_project = await session.execute(
            select(TimeLog.project_name, func.sum(TimeLog.duration_minutes))
            .where(
                TimeLog.user_id == user_id,
                TimeLog.started_at >= start_local,
                col(TimeLog.ended_at).is_not(None),
            )
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
        "running_timer": {
            "project": running.project_name,
            "started_at": _fmt(running.started_at),
        }
        if running
        else None,
        "notes_count": len(notes),
        "latest_notes": [n.content for n in notes[:5]],
    }


# ---------------------------------------------------------------------------
# Agent & Runner
# ---------------------------------------------------------------------------
INSTRUCTION = """
            Kamu adalah asisten "second brain" pribadi di Telegram. Tugasmu menangkap ide tanpa hambatan dan melacak waktu deep work.
            Aturan:
            1. Jika pesan berisi ide/catatan: panggil save_note.
            2. Mulai fokus: start_timer.
            3. Selesai: stop_timer.
            4. Rekap: get_summary.
            5. Cari: search_notes.
            Gaya balasan: singkat, teks polos tanpa markdown.
            """

root_agent = Agent(
    name="second_brain_agent",
    model=GEMINI_MODEL,
    description="Asisten second brain.",
    instruction=INSTRUCTION,
    tools=[save_note, search_notes, start_timer, stop_timer, get_summary],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


async def run_agent(user_id: UUID, chat_id: int, text: str) -> str:
    """Kirim satu pesan user ke agent, simpan riwayat, dan kembalikan balasan."""
    uid = str(user_id)
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

    final_reply = reply.strip() or "✅ Beres."
    try:
        async with SessionLocal() as db_session:
            db_session.add(ChatHistory(user_id=user_id, role="user", content=text))
            db_session.add(
                ChatHistory(user_id=user_id, role="assistant", content=final_reply)
            )
            await db_session.commit()
            print(f"[INFO] Chat history saved: user={user_id}, text={text[:50]}")
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan chat history: {e}")
        import traceback

        traceback.print_exc()

    return final_reply
