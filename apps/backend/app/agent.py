from datetime import date, datetime, time, timedelta
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
from .habits import check_habit_for_today, get_user_habits_status
from .models import (
    Area,
    ChatHistory,
    Habit,
    HabitLog,
    Note,
    Profile,
    Task,
    TimeLog,
    utcnow,
)
from .scheduler import is_past_night_cutoff
from .recharge import (
    YOUTUBE_MUSIC_PLAYLISTS,
    build_shopeefood_url,
    get_random_activity,
    get_random_movie,
)
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

        profile = await session.get(Profile, user_id)
        night_cutoff = (
            profile.night_cutoff_time
            if (profile and profile.night_cutoff_time)
            else time(23, 0)
        )
        now_local = datetime.now(LOCAL_TZ)
        is_late_night = is_past_night_cutoff(now_local.time(), night_cutoff)

        log = TimeLog(
            user_id=user_id,
            project_name=project_name.strip(),
            night_warning_sent=is_late_night,
        )
        session.add(log)
        try:
            await session.commit()
        except IntegrityError:
            return {"status": "error", "reason": "timer_already_running"}
        await session.refresh(log)

    res = {
        "status": "success",
        "project": log.project_name,
        "started_at": _fmt(log.started_at),
    }
    if is_late_night:
        cutoff_str = night_cutoff.strftime("%H:%M")
        curr_str = now_local.strftime("%H:%M")
        warning_msg = (
            f"⚠️ Peringatan: Sekarang sudah larut malam (pukul {curr_str}, "
            f"melewati batas jam kerja {cutoff_str}). Jangan lupa jaga kesehatan dan segera istirahat!"
        )
        res["night_warning"] = warning_msg
        res["message"] = (
            f"Timer untuk '{log.project_name}' dimulai pada {_fmt(log.started_at)}. {warning_msg}"
        )
    return res


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
# Task Tools
# ---------------------------------------------------------------------------
async def add_task(
    title: str,
    area_name: str,
    deadline: str | None = None,
    is_urgent: bool = False,
    tool_context: ToolContext = None,
) -> dict:
    user_id = _user_id(tool_context)
    title = (title or "").strip()
    if not title:
        return {
            "status": "error",
            "reason": "empty_title",
            "message": "Judul tugas tidak boleh kosong.",
        }

    parsed_deadline = None
    if deadline:
        deadline_str = str(deadline).strip()
        if deadline_str and deadline_str.lower() not in ("none", "null"):
            try:
                parsed_deadline = date.fromisoformat(deadline_str)
            except (ValueError, TypeError):
                return {
                    "status": "error",
                    "reason": "invalid_date_format",
                    "message": f"Format deadline '{deadline}' tidak valid. Gunakan format ISO YYYY-MM-DD.",
                }

    async with SessionLocal() as session:
        areas_res = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position.asc())
        )
        user_areas = areas_res.scalars().all()
        if not user_areas:
            return {
                "status": "error",
                "reason": "no_areas_configured",
                "message": (
                    "Kamu belum membuat area hidup. Di Second Brain, setiap tugas "
                    "perlu masuk ke suatu area agar bisa diprioritaskan. "
                    "Mau buat area apa saja? (Contoh: kirim 'area saya: Kuliah, Usaha, Pribadi')"
                ),
            }

        target_area = None
        clean_area_name = (area_name or "").strip().lower()
        for a in user_areas:
            if a.name.lower() == clean_area_name:
                target_area = a
                break

        if target_area is None:
            valid_names = ", ".join(f"'{a.name}'" for a in user_areas)
            return {
                "status": "error",
                "reason": "area_not_found",
                "message": f"Area '{area_name}' tidak ditemukan. Area yang kamu miliki: {valid_names}.",
            }

        task = Task(
            user_id=user_id,
            area_id=target_area.id,
            title=title,
            deadline=parsed_deadline,
            is_urgent=bool(is_urgent),
            status="pending",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

    return {
        "status": "success",
        "task": {
            "id": task.id,
            "title": task.title,
            "area_name": target_area.name,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "is_urgent": task.is_urgent,
        },
    }


async def mark_urgent(
    task_id: int,
    is_urgent: bool = True,
    tool_context: ToolContext = None,
) -> dict:
    user_id = _user_id(tool_context)
    try:
        clean_id = int(str(task_id).lstrip("#").strip())
    except (ValueError, TypeError):
        return {
            "status": "error",
            "reason": "invalid_id",
            "message": "ID tugas harus berupa angka.",
        }

    async with SessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.id == clean_id, Task.user_id == user_id)
        )
        task = result.scalars().first()
        if task is None:
            return {
                "status": "error",
                "reason": "not_found",
                "message": f"Tugas #{clean_id} tidak ditemukan.",
            }

        task.is_urgent = bool(is_urgent)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        title = task.title

    status_str = "mendesak" if task.is_urgent else "biasa"
    return {
        "status": "success",
        "task_id": clean_id,
        "title": title,
        "is_urgent": task.is_urgent,
        "message": f"Tugas #{clean_id} ('{title}') ditandai sebagai {status_str}.",
    }


