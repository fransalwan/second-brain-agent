# apps/backend/tests/test_v1_features.py
"""Unit tests untuk fitur rilis v1.0:
- Interactive task completion callback (task:done:<id>)
- Interactive habit check callback (habit:check:<id>)
- Interactive timer stop callback (timer:stop)
- 1-Click Starter Presets (/preset & preset:academic)
- Data export to Markdown (/export)
- Privacy transparency (/privacy)
- Self-service disconnect (/disconnect)
"""

import asyncio
from datetime import date, datetime, timezone
import io
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, col, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Area, Habit, HabitLog, Note, Profile, Task, TimeLog, utcnow
import app.bot as bot_module


class MockCallbackQuery:
    def __init__(self, data: str, chat_id: int):
        self.data = data
        self.message = MockMessage()
        self.answered = False
        self.answer_text = None
        self.edited_text = None

    async def answer(self, text: str = None, show_alert: bool = False):
        self.answered = True
        self.answer_text = text

    async def edit_message_text(self, text: str, **kwargs):
        self.edited_text = text


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str, *args, **kwargs):
        self.replies.append(text)


class MockBot:
    def __init__(self):
        self.sent_documents = []

    async def send_document(self, chat_id: int, document, filename: str, caption: str, **kwargs):
        self.sent_documents.append({
            "chat_id": chat_id,
            "filename": filename,
            "content": document.getvalue().decode("utf-8"),
            "caption": caption,
        })


class MockUpdate:
    def __init__(self, chat_id: int, callback_data: str = None):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()
        self.callback_query = (
            MockCallbackQuery(callback_data, chat_id) if callback_data else None
        )


class MockContext:
    def __init__(self, args=None):
        self.args = args or []
        self.bot = MockBot()


@pytest.fixture
async def setup_test_db():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 998877

    async with TestSessionLocal() as session:
        profile = Profile(
            id=user_id,
            email="v1tester@example.com",
            full_name="V1 Tester",
            telegram_chat_id=chat_id,
        )
        session.add(profile)
        await session.commit()

    yield {"user_id": user_id, "chat_id": chat_id, "session_factory": TestSessionLocal}
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_privacy_command(setup_test_db):
    chat_id = setup_test_db["chat_id"]
    update = MockUpdate(chat_id)
    await bot_module.privacy_cmd(update, MockContext())

    assert len(update.effective_message.replies) == 1
    reply = update.effective_message.replies[0]
    assert "Jaminan Privasi & Keamanan Data" in reply
    assert "PostgreSQL RLS" in reply


@pytest.mark.asyncio
async def test_interactive_task_done_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    async with Session() as session:
        task = Task(user_id=user_id, title="Test Interactive Task", status="pending")
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id

    update = MockUpdate(chat_id, callback_data=f"task:done:{task_id}")
    await bot_module.task_callback(update, MockContext())

    assert update.callback_query.answered is True
    assert f"#{task_id}" in update.callback_query.answer_text

    async with Session() as session:
        t = await session.get(Task, task_id)
        assert t.status == "completed"
        assert t.completed_at is not None


@pytest.mark.asyncio
async def test_interactive_habit_check_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    async with Session() as session:
        habit = Habit(user_id=user_id, name="Olahraga Pagi", is_active=True)
        session.add(habit)
        await session.commit()
        await session.refresh(habit)
        habit_id = habit.id

    update = MockUpdate(chat_id, callback_data=f"habit:check:{habit_id}")
    await bot_module.habit_callback(update, MockContext())

    assert update.callback_query.answered is True
    assert "Olahraga Pagi dicentang!" in update.callback_query.answer_text


@pytest.mark.asyncio
async def test_interactive_timer_stop_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    async with Session() as session:
        timer = TimeLog(user_id=user_id, project_name="Deep Learning Riset")
        session.add(timer)
        await session.commit()

    update = MockUpdate(chat_id, callback_data="timer:stop")
    await bot_module.timer_callback(update, MockContext())

    assert update.callback_query.answered is True
    assert "Sesi Fokus Dihentikan" in update.callback_query.edited_text

    async with Session() as session:
        t_res = await session.execute(
            select(TimeLog).where(TimeLog.user_id == user_id, col(TimeLog.ended_at).is_(None))
        )
        assert t_res.scalars().first() is None


@pytest.mark.asyncio
async def test_preset_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    update = MockUpdate(chat_id, callback_data="preset:academic")
    await bot_module.preset_callback(update, MockContext())

    assert update.callback_query.answered is True
    assert "Berhasil Diterapkan" in update.callback_query.edited_text

    async with Session() as session:
        areas_res = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position)
        )
        areas = areas_res.scalars().all()
        assert len(areas) == 4
        assert areas[0].name == "Kesehatan"

        habits_res = await session.execute(
            select(Habit).where(Habit.user_id == user_id)
        )
        habits = habits_res.scalars().all()
        assert len(habits) >= 2


@pytest.mark.asyncio
async def test_export_command(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    async with Session() as session:
        session.add(Note(user_id=user_id, content="Catatan penting riset", tags=["riset", "ai"]))
        session.add(Task(user_id=user_id, title="Tugas evaluasi model", status="pending"))
        await session.commit()

    update = MockUpdate(chat_id)
    context = MockContext()
    await bot_module.export_cmd(update, context)

    assert len(context.bot.sent_documents) == 1
    doc = context.bot.sent_documents[0]
    assert doc["filename"].endswith(".md")
    assert "Catatan penting riset" in doc["content"]
    assert "Tugas evaluasi model" in doc["content"]


@pytest.mark.asyncio
async def test_disconnect_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    update = MockUpdate(chat_id, callback_data="disconnect:confirm")
    await bot_module.disconnect_callback(update, MockContext())

    assert "Tautan Akun Berhasil Diputuskan" in update.callback_query.edited_text

    async with Session() as session:
        prof = await session.get(Profile, user_id)
        assert prof.telegram_chat_id is None
