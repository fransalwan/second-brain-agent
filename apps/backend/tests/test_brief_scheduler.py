# apps/backend/tests/test_brief_scheduler.py
import asyncio
from datetime import date, datetime, time, timezone
from pathlib import Path
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.brief_formatter import format_brief_message
from app.models import Area, Profile, Task
from app.priority import (
    PrioritizedTask,
    PriorityTier,
    get_top_tasks_for_brief,
    prioritize_tasks,
)
import app.scheduler as scheduler_module


class MockBot:
    def __init__(self, fail_for_chat_id: int | None = None):
        self.sent_messages = []
        self.fail_for_chat_id = fail_for_chat_id

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        if self.fail_for_chat_id and chat_id == self.fail_for_chat_id:
            raise Exception("Telegram Forbidden: bot was blocked by the user")
        self.sent_messages.append(
            {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        )


def test_brief_formatter_empty():
    today = date(2026, 9, 21)
    text = format_brief_message([], total_overdue_count=0, target_date=today)
    assert "☀️ <b>Brief Pagi</b> | Senin, 21 September 2026" in text
    assert "Tidak ada tugas pending saat ini" in text
    assert "⚠️" not in text
    assert "/tasks" in text
    print("Test Formatter 1 PASSED: Format brief kosong terverifikasi.")


def test_brief_formatter_with_tasks_and_overdue():
    today = date(2026, 9, 21)
    area = Area(name="Kuliah", position=1)
    t1 = Task(id=1, title="Thesis Bab 2 & Analisis <Data>", deadline=today)
    t2 = Task(id=2, title="Kirim Email Dosen", deadline=today)

    p1 = PrioritizedTask(
        task=t1, area=area, tier=PriorityTier.NOW, reason="deadline hari ini"
    )
    p2 = PrioritizedTask(
        task=t2, area=area, tier=PriorityTier.NOW, reason="deadline hari ini"
    )

    top_tasks = [(p1, True), (p2, False)]
    text = format_brief_message(top_tasks, total_overdue_count=2, target_date=today)

    assert "⚠️ <b>Perhatian:</b> Ada 2 tugas yang sudah lewat deadline!" in text
    assert (
        "👉 <b>Mulai dari sini:</b> <b>Thesis Bab 2 &amp; Analisis &lt;Data&gt;</b> [Kuliah]"
        in text
    )
    assert "<i>Alasan: deadline hari ini</i>" in text
    assert "• <b>Kirim Email Dosen</b> [Kuliah]" in text
    print(
        "Test Formatter 2 PASSED: Format brief dengan tugas, overdue banner, dan HTML escaping terverifikasi."
    )


async def test_scheduler_catch_up_and_deduplication():
    # Gunakan SQLite in-memory murni (Aturan 13: tidak menyentuh database asli)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    scheduler_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    today = date(2026, 9, 21)
    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()
    u4_id = uuid.uuid4()

    async with TestSessionLocal() as session:
        # User 1: Eligible (brief_time 07:00, last_brief_date None)
        p1 = Profile(
            id=u1_id,
            full_name="User 1",
            telegram_chat_id=111111,
            brief_time=time(7, 0),
            last_brief_date=None,
        )
        # User 2: Sudah dikirim hari ini (last_brief_date = today)
        p2 = Profile(
            id=u2_id,
            full_name="User 2",
            telegram_chat_id=222222,
            brief_time=time(7, 0),
            last_brief_date=today,
        )
        # User 3: Belum waktunya (brief_time 23:59 malam)
        p3 = Profile(
            id=u3_id,
            full_name="User 3",
            telegram_chat_id=333333,
            brief_time=time(23, 59),
            last_brief_date=None,
        )
        # User 4: Belum connect Telegram (telegram_chat_id None)
        p4 = Profile(
            id=u4_id,
            full_name="User 4",
            telegram_chat_id=None,
            brief_time=time(7, 0),
            last_brief_date=None,
        )

        session.add_all([p1, p2, p3, p4])

        # Tambahkan area dan task untuk User 1
        area1 = Area(user_id=u1_id, name="Kuliah", position=1)
        session.add(area1)
        await session.flush()

        task1 = Task(
            user_id=u1_id, area_id=area1.id, title="Belajar Ujian", status="pending"
        )
        session.add(task1)
        await session.commit()

    mock_bot = MockBot()

    # Eksekusi scheduler pertama kali
    sent = await scheduler_module.check_and_send_briefs(mock_bot)

    # 1. Verifikasi hanya User 1 yang terkirim
    assert sent == 1
    assert len(mock_bot.sent_messages) == 1
    assert mock_bot.sent_messages[0]["chat_id"] == 111111
    assert "Belajar Ujian" in mock_bot.sent_messages[0]["text"]
    assert mock_bot.sent_messages[0]["parse_mode"] == "HTML"
    print("Test Scheduler 1 PASSED: Hanya user eligible yang dikirimi brief.")

    # 2. Verifikasi last_brief_date User 1 ter-update ke today di database
    async with TestSessionLocal() as session:
        p1_check = await session.get(Profile, u1_id)
        assert p1_check.last_brief_date == today
    print("Test Scheduler 2 PASSED: last_brief_date ter-update di database.")

    # 3. Eksekusi scheduler kedua kali (simulasi restart / --reload / interval 15 menit berikutnya)
    mock_bot_second = MockBot()
    sent_second = await scheduler_module.check_and_send_briefs(mock_bot_second)

    # Verifikasi tidak ada pengiriman duplikat
    assert sent_second == 0
    assert len(mock_bot_second.sent_messages) == 0
    print(
        "Test Scheduler 3 PASSED: Tidak ada pengiriman duplikat pada eksekusi ulang di hari yang sama."
    )


async def test_scheduler_error_isolation():
    """Jika pengiriman ke satu user gagal (misal diblokir), user lain tetap terkirim,
    dan last_brief_date user yang gagal TIDAK di-update."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    scheduler_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    u_fail_id = uuid.uuid4()
    u_ok_id = uuid.uuid4()

    async with TestSessionLocal() as session:
        p_fail = Profile(
            id=u_fail_id,
            full_name="User Blocked",
            telegram_chat_id=999999,
            brief_time=time(7, 0),
            last_brief_date=None,
        )
        p_ok = Profile(
            id=u_ok_id,
            full_name="User Normal",
            telegram_chat_id=888888,
            brief_time=time(7, 0),
            last_brief_date=None,
        )
        session.add_all([p_fail, p_ok])
        await session.commit()

    # Mock bot yang melempar exception khusus untuk chat_id 999999
    mock_bot = MockBot(fail_for_chat_id=999999)
    sent = await scheduler_module.check_and_send_briefs(mock_bot)

    # User Normal tetap terkirim
    assert sent == 1
    assert len(mock_bot.sent_messages) == 1
    assert mock_bot.sent_messages[0]["chat_id"] == 888888

    # Cek database: p_ok ter-update, p_fail tetap None
    async with TestSessionLocal() as session:
        check_ok = await session.get(Profile, u_ok_id)
        check_fail = await session.get(Profile, u_fail_id)
        assert check_ok.last_brief_date is not None
        assert check_fail.last_brief_date is None
    print(
        "Test Scheduler 4 PASSED: Isolasi error terverifikasi, user gagal tidak di-update."
    )


async def main():
    test_brief_formatter_empty()
    test_brief_formatter_with_tasks_and_overdue()
    await test_scheduler_catch_up_and_deduplication()
    await test_scheduler_error_isolation()
    print("\nALL BRIEF SCHEDULER TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
