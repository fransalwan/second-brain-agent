# apps/backend/tests/test_habits.py
import asyncio
from datetime import date, timedelta
from pathlib import Path
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.brief_formatter import format_brief_message
import app.habits as habits_module
from app.habits import (
    HabitStatus,
    calculate_streak,
    check_habit_for_today,
    get_user_habits_status,
)
from app.models import Habit, HabitLog, Profile
import app.bot as bot_module
import app.agent as agent_module


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str, *args, **kwargs):
        self.replies.append(text)


class MockUpdate:
    def __init__(self, chat_id: int):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()


class MockContext:
    def __init__(self, args=None):
        self.args = args or []


class MockToolContext:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = str(user_id)


def test_calculate_streak():
    today = date(2026, 9, 21)

    # 1. Belum pernah selesai
    assert calculate_streak(set(), today) == 0

    # 2. Selesai hari ini saja
    assert calculate_streak({today}, today) == 1

    # 3. Selesai hari ini, kemarin, dan lusa kemarin
    d_yesterday = today - timedelta(days=1)
    d_prev2 = today - timedelta(days=2)
    assert calculate_streak({today, d_yesterday, d_prev2}, today) == 3

    # 4. Selesai kemarin dan 2 hari lalu (hari ini belum diceklis -> streak masih hidup!)
    assert calculate_streak({d_yesterday, d_prev2}, today) == 2

    # 5. Selesai hari ini tapi kemarin bolong
    assert calculate_streak({today, d_prev2}, today) == 1

    # 6. Selesai 2 hari lalu tapi kemarin dan hari ini bolong (streak putus)
    assert calculate_streak({d_prev2}, today) == 0

    print("Test 1 PASSED: Algoritma calculate_streak terverifikasi akurat.")


def test_brief_formatter_with_habits():
    today = date(2026, 9, 21)
    h1 = Habit(id=1, name="Olahraga 15 menit")
    h2 = Habit(id=2, name="Baca Jurnal")

    habits = [
        HabitStatus(habit=h1, is_completed_today=True, streak=3),
        HabitStatus(habit=h2, is_completed_today=False, streak=0),
    ]

    text = format_brief_message(
        [], total_overdue_count=0, target_date=today, habits=habits
    )
    assert "🌱 <b>Habit hari ini (1/2):</b>" in text
    assert "[✓] Olahraga 15 menit" in text
    assert "[ ] Baca Jurnal" in text
    print("Test 2 PASSED: Brief formatter menyertakan ringkasan habit.")


