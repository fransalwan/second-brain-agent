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
from .models import Area, ChatHistory, Note, Task, TimeLog, utcnow
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
    period = (period or "").strip().lower()
    is_week = period in {"week", "weekly", "minggu", "minggu ini", "this week"}
    if is_week:
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
# Area Tools
# ---------------------------------------------------------------------------
async def set_areas(names: list[str], tool_context: ToolContext) -> dict:
    user_id = _user_id(tool_context)
    cleaned = [n.strip() for n in names if n.strip()]
    if not cleaned:
        return {
            "status": "error",
            "reason": "empty_names",
            "message": "Daftar nama area tidak boleh kosong.",
        }

    async with SessionLocal() as session:
        existing = await session.execute(select(Area).where(Area.user_id == user_id))
        if existing.scalars().first() is not None:
            return {
                "status": "error",
                "reason": "already_configured",
                "message": "Kamu sudah memiliki area terdaftar. Area hanya dapat diatur sekaligus saat akun belum memiliki area sama sekali. Jika ingin menambah area baru, kirim 'tambah area <nama>'. Jika ingin mengubah urutan, kirim 'ubah urutan area: <daftar area>'.",
            }

        areas = []
        for idx, name in enumerate(cleaned, start=1):
            area = Area(user_id=user_id, name=name, position=idx)
            session.add(area)
            areas.append(area)
        await session.commit()
        for a in areas:
            await session.refresh(a)

    return {
        "status": "success",
        "count": len(areas),
        "areas": [{"id": a.id, "name": a.name, "position": a.position} for a in areas],
    }


async def list_areas(tool_context: ToolContext) -> dict:
    user_id = _user_id(tool_context)
    async with SessionLocal() as session:
        result = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position.asc())
        )
        areas = result.scalars().all()

    return {
        "status": "success",
        "count": len(areas),
        "areas": [{"id": a.id, "name": a.name, "position": a.position} for a in areas],
    }


async def add_area(name: str, tool_context: ToolContext) -> dict:
    user_id = _user_id(tool_context)
    name = name.strip()
    if not name:
        return {
            "status": "error",
            "reason": "empty_name",
            "message": "Nama area tidak boleh kosong.",
        }

    async with SessionLocal() as session:
        existing = await session.execute(
            select(Area).where(
                Area.user_id == user_id,
                func.lower(Area.name) == name.lower(),
            )
        )
        if existing.scalars().first() is not None:
            return {
                "status": "error",
                "reason": "already_exists",
                "message": f"Area '{name}' sudah ada.",
            }

        result = await session.execute(
            select(func.coalesce(func.max(Area.position), 0)).where(
                Area.user_id == user_id
            )
        )
        max_pos = result.scalar_one()

        area = Area(user_id=user_id, name=name, position=max_pos + 1)
        session.add(area)
        await session.commit()
        await session.refresh(area)

    return {
        "status": "success",
        "area": {"id": area.id, "name": area.name, "position": area.position},
    }


async def reorder_areas(ordered_names: list[str], tool_context: ToolContext) -> dict:
    user_id = _user_id(tool_context)
    cleaned_input = [n.strip() for n in ordered_names if n.strip()]
    if not cleaned_input:
        return {
            "status": "error",
            "reason": "empty_names",
            "message": "Daftar nama area baru tidak boleh kosong.",
        }

    async with SessionLocal() as session:
        result = await session.execute(select(Area).where(Area.user_id == user_id))
        existing_areas = result.scalars().all()
        if not existing_areas:
            return {
                "status": "error",
                "reason": "no_areas",
                "message": "Kamu belum memiliki area terdaftar. Gunakan set_areas terlebih dahulu.",
            }

        name_to_area = {a.name.lower(): a for a in existing_areas}
        reordered = []
        seen_ids = set()

        for name in cleaned_input:
            key = name.lower()
            if key in name_to_area and name_to_area[key].id not in seen_ids:
                area = name_to_area[key]
                reordered.append(area)
                seen_ids.add(area.id)

        # Pertahankan area yang tidak tercantum dalam input di urutan belakang
        for area in sorted(existing_areas, key=lambda a: a.position):
            if area.id not in seen_ids:
                reordered.append(area)
                seen_ids.add(area.id)

        for idx, area in enumerate(reordered, start=1):
            area.position = idx
            session.add(area)

        await session.commit()
        for a in reordered:
            await session.refresh(a)

    return {
        "status": "success",
        "count": len(reordered),
        "areas": [
            {"id": a.id, "name": a.name, "position": a.position} for a in reordered
        ],
    }