# ---------------------------------------------------------------------------
# Habit Tools
# ---------------------------------------------------------------------------
async def add_habit(name: str, tool_context: ToolContext = None) -> dict:
    user_id = _user_id(tool_context)
    name = (name or "").strip()
    if not name:
        return {
            "status": "error",
            "reason": "empty_name",
            "message": "Nama habit tidak boleh kosong.",
        }

    async with SessionLocal() as session:
        existing = await session.execute(
            select(Habit).where(
                Habit.user_id == user_id,
                func.lower(Habit.name) == name.lower(),
                Habit.is_active.is_(True),
            )
        )
        if existing.scalars().first():
            return {
                "status": "error",
                "reason": "already_exists",
                "message": f"Habit '{name}' sudah ada.",
            }

        max_pos_res = await session.execute(
            select(func.coalesce(func.max(Habit.position), 0)).where(
                Habit.user_id == user_id
            )
        )
        max_pos = max_pos_res.scalar_one()

        habit = Habit(user_id=user_id, name=name, position=max_pos + 1)
        session.add(habit)
        await session.commit()
        await session.refresh(habit)

    return {
        "status": "success",
        "habit": {"id": habit.id, "name": habit.name},
        "message": f"Habit '{habit.name}' berhasil ditambahkan.",
    }


async def list_habits(tool_context: ToolContext = None) -> dict:
    user_id = _user_id(tool_context)
    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        habits_status = await get_user_habits_status(session, user_id, today)

    if not habits_status:
        return {
            "status": "success",
            "habits": [],
            "message": "Kamu belum memiliki habit terdaftar.",
        }

    return {
        "status": "success",
        "habits": [
            {
                "id": h.habit.id,
                "name": h.habit.name,
                "is_completed_today": h.is_completed_today,
                "streak": h.streak,
            }
            for h in habits_status
        ],
    }


async def check_habit(name_or_id: str, tool_context: ToolContext = None) -> dict:
    user_id = _user_id(tool_context)
    clean_val = str(name_or_id).strip()
    if not clean_val:
        return {
            "status": "error",
            "reason": "empty_input",
            "message": "Sebutkan nama atau ID habit yang ingin dicentang.",
        }

    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        target_habit = None
        if clean_val.lstrip("#").isdigit():
            hid = int(clean_val.lstrip("#"))
            target_habit = await session.get(Habit, hid)
            if target_habit and (
                target_habit.user_id != user_id or not target_habit.is_active
            ):
                target_habit = None
        else:
            res = await session.execute(
                select(Habit).where(
                    Habit.user_id == user_id,
                    Habit.is_active.is_(True),
                    func.lower(Habit.name).like(f"%{clean_val.lower()}%"),
                )
            )
            target_habit = res.scalars().first()

        if target_habit is None:
            return {
                "status": "error",
                "reason": "not_found",
                "message": f"Habit '{clean_val}' tidak ditemukan.",
            }

        habit, already_done, streak = await check_habit_for_today(
            session, user_id, target_habit.id, today
        )

    streak_str = (
        f" 🔥 {streak} hari berturut-turut!"
        if streak > 1
        else (" 🔥 Hari ke-1!" if streak == 1 else "")
    )
    if already_done:
        msg = f"Habit '{habit.name}' sudah dicentang hari ini.{streak_str}"
    else:
        msg = f"✅ Beres! Habit '{habit.name}' berhasil dicentang hari ini.{streak_str}"

    return {
        "status": "success",
        "habit_id": habit.id,
        "name": habit.name,
        "already_done": already_done,
        "streak": streak,
        "message": msg,
    }


