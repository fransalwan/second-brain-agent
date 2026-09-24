# apps/backend/tests/test_health_module.py
"""Unit tests untuk Modul Kesehatan:
- /tidur & callback health:sleep (durasi, kualitas, 7-day average)
- /minum & callback health:water (penambahan gelas air, visual progress bar, reset)
- /stretch & callback health:stretch (micro-stretching guide, auto-check habit)
- /vitamin & callback health:vitamin (check-in suplemen, auto-check habit)
- /kesehatan & kalkulasi Burnout Risk Index
"""

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Habit, HabitLog, HealthCheckLog, HydrationLog, Profile, SleepLog, TimeLog, utcnow
import app.bot as bot_module
import app.health as health_module


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
        self.reply_markups = []

    async def reply_text(self, text: str, *args, **kwargs):
        self.replies.append(text)
        if "reply_markup" in kwargs:
            self.reply_markups.append(kwargs["reply_markup"])


class MockBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id: int, text: str, **kwargs):
        self.sent_messages.append({"chat_id": chat_id, "text": text, **kwargs})


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
    health_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 998811

    async with TestSessionLocal() as session:
        profile = Profile(
            id=user_id,
            email="health_user@example.com",
            full_name="Healthy Developer",
            telegram_chat_id=chat_id,
        )
        session.add(profile)
        await session.commit()

    yield {"user_id": user_id, "chat_id": chat_id, "session_factory": TestSessionLocal}
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_tidur_cmd_and_interactive_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. /tidur tanpa argumen saat belum ada log
    update1 = MockUpdate(chat_id)
    await bot_module.tidur_cmd(update1, MockContext())
    assert len(update1.effective_message.replies) == 1
    reply1 = update1.effective_message.replies[0]
    assert "Pelacak Tidur & Pemulihan" in reply1
    assert "Belum dicatat" in reply1

    # 2. Callback 1-tap tidur 7 jam cukup
    update_cb = MockUpdate(chat_id, callback_data="health:sleep:7.0:Cukup")
    await bot_module.health_callback(update_cb, MockContext())
    assert update_cb.callback_query.answered is True
    assert "Tidur 7.0 jam (Cukup) berhasil dicatat!" in update_cb.callback_query.answer_text

    # Verifikasi di database
    async with Session() as session:
        res = await session.execute(select(SleepLog).where(SleepLog.user_id == user_id))
        logs = res.scalars().all()
        assert len(logs) == 1
        assert logs[0].hours == 7.0
        assert logs[0].quality == "Cukup"

    # 3. Direct command /tidur 8.5 jam nyenyak
    update2 = MockUpdate(chat_id)
    await bot_module.tidur_cmd(update2, MockContext(args=["8.5", "jam", "nyenyak"]))
    reply2 = update2.effective_message.replies[0]
    assert "Tidur Berhasil Dicatat" in reply2
    assert "8.5 Jam" in reply2
    assert "Nyenyak" in reply2

    # Verifikasi update di database (tetap 1 log per tanggal hari ini)
    async with Session() as session:
        res = await session.execute(select(SleepLog).where(SleepLog.user_id == user_id))
        logs = res.scalars().all()
        assert len(logs) == 1
        assert logs[0].hours == 8.5