async def delete_area(name: str, tool_context: ToolContext) -> dict:
    user_id = _user_id(tool_context)
    name = name.strip()
    if not name:
        return {
            "status": "error",
            "reason": "empty_name",
            "message": "Nama area tidak boleh kosong.",
        }

    async with SessionLocal() as session:
        result = await session.execute(
            select(Area).where(
                Area.user_id == user_id,
                func.lower(Area.name) == name.lower(),
            )
        )
        area = result.scalars().first()
        if area is None:
            return {
                "status": "error",
                "reason": "not_found",
                "message": f"Area '{name}' tidak ditemukan.",
            }

        # Jangan hapus area kalau masih punya tugas pending
        pending_result = await session.execute(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.area_id == area.id,
                Task.status == "pending",
            )
        )
        pending_count = pending_result.scalar_one()
        if pending_count > 0:
            return {
                "status": "error",
                "reason": "has_pending_tasks",
                "message": f"Area '{area.name}' tidak dapat dihapus karena masih memiliki {pending_count} tugas pending. Selesaikan atau pindahkan tugas tersebut terlebih dahulu.",
            }

        await session.delete(area)

        # Rapatkan kembali urutan area yang tersisa
        remaining = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position.asc())
        )
        for idx, a in enumerate(remaining.scalars().all(), start=1):
            a.position = idx
            session.add(a)

        await session.commit()

    return {
        "status": "success",
        "message": f"Area '{area.name}' berhasil dihapus.",
    }


# ---------------------------------------------------------------------------
# Agent & Runner
# ---------------------------------------------------------------------------
INSTRUCTION = """
            Kamu adalah asisten "second brain" pribadi di Telegram. Tugasmu mengelola area hidup, menangkap ide tanpa hambatan, dan melacak waktu deep work.
            Aturan:
            1. Penolakan tool adalah final (PENTING):
               Jika pemanggilan tool menghasilkan error atau penolakan (misal status='error' pada set_areas atau delete_area):
               - JANGAN PERNAH mencoba memanggil tool lain secara otomatis di giliran yang sama.
               - Langsung sampaikan isi pesan penolakan tersebut kepada pengguna apa adanya dan tunggu keputusan pengguna di pesan berikutnya.
            2. Area hidup:
               - Pengguna menentukan daftar area pertama kali: panggil set_areas(names=[...]). Ingat: set_areas hanya untuk setup awal saat belum punya area.
               - Melihat daftar area: panggil list_areas().
               - Menambah area baru: panggil add_area(name=...).
               - Mengubah urutan prioritas area: panggil reorder_areas(ordered_names=[...]).
               - Menghapus area: panggil delete_area(name=...). Jangan hapus jika masih punya tugas pending.
            3. Jika pesan berisi ide/catatan: panggil save_note.
            4. Mulai fokus: start_timer.
            5. Selesai: stop_timer.
            6. Rekap: panggil get_summary dengan period="day" untuk hari ini, atau period="week" untuk minggu ini. Hanya dua nilai itu yang valid.
            7. Cari catatan: search_notes.
            Gaya balasan: singkat, teks polos tanpa markdown. Sebutkan urutan nomor saat menampilkan area.
            """

root_agent = Agent(
    name="second_brain_agent",
    model=GEMINI_MODEL,
    description="Asisten second brain.",
    instruction=INSTRUCTION,
    tools=[
        save_note,
        search_notes,
        start_timer,
        stop_timer,
        get_summary,
        set_areas,
        list_areas,
        add_area,
        reorder_areas,
        delete_area,
    ],
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
