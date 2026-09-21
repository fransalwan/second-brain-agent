# apps/backend/tests/test_break_reminder.py
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Profile, TimeLog
import app.scheduler as scheduler_module
import app.bot as bot_module


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str):
        self.replies.append(text)


class MockUpdate:
    def __init__(self, chat_id: int):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()


class MockContext:
    def __init__(self, args=None):
        self.args = args or []


class MockBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        self.sent_messages.append(
            {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        )


async def test_break_reminder_logic():
    # Gunakan SQLite in-memory murni (Aturan 13)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    scheduler_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    now_utc = datetime.now(timezone.utc)
    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()
    u4_id = uuid.uuid4()

    async with TestSessionLocal() as session:
        # Profile 1: Timer baru berjalan 30 menit (belum waktunya)
        p1 = Profile(id=u1_id, full_name="User 1", telegram_chat_id=111111)
        # Profile 2: Timer sudah berjalan 95 menit (waktunya istirahat!)
        p2 = Profile(id=u2_id, full_name="User 2", telegram_chat_id=222222)
        # Profile 3: Timer 120 menit tapi sudah pernah diingatkan (break_reminder_sent=True)
        p3 = Profile(id=u3_id, full_name="User 3", telegram_chat_id=333333)
        # Profile 4: Timer sudah selesai (ended_at not None)
        p4 = Profile(id=u4_id, full_name="User 4", telegram_chat_id=444444)

        session.add_all([p1, p2, p3, p4])

        t1 = TimeLog(
            user_id=u1_id,
            project_name="Short Task",
            started_at=now_utc - timedelta(minutes=30),
            ended_at=None,
            break_reminder_sent=False,
        )
        t2 = TimeLog(
            user_id=u2_id,
            project_name="Thesis Long Work",
            started_at=now_utc - timedelta(minutes=95),
            ended_at=None,
            break_reminder_sent=False,
        )
        t3 = TimeLog(
            user_id=u3_id,
            project_name="Already Reminded",
            started_at=now_utc - timedelta(minutes=120),
            ended_at=None,
            break_reminder_sent=True,
        )
        t4 = TimeLog(
            user_id=u4_id,
            project_name="Ended Task",
            started_at=now_utc - timedelta(minutes=100),
            ended_at=now_utc - timedelta(minutes=5),
            duration_minutes=95,
            break_reminder_sent=False,
        )

        session.add_all([t1, t2, t3, t4])
        await session.commit()

    mock_bot = MockBot()

    # Eksekusi pengecekan pengingat pertama
    sent = await scheduler_module.check_and_send_break_reminders(mock_bot)

    # 1. Hanya User 2 yang dikirimi pengingat
    assert sent == 1
    assert len(mock_bot.sent_messages) == 1
    assert mock_bot.sent_messages[0]["chat_id"] == 222222
    assert "Waktunya Istirahat Sejenak!" in mock_bot.sent_messages[0]["text"]
    assert "Thesis Long Work" in mock_bot.sent_messages[0]["text"]
    assert "95 menit" in mock_bot.sent_messages[0]["text"]
    print("Test 1 PASSED: Pengingat istirahat hanya terkirim ke timer >= 90 menit.")

    # 2. Verifikasi status break_reminder_sent ter-update di database
    async with TestSessionLocal() as session:
        t2_check = (
            await session.execute(select(TimeLog).where(TimeLog.user_id == u2_id))
        ).scalar_one()
        assert t2_check.break_reminder_sent is True
    print("Test 2 PASSED: break_reminder_sent berubah menjadi True setelah terkirim.")

    # 3. Eksekusi kedua kali (anti-spam) -> tidak ada pesan baru
    mock_bot_second = MockBot()
    sent_second = await scheduler_module.check_and_send_break_reminders(mock_bot_second)
    assert sent_second == 0
    assert len(mock_bot_second.sent_messages) == 0
    print("Test 3 PASSED: Anti-spam terverifikasi (1x pengingat per sesi fokus).")


async def test_timer_and_stop_commands():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    u_id = uuid.uuid4()
    chat_id = 998877

    async with TestSessionLocal() as session:
        prof = Profile(id=u_id, full_name="Tester", telegram_chat_id=chat_id)
        session.add(prof)
        await session.commit()

    # 1. Cek /timer saat belum ada timer berjalan
    u1 = MockUpdate(chat_id)
    await bot_module.timer_cmd(u1, MockContext())
    assert "Tidak ada timer yang sedang berjalan" in u1.effective_message.replies[-1]
    print("Test 4 PASSED: /timer saat kosong.")

    # 2. Mulai timer di database
    now_utc = datetime.now(timezone.utc)
    async with TestSessionLocal() as session:
        t = TimeLog(
            user_id=u_id,
            project_name="Deep Work Thesis",
            started_at=now_utc - timedelta(minutes=45),
            ended_at=None,
        )
        session.add(t)
        await session.commit()

    # 3. Cek /timer saat ada timer aktif
    u2 = MockUpdate(chat_id)
    await bot_module.timer_cmd(u2, MockContext())
    reply_timer = u2.effective_message.replies[-1]
    assert "Timer Aktif: 'Deep Work Thesis'" in reply_timer
    assert "45 menit" in reply_timer
    print("Test 5 PASSED: /timer menampilkan timer aktif dan durasi berjalan.")

    # 4. Hentikan timer via /stop
    u3 = MockUpdate(chat_id)
    await bot_module.stop_cmd(u3, MockContext())
    reply_stop = u3.effective_message.replies[-1]
    assert "Timer 'Deep Work Thesis' dihentikan" in reply_stop
    assert "Total durasi fokus: 45 menit" in reply_stop

    # Verifikasi di database timer sudah selesai
    async with TestSessionLocal() as session:
        t_check = (
            await session.execute(select(TimeLog).where(TimeLog.user_id == u_id))
        ).scalar_one()
        assert t_check.ended_at is not None
        assert t_check.duration_minutes == 45
    print("Test 6 PASSED: /stop berhasil menghentikan timer dan mencatat durasi.")

    # 5. Cek /stop lagi setelah berhenti -> ditolak
    u4 = MockUpdate(chat_id)
    await bot_module.stop_cmd(u4, MockContext())
    assert "Tidak ada timer yang sedang berjalan" in u4.effective_message.replies[-1]
    print("Test 7 PASSED: /stop saat tidak ada timer aktif ditolak dengan benar.")


async def main():
    await test_break_reminder_logic()
    await test_timer_and_stop_commands()
    print("\nALL BREAK REMINDER TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
