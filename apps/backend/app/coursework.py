# apps/backend/app/coursework.py
"""Modul Akademik & Kuliah (Tugas Matkul, Persiapan UTS/UAS, & Final Project).

Menyediakan fungsi pendukung untuk:
- Pelacakan tugas kuliah per mata kuliah, bobot nilai, dan urgensi deadline
- Radar persiapan ujian UTS & UAS lengkap dengan checklist penguasaan materi (kisi-kisi)
- Manajemen tugas besar / Final Project bertahap (milestone, PIC tim, berkas deliverable)
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import col, desc, select

from .config import settings
from .models import CourseAssignment, CourseExam, CourseProject, utcnow

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)

DEFAULT_PROJECT_MILESTONES = [
    {"step": "Proposal & Desain Arsitektur", "status": "pending", "pic": "Tim"},
    {"step": "Implementasi & Coding / Eksperimen", "status": "pending", "pic": "Tim"},
    {"step": "Pengujian & Laporan Akhir", "status": "pending", "pic": "Tim"},
    {"step": "Slide Presentasi & Demo / Video", "status": "pending", "pic": "Tim"},
]

DEFAULT_PROJECT_DELIVERABLES = [
    {"item": "Repository GitHub / Source Code", "done": False},
    {"item": "Naskah Laporan Akhir (PDF)", "done": False},
    {"item": "Slide Presentasi (PPT/Canva)", "done": False},
    {"item": "Video Demo / Deployment URL", "done": False},
]


def render_progress_bar(percent: int, length: int = 10) -> str:
    """Menghasilkan visual progress bar bergaya [████░░░░░░]."""
    clamped = max(0, min(100, percent))
    filled_len = int(round(length * clamped / 100))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {clamped}%"


# ============================================================================
# 1. SMART TUGAS KULIAH (CourseAssignment)
# ============================================================================

async def add_course_assignment(
    session: AsyncSession,
    user_id: UUID,
    course_name: str,
    title: str,
    assignment_type: str = "Individu",
    deadline: Optional[datetime] = None,
    weight_percent: Optional[int] = None,
    notes: Optional[str] = None,
) -> CourseAssignment:
    """Menambahkan tugas kuliah baru."""
    assignment = CourseAssignment(
        user_id=user_id,
        course_name=course_name,
        title=title,
        assignment_type=assignment_type,
        deadline=deadline,
        weight_percent=weight_percent,
        notes=notes,
        status="pending",
        created_at=utcnow(),
    )
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


async def get_active_course_assignments(
    session: AsyncSession, user_id: UUID
) -> List[CourseAssignment]:
    """Mengambil tugas kuliah yang belum selesai (pending), terurut deadline terdekat."""
    result = await session.execute(
        select(CourseAssignment)
        .where(
            CourseAssignment.user_id == user_id,
            CourseAssignment.status == "pending",
        )
        .order_by(
            CourseAssignment.deadline.asc().nulls_last(),
            CourseAssignment.id.asc(),
        )
    )
    return list(result.scalars().all())


async def mark_course_assignment_done(
    session: AsyncSession, user_id: UUID, assignment_id: int
) -> Optional[CourseAssignment]:
    """Menandai tugas kuliah sebagai selesai."""
    result = await session.execute(
        select(CourseAssignment).where(
            CourseAssignment.user_id == user_id,
            CourseAssignment.id == assignment_id,
        )
    )
    assignment = result.scalars().first()
    if not assignment:
        return None

    assignment.status = "done"
    assignment.completed_at = utcnow()
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


def format_assignments_html(
    assignments: List[CourseAssignment], tz: ZoneInfo = LOCAL_TZ
) -> str:
    """Format visual ringkasan tugas kuliah ke dalam HTML Telegram."""
    if not assignments:
        return (
            "🎉 <b>Tidak ada tugas kuliah yang pending!</b>\n\n"
            "Semua tugas kuliahmu sudah selesai dikumpulkan. Waktu santai atau fokus riset!\n"
            "<i>Ketik pesan bebas untuk menambah tugas (contoh: 'tambah tugas praktikum Jaringan Komputer deadline jumat').</i>"
        )

    now = datetime.now(tz)
    critical_items: List[Tuple[CourseAssignment, str]] = []
    week_items: List[Tuple[CourseAssignment, str]] = []
    later_items: List[Tuple[CourseAssignment, str]] = []

    for item in assignments:
        if item.deadline:
            dl_local = (
                item.deadline.astimezone(tz)
                if item.deadline.tzinfo
                else item.deadline.replace(tzinfo=timezone.utc).astimezone(tz)
            )
            days_left = (dl_local.date() - now.date()).days

            if days_left < 0:
                status_badge = f"🔴 TERLAMBAT {abs(days_left)} HARI ({dl_local.strftime('%d %b, %H:%M')})"
                critical_items.append((item, status_badge))
            elif days_left == 0:
                status_badge = f"🔥 HARI INI! ({dl_local.strftime('%H:%M WIB')})"
                critical_items.append((item, status_badge))
            elif days_left == 1:
                status_badge = f"⚠️ BESOK ({dl_local.strftime('%H:%M WIB')})"
                critical_items.append((item, status_badge))
            elif days_left <= 7:
                status_badge = f"⏳ {days_left} hari lagi ({dl_local.strftime('%a, %d %b')})"
                week_items.append((item, status_badge))
            else:
                status_badge = f"🗓️ {dl_local.strftime('%d %b %Y')}"
                later_items.append((item, status_badge))
        else:
            later_items.append((item, "🗓️ Tanpa Deadline"))

    lines = [
        "📝 <b>DAFTAR TUGAS KULIAH AKTIF</b>",
        f"<i>Total tugas pending: {len(assignments)} tugas</i>\n",
    ]

    def render_group(header: str, group: List[Tuple[CourseAssignment, str]]):
        if not group:
            return
        lines.append(f"<b>{header}</b>")
        for item, badge in group:
            weight_str = f" • Bobot: {item.weight_percent}%" if item.weight_percent else ""
            type_str = f"[{item.assignment_type}] " if item.assignment_type else ""
            lines.append(
                f"• <b>{item.course_name}</b>: {type_str}{item.title}\n"
                f"  └ {badge}{weight_str}"
            )
        lines.append("")

    render_group("🔴 KRITIS / DEADLINE DEKAT:", critical_items)
    render_group("🟡 MINGGU INI:", week_items)
    render_group("⏳ MENDATANG / LAINNYA:", later_items)

    lines.append("<i>Pilih tombol di bawah untuk menandai tugas yang sudah selesai kumpul:</i>")
    return "\n".join(lines).strip()


# ============================================================================
# 2. UTS & UAS PREP RADAR (CourseExam)
# ============================================================================

async def add_course_exam(
    session: AsyncSession,
    user_id: UUID,
    course_name: str,
    exam_type: str = "UTS",
    exam_date: datetime = None,
    room_or_link: Optional[str] = None,
    rules: str = "Closed Book",
    topics: Optional[List[dict]] = None,
    target_score: int = 85,
) -> CourseExam:
    """Mendaftarkan jadwal ujian baru beserta kisi-kisi topik materi."""
    if not exam_date:
        exam_date = utcnow()
    if topics is None:
        topics = [
            {"title": "Materi Bagian 1 (Pertemuan 1 - 3)", "status": "paham"},
            {"title": "Materi Bagian 2 (Pertemuan 4 - 5)", "status": "latihan"},
            {"title": "Materi Bagian 3 (Pertemuan 6 - 7)", "status": "belum"},
        ]

    exam = CourseExam(
        user_id=user_id,
        course_name=course_name,
        exam_type=exam_type,
        exam_date=exam_date,
        room_or_link=room_or_link,
        rules=rules,
        topics=topics,
        target_score=target_score,
        created_at=utcnow(),
    )
    session.add(exam)
    await session.commit()
    await session.refresh(exam)
    return exam


async def get_upcoming_exams(
    session: AsyncSession, user_id: UUID
) -> List[CourseExam]:
    """Mengambil daftar ujian mendatang terurut tanggal ujian."""
    result = await session.execute(
        select(CourseExam)
        .where(CourseExam.user_id == user_id)
        .order_by(CourseExam.exam_date.asc())
    )
    return list(result.scalars().all())


async def update_exam_topic_status(
    session: AsyncSession,
    user_id: UUID,
    exam_id: int,
    topic_index: int,
    new_status: str,
) -> Optional[CourseExam]:
    """Memperbarui tingkat penguasaan kisi-kisi topik materi ujian."""
    result = await session.execute(
        select(CourseExam).where(
            CourseExam.user_id == user_id,
            CourseExam.id == exam_id,
        )
    )
    exam = result.scalars().first()
    if not exam or not exam.topics or topic_index >= len(exam.topics):
        return None

    updated_topics = [dict(t) for t in exam.topics]
    updated_topics[topic_index]["status"] = new_status
    exam.topics = updated_topics
    flag_modified(exam, "topics")
    session.add(exam)
    await session.commit()
    await session.refresh(exam)
    return exam


def calculate_exam_mastery(topics: Optional[List[dict]]) -> int:
    """Menghitung persentase kesiapan materi berdasarkan bobot status penguasaan.
    
    Status bobot:
    - siap: 100%
    - latihan: 75%
    - paham: 40%
    - belum: 0%
    """
    if not topics:
        return 0
    scores = {"siap": 100, "latihan": 75, "paham": 40, "belum": 0}
    total = sum(scores.get(t.get("status", "belum"), 0) for t in topics)
    return total // len(topics)


def format_exams_html(exams: List[CourseExam], tz: ZoneInfo = LOCAL_TZ) -> str:
    """Format visual radar persiapan ujian ke dalam HTML Telegram."""
    if not exams:
        return (
            "🎯 <b>Tidak ada jadwal ujian dalam radar!</b>\n\n"
            "Belum ada agenda UTS/UAS terdaftar. Fokus pelajari materi kuliah harian dengan konsisten."
        )

    now = datetime.now(tz)
    lines = [
        "🎯 <b>RADAR PERSIAPAN UJIAN (UTS & UAS)</b>",
        f"<i>Terdaftar: {len(exams)} ujian mendatang</i>\n",
    ]

    status_icons = {
        "siap": "✅ Siap",
        "latihan": "✍️ Latihan",
        "paham": "📖 Paham",
        "belum": "⚪ Belum",
    }

    for ex in exams:
        ex_local = (
            ex.exam_date.astimezone(tz)
            if ex.exam_date.tzinfo
            else ex.exam_date.replace(tzinfo=timezone.utc).astimezone(tz)
        )
        days_left = (ex_local.date() - now.date()).days

        if days_left < 0:
            time_badge = f"🔴 SELESAI ({abs(days_left)} hari lalu)"
        elif days_left == 0:
            time_badge = "🔥 HARI INI!"
        elif days_left == 1:
            time_badge = "⚠️ BESOK!"
        else:
            time_badge = f"⏳ Sisa {days_left} hari"

        mastery_percent = calculate_exam_mastery(ex.topics)
        bar = render_progress_bar(mastery_percent, length=8)

        room_str = f" • Ruang: <code>{ex.room_or_link}</code>" if ex.room_or_link else ""
        lines.append(
            f"📅 <b>{ex.exam_type}: {ex.course_name}</b> ({time_badge})\n"
            f"• Waktu: {ex_local.strftime('%A, %d %b %Y • %H:%M WIB')}{room_str}\n"
            f"• Aturan: <i>{ex.rules}</i> • Target Nilai: <b>{ex.target_score}</b>\n"
            f"• Kesiapan Materi: {bar}"
        )

        if ex.topics:
            lines.append("  <b>Topik Kisi-kisi:</b>")
            for idx, t in enumerate(ex.topics, 1):
                icon = status_icons.get(t.get("status", "belum"), "⚪")
                lines.append(f"  {idx}. {t.get('title', 'Topik')} [{icon}]")

        lines.append("")

    lines.append("<i>Pilih tombol di bawah untuk memperbarui status penguasaan materi:</i>")
    return "\n".join(lines).strip()


# ============================================================================
# 3. FINAL PROJECT / TUGAS BESAR HUB (CourseProject)
# ============================================================================

async def add_course_project(
    session: AsyncSession,
    user_id: UUID,
    course_name: str,
    title: str,
    deadline: Optional[datetime] = None,
    milestones: Optional[List[dict]] = None,
    deliverables: Optional[List[dict]] = None,
) -> CourseProject:
    """Mendaftarkan proyek besar / Final Project mata kuliah baru."""
    if milestones is None:
        milestones = [dict(m) for m in DEFAULT_PROJECT_MILESTONES]
    if deliverables is None:
        deliverables = [dict(d) for d in DEFAULT_PROJECT_DELIVERABLES]

    project = CourseProject(
        user_id=user_id,
        course_name=course_name,
        title=title,
        deadline=deadline,
        milestones=milestones,
        deliverables=deliverables,
        status="in_progress",
        created_at=utcnow(),
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def get_active_course_projects(
    session: AsyncSession, user_id: UUID
) -> List[CourseProject]:
    """Mengambil proyek besar aktif yang belum selesai."""
    result = await session.execute(
        select(CourseProject)
        .where(
            CourseProject.user_id == user_id,
            CourseProject.status == "in_progress",
        )
        .order_by(
            CourseProject.deadline.asc().nulls_last(),
            CourseProject.id.asc(),
        )
    )
    return list(result.scalars().all())


async def update_project_milestone(
    session: AsyncSession,
    user_id: UUID,
    project_id: int,
    milestone_index: int,
    new_status: str,
    pic: Optional[str] = None,
) -> Optional[CourseProject]:
    """Mengupdate status milestone tugas besar (done, in_progress, pending)."""
    result = await session.execute(
        select(CourseProject).where(
            CourseProject.user_id == user_id,
            CourseProject.id == project_id,
        )
    )
    project = result.scalars().first()
    if not project or not project.milestones or milestone_index >= len(project.milestones):
        return None

    updated_milestones = [dict(m) for m in project.milestones]
    updated_milestones[milestone_index]["status"] = new_status
    if pic:
        updated_milestones[milestone_index]["pic"] = pic
    project.milestones = updated_milestones
    flag_modified(project, "milestones")

    # Jika semua milestone selesai, otomatis tandai completed
    if all(m.get("status") == "done" for m in updated_milestones):
        project.status = "completed"

    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def toggle_project_deliverable(
    session: AsyncSession,
    user_id: UUID,
    project_id: int,
    deliverable_index: int,
) -> Optional[CourseProject]:
    """Menandai centang/tidak berkas pengumpulan akhir (deliverable checklist)."""
    result = await session.execute(
        select(CourseProject).where(
            CourseProject.user_id == user_id,
            CourseProject.id == project_id,
        )
    )
    project = result.scalars().first()
    if not project or not project.deliverables or deliverable_index >= len(project.deliverables):
        return None

    updated = [dict(d) for d in project.deliverables]
    updated[deliverable_index]["done"] = not updated[deliverable_index].get("done", False)
    project.deliverables = updated
    flag_modified(project, "deliverables")
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


def calculate_project_progress(project: CourseProject) -> int:
    """Menghitung progres keseluruhan proyek besar gabungan milestone dan berkas."""
    milestones = project.milestones or []
    deliverables = project.deliverables or []

    m_score = 0
    if milestones:
        for m in milestones:
            st = m.get("status", "pending")
            if st == "done":
                m_score += 100
            elif st == "in_progress":
                m_score += 50
        m_percent = m_score // len(milestones)
    else:
        m_percent = 0

    d_score = 0
    if deliverables:
        d_score = sum(100 for d in deliverables if d.get("done", False))
        d_percent = d_score // len(deliverables)
    else:
        d_percent = 0

    # Bobot: Milestones 70%, Deliverables 30%
    return int((m_percent * 0.7) + (d_percent * 0.3))


def format_projects_html(projects: List[CourseProject], tz: ZoneInfo = LOCAL_TZ) -> str:
    """Format visual ringkasan Final Project / Tugas Besar ke dalam HTML Telegram."""
    if not projects:
        return (
            "🚀 <b>Tidak ada Final Project aktif saat ini!</b>\n\n"
            "Semua tugas besar perkuliahan sudah rampung atau belum ada yang didaftarkan."
        )

    now = datetime.now(tz)
    lines = [
        "🚀 <b>FINAL PROJECT & TUGAS BESAR HUB</b>",
        f"<i>Proyek Aktif: {len(projects)} tugas besar</i>\n",
    ]

    status_map = {
        "done": "✅ Selesai",
        "in_progress": "⏳ On Progress",
        "pending": "⚪ Belum Mulai",
    }

    for prj in projects:
        if prj.deadline:
            dl_local = (
                prj.deadline.astimezone(tz)
                if prj.deadline.tzinfo
                else prj.deadline.replace(tzinfo=timezone.utc).astimezone(tz)
            )
            days_left = (dl_local.date() - now.date()).days
            if days_left < 0:
                time_badge = f"🔴 TERLAMBAT {abs(days_left)} HARI"
            elif days_left == 0:
                time_badge = "🔥 HARI INI!"
            elif days_left == 1:
                time_badge = "⚠️ BESOK!"
            else:
                time_badge = f"⏳ Sisa {days_left} hari ({dl_local.strftime('%d %b')})"
        else:
            time_badge = "🗓️ Tanpa Deadline"

        prog_percent = calculate_project_progress(prj)
        bar = render_progress_bar(prog_percent, length=10)

        lines.append(
            f"📌 <b>{prj.title}</b>\n"
            f"• Matkul: <b>{prj.course_name}</b> ({time_badge})\n"
            f"• Progres: {bar}\n"
            f"<b>Milestone & Pembagian Tim:</b>"
        )

        for idx, m in enumerate(prj.milestones or [], 1):
            st = status_map.get(m.get("status", "pending"), "⚪")
            pic = f" <i>(PIC: {m.get('pic')})</i>" if m.get("pic") else ""
            lines.append(f"  {idx}. {m.get('step', 'Step')} — {st}{pic}")

        if prj.deliverables:
            lines.append("<b>Berkas Pengumpulan (Deliverables):</b>")
            for d in prj.deliverables:
                chk = "☑️" if d.get("done") else "⬜"
                lines.append(f"  {chk} {d.get('item')}")

        lines.append("")

    lines.append("<i>Gunakan tombol di bawah untuk memperbarui progres milestone & berkas:</i>")
    return "\n".join(lines).strip()
