# apps/backend/tests/test_connect_email.py
import asyncio
from datetime import timedelta
from pathlib import Path
import sys
from unittest.mock import AsyncMock
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import InviteCode, Profile, utcnow
import app.bot as bot_module


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


async def test_connect_email_success():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 112233

    async with TestSessionLocal() as session:
        session.add(
            Profile(
                id=user_id,
                email="budi@example.com",
                full_name="Budi Santoso",
                telegram_chat_id=None,
            )
        )
        await session.commit()

    u = MockUpdate(chat_id)
    ctx = MockContext(args=["budi@example.com"])

    await bot_module.connect(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]["text"]
    assert "Berhasil terhubung, Budi Santoso" in reply
    assert "budi@example.com" in reply

    async with TestSessionLocal() as session:
        prof = await session.get(Profile, user_id)
        assert prof.telegram_chat_id == chat_id

    print("Test 1 PASSED: /connect dengan email berhasil menautkan Telegram Chat ID.")


async def test_connect_email_case_insensitive():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 445566

    async with TestSessionLocal() as session:
        session.add(
            Profile(
                id=user_id,
                email="Siti.Rahma@Domain.COM",
                full_name="Siti Rahma",
                telegram_chat_id=None,
            )
        )
        await session.commit()

    u = MockUpdate(chat_id)
    ctx = MockContext(args=["siti.rahma@domain.com"])

    await bot_module.connect(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]["text"]
    assert "Berhasil terhubung, Siti Rahma" in reply

    async with TestSessionLocal() as session:
        prof = await session.get(Profile, user_id)
        assert prof.telegram_chat_id == chat_id

    print("Test 2 PASSED: /connect email bersifat case-insensitive.")


async def test_connect_email_already_linked_to_other():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    existing_chat = 12345
    new_attacker_chat = 99999

    async with TestSessionLocal() as session:
        session.add(
            Profile(
                id=user_id,
                email="victor@example.com",
                full_name="Victor",
                telegram_chat_id=existing_chat,
            )
        )
        await session.commit()

    u = MockUpdate(new_attacker_chat)
    ctx = MockContext(args=["victor@example.com"])

    await bot_module.connect(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]["text"]
    assert "sudah terhubung ke akun Telegram lain" in reply

    async with TestSessionLocal() as session:
        prof = await session.get(Profile, user_id)
        # Tetap milik existing_chat, tidak boleh berubah
        assert prof.telegram_chat_id == existing_chat

    print("Test 3 PASSED: Pembajakan email yang sudah terhubung ditolak tegas.")


async def test_connect_email_not_registered():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    u = MockUpdate(778899)
    ctx = MockContext(args=["unknown@domain.com"])

    await bot_module.connect(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]["text"]
    assert "belum terdaftar" in reply
    assert "daftar akun terlebih dahulu" in reply

    print(
        "Test 4 PASSED: Email belum terdaftar memberikan arahan registrasi di web dashboard."
    )


async def test_connect_invite_code_fallback():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 665544
    code = "SB-ABCD-1234"

    async with TestSessionLocal() as session:
        session.add(
            InviteCode(
                code=code,
                auth_user_id=user_id,
                full_name="User Invite",
                expires_at=utcnow() + timedelta(days=1),
            )
        )
        await session.commit()

    u = MockUpdate(chat_id)
    ctx = MockContext(args=[code])

    await bot_module.connect(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]["text"]
    assert "Berhasil terhubung, User Invite" in reply

    async with TestSessionLocal() as session:
        prof = await session.get(Profile, user_id)
        assert prof is not None
        assert prof.telegram_chat_id == chat_id

    print(
        "Test 5 PASSED: Penautan legacy via kode undangan SB-XXXX tetap berfungsi 100%."
    )


def main():
    asyncio.run(test_connect_email_success())
    asyncio.run(test_connect_email_case_insensitive())
    asyncio.run(test_connect_email_already_linked_to_other())
    asyncio.run(test_connect_email_not_registered())
    asyncio.run(test_connect_invite_code_fallback())
    print("\nALL CONNECT EMAIL TESTS PASSED! (100% SUCCESS)")


if __name__ == "__main__":
    main()