async def delete_habit(name_or_id: str, tool_context: ToolContext = None) -> dict:
    user_id = _user_id(tool_context)
    clean_val = str(name_or_id).strip()
    if not clean_val:
        return {
            "status": "error",
            "reason": "empty_input",
            "message": "Sebutkan nama atau ID habit yang ingin dihapus.",
        }

    async with SessionLocal() as session:
        target_habit = None
        if clean_val.lstrip("#").isdigit():
            hid = int(clean_val.lstrip("#"))
            target_habit = await session.get(Habit, hid)
            if target_habit and target_habit.user_id != user_id:
                target_habit = None
        else:
            res = await session.execute(
                select(Habit).where(
                    Habit.user_id == user_id,
                    func.lower(Habit.name) == clean_val.lower(),
                )
            )
            target_habit = res.scalars().first()

        if target_habit is None:
            return {
                "status": "error",
                "reason": "not_found",
                "message": f"Habit '{clean_val}' tidak ditemukan.",
            }

        target_habit.is_active = False
        session.add(target_habit)
        await session.commit()

    return {
        "status": "success",
        "message": f"Habit '{target_habit.name}' berhasil dinonaktifkan.",
    }


# ---------------------------------------------------------------------------
# Mode Jeda / Recharge Tool
# ---------------------------------------------------------------------------
async def get_recharge_suggestion(
    category: str = "all", tool_context: ToolContext = None
) -> dict:
    """Mengambil rekomendasi relaksasi (musik YouTube Music, kopi ShopeeFood, rekomendasi tontonan santai, atau ide aktivitas offline) saat pengguna merasa jenuh, stres, atau lelah."""
    cat = (category or "all").lower().strip()
    res = {
        "status": "success",
        "message": "Pikiran butuh jeda agar bisa kembali jernih dan segar.",
        "youtube_music": {
            "title": YOUTUBE_MUSIC_PLAYLISTS[0]["title"],
            "url": YOUTUBE_MUSIC_PLAYLISTS[0]["url"],
            "desc": YOUTUBE_MUSIC_PLAYLISTS[0]["desc"],
        },
        "shopeefood_coffee": {
            "preset": "Kopi Susu Gula Aren",
            "url": build_shopeefood_url("kopi susu gula aren"),
        },
    }
    if cat in {"movie", "film", "nonton", "all"}:
        m = get_random_movie()
        res["recommended_movie"] = {
            "title": m["title"],
            "type": m["type"],
            "platform": m["platform"],
            "reason": m["reason"],
        }
    if cat in {"activity", "hangout", "refresh", "all"}:
        a = get_random_activity()
        res["offline_activity"] = {
            "title": a["title"],
            "detail": a["detail"],
        }
    return res


