# apps/backend/app/thesis.py
"""Modul Kuliah dan Riset (Thesis, Bimbingan Dospem, Metrik Eksperimen, & Tugas Matkul).

Menyediakan fungsi pendukung untuk:
- Pelacakan bab naskah thesis (Bab 1 - 5) beserta progress bar visual
- Notulensi bimbingan dosen pembimbing dan pencegah ghosting
- Pencatatan metrik evaluasi eksperimen model
- Pemantauan deadline tugas kuliah (Coursework)
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, desc, select

from .config import settings
from .models import (
    Area,
    ExperimentMetric,
    SupervisionLog,
    Task,
    ThesisChapter,
    utcnow,
)

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)

DEFAULT_CHAPTERS = [
    (1, "Pendahuluan"),
    (2, "Landasan Teori"),
    (3, "Metodologi Penelitian"),
    (4, "Hasil & Pembahasan"),
    (5, "Kesimpulan & Saran"),
]


def render_progress_bar(percent: int, length: int = 10) -> str:
    """Menghasilkan progress bar visual bergaya [████░░░░░░]."""
    clamped = max(0, min(100, percent))
    filled_len = int(round(length * clamped / 100))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {clamped}%"


async def get_or_create_thesis_chapters(
    session: AsyncSession, user_id: UUID
) -> List[ThesisChapter]:
    """Mengambil bab thesis pengguna, atau membuatkan default Bab 1 - 5 jika belum ada."""
    result = await session.execute(
        select(ThesisChapter)
        .where(ThesisChapter.user_id == user_id)
        .order_by(ThesisChapter.chapter_num.asc())
    )
    chapters = result.scalars().all()

    if len(chapters) < 5:
        existing_nums = {c.chapter_num for c in chapters}
        new_chapters = []
        for num, title in DEFAULT_CHAPTERS:
            if num not in existing_nums:
                ch = ThesisChapter(
                    user_id=user_id,
                    chapter_num=num,
                    title=title,
                    status="Belum Mulai",
                    progress=0,
                )
                session.add(ch)
                new_chapters.append(ch)

        if new_chapters:
            await session.commit()
            for ch in new_chapters:
                await session.refresh(ch)

        # Ambil ulang terurut
        result = await session.execute(
            select(ThesisChapter)
            .where(ThesisChapter.user_id == user_id)
            .order_by(ThesisChapter.chapter_num.asc())
        )
        chapters = result.scalars().all()

    return list(chapters)


async def update_thesis_chapter(
    session: AsyncSession,
    user_id: UUID,
    chapter_num: int,
    status: str,
    progress: int,
) -> Optional[ThesisChapter]:
    """Memperbarui status dan progres bab thesis tertentu."""
    result = await session.execute(
        select(ThesisChapter).where(
            ThesisChapter.user_id == user_id,
            ThesisChapter.chapter_num == chapter_num,
        )
    )
    chapter = result.scalars().first()
    if not chapter:
        return None

    chapter.status = status
    chapter.progress = max(0, min(100, progress))
    chapter.updated_at = utcnow()
    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)
    return chapter


def format_thesis_progress_html(chapters: List[ThesisChapter]) -> str:
    """Format visual ringkasan bab thesis dalam HTML Telegram."""
    total_progress = (
        sum(c.progress for c in chapters) // len(chapters) if chapters else 0
    )
    overall_bar = render_progress_bar(total_progress, length=12)

    lines = [
        "🎓 <b>Status & Progres Naskah Thesis</b>",
        f"<b>Total Progres:</b> {overall_bar}\n",
    ]

    status_emojis = {
        "Selesai": "✅",
        "Revisi": "✍️",
        "Drafting": "📝",
        "Review Dospem": "👀",
        "Belum Mulai": "⚪",
    }

    for ch in chapters:
        emoji = status_emojis.get(ch.status, "📌")
        bar = render_progress_bar(ch.progress, length=8)
        lines.append(
            f"<b>Bab {ch.chapter_num}: {ch.title}</b>\n"
            f"  {bar} • {emoji} <i>{ch.status}</i>"
        )

    lines.append(
        "\n<i>Klik tombol di bawah untuk mengupdate status bab secara cepat:</i>"
    )
    return "\n".join(lines)


async def add_supervision_log(
    session: AsyncSession,
    user_id: UUID,
    notes: str,
    action_items: Optional[str] = None,
) -> SupervisionLog:
    """Mencatat notulensi bimbingan dosen pembimbing."""
    log = SupervisionLog(
        user_id=user_id,
        notes=notes,
        action_items=action_items,
        created_at=utcnow(),
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_supervision_summary(
    session: AsyncSession, user_id: UUID
) -> Tuple[List[SupervisionLog], Optional[int]]:
    """Mengambil log bimbingan terbaru dan menghitung hari sejak bimbingan terakhir."""
    result = await session.execute(
        select(SupervisionLog)
        .where(SupervisionLog.user_id == user_id)
        .order_by(desc(SupervisionLog.created_at))
        .limit(5)
    )
    logs = list(result.scalars().all())

    days_since_last = None
    if logs:
        last_dt = logs[0].created_at
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        now_dt = utcnow()
        days_since_last = (now_dt.date() - last_dt.astimezone(LOCAL_TZ).date()).days

    return logs, days_since_last


async def add_experiment_metric(
    session: AsyncSession,
    user_id: UUID,
    model_name: str,
    metrics_summary: str,
    parameters: Optional[str] = None,
) -> ExperimentMetric:
    """Mencatat metrik evaluasi eksperimen model."""
    metric = ExperimentMetric(
        user_id=user_id,
        model_name=model_name,
        metrics_summary=metrics_summary,
        parameters=parameters,
        created_at=utcnow(),
    )
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def get_recent_metrics(
    session: AsyncSession, user_id: UUID, limit: int = 5
) -> List[ExperimentMetric]:
    """Mengambil riwayat metrik eksperimen terbaru."""
    result = await session.execute(
        select(ExperimentMetric)
        .where(ExperimentMetric.user_id == user_id)
        .order_by(desc(ExperimentMetric.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_coursework_tasks(
    session: AsyncSession, user_id: UUID, today: date
) -> List[Tuple[Task, str, int]]:
    """Mengambil tugas perkuliahan (di area Kuliah dan Riset) terurut deadline terdekat.

    Mengembalikan daftar tuple: (Task, status_deadline_str, days_left).
    """
    areas_res = await session.execute(
        select(Area).where(
            Area.user_id == user_id,
            col(Area.name).in_(["Kuliah dan Riset", "Kuliah & Riset", "Kuliah"]),
        )
    )
    kuliah_areas = areas_res.scalars().all()
    if not kuliah_areas:
        return []

    area_ids = [a.id for a in kuliah_areas]

    tasks_res = await session.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.status == "pending",
            col(Task.area_id).in_(area_ids),
        )
    )
    tasks = tasks_res.scalars().all()

    # Pisahkan tugas dengan deadline dan tanpa deadline
    with_deadline = [t for t in tasks if t.deadline is not None]
    with_deadline.sort(key=lambda t: t.deadline)

    result = []
    for t in with_deadline:
        days_left = (t.deadline - today).days
        if days_left < 0:
            status_str = f"🔴 TERLAMBAT {abs(days_left)} HARI"
        elif days_left == 0:
            status_str = "🔥 HARI INI!"
        elif days_left == 1:
            status_str = "⚠️ BESOK!"
        else:
            status_str = f"⏳ Sisa {days_left} hari"
        result.append((t, status_str, days_left))

    return result
