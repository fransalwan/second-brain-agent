# apps/backend/app/ambient.py
"""Modul logika ambient tracking: pelacakan otomatis via OS watcher / VS Code."""

from datetime import datetime, time, timezone
import html
import logging
import re
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlmodel import col, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.constants import ParseMode

from .config import settings
from .habits import check_habit_for_today, get_user_habits_status
from .models import Area, Habit, HabitLog, Note, Profile, Task, TimeLog, utcnow
from .scheduler import is_past_night_cutoff

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _fmt_duration(minutes: int) -> str:
    """Format menit ke format jam dan menit yang ramah dibaca."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours} jam {mins} menit"
    elif hours > 0:
        return f"{hours} jam"
    return f"{mins} menit"


def _diff_seconds(t1: datetime, t2: datetime) -> float:
    """Hitung selisih detik antara t1 dan t2, aman untuk offset-naive (SQLite) & offset-aware (PostgreSQL)."""
    if t1.tzinfo is not None and t2.tzinfo is None:
        t2 = t2.replace(tzinfo=timezone.utc)
    elif t1.tzinfo is None and t2.tzinfo is not None:
        t1 = t1.replace(tzinfo=timezone.utc)
    return (t1 - t2).total_seconds()


async def get_profile_by_email(session: AsyncSession, email: str) -> Optional[Profile]:
    """Cari profil user berdasarkan email (case-insensitive)."""
    clean_email = email.strip().lower()
    res = await session.execute(select(Profile).where(Profile.email == clean_email))
    return res.scalars().first()


async def start_ambient_timer(
    session: AsyncSession,
    email: str,
    project_name: str,
    source: str = "vscode",
    context: Optional[str] = None,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memulai timer fokus secara otomatis dari ambient watcher."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_project = project_name.strip()
    if not clean_project:
        return {"status": "error", "message": "project_name tidak boleh kosong"}

    # Cek timer aktif saat ini
    res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res.scalars().first()

    # 1. Idempotent: jika project yang sama sudah berjalan, jangan buat timer ganda
    if running and running.project_name.lower() == clean_project.lower():
        now_utc = utcnow()
        elapsed_min = int(max(0, _diff_seconds(now_utc, running.started_at)) // 60)
        return {
            "status": "already_running",
            "project": running.project_name,
            "started_at": running.started_at.isoformat(),
            "elapsed_minutes": elapsed_min,
        }

    # 2. Context Switching: jika project lain sedang jalan, selesaikan dulu project lama
    switched_from = None
    if running:
        switched_from = running.project_name
        running.ended_at = utcnow()
        duration_sec = _diff_seconds(running.ended_at, running.started_at)
        if duration_sec < 60:
            # Sesi mikro kurang dari 1 menit -> abaikan
            await session.delete(running)
        else:
            running.duration_minutes = int(duration_sec // 60)
            session.add(running)
        await session.commit()

    # 3. Cek Night Cutoff (Bedtime Guardian)
    night_cutoff = (
        profile.night_cutoff_time if profile.night_cutoff_time else time(23, 0)
    )
    now_local = datetime.now(LOCAL_TZ)
    is_late_night = is_past_night_cutoff(now_local.time(), night_cutoff)

    # 4. Buat TimeLog baru
    new_timer = TimeLog(
        user_id=profile.id,
        project_name=clean_project,
        night_warning_sent=is_late_night,
    )
    session.add(new_timer)
    await session.commit()
    await session.refresh(new_timer)

    # 5. Notifikasi Telegram Pasif (jika user punya chat ID dan bot aktif)
    if notify_telegram and profile.telegram_chat_id and bot:
        try:
            msg = (
                f"⏱️ <b>[Auto-Timer]</b> Sesi fokus dimulai untuk: "
                f"<b>{html.escape(clean_project)}</b> (via {html.escape(source)})"
            )
            if context:
                msg += f"\n🎯 <i>Aktivitas: {html.escape(context)}</i>"
            if switched_from:
                msg += f"\n<i>(Menggantikan sesi sebelumnya: {html.escape(switched_from)})</i>"
            if is_late_night:
                cutoff_str = night_cutoff.strftime("%H:%M")
                curr_str = now_local.strftime("%H:%M")
                msg += (
                    f"\n\n⚠️ <i>Peringatan: Sekarang pukul {curr_str}, "
                    f"melewati batas jam kerja ({cutoff_str}). Jangan begadang ya!</i>"
                )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram ambient start: {e}")

    return {
        "status": "started",
        "project": new_timer.project_name,
        "started_at": new_timer.started_at.isoformat(),
        "is_late_night": is_late_night,
    }


async def stop_ambient_timer(
    session: AsyncSession,
    email: str,
    project_name: Optional[str] = None,
    reason: str = "window_closed",
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Menghentikan timer fokus secara otomatis saat window ditutup atau idle."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res.scalars().first()

    if not running:
        return {
            "status": "no_active_timer",
            "message": "Tidak ada timer yang sedang berjalan",
        }

    if project_name and running.project_name.lower() != project_name.strip().lower():
        return {
            "status": "ignored",
            "reason": "different_project_running",
            "running_project": running.project_name,
        }

    # Hitung durasi
    now_utc = utcnow()
    duration_sec = _diff_seconds(now_utc, running.started_at)
    project = running.project_name

    # Filter sesi mikro (< 60 detik)
    if duration_sec < 60:
        await session.delete(running)
        await session.commit()
        return {
            "status": "discarded",
            "project": project,
            "reason": "duration_too_short",
            "duration_seconds": int(duration_sec),
        }

    duration_min = int(duration_sec // 60)
    running.ended_at = now_utc
    running.duration_minutes = duration_min
    session.add(running)
    await session.commit()

    # Otomatis centang habit kerja/ngoding jika durasi memenuhi syarat (>= 15 menit)
    auto_habits = await auto_check_habits_on_focus(
        session=session,
        user_id=profile.id,
        project_name=project,
        duration_minutes=duration_min,
        min_minutes=15,
    )

    # Notifikasi ringkasan pasif jika durasi cukup berarti (>= 2 menit)
    if notify_telegram and profile.telegram_chat_id and bot and duration_min >= 2:
        try:
            dur_text = _fmt_duration(duration_min)
            reason_label = (
                "VS Code ditutup" if reason == "window_closed" else "Waktu idle / jeda"
            )
            msg = (
                f"⏱️ <b>[Auto-Timer]</b> Sesi fokus selesai: <b>{html.escape(project)}</b>\n"
                f"⏳ Durasi: <b>{dur_text}</b> ({reason_label})\n"
            )
            if auto_habits:
                msg += "🔥 <b>Habit Harian Otomatis Dicentang:</b>\n"
                for ah in auto_habits:
                    msg += f"• <b>{html.escape(ah['name'])}</b> (Streak: {ah['streak']} hari 🔥)\n"
            msg += "Data berhasil disinkronkan ke dashboard! 🎯"
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram ambient stop: {e}")

    return {
        "status": "stopped",
        "project": project,
        "duration_minutes": duration_min,
        "reason": reason,
        "auto_checked_habits": auto_habits,
    }


DEFAULT_WORK_HABIT_KEYWORDS = {
    "ngoding",
    "coding",
    "code",
    "fokus",
    "deep work",
    "kerja",
    "work",
    "project",
    "belajar",
    "riset",
    "program",
    "build",
}


async def auto_check_habits_on_focus(
    session: AsyncSession,
    user_id: UUID,
    project_name: str,
    duration_minutes: int,
    min_minutes: int = 15,
) -> list[dict]:
    """Mencari dan mencentang habit kerja/ngoding yang cocok jika durasi fokus memenuhi syarat."""
    if duration_minutes < min_minutes:
        return []

    today = datetime.now(LOCAL_TZ).date()
    statuses = await get_user_habits_status(session, user_id, today)

    project_words = {w.lower() for w in project_name.split() if len(w) > 2}

    checked = []
    for s in statuses:
        if s.is_completed_today:
            continue
        h_name_lower = s.habit.name.lower()
        is_match = any(kw in h_name_lower for kw in DEFAULT_WORK_HABIT_KEYWORDS) or any(
            pw in h_name_lower for pw in project_words
        )
        if is_match and s.habit.id is not None:
            habit, already_done, streak = await check_habit_for_today(
                session, user_id, s.habit.id, today
            )
            if habit and not already_done:
                checked.append(
                    {
                        "id": habit.id,
                        "name": habit.name,
                        "streak": streak,
                    }
                )
    return checked


async def check_habit_by_keyword(
    session: AsyncSession,
    email: str,
    habit_keyword: str,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Mencentang habit berdasarkan nama atau kata kunci (untuk trigger ambient mandiri)."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    today = datetime.now(LOCAL_TZ).date()
    statuses = await get_user_habits_status(session, profile.id, today)

    kw_lower = habit_keyword.strip().lower()
    target_status = None
    for s in statuses:
        if kw_lower in s.habit.name.lower():
            target_status = s
            break

    if not target_status or target_status.habit.id is None:
        return {
            "status": "not_found",
            "message": f"Tidak ditemukan habit aktif yang mengandung kata '{habit_keyword}'",
        }

    habit, already_done, streak = await check_habit_for_today(
        session, profile.id, target_status.habit.id, today
    )
    if not habit:
        return {"status": "error", "message": "Gagal memproses habit"}

    if notify_telegram and profile.telegram_chat_id and bot and not already_done:
        try:
            msg = (
                f"🔥 <b>[Auto-Habit]</b> Habit harian berhasil dicentang!\n"
                f"🎯 <b>{html.escape(habit.name)}</b>\n"
                f"⚡ Streak saat ini: <b>{streak} hari berturut-turut!</b>"
            )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram auto habit: {e}")

    return {
        "status": "success",
        "habit_id": habit.id,
        "habit_name": habit.name,
        "already_completed": already_done,
        "streak": streak,
    }


async def get_ambient_status(session: AsyncSession, email: str) -> dict:
    """Mendapatkan status terkini untuk daemon ambient: timer aktif, area hidup, dll."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    # Timer aktif
    res_timer = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res_timer.scalars().first()

    active_timer_data = None
    if running:
        elapsed = int(max(0, _diff_seconds(utcnow(), running.started_at)) // 60)
        active_timer_data = {
            "project_name": running.project_name,
            "started_at": running.started_at.isoformat(),
            "elapsed_minutes": elapsed,
        }

    # Area hidup
    res_areas = await session.execute(
        select(Area).where(Area.user_id == profile.id).order_by(Area.position.asc())
    )
    areas = [
        {"id": a.id, "name": a.name, "position": a.position}
        for a in res_areas.scalars().all()
    ]

    return {
        "status": "ok",
        "user": {
            "id": str(profile.id),
            "email": profile.email,
            "full_name": profile.full_name,
            "has_telegram": profile.telegram_chat_id is not None,
        },
        "active_timer": active_timer_data,
        "areas": areas,
    }


async def handle_git_commit_event(
    session: AsyncSession,
    email: str,
    commit_message: str,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memproses event git commit: otomatis menyelesaikan task terkait dan mencentang habit coding."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_msg = commit_message.strip()
    if not clean_msg:
        return {"status": "ignored", "reason": "empty_commit_message"}

    # 1. Ekstrak Task ID eksplisit: #12, task #12, fix #12, tugas 12, dll.
    explicit_ids = set()
    for m in re.finditer(r"#(\d+)", clean_msg):
        explicit_ids.add(int(m.group(1)))
    for m in re.finditer(
        r"(?i)\b(?:tugas|task|id:?|fix|fixes|fixed|closes?|closed|done)\s*#?(\d+)\b",
        clean_msg,
    ):
        explicit_ids.add(int(m.group(1)))

    completed_tasks = []
    now_utc = utcnow()

    if explicit_ids:
        # Cari task pending berdasarkan ID yang diekstrak
        res_tasks = await session.execute(
            select(Task).where(
                Task.user_id == profile.id,
                col(Task.id).in_(list(explicit_ids)),
                Task.status == "pending",
            )
        )
        tasks_to_complete = res_tasks.scalars().all()
        for t in tasks_to_complete:
            t.status = "completed"
            t.completed_at = now_utc
            session.add(t)
            completed_tasks.append({"id": t.id, "title": t.title})
        if tasks_to_complete:
            await session.commit()

    # 2. Jika tidak ada task ID eksplisit, coba pencocokan kata kunci judul tugas
    if not completed_tasks:
        res_all_pending = await session.execute(
            select(Task).where(
                Task.user_id == profile.id,
                Task.status == "pending",
            )
        )
        pending_tasks = res_all_pending.scalars().all()

        git_stop_words = {
            "feat",
            "fix",
            "chore",
            "refactor",
            "docs",
            "test",
            "style",
            "perf",
            "merge",
            "branch",
            "update",
            "wip",
            "selesaikan",
            "beres",
            "kelar",
            "done",
            "tambah",
            "ubah",
            "hapus",
            "add",
            "remove",
            "dan",
            "yang",
            "di",
            "ke",
            "dari",
            "ini",
            "itu",
        }
        msg_words = {
            w.lower().strip(".,:;!()[]{}'\"") for w in clean_msg.split() if len(w) > 2
        } - git_stop_words

        for t in pending_tasks:
            t_words = {
                w.lower().strip(".,:;!()[]{}'\"") for w in t.title.split() if len(w) > 2
            } - git_stop_words
            overlap = t_words.intersection(msg_words)
            # Jika ada minimal 2 kata kunci spesifik yang cocok atau seluruh kata kunci pendek tugas ada di commit
            if len(overlap) >= 2 or (len(t_words) == 1 and len(overlap) == 1):
                t.status = "completed"
                t.completed_at = now_utc
                session.add(t)
                completed_tasks.append({"id": t.id, "title": t.title})
                await session.commit()
                break

    # 3. Otomatis centang habit coding hari ini jika ada commit
    auto_habits = await auto_check_habits_on_focus(
        session=session,
        user_id=profile.id,
        project_name=repo_name or "Coding",
        duration_minutes=20,
        min_minutes=15,
    )

    # 4. Kirim notifikasi Telegram pasif
    if (
        notify_telegram
        and profile.telegram_chat_id
        and bot
        and (completed_tasks or auto_habits)
    ):
        try:
            repo_display = html.escape(repo_name) if repo_name else "local-repo"
            branch_display = f" ({html.escape(branch)})" if branch else ""
            msg = (
                f"🎯 <b>[Git Auto-Sync]</b> Commit terdeteksi!\n"
                f"📦 <code>{repo_display}</code>{branch_display}\n"
                f'💬 <i>"{html.escape(clean_msg[:120])}"</i>\n\n'
            )
            if completed_tasks:
                msg += "✅ <b>Tugas Berhasil Diselesaikan:</b>\n"
                for ct in completed_tasks:
                    msg += f"• <b>{html.escape(ct['title'])}</b> (ID: #{ct['id']})\n"
            if auto_habits:
                msg += "\n🔥 <b>Habit Harian Tercentang:</b>\n"
                for ah in auto_habits:
                    msg += f"• <b>{html.escape(ah['name'])}</b> (Streak: {ah['streak']} hari 🔥)\n"

            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram git commit: {e}")

    return {
        "status": "success",
        "completed_tasks": completed_tasks,
        "auto_checked_habits": auto_habits,
        "repo": repo_name,
        "branch": branch,
    }


async def check_bedtime_status(session: AsyncSession, email: str) -> dict:
    """Mengecek status jam malam untuk ambient watcher (sinkronisasi cutoff dari profil DB)."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    night_cutoff = (
        profile.night_cutoff_time if profile.night_cutoff_time else time(23, 0)
    )
    now_local = datetime.now(LOCAL_TZ)
    current_t = now_local.time()
    past_bedtime = is_past_night_cutoff(current_t, night_cutoff)

    cutoff_str = night_cutoff.strftime("%H:%M")
    current_str = now_local.strftime("%H:%M")

    if past_bedtime:
        message = (
            f"🌙 Sudah pukul {current_str} (batas jam malam {cutoff_str}). "
            f"Waktunya istirahat dan simpan pekerjaanmu!"
        )
    else:
        message = (
            f"✅ Masih dalam jam kerja ({current_str}). Batas malam: {cutoff_str}."
        )

    return {
        "status": "ok",
        "is_past_bedtime": past_bedtime,
        "cutoff_time": cutoff_str,
        "current_time": current_str,
        "message": message,
    }


async def handle_quick_capture(
    session: AsyncSession,
    email: str,
    text: str,
    source: str = "quick_capture",
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memproses tangkapan ide/tugas cepat dari Global Desktop Quick Capture."""
    import asyncio

    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_text = text.strip()
    if not clean_text:
        return {"status": "error", "message": "Teks tangkapan tidak boleh kosong"}

    reply = ""
    processed_by = "agent_ai"
    try:
        from .agent import run_agent

        chat_id = profile.telegram_chat_id or 0
        # Timeout 10s untuk agent processing (fallback jika hang)
        reply = await asyncio.wait_for(
            run_agent(profile.id, chat_id, clean_text), timeout=10.0
        )
    except asyncio.TimeoutError:
        logger.warning("Agent processing timeout, using Zero Data Loss fallback (note)")
        new_note = Note(
            user_id=profile.id,
            content=clean_text,
            source=source,
            tags=["quick_capture", "inbox"],
        )
        session.add(new_note)
        await session.commit()
        reply = "⏱️ Ide disimpan ke Inbox (agent timeout)"
        processed_by = "note_fallback_timeout"
    except Exception as e:
        logger.warning(
            f"Gagal memproses via AI agent ({type(e).__name__}), fallback: {e}"
        )
        new_note = Note(
            user_id=profile.id,
            content=clean_text,
            source=source,
            tags=["quick_capture", "inbox"],
        )
        session.add(new_note)
        await session.commit()
        reply = "Ide disimpan ke Inbox."
        processed_by = "note_fallback"

    if notify_telegram and profile.telegram_chat_id and bot:
        try:
            msg = (
                f"💡 <b>[Quick Capture]</b> Tangkapan baru diterima:\n"
                f'📝 <i>"{html.escape(clean_text)}"</i>\n\n'
                f"🤖 <b>Respon:</b> {html.escape(reply)}"
            )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram quick capture: {e}")

    return {
        "status": "success",
        "processed_by": processed_by,
        "reply": reply,
        "text": clean_text,
    }
