# apps/backend/tests/test_weekly_report.py
import asyncio
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Habit, HabitLog, Profile, Task, TimeLog, utcnow
from app.weekly_report import (
    format_weekly_report_html,
    generate_weekly_insight_llm,
    get_week_boundaries,
    get_weekly_stats,
)
import app.bot as bot_module
import app.scheduler as scheduler_module


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str, parse_mode: str = None, reply_markup=None):
        self.replies.append(
            {"text": text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        )


class MockUpdate:
    def __init__(self, chat_id: int):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()


class MockContext:
    def __init__(self, args=None):
        self.args = args or []
        self.bot = AsyncMock()


def test_week_boundaries():
    # 2026-09-14 adalah Senin, 2026-09-20 adalah Minggu
    mon = date(2026, 9, 14)
    wed = date(2026, 9, 16)
    sun = date(2026, 9, 20)

    start_mon, end_mon = get_week_boundaries(mon)
    assert start_mon == date(2026, 9, 14)
    assert end_mon == date(2026, 9, 20)

    start_wed, end_wed = get_week_boundaries(wed)
    assert start_wed == date(2026, 9, 14)
    assert end_wed == date(2026, 9, 20)

    start_sun, end_sun = get_week_boundaries(sun)
    assert start_sun == date(2026, 9, 14)
    assert end_sun == date(2026, 9, 20)

    print("Test 1 PASSED: Perhitungan rentang pekan (Senin s/d Minggu) valid.")


async def test_get_weekly_stats_and_formatting():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    ref_date = date(2026, 9, 20)  # Minggu
    local_tz = ZoneInfo("Asia/Jakarta")

    async with TestSessionLocal() as session:
        prof = Profile(
            id=user_id,
            full_name="Budi Produktif",
            telegram_chat_id=123456,
            night_cutoff_time=time(23, 0),
        )
        session.add(prof)

        # 1. Sesi Fokus (TimeLog)
        # Sesi 1: Rabu 14:00 - 15:00 WIB (60m)
        s1_start = datetime(2026, 9, 16, 14, 0, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        s1_end = datetime(2026, 9, 16, 15, 0, tzinfo=local_tz).astimezone(timezone.utc)
        session.add(
            TimeLog(
                user_id=user_id,
                project_name="Deep Work A",
                started_at=s1_start,
                ended_at=s1_end,
                duration_minutes=60,
            )
        )
        # Sesi 2: Kamis 10:00 - 10:45 WIB (45m)
        s2_start = datetime(2026, 9, 17, 10, 0, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        s2_end = datetime(2026, 9, 17, 10, 45, tzinfo=local_tz).astimezone(timezone.utc)
        session.add(
            TimeLog(
                user_id=user_id,
                project_name="Deep Work B",
                started_at=s2_start,
                ended_at=s2_end,
                duration_minutes=45,
            )
        )
        # Sesi 3 (Lembur Larut Malam): Jumat 23:30 WIB
        s3_start = datetime(2026, 9, 18, 23, 30, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        s3_end = datetime(2026, 9, 19, 0, 15, tzinfo=local_tz).astimezone(timezone.utc)
        session.add(
            TimeLog(
                user_id=user_id,
                project_name="Night Coding",
                started_at=s3_start,
                ended_at=s3_end,
                duration_minutes=45,
            )
        )

        # 2. Tugas (Task)
        # 2 selesai pekan ini
        t1_completed = datetime(2026, 9, 15, 16, 0, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        t2_completed = datetime(2026, 9, 18, 11, 0, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        session.add(
            Task(
                user_id=user_id,
                title="Tugas Selesai 1",
                status="completed",
                completed_at=t1_completed,
            )
        )
        session.add(
            Task(
                user_id=user_id,
                title="Tugas Selesai 2",
                status="completed",
                completed_at=t2_completed,
            )
        )
        # 1 tugas selesai minggu lalu (di luar rentang)
        old_completed = datetime(2026, 9, 5, 10, 0, tzinfo=local_tz).astimezone(
            timezone.utc
        )
        session.add(
            Task(
                user_id=user_id,
                title="Tugas Lama",
                status="completed",
                completed_at=old_completed,
            )
        )
        # 2 tugas pending
        session.add(Task(user_id=user_id, title="Tugas Pending 1", status="pending"))
        session.add(Task(user_id=user_id, title="Tugas Pending 2", status="pending"))

        # 3. Habits
        h1 = Habit(user_id=user_id, name="Olahraga", is_active=True)
        h2 = Habit(user_id=user_id, name="Membaca", is_active=True)
        session.add(h1)
        session.add(h2)
        await session.commit()
        await session.refresh(h1)
        await session.refresh(h2)

        # 5 log centang dalam pekan ini
        for d in [14, 15, 16]:
            session.add(
                HabitLog(
                    user_id=user_id, habit_id=h1.id, completed_date=date(2026, 9, d)
                )
            )
        for d in [15, 17]:
            session.add(
                HabitLog(
                    user_id=user_id, habit_id=h2.id, completed_date=date(2026, 9, d)
                )
            )

        await session.commit()

        # Jalankan get_weekly_stats
        stats = await get_weekly_stats(session, user_id, ref_date)

    # Validasi Statistik
    # Fokus total: 60 + 45 + 45 = 150 menit = 2 jam 30 menit
    assert stats["total_focus_minutes"] == 150
    assert stats["completed_tasks_count"] == 2
    assert stats["pending_tasks_count"] == 2
    assert stats["active_habits_count"] == 2
    assert stats["total_habit_checks"] == 5
    # Target habit = 2 habits * 7 hari = 14. 5 / 14 = 36%
    assert stats["habit_consistency_pct"] == 36
    # Malam lembur: 18 September (23:30). Sisa 6 malam bersih.
    assert stats["clean_sleep_nights"] == 6

    # Validasi Formatting HTML
    html_report = format_weekly_report_html(stats, insight="Semangat terus!")
    assert "Laporan Mingguan Pola Kerja" in html_report
    assert "2 jam 30 menit" in html_report
    assert "2 tugas berhasil diselesaikan" in html_report
    assert "36%" in html_report
    assert "6 dari 7 malam" in html_report
    assert "Semangat terus!" in html_report

    print("Test 2 PASSED: Agregasi metrik mingguan dan format HTML valid.")


async def test_weekly_command():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 771122

    async with TestSessionLocal() as session:
        prof = Profile(id=user_id, full_name="User Bot", telegram_chat_id=chat_id)
        session.add(prof)
        await session.commit()

    u = MockUpdate(chat_id)
    ctx = MockContext()

    with patch(
        "app.bot.generate_weekly_insight_llm", return_value="Refleksi AI Mantap"
    ):
        await bot_module.weekly_cmd(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert "Laporan Mingguan Pola Kerja" in reply["text"]
    assert "Refleksi AI Mantap" in reply["text"]
    assert reply["parse_mode"] == "HTML"

    print(
        "Test 3 PASSED: Perintah /weekly Telegram berfungsi dan mengirim laporan berformat HTML."
    )


async def test_scheduler_weekly_report():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    scheduler_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 998811

    async with TestSessionLocal() as session:
        prof = Profile(
            id=user_id,
            full_name="Scheduler User",
            telegram_chat_id=chat_id,
            last_weekly_report_date=None,
        )
        session.add(prof)
        await session.commit()

    mock_bot = AsyncMock()

    # 1. Test hari bukan Minggu (misal Rabu 2026-09-16)
    wed_dt = datetime(2026, 9, 16, 20, 15, tzinfo=ZoneInfo("Asia/Jakarta"))
    with patch("app.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = wed_dt
        mock_dt.combine = datetime.combine
        sent = await scheduler_module.check_and_send_weekly_reports(mock_bot)
        assert sent == 0
        mock_bot.send_message.assert_not_called()

    # 2. Test hari Minggu pukul 20:15 WIB (seharusnya terkirim)
    sun_dt = datetime(2026, 9, 20, 20, 15, tzinfo=ZoneInfo("Asia/Jakarta"))
    with patch("app.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = sun_dt
        mock_dt.combine = datetime.combine
        with patch(
            "app.scheduler.generate_weekly_insight_llm", return_value="Insight Minggu"
        ):
            sent = await scheduler_module.check_and_send_weekly_reports(mock_bot)
            assert sent == 1
            mock_bot.send_message.assert_called_once()
            args, kwargs = mock_bot.send_message.call_args
            assert kwargs["chat_id"] == chat_id
            assert "Laporan Mingguan Pola Kerja" in kwargs["text"]

    # 3. Test idempotency (jika dipanggil lagi di hari Minggu yang sama, tidak dobel kirim)
    mock_bot.reset_mock()
    with patch("app.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = sun_dt
        mock_dt.combine = datetime.combine
        sent_again = await scheduler_module.check_and_send_weekly_reports(mock_bot)
        assert sent_again == 0
        mock_bot.send_message.assert_not_called()

    print(
        "Test 4 PASSED: Scheduler laporan mingguan berjalan tepat di Minggu malam dan idempotent."
    )


def main():
    test_week_boundaries()
    asyncio.run(test_get_weekly_stats_and_formatting())
    asyncio.run(test_weekly_command())
    asyncio.run(test_scheduler_weekly_report())
    print("\nALL WEEKLY REPORT TESTS PASSED! (100% SUCCESS)")


if __name__ == "__main__":
    main()