@pytest.mark.asyncio
async def test_minum_cmd_and_callback(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. /minum menambah +1 gelas pertama kali
    update1 = MockUpdate(chat_id)
    await bot_module.minum_cmd(update1, MockContext())
    reply1 = update1.effective_message.replies[0]
    assert "Pencatat Hidrasi Tubuh" in reply1
    assert "1/8 Gelas (250 / 2000 ml)" in reply1

    # 2. Callback +2 gelas
    update_cb1 = MockUpdate(chat_id, callback_data="health:water:add2")
    await bot_module.health_callback(update_cb1, MockContext())
    assert "+2 Gelas dicatat (3/8 gelas)!" in update_cb1.callback_query.answer_text
    assert "3/8 Gelas (750 / 2000 ml)" in update_cb1.callback_query.edited_text

    # 3. Callback +1 gelas
    update_cb2 = MockUpdate(chat_id, callback_data="health:water:add1")
    await bot_module.health_callback(update_cb2, MockContext())
    assert "+1 Gelas dicatat (4/8 gelas)!" in update_cb2.callback_query.answer_text
    assert "4/8 Gelas (1000 / 2000 ml)" in update_cb2.callback_query.edited_text

    # 4. /minum status tanpa menambah
    update_status = MockUpdate(chat_id)
    await bot_module.minum_cmd(update_status, MockContext(args=["status"]))
    assert "4/8 Gelas (1000 / 2000 ml)" in update_status.effective_message.replies[0]

    # 5. Callback reset ke 0
    update_reset = MockUpdate(chat_id, callback_data="health:water:reset")
    await bot_module.health_callback(update_reset, MockContext())
    assert "Hitungan air di-reset ke 0" in update_reset.callback_query.answer_text
    assert "0/8 Gelas (0 / 2000 ml)" in update_reset.callback_query.edited_text


@pytest.mark.asyncio
async def test_stretch_cmd_and_habit_auto_check(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # Buat habit "Peregangan Leher & Bahu"
    async with Session() as session:
        h = Habit(user_id=user_id, name="Peregangan Ringan", is_active=True)
        session.add(h)
        await session.commit()

    # 1. Jalankan /stretch
    update1 = MockUpdate(chat_id)
    await bot_module.stretch_cmd(update1, MockContext())
    reply1 = update1.effective_message.replies[0]
    assert "Panduan Micro-Stretching 3 Menit" in reply1
    assert "Neck Release" in reply1
    assert "Wrist & Forearm Flex" in reply1

    # 2. Callback selesai peregangan
    update_cb = MockUpdate(chat_id, callback_data="health:stretch:done")
    await bot_module.health_callback(update_cb, MockContext())
    assert "Peregangan selesai" in update_cb.callback_query.answer_text
    assert "Peregangan Berhasil Dicatat" in update_cb.callback_query.edited_text

    # 3. Verifikasi habit otomatis dicentang di habit_logs
    today = date.today()
    async with Session() as session:
        hl_res = await session.execute(
            select(HabitLog).where(
                HabitLog.user_id == user_id, HabitLog.completed_date == today
            )
        )
        logs = hl_res.scalars().all()
        assert len(logs) == 1


@pytest.mark.asyncio
async def test_vitamin_cmd_and_habit_auto_check(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # Buat habit "Minum Vitamin C"
    async with Session() as session:
        h = Habit(user_id=user_id, name="Minum Vitamin Harian", is_active=True)
        session.add(h)
        await session.commit()

    # 1. Jalankan /vitamin
    update1 = MockUpdate(chat_id)
    await bot_module.vitamin_cmd(update1, MockContext())
    reply1 = update1.effective_message.replies[0]
    assert "Check-in Vitamin & Suplemen" in reply1
    assert "otomatis dicentang" in reply1
    assert "Minum Vitamin" in reply1

    # 2. Callback vitamin done
    update_cb = MockUpdate(chat_id, callback_data="health:vitamin:done")
    await bot_module.health_callback(update_cb, MockContext())
    assert "Vitamin dicatat" in update_cb.callback_query.answer_text
    assert "Vitamin Hari Ini Selesai" in update_cb.callback_query.edited_text


@pytest.mark.asyncio
async def test_kesehatan_dashboard_and_burnout_calculation(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # Simulasikan kondisi beban:
    # 1. Catat tidur kurang (< 6 jam) selama 2 hari terakhir
    today = date.today()
    async with Session() as session:
        s1 = SleepLog(user_id=user_id, date=today - timedelta(days=1), hours=4.5, quality="Kurang")
        s2 = SleepLog(user_id=user_id, date=today, hours=5.0, quality="Kurang")
        # Catat hidrasi 5 gelas
        hyd = HydrationLog(user_id=user_id, date=today, glasses=5, target_glasses=8)
        session.add_all([s1, s2, hyd])
        await session.commit()

    # Panggil /kesehatan
    update = MockUpdate(chat_id)
    await bot_module.kesehatan_cmd(update, MockContext())
    reply = update.effective_message.replies[0]

    assert "Dashboard Kesehatan & Vitalitas Pengembang" in reply
    assert "5.0 Jam" in reply
    assert "Kurang" in reply
    assert "5/8 Gelas" in reply
    assert "Burnout Risk Index" in reply
    assert "Kurang tidur (< 6 jam)" in reply
