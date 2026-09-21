# apps/backend/app/ambient.py
"""Modul logika ambient tracking: pelacakan otomatis via OS watcher / VS Code."""

import html
import logging
from datetime import datetime, time, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlmodel import col, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.constants import ParseMode

from .config import settings
from .models import Area, Profile, TimeLog, utcnow
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
    res = await session.execute(
        select(Profile).where(Profile.email == clean_email)
    )
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
        return {"status": "error", "message": f"User dengan email '{email}' tidak ditemukan"}

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
    night_cutoff = profile.night_cutoff_time if profile.night_cutoff_time else time(23, 0)
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
        return {"status": "error", "message": f"User dengan email '{email}' tidak ditemukan"}

    res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res.scalars().first()

    if not running:
        return {"status": "no_active_timer", "message": "Tidak ada timer yang sedang berjalan"}

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

    # Notifikasi ringkasan pasif jika durasi cukup berarti (>= 2 menit)
    if notify_telegram and profile.telegram_chat_id and bot and duration_min >= 2:
        try:
            dur_text = _fmt_duration(duration_min)
            reason_label = "VS Code ditutup" if reason == "window_closed" else "Waktu idle / jeda"
            msg = (
                f"⏱️ <b>[Auto-Timer]</b> Sesi fokus selesai: <b>{html.escape(project)}</b>\n"
                f"⏳ Durasi: <b>{dur_text}</b> ({reason_label})\n"
                f"Data berhasil disinkronkan ke dashboard! 🎯"
            )
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
    }


async def get_ambient_status(session: AsyncSession, email: str) -> dict:
    """Mendapatkan status terkini untuk daemon ambient: timer aktif, area hidup, dll."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {"status": "error", "message": f"User dengan email '{email}' tidak ditemukan"}

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
    areas = [{"id": a.id, "name": a.name, "position": a.position} for a in res_areas.scalars().all()]

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
