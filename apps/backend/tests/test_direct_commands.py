# apps/backend/tests/test_direct_commands.py
import asyncio
import uuid
from datetime import date, datetime
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Area, Task, Profile
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


async def run_all_tests():
    # Gunakan SQLite in-memory murni (Aturan 13: tidak menyentuh database asli)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_a_id = uuid.uuid4()
    chat_a_id = 111111

    user_b_id = uuid.uuid4()
    chat_b_id = 222222

    async with TestSessionLocal() as session:
        prof_a = Profile(id=user_a_id, full_name="User A", telegram_chat_id=chat_a_id)
        prof_b = Profile(id=user_b_id, full_name="User B", telegram_chat_id=chat_b_id)
        session.add(prof_a)
        session.add(prof_b)

        # Tambahkan area untuk User A
        area_a = Area(user_id=user_a_id, name="Kuliah", position=1)
        session.add(area_a)
        await session.flush()

        # User A memiliki tugas #1
        task_a = Task(
            id=1,
            user_id=user_a_id,
            area_id=area_a.id,
            title="Tugas Rahasia User A",
            deadline=date(2026, 9, 25),
            status="pending",
        )
        session.add(task_a)
        await session.commit()

    # User A melihat /tasks (memakai fungsi prioritas)
    u_a_tasks = MockUpdate(chat_a_id)
    await bot_module.tasks_cmd(u_a_tasks, MockContext())
    tasks_reply = u_a_tasks.effective_message.replies[-1]
    assert "#1 [Kuliah] Tugas Rahasia User A — " in tasks_reply

    # 1. User B mencoba menjalankan /done 1 (tugas milik User A)
    u_b = MockUpdate(chat_b_id)
    c_b = MockContext(args=["1"])
    await bot_module.done_cmd(u_b, c_b)

    # 2. User B mencoba menjalankan /done 999 (ID tugas fiktif)
    u_b_nonexistent = MockUpdate(chat_b_id)
    c_b_nonexistent = MockContext(args=["999"])
    await bot_module.done_cmd(u_b_nonexistent, c_b_nonexistent)

    reply_unauthorized = u_b.effective_message.replies[-1]
    reply_nonexistent = u_b_nonexistent.effective_message.replies[-1]

    # Pesan penolakan harus IDENTIK (tidak boleh membocorkan keberadaan ID orang lain)
    assert reply_unauthorized == "Tugas #1 tidak ditemukan."
    assert reply_nonexistent == "Tugas #999 tidak ditemukan."
    print("Test Cross-User 1 PASSED: Pesan penolakan identik, tanpa kebocoran ID.")

    # Verifikasi tugas User A tetap pending di database
    async with TestSessionLocal() as session:
        t_check = (await session.execute(select(Task).where(Task.id == 1))).scalar_one()
        assert t_check.status == "pending"
        assert t_check.completed_at is None
    print("Test Cross-User 2 PASSED: Tugas User A tidak berubah statusnya.")

    # 3. User A menjalankan /done 1 (pemilik asli) -> Berhasil
    u_a = MockUpdate(chat_a_id)
    c_a = MockContext(args=["1"])
    await bot_module.done_cmd(u_a, c_a)
    assert "✅ Selesai: #1 - Tugas Rahasia User A" in u_a.effective_message.replies[-1]

    async with TestSessionLocal() as session:
        t_final = (await session.execute(select(Task).where(Task.id == 1))).scalar_one()
        assert t_final.status == "completed"
        assert t_final.completed_at is not None
        assert isinstance(t_final.completed_at, datetime)
    print("Test Cross-User 3 PASSED: Pemilik asli berhasil menyelesaikan tugas.")

    # 4. User B melihat /tasks -> kosong
    u_b_tasks = MockUpdate(chat_b_id)
    await bot_module.tasks_cmd(u_b_tasks, MockContext())
    assert "Tidak ada tugas pending." in u_b_tasks.effective_message.replies[-1]
    print("Test Cross-User 4 PASSED: /tasks User B terisolasi dari tugas User A.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