async def test_habits_database_and_bot():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal
    agent_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    today = date(2026, 9, 21)
    u_a = uuid.uuid4()
    u_b = uuid.uuid4()
    chat_a = 111111
    chat_b = 222222

    async with TestSessionLocal() as session:
        prof_a = Profile(id=u_a, full_name="User A", telegram_chat_id=chat_a)
        prof_b = Profile(id=u_b, full_name="User B", telegram_chat_id=chat_b)
        session.add_all([prof_a, prof_b])
        await session.commit()

    ctx_a = MockToolContext(u_a)
    ctx_b = MockToolContext(u_b)

    # 1. User A menambah habit via agent tool
    res_add1 = await agent_module.add_habit("Olahraga", tool_context=ctx_a)
    assert res_add1["status"] == "success"
    h1_id = res_add1["habit"]["id"]

    res_add2 = await agent_module.add_habit("Baca Buku", tool_context=ctx_a)
    assert res_add2["status"] == "success"
    h2_id = res_add2["habit"]["id"]

    # Menambah duplikat nama ditolak
    res_dup = await agent_module.add_habit("Olahraga", tool_context=ctx_a)
    assert res_dup["status"] == "error"
    assert res_dup["reason"] == "already_exists"
    print("Test 3 PASSED: Tambah habit dan penolakan nama duplikat.")

    # 2. User A melihat /habits
    up_a = MockUpdate(chat_a)
    await bot_module.habits_cmd(up_a, MockContext())
    reply = up_a.effective_message.replies[-1]
    assert "Progres: 0/2 selesai" in reply
    assert f"#{h1_id} [ ] Olahraga" in reply
    assert f"#{h2_id} [ ] Baca Buku" in reply
    print("Test 4 PASSED: /habits menampilkan daftar habit aktif.")

    # 3. User B mencoba /check habit milik User A (Cross-User Protection)
    up_b = MockUpdate(chat_b)
    await bot_module.check_cmd(up_b, MockContext(args=[str(h1_id)]))
    reply_unauth = up_b.effective_message.replies[-1]

    # User B mencoba /check ID 9999
    up_b_none = MockUpdate(chat_b)
    await bot_module.check_cmd(up_b_none, MockContext(args=["9999"]))
    reply_none = up_b_none.effective_message.replies[-1]

    # Pesan penolakan HARUS identik (Aturan 3 & Keamanan)
    assert reply_unauth == f"Habit #{h1_id} tidak ditemukan."
    assert reply_none == "Habit #9999 tidak ditemukan."
    print("Test 5 PASSED: Cross-user isolation pada /check habit terverifikasi.")

    # 4. User A menjalankan /check 1 (Centang pertama kali)
    up_a_check = MockUpdate(chat_a)
    await bot_module.check_cmd(up_a_check, MockContext(args=[str(h1_id)]))
    assert (
        f"✅ Mantap! Habit #{h1_id} ('Olahraga') selesai hari ini."
        in up_a_check.effective_message.replies[-1]
    )

    # Verifikasi log di database
    async with TestSessionLocal() as session:
        logs = (
            (await session.execute(select(HabitLog).where(HabitLog.habit_id == h1_id)))
            .scalars()
            .all()
        )
        assert len(logs) == 1

    # 5. User A menjalankan /check 1 kedua kali (Idempotency - Opsi A)
    up_a_check2 = MockUpdate(chat_a)
    await bot_module.check_cmd(up_a_check2, MockContext(args=[str(h1_id)]))
    assert (
        f"Habit #{h1_id} ('Olahraga') sudah dicentang hari ini."
        in up_a_check2.effective_message.replies[-1]
    )

    # Pastikan tidak ada duplikasi baris di database
    async with TestSessionLocal() as session:
        logs2 = (
            (await session.execute(select(HabitLog).where(HabitLog.habit_id == h1_id)))
            .scalars()
            .all()
        )
        assert len(logs2) == 1
    print("Test 6 PASSED: Centang habit idempotent tanpa duplikasi log.")

    # 6. User A cek /habits kembali
    up_a_status2 = MockUpdate(chat_a)
    await bot_module.habits_cmd(up_a_status2, MockContext())
    reply2 = up_a_status2.effective_message.replies[-1]
    assert "Progres: 1/2 selesai" in reply2
    assert f"#{h1_id} [✓] Olahraga 🔥 1 hari" in reply2
    assert f"#{h2_id} [ ] Baca Buku" in reply2
    print("Test 7 PASSED: /habits mencerminkan status centang terbaru.")

    # 7. Soft delete habit
    del_res = await agent_module.delete_habit(str(h2_id), tool_context=ctx_a)
    assert del_res["status"] == "success"

    up_a_status3 = MockUpdate(chat_a)
    await bot_module.habits_cmd(up_a_status3, MockContext())
    reply3 = up_a_status3.effective_message.replies[-1]
    assert "Progres: 1/1 selesai" in reply3
    assert "Baca Buku" not in reply3
    print("Test 8 PASSED: delete_habit menonaktifkan habit dari daftar aktif.")


async def main():
    test_calculate_streak()
    test_brief_formatter_with_habits()
    await test_habits_database_and_bot()
    print("\nALL HABITS UNIT & INTEGRATION TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
