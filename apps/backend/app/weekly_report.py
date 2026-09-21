# apps/backend/app/weekly_report.py
"""Modul Laporan Mingguan Pola Kerja (Weekly Intelligence & Balance).

Mengumpulkan metrik performa 7 hari (fokus kerja, penyelesaian tugas, konsistensi habit,
dan kepatuhan jam istirahat), lalu menyajikannya dalam format refleksi yang ramah.
"""

from datetime import date, datetime, time, timedelta, timezone
import html
import logging
from typing import Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlmodel import col, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import Area, Habit, HabitLog, Profile, Task, TimeLog

logger = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)
INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
INDO_MONTHS = [
    "",
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


def get_week_boundaries(reference_date: date) -> tuple[date, date]:
    """Mengembalikan tanggal Senin dan Minggu dari pekan yang memuat reference_date."""
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


async def get_weekly_stats(
    session: AsyncSession, user_id: UUID, reference_date: date
) -> dict:
    """Mengumpulkan statistik kerja, tugas, habit, dan jam istirahat selama satu pekan."""
    start_of_week, end_of_week = get_week_boundaries(reference_date)

    start_local = datetime.combine(start_of_week, time.min).replace(tzinfo=LOCAL_TZ)
    end_local = datetime.combine(end_of_week, time.max).replace(tzinfo=LOCAL_TZ)

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    # 1. Sesi Fokus (Time Logs)
    logs_res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.started_at >= start_utc,
            TimeLog.started_at <= end_utc,
            col(TimeLog.ended_at).is_not(None),
        )
    )
    time_logs = logs_res.scalars().all()

    total_focus_minutes = sum(l.duration_minutes or 0 for l in time_logs)

    # Breakdown per project
    project_minutes: Dict[str, int] = {}
    # Distribusi harian (0 = Senin, 6 = Minggu)
    daily_minutes: Dict[int, int] = {i: 0 for i in range(7)}
    late_night_days: set[date] = set()

    prof_res = await session.execute(select(Profile).where(Profile.id == user_id))
    profile = prof_res.scalars().first()
    cutoff_time = (
        profile.night_cutoff_time
        if profile and profile.night_cutoff_time
        else time(23, 0)
    )

    for l in time_logs:
        p_name = l.project_name or "Umum"
        project_minutes[p_name] = project_minutes.get(p_name, 0) + (
            l.duration_minutes or 0
        )

        # Waktu lokal log
        started_local = l.started_at.astimezone(LOCAL_TZ)
        day_idx = started_local.weekday()
        daily_minutes[day_idx] += l.duration_minutes or 0

        from .scheduler import is_past_night_cutoff

        if l.night_warning_sent or is_past_night_cutoff(
            started_local.time(), cutoff_time
        ):
            late_night_days.add(started_local.date())

    sorted_projects = sorted(project_minutes.items(), key=lambda x: x[1], reverse=True)

    # Hari paling produktif
    best_day_idx = max(daily_minutes.keys(), key=lambda k: daily_minutes[k])
    best_day_name = INDO_DAYS[best_day_idx]
    best_day_minutes = daily_minutes[best_day_idx]

    # 2. Tugas (Tasks)
    completed_res = await session.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.completed_at >= start_utc,
            Task.completed_at <= end_utc,
        )
    )
    completed_tasks = completed_res.scalars().all()

    pending_res = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.status == "pending")
    )
    pending_tasks = pending_res.scalars().all()

    # 3. Habits & Habit Logs
    habits_res = await session.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True))
    )
    active_habits = habits_res.scalars().all()

    habit_logs_res = await session.execute(
        select(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.completed_date >= start_of_week,
            HabitLog.completed_date <= end_of_week,
        )
    )
    week_habit_logs = habit_logs_res.scalars().all()

    total_expected_habits = len(active_habits) * 7
    habit_consistency_pct = (
        round((len(week_habit_logs) / max(1, total_expected_habits)) * 100)
        if total_expected_habits > 0
        else 0
    )

    clean_sleep_nights = max(0, 7 - len(late_night_days))

    return {
        "start_of_week": start_of_week,
        "end_of_week": end_of_week,
        "total_focus_minutes": total_focus_minutes,
        "total_sessions": len(time_logs),
        "sorted_projects": sorted_projects,
        "best_day_name": best_day_name,
        "best_day_minutes": best_day_minutes,
        "completed_tasks_count": len(completed_tasks),
        "pending_tasks_count": len(pending_tasks),
        "active_habits_count": len(active_habits),
        "total_habit_checks": len(week_habit_logs),
        "habit_consistency_pct": habit_consistency_pct,
        "clean_sleep_nights": clean_sleep_nights,
    }


