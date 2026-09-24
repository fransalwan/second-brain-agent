# apps/backend/tests/test_coursework_module.py
"""Unit tests untuk Modul Kuliah & Akademik:
- Smart Coursework (/tugas): Manajemen tugas kuliah, deadline urgency, bobot, 1-tap done
- UTS & UAS Prep Radar (/ujian): Radar jadwal ujian, checklist kisi-kisi topik, progress bar penguasaan materi
- Final Project Hub (/tubes): Milestone pengerjaan 4 tahap, delegasi tugas tim, checklist deliverable
- Kuliah Command Center (/kuliah): Master overview & navigasi antarmuka
- Bot command handlers & interactive callbacks
"""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import (
    CourseAssignment,
    CourseExam,
    CourseProject,
    Profile,
    utcnow,
)
from app.coursework import (
    add_course_assignment,
    add_course_exam,
    add_course_project,
    calculate_exam_mastery,
    calculate_project_progress,
    format_assignments_html,
    format_exams_html,
    format_projects_html,
    get_active_course_assignments,
    get_active_course_projects,
    get_upcoming_exams,
    mark_course_assignment_done,
    render_progress_bar,
    toggle_project_deliverable,
    update_exam_topic_status,
    update_project_milestone,
)
import app.bot as bot_module


class MockCallbackQuery:
    def __init__(self, data: str, chat_id: int):
        self.data = data
        self.message = MockMessage()
        self.answered = False
        self.answer_text = None
        self.edited_text = None
        self.reply_markup = None

    async def answer(self, text: str = None, show_alert: bool = False):
        self.answered = True
        self.answer_text = text

    async def edit_message_text(self, text: str, **kwargs):
        self.edited_text = text
        if "reply_markup" in kwargs:
            self.reply_markup = kwargs["reply_markup"]


class MockMessage:
    def __init__(self):
        self.replies = []
        self.reply_markups = []

    async def reply_text(self, text: str, *args, **kwargs):
        self.replies.append(text)
        if "reply_markup" in kwargs:
            self.reply_markups.append(kwargs["reply_markup"])


class MockUpdate:
    def __init__(self, chat_id: int, text: str = "", callback_data: str = None):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()
        self.callback_query = (
            MockCallbackQuery(callback_data, chat_id) if callback_data else None
        )


class MockContext:
    def __init__(self, args: list = None):
        self.args = args or []


@pytest_asyncio.fixture
async def setup_test_db():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 99912345

    async with TestSessionLocal() as session:
        profile = Profile(
            id=user_id,
            email="mahasiswa@kampus.ac.id",
            full_name="Frans Mahasiswa",
            telegram_chat_id=chat_id,
        )
        session.add(profile)
        await session.commit()

    yield {"user_id": user_id, "chat_id": chat_id, "session_factory": TestSessionLocal}
    await test_engine.dispose()


# ============================================================================
# 1. TEST COURSEWORK ASSIGNMENTS
# ============================================================================

@pytest.mark.asyncio
async def test_coursework_assignment_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]
    now = utcnow()
    dl_tomorrow = now + timedelta(days=1)
    dl_next_week = now + timedelta(days=5)

    async with session_factory() as session:
        # 1. Tambah tugas
        a1 = await add_course_assignment(
            session=session,
            user_id=user_id,
            course_name="Machine Learning",
            title="Laporan Praktikum Neural Network",
            assignment_type="Praktikum",
            deadline=dl_tomorrow,
            weight_percent=15,
            notes="Implementasi backprop manual di PyTorch",
        )
        assert a1.id is not None
        assert a1.status == "pending"

        a2 = await add_course_assignment(
            session=session,
            user_id=user_id,
            course_name="Sistem Terdistribusi",
            title="Tugas Besar Consensus Raft",
            assignment_type="Kelompok",
            deadline=dl_next_week,
            weight_percent=20,
        )
        assert a2.id is not None

        # 2. Query pending
        pending = await get_active_course_assignments(session, user_id)
        assert len(pending) == 2
        assert pending[0].id == a1.id  # Terurut deadline terdekat

        # 3. Format HTML
        html = format_assignments_html(pending)
        assert "Laporan Praktikum Neural Network" in html
        assert "Machine Learning" in html
        assert "Praktikum" in html
        assert "Bobot: 15%" in html

        # 4. Selesaikan tugas a1
        done_item = await mark_course_assignment_done(session, user_id, a1.id)
        assert done_item.status == "done"
        assert done_item.completed_at is not None

        # 5. Query ulang pending
        pending_after = await get_active_course_assignments(session, user_id)
        assert len(pending_after) == 1
        assert pending_after[0].id == a2.id


# ============================================================================
# 2. TEST EXAM PREP RADAR
# ============================================================================

@pytest.mark.asyncio
async def test_exam_radar_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]
    exam_dt = utcnow() + timedelta(days=6)

    async with session_factory() as session:
        topics = [
            {"title": "P1-P3 Supervised Learning", "status": "siap"},
            {"title": "P4 Neural Networks", "status": "latihan"},
            {"title": "P5-P7 SVM & Ensemble", "status": "belum"},
        ]
        exam = await add_course_exam(
            session=session,
            user_id=user_id,
            course_name="Machine Learning",
            exam_type="UTS",
            exam_date=exam_dt,
            room_or_link="Lab Komputer 301",
            rules="Open Book & Laptop",
            topics=topics,
            target_score=90,
        )
        assert exam.id is not None
        assert exam.course_name == "Machine Learning"

        # Cek persentase penguasaan materi:
        # siap (100) + latihan (75) + belum (0) = 175 // 3 = 58%
        mastery = calculate_exam_mastery(exam.topics)
        assert mastery == 58

        # Update topik index 2 (belum -> paham)
        await update_exam_topic_status(session, user_id, exam.id, 2, "paham")
        exams = await get_upcoming_exams(session, user_id)
        assert len(exams) == 1
        assert exams[0].topics[2]["status"] == "paham"

        # Format HTML
        html = format_exams_html(exams)
        assert "UTS: Machine Learning" in html
        assert "Open Book & Laptop" in html
        assert "Lab Komputer 301" in html
        assert "Kesiapan Materi" in html


