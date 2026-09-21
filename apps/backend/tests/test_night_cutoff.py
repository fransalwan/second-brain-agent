# apps/backend/tests/test_night_cutoff.py
import asyncio
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Profile, TimeLog
import app.scheduler as scheduler_module
import app.agent as agent_module
import app.bot as bot_module
from app.scheduler import is_past_night_cutoff


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str, parse_mode: str = None):
        self.replies.append({"text": text, "parse_mode": parse_mode})


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


class MockToolContext:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = str(user_id)


def test_is_past_night_cutoff_logic():
    # 1. Cutoff standar 23:00 (reset pagi 04:00)
    cutoff = time(23, 0)
    assert not is_past_night_cutoff(time(22, 59), cutoff)
    assert is_past_night_cutoff(time(23, 0), cutoff)
    assert is_past_night_cutoff(time(23, 45), cutoff)
    assert is_past_night_cutoff(time(0, 30), cutoff)
    assert is_past_night_cutoff(time(3, 59), cutoff)
    assert not is_past_night_cutoff(time(4, 0), cutoff)
    assert not is_past_night_cutoff(time(14, 0), cutoff)

    # 2. Cutoff tengah malam 00:00
    cutoff_midnight = time(0, 0)
    assert not is_past_night_cutoff(time(23, 59), cutoff_midnight)
    assert is_past_night_cutoff(time(0, 0), cutoff_midnight)
    assert is_past_night_cutoff(time(1, 15), cutoff_midnight)
    assert not is_past_night_cutoff(time(4, 0), cutoff_midnight)

    # 3. Cutoff pukul 22:30
    cutoff_early = time(22, 30)
    assert not is_past_night_cutoff(time(22, 29), cutoff_early)
    assert is_past_night_cutoff(time(22, 30), cutoff_early)
    assert is_past_night_cutoff(time(23, 0), cutoff_early)

    print(
        "Test 1 PASSED: Logika is_past_night_cutoff valid untuk berbagai skenario jam."
    )


async def test_scheduler_night_warnings():
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
        # Profile 1: Batas 23:00, timer aktif
        p1 = Profile(
            id=u1_id,
            full_name="User Late Night",
            telegram_chat_id=111111,
            night_cutoff_time=time(23, 0),
        )
        # Profile 2: Batas 22:00, timer sudah ada warning (night_warning_sent=True)
        p2 = Profile(
            id=u2_id,
            full_name="User Already Reminded",
            telegram_chat_id=222222,
            night_cutoff_time=time(22, 0),
        )
        # Profile 3: Batas 23:00, timer sudah selesai (ended_at not None)
        p3 = Profile(
            id=u3_id,
            full_name="User Ended",
            telegram_chat_id=333333,
            night_cutoff_time=time(23, 0),
        )
        # Profile 4: Batas 01:00 (belum lewat batas jika saat ini 23:30)
        p4 = Profile(
            id=u4_id,
            full_name="User Later Cutoff",
            telegram_chat_id=444444,
            night_cutoff_time=time(1, 0),
        )
        session.add_all([p1, p2, p3, p4])

        t1 = TimeLog(
            user_id=u1_id,
            project_name="Night Coding",
            started_at=now_utc - timedelta(minutes=45),
            ended_at=None,
            night_warning_sent=False,
        )
        t2 = TimeLog(
            user_id=u2_id,
            project_name="Already Warned",
            started_at=now_utc - timedelta(minutes=60),
            ended_at=None,
            night_warning_sent=True,
        )
        t3 = TimeLog(
            user_id=u3_id,
            project_name="Ended Night Task",
            started_at=now_utc - timedelta(minutes=80),
            ended_at=now_utc - timedelta(minutes=20),
            duration_minutes=60,
            night_warning_sent=False,
        )
        t4 = TimeLog(
            user_id=u4_id,
            project_name="Later Task",
            started_at=now_utc - timedelta(minutes=30),
            ended_at=None,
            night_warning_sent=False,
        )
        session.add_all([t1, t2, t3, t4])
        await session.commit()

    # Simulasi waktu lokal pukul 23:30 WIB
    class MockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 21, 23, 30, 0, tzinfo=tz)

    orig_dt = scheduler_module.datetime
    scheduler_module.datetime = MockDatetime
    try:
        mock_bot = MockBot()
        sent = await scheduler_module.check_and_send_night_warnings(mock_bot)

        # 1. Hanya User 1 yang memenuhi syarat (batas 23:00, jam simulasi 23:30)
        # User 2: night_warning_sent=True
        # User 3: ended_at not None
        # User 4: cutoff 01:00 (23:30 belum lewat cutoff)
        assert sent == 1
        assert len(mock_bot.sent_messages) == 1
        msg = mock_bot.sent_messages[0]
        assert msg["chat_id"] == 111111
        assert "Sudah Larut Malam!" in msg["text"]
        assert "23:00" in msg["text"]
        assert "Night Coding" in msg["text"]
        assert "45 menit" in msg["text"]
        print(
            "Test 2 PASSED: Pengingat jam malam proaktif hanya terkirim ke user yang memenuhi syarat."
        )

        # 2. Verifikasi status di database ter-update
        async with TestSessionLocal() as session:
            t1_check = (
                await session.execute(select(TimeLog).where(TimeLog.user_id == u1_id))
            ).scalar_one()
            assert t1_check.night_warning_sent is True
        print("Test 3 PASSED: night_warning_sent di-update ke True di DB.")

        # 3. Eksekusi kedua -> Anti-spam (0 pesan terkirim)
        mock_bot_second = MockBot()
        sent_second = await scheduler_module.check_and_send_night_warnings(
            mock_bot_second
        )
        assert sent_second == 0
        assert len(mock_bot_second.sent_messages) == 0
        print("Test 4 PASSED: Anti-spam pengingat jam malam berfungsi normal.")
    finally:
        scheduler_module.datetime = orig_dt