def format_weekly_report_html(stats: dict, insight: Optional[str] = None) -> str:
    """Merangkai pesan laporan mingguan ke format HTML yang rapi (0 kuota LLM)."""
    s_date = stats["start_of_week"]
    e_date = stats["end_of_week"]

    start_str = f"{s_date.day} {INDO_MONTHS[s_date.month]}"
    end_str = f"{e_date.day} {INDO_MONTHS[e_date.month]} {e_date.year}"

    total_mins = stats["total_focus_minutes"]
    hours = total_mins // 60
    mins = total_mins % 60
    duration_str = f"{hours} jam {mins} menit" if hours > 0 else f"{mins} menit"

    lines = [
        "📊 <b>Laporan Mingguan Pola Kerja</b>",
        f"<i>Periode: {start_str} – {end_str}</i>\n",
        f"⏱️ <b>Total Waktu Fokus:</b> {duration_str} ({stats['total_sessions']} sesi)",
    ]

    if stats["best_day_minutes"] > 0:
        b_hrs = stats["best_day_minutes"] // 60
        b_mins = stats["best_day_minutes"] % 60
        b_str = f"{b_hrs}j {b_mins}m" if b_hrs > 0 else f"{b_mins} menit"
        lines.append(
            f"🏆 <b>Hari Paling Produktif:</b> {stats['best_day_name']} ({b_str})"
        )

    # Alokasi per project
    projects = stats["sorted_projects"]
    if projects:
        lines.append("\n🎯 <b>Alokasi Waktu per Project:</b>")
        for name, p_mins in projects[:4]:
            p_hrs = p_mins // 60
            p_m = p_mins % 60
            dur = f"{p_hrs}j {p_m}m" if p_hrs > 0 else f"{p_m}m"
            pct = int((p_mins / max(1, total_mins)) * 100)
            lines.append(f"• <b>{html.escape(name)}</b>: {dur} ({pct}%)")

    # Tugas
    lines.append("\n✅ <b>Penyelesaian Tugas:</b>")
    lines.append(
        f"• {stats['completed_tasks_count']} tugas berhasil diselesaikan pekan ini"
    )
    lines.append(f"• {stats['pending_tasks_count']} tugas menunggu di daftar prioritas")

    # Habits
    if stats["active_habits_count"] > 0:
        lines.append("\n🔥 <b>Konsistensi Kebiasaan:</b>")
        lines.append(
            f"• Skor Ketercapaian: <b>{stats['habit_consistency_pct']}%</b> ({stats['total_habit_checks']} centang)"
        )

    # Tidur
    lines.append(f"\n🌙 <b>Penjaga Waktu Tidur:</b>")
    lines.append(
        f"• {stats['clean_sleep_nights']} dari 7 malam bebas lembur larut malam"
    )

    # Insight Refleksi
    if insight:
        lines.append(
            f'\n💡 <b>Refleksi Singkat:</b>\n<i>"{html.escape(insight.strip())}"</i>'
        )
    else:
        # Default coaching insight
        if stats["completed_tasks_count"] > 5 and stats["clean_sleep_nights"] >= 5:
            default_insight = "Keseimbangan yang luar biasa pekan ini! Ritme kerja dan waktu istirahatmu sangat terjaga."
        elif stats["clean_sleep_nights"] < 4:
            default_insight = "Pekan ini kamu cukup sering bekerja larut malam. Prioritaskan tidur lebih awal di pekan depan agar tidak burnout."
        else:
            default_insight = "Awali pekan baru besok dengan fokus pada 1 tugas prioritas utama terlebih dahulu."
        lines.append(f'\n💡 <b>Refleksi Singkat:</b>\n<i>"{default_insight}"</i>')

    return "\n".join(lines)


async def generate_weekly_insight_llm(stats: dict) -> Optional[str]:
    """Menghasilkan 1-2 kalimat motivasi/evaluasi personal lewat Gemini AI."""
    try:
        from google.genai import Client

        genai_client = Client(api_key=settings.GOOGLE_API_KEY)
        prompt = (
            f"Berdasarkan data produktivitas mingguan pengguna berikut:\n"
            f"- Total fokus: {stats['total_focus_minutes']} menit\n"
            f"- Tugas selesai: {stats['completed_tasks_count']}, pending: {stats['pending_tasks_count']}\n"
            f"- Konsistensi habit: {stats['habit_consistency_pct']}%\n"
            f"- Malam bebas lembur: {stats['clean_sleep_nights']}/7\n\n"
            "Tuliskan 1 sampai 2 kalimat refleksi dan pesan penyemangat yang hangat, suportif, dan realistis untuk pekan depan. "
            "Gunakan bahasa Indonesia santai tapi sopan. JANGAN gunakan bullet points atau tanda kutip pembuka/penutup."
        )
        resp = genai_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt],
        )
        return resp.text.strip() if resp and resp.text else None
    except Exception as e:
        logger.warning("Gagal memanggil Gemini untuk weekly insight: %s", e)
        return None