# ---------------------------------------------------------------------------
# Agent & Dynamic Instruction Runner
# ---------------------------------------------------------------------------
INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def get_instruction(ctx: object = None) -> str:
    """Instruksi yang dihitung ulang dinamis di setiap request berdasarkan APP_TIMEZONE."""
    now_local = datetime.now(LOCAL_TZ)
    day_name = INDO_DAYS[now_local.weekday()]
    date_iso = now_local.strftime("%Y-%m-%d")
    date_human = now_local.strftime("%d %B %Y")

    return f"""Kamu adalah asisten "second brain" pribadi di Telegram. Tugasmu mengelola tugas, area hidup, menangkap ide tanpa hambatan, dan melacak waktu deep work.

KONTEKS WAKTU SAAT INI (APP_TIMEZONE: {settings.APP_TIMEZONE}):
- Hari ini: {day_name}, {date_human} (ISO: {date_iso})

Aturan Pengelolaan Tugas:
1. Menambah tugas: panggil add_task(title=..., area_name=..., deadline=..., is_urgent=...).
   - Format deadline HANYA boleh ISO YYYY-MM-DD atau None jika tanpa deadline.
   - Aturan konversi tanggal deadline relatif:
     * "hari ini" = {date_iso}
     * "besok" = 1 hari setelah hari ini
     * "lusa" = 2 hari setelah hari ini
     * Nama hari (misal "jumat", "senin", dll):
       - PENTING: Jika pengguna menyebut nama hari yang SAMA dengan hari ini (contoh: menyebut "jumat" saat hari ini {day_name}), gunakan tanggal HARI INI ({date_iso}). JANGAN gunakan minggu depan!
       - Jika pengguna menyebut "jumat depan" (ada kata "depan"), barulah dihitung 7 hari ke depan dari jumat ini.
   - Penentuan area tugas:
     * Gunakan area yang disebut pengguna (misal "tugas kuliah: ...").
     * Jika pengguna TIDAK menyebut area, tebak secara semantik dari daftar area pengguna yang ada (cocokkan konteks tugas).
     * Jika benar-benar ambigu dan tidak ada kecocokan, tanyakan kepada pengguna ingin dimasukkan ke area mana.
   - Balasan setelah menambah tugas WAJIB menyebutkan: area terpilih, nama hari, dan tanggal lengkap deadline (contoh: "Tugas dicatat di [Kuliah]: Revisi bab 2 (Deadline: Jumat, 25 Sep 2026)").
2. Menandai tugas mendesak:
   - Panggil mark_urgent(task_id=..., is_urgent=True).
3. Penolakan tool adalah final (PENTING):
   - Jika pemanggilan tool menghasilkan error atau penolakan (status="error", misal set_areas, delete_area, add_task):
     * JANGAN PERNAH mencoba memanggil tool lain secara otomatis di giliran yang sama.
     * Langsung sampaikan isi pesan penolakan tersebut kepada pengguna apa adanya dan tunggu keputusan pengguna di pesan berikutnya.
4. Area hidup:
   - Pengguna menentukan daftar area pertama kali: panggil set_areas(names=[...]). Hanya untuk setup awal saat belum punya area.
   - Melihat daftar area: panggil list_areas().
   - Menambah area baru: panggil add_area(name=...).
   - Mengubah urutan prioritas area: panggil reorder_areas(ordered_names=[...]).
   - Menghapus area: panggil delete_area(name=...). Jangan hapus jika masih punya tugas pending.
5. Jika pesan berisi ide/catatan: panggil save_note.
6. Mulai fokus: start_timer. Jika respons mengandung night_warning, sertakan pesan pengingat tersebut kepada pengguna dengan ramah dan peduli agar segera istirahat.
7. Selesai: stop_timer.
8. Rekap: panggil get_summary dengan period="day" untuk hari ini, atau period="week" untuk minggu ini. Hanya dua nilai itu yang valid.
9. Cari catatan: search_notes.
10. Habit harian:
    - Menambah habit baru: panggil add_habit(name=...).
    - Melihat daftar habit: panggil list_habits().
    - Mencentang habit: panggil check_habit(name_or_id=...).
    - Menghapus habit: panggil delete_habit(name_or_id=...).
11. Mode Jeda & Empati Kelelahan (PENTING):
    - Jika pengguna mengeluh lelah, jenuh, penat, pusing, ingin ngopi, atau butuh refreshing ("jenuh", "burnout", "capek banget", "pengen ngopi", "pusing"):
      * JANGAN menyuruh pengguna mengerjakan tugas atau menagih deadline.
      * Berikan balasan yang hangat, suportif, dan dorong pengguna untuk istirahat sejenak.
      * Panggil get_recharge_suggestion untuk menyertakan tautan musik YouTube Music, link pesan kopi di ShopeeFood, rekomendasi tontonan, atau ide hangout santai.
      * Beri tahu pengguna bahwa mereka juga bisa mengetik /chill kapan saja untuk membuka menu jeda interaktif.

Gaya balasan: singkat, teks polos tanpa markdown. Sebutkan urutan nomor saat menampilkan area."""


root_agent = Agent(
    name="second_brain_agent",
    model=GEMINI_MODEL,
    description="Asisten second brain.",
    instruction=get_instruction,
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
        add_task,
        mark_urgent,
        add_habit,
        list_habits,
        check_habit,
        delete_habit,
        get_recharge_suggestion,
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