async def test_start_timer_night_warning():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    agent_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    u_id = uuid.uuid4()
    async with TestSessionLocal() as session:
        prof = Profile(
            id=u_id,
            full_name="Night Owl",
            telegram_chat_id=555555,
            night_cutoff_time=time(23, 0),
        )
        session.add(prof)
        await session.commit()

    tool_ctx = MockToolContext(u_id)

    # 1. Start timer saat siang hari (pukul 14:00)
    class DaytimeMock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 21, 14, 0, 0, tzinfo=tz)

    orig_dt = agent_module.datetime
    agent_module.datetime = DaytimeMock
    try:
        res_day = await agent_module.start_timer("Siang Task", tool_ctx)
        assert res_day["status"] == "success"
        assert "night_warning" not in res_day
        async with TestSessionLocal() as session:
            log_day = (
                await session.execute(
                    select(TimeLog).where(TimeLog.project_name == "Siang Task")
                )
            ).scalar_one()
            assert log_day.night_warning_sent is False
            # Hentikan timer agar bisa uji berikutnya
            log_day.ended_at = datetime.now(timezone.utc)
            session.add(log_day)
            await session.commit()
        print("Test 5 PASSED: start_timer di siang hari tidak memicu night warning.")
    finally:
        agent_module.datetime = orig_dt

    # 2. Start timer saat larut malam (pukul 23:15)
    class NighttimeMock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 21, 23, 15, 0, tzinfo=tz)

    agent_module.datetime = NighttimeMock
    try:
        res_night = await agent_module.start_timer("Malam Urgent", tool_ctx)
        assert res_night["status"] == "success"
        assert "night_warning" in res_night
        assert "larut malam" in res_night["night_warning"]
        assert "23:15" in res_night["night_warning"]
        assert "23:00" in res_night["night_warning"]
        assert "Malam Urgent" in res_night["message"]

        # Verifikasi flag night_warning_sent = True agar scheduler tidak mengirim notifikasi ganda
        async with TestSessionLocal() as session:
            log_night = (
                await session.execute(
                    select(TimeLog).where(TimeLog.project_name == "Malam Urgent")
                )
            ).scalar_one()
            assert log_night.night_warning_sent is True
        print(
            "Test 6 PASSED: start_timer di larut malam menyertakan soft warning & men-set night_warning_sent=True."
        )
    finally:
        agent_module.datetime = orig_dt


async def test_night_command():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    u_id = uuid.uuid4()
    chat_id = 777888

    async with TestSessionLocal() as session:
        prof = Profile(
            id=u_id,
            full_name="Tester Bedtime",
            telegram_chat_id=chat_id,
            night_cutoff_time=time(23, 0),
        )
        session.add(prof)
        await session.commit()

    # 1. Cek /night tanpa argumen -> tampilkan batas saat ini (23:00)
    u1 = MockUpdate(chat_id)
    await bot_module.night_cmd(u1, MockContext([]))
    reply1 = u1.effective_message.replies[-1]["text"]
    assert "23:00" in reply1
    assert "/night HH:MM" in reply1
    print(
        "Test 7 PASSED: /night tanpa argumen menampilkan batas jam kerja malam saat ini."
    )

    # 2. Ubah batas jam dengan /night 22:15
    u2 = MockUpdate(chat_id)
    await bot_module.night_cmd(u2, MockContext(["22:15"]))
    reply2 = u2.effective_message.replies[-1]["text"]
    assert "berhasil diubah ke pukul <b>22:15</b>" in reply2

    # Verifikasi perubahan tersimpan di database
    async with TestSessionLocal() as session:
        p_check = (
            await session.execute(select(Profile).where(Profile.id == u_id))
        ).scalar_one()
        assert p_check.night_cutoff_time == time(22, 15)
    print(
        "Test 8 PASSED: /night 22:15 berhasil memperbarui batas jam malam di database."
    )

    # 3. Format tidak valid (/night 25:00 atau /night abc)
    u3 = MockUpdate(chat_id)
    await bot_module.night_cmd(u3, MockContext(["25:00"]))
    reply3 = u3.effective_message.replies[-1]["text"]
    assert "Format jam tidak valid" in reply3

    u4 = MockUpdate(chat_id)
    await bot_module.night_cmd(u4, MockContext(["tengah_malam"]))
    reply4 = u4.effective_message.replies[-1]["text"]
    assert "Format jam tidak valid" in reply4
    print("Test 9 PASSED: Validasi format jam /night menolak input tidak valid.")

    # 4. User belum terhubung (/night dari unknown chat)
    u5 = MockUpdate(999999)
    await bot_module.night_cmd(u5, MockContext([]))
    reply5 = u5.effective_message.replies[-1]["text"]
    assert "belum terhubung" in reply5
    print("Test 10 PASSED: /night untuk chat_id yang belum terhubung ditolak.")


async def main():
    test_is_past_night_cutoff_logic()
    await test_scheduler_night_warnings()
    await test_start_timer_night_warning()
    await test_night_command()
    print("\nALL NIGHT WORK LIMIT / BEDTIME GUARDIAN TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