# ============================================================================
# 3. TEST FINAL PROJECT HUB
# ============================================================================

@pytest.mark.asyncio
async def test_course_project_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]
    deadline_proj = utcnow() + timedelta(days=20)

    async with session_factory() as session:
        prj = await add_course_project(
            session=session,
            user_id=user_id,
            course_name="Sistem Informasi Lanjut",
            title="Sistem Rekomendasi E-Commerce Multi-tenant",
            deadline=deadline_proj,
        )
        assert prj.id is not None
        assert len(prj.milestones) == 4
        assert len(prj.deliverables) == 4

        # Initial progress
        init_prog = calculate_project_progress(prj)
        assert init_prog == 0

        # Update milestone 0 to done
        await update_project_milestone(
            session, user_id, prj.id, 0, "done", pic="Frans"
        )
        # Update milestone 1 to in_progress
        await update_project_milestone(
            session, user_id, prj.id, 1, "in_progress", pic="Frans & B"
        )
        # Toggle deliverable 0 (Repo GitHub)
        await toggle_project_deliverable(session, user_id, prj.id, 0)

        projects = await get_active_course_projects(session, user_id)
        assert len(projects) == 1
        p = projects[0]
        assert p.milestones[0]["status"] == "done"
        assert p.milestones[0]["pic"] == "Frans"
        assert p.deliverables[0]["done"] is True

        prog_after = calculate_project_progress(p)
        assert prog_after > 0

        html = format_projects_html(projects)
        assert "Sistem Rekomendasi E-Commerce" in html
        assert "Milestone & Pembagian Tim" in html
        assert "Berkas Pengumpulan" in html


# ============================================================================
# 4. TEST KEYBOARD BUILDERS & COMMAND HANDLERS
# ============================================================================

@pytest.mark.asyncio
async def test_bot_coursework_commands_and_callbacks(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    session_factory = setup_test_db["session_factory"]

    # Seed data awal
    async with session_factory() as session:
        a = await add_course_assignment(
            session, user_id, "Jaringan Komputer", "Analisis Wireshark", "Praktikum"
        )
        ex = await add_course_exam(
            session, user_id, "Jaringan Komputer", "UAS", utcnow() + timedelta(days=10)
        )
        prj = await add_course_project(
            session, user_id, "Jaringan Komputer", "Simulasi Jaringan Kampus"
        )
        aid = a.id
        ex_id = ex.id
        p_id = prj.id

    # 1. /tugas command
    update_tugas = MockUpdate(chat_id)
    await bot_module.tugas_cmd(update_tugas, MockContext())
    assert len(update_tugas.effective_message.replies) == 1
    assert "DAFTAR TUGAS KULIAH AKTIF" in update_tugas.effective_message.replies[0]
    assert update_tugas.effective_message.reply_markups is not None

    # 2. Callback 1-tap done tugas
    update_cb_done = MockUpdate(chat_id, callback_data=f"coursework:done:{aid}")
    await bot_module.coursework_callback(update_cb_done, MockContext())
    assert update_cb_done.callback_query.answered is True
    assert "Tugas berhasil ditandai selesai" in update_cb_done.callback_query.answer_text

    # 3. /ujian command
    update_ujian = MockUpdate(chat_id)
    await bot_module.ujian_cmd(update_ujian, MockContext())
    assert len(update_ujian.effective_message.replies) == 1
    assert "RADAR PERSIAPAN UJIAN" in update_ujian.effective_message.replies[0]

    # 4. Callback cycle topic status
    update_cb_topic = MockUpdate(chat_id, callback_data=f"coursework:topic:{ex_id}:0")
    await bot_module.coursework_callback(update_cb_topic, MockContext())
    assert update_cb_topic.callback_query.answered is True

    # 5. /tubes command
    update_tubes = MockUpdate(chat_id)
    await bot_module.tubes_cmd(update_tubes, MockContext())
    assert len(update_tubes.effective_message.replies) == 1
    assert "FINAL PROJECT & TUGAS BESAR HUB" in update_tubes.effective_message.replies[0]

    # 6. Callback cycle milestone & toggle deliverable
    update_cb_m = MockUpdate(chat_id, callback_data=f"coursework:milestone:{p_id}:0")
    await bot_module.coursework_callback(update_cb_m, MockContext())
    assert update_cb_m.callback_query.answered is True

    update_cb_d = MockUpdate(chat_id, callback_data=f"coursework:deliv:{p_id}:0")
    await bot_module.coursework_callback(update_cb_d, MockContext())
    assert update_cb_d.callback_query.answered is True

    # 7. /kuliah command center
    update_kuliah = MockUpdate(chat_id)
    await bot_module.kuliah_cmd(update_kuliah, MockContext())
    assert len(update_kuliah.effective_message.replies) == 1
    assert "KULIAH COMMAND CENTER" in update_kuliah.effective_message.replies[0]

    # 8. Callback menu navigation
    update_cb_menu = MockUpdate(chat_id, callback_data="coursework:menu:ujian")
    await bot_module.coursework_callback(update_cb_menu, MockContext())
    assert update_cb_menu.callback_query.answered is True
