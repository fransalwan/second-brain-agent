# apps/backend/tests/test_voice_transcriber.py
import asyncio
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Note, Profile
import app.bot as bot_module


class MockVoice:
    def __init__(
        self,
        file_id: str = "voice_file_123",
        duration: int = 15,
        mime_type: str = "audio/ogg",
    ):
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type


class MockMessage:
    def __init__(self, voice=None, audio=None):
        self.voice = voice
        self.audio = audio
        self.text = ""
        self.replies = []

    async def reply_text(self, text: str, parse_mode: str = None, reply_markup=None):
        self.replies.append(
            {"text": text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        )


class MockUpdate:
    def __init__(self, chat_id: int, voice=None, audio=None):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage(voice=voice, audio=audio)


class MockContext:
    def __init__(self):
        self.args = []
        self.bot = AsyncMock()


async def test_voice_message_success():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 882211

    async with TestSessionLocal() as session:
        prof = Profile(id=user_id, full_name="User Voice", telegram_chat_id=chat_id)
        session.add(prof)
        await session.commit()

    voice = MockVoice(duration=10)
    u = MockUpdate(chat_id, voice=voice)
    ctx = MockContext()

    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"fake_audio_bytes")
    ctx.bot.get_file.return_value = mock_file

    mock_genai_response = MagicMock()
    mock_genai_response.text = "tambah tugas beli susu besok"

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_genai_response
        mock_client_cls.return_value = mock_client

        with patch(
            "app.bot.run_agent",
            return_value="✅ Tugas #1 'beli susu' dicatat untuk besok.",
        ) as mock_run:
            await bot_module.handle_voice_message(u, ctx)

            # Validasi pemanggilan run_agent
            mock_run.assert_called_once_with(
                user_id, chat_id, "tambah tugas beli susu besok"
            )

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert '🎙️ "tambah tugas beli susu besok"' in reply["text"]
    assert "✅ Tugas #1 'beli susu' dicatat" in reply["text"]

    print("Test 1 PASSED: Transkripsi voice note berhasil dan diteruskan ke Agent.")


async def test_voice_message_agent_error_fallback():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 991100

    async with TestSessionLocal() as session:
        prof = Profile(
            id=user_id, full_name="User Voice Fallback", telegram_chat_id=chat_id
        )
        session.add(prof)
        await session.commit()

    voice = MockVoice(duration=8)
    u = MockUpdate(chat_id, voice=voice)
    ctx = MockContext()

    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"fake_voice")
    ctx.bot.get_file.return_value = mock_file

    mock_genai_response = MagicMock()
    mock_genai_response.text = "ide fitur backup otomatis ke cloud"

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_genai_response
        mock_client_cls.return_value = mock_client

        with patch("app.bot.run_agent", side_effect=Exception("API timeout")):
            await bot_module.handle_voice_message(u, ctx)

    # Verifikasi catatan tersimpan di database
    async with TestSessionLocal() as session:
        res = await session.execute(select(Note).where(Note.user_id == user_id))
        notes = res.scalars().all()
        assert len(notes) == 1
        assert notes[0].content == "[Voice Note]: ide fitur backup otomatis ke cloud"

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert '🎙️ "ide fitur backup otomatis ke cloud"' in reply["text"]
    assert "disimpan sebagai catatan mentah" in reply["text"]

    print(
        "Test 2 PASSED: Fallback voice note tersimpan rapi sebagai catatan saat Agent error."
    )


async def test_voice_message_duration_limit():
    user_id = uuid.uuid4()
    chat_id = 445566

    # Voice lebih dari 300 detik (5 menit)
    voice = MockVoice(duration=360)
    u = MockUpdate(chat_id, voice=voice)
    ctx = MockContext()

    with patch(
        "app.bot.get_profile_by_chat_id",
        return_value=Profile(id=user_id, telegram_chat_id=chat_id),
    ):
        await bot_module.handle_voice_message(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert "maksimal 5 menit" in reply["text"]

    print("Test 3 PASSED: Voice note lebih dari 5 menit ditolak ramah.")


async def test_voice_message_empty_transcript():
    user_id = uuid.uuid4()
    chat_id = 778899

    voice = MockVoice(duration=5)
    u = MockUpdate(chat_id, voice=voice)
    ctx = MockContext()

    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"silent_voice")
    ctx.bot.get_file.return_value = mock_file

    mock_genai_response = MagicMock()
    mock_genai_response.text = "   "  # Kosong / hening

    with patch(
        "app.bot.get_profile_by_chat_id",
        return_value=Profile(id=user_id, telegram_chat_id=chat_id),
    ):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_genai_response
            mock_client_cls.return_value = mock_client

            await bot_module.handle_voice_message(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert "tidak terdengar jelas atau kosong" in reply["text"]

    print("Test 4 PASSED: Audio kosong/hening ditangani dengan peringatan informatif.")


async def test_voice_unlinked_user():
    chat_id = 112233
    voice = MockVoice(duration=5)
    u = MockUpdate(chat_id, voice=voice)
    ctx = MockContext()

    with patch("app.bot.get_profile_by_chat_id", return_value=None):
        await bot_module.handle_voice_message(u, ctx)

    assert len(u.effective_message.replies) == 1
    reply = u.effective_message.replies[0]
    assert "belum terhubung" in reply["text"]

    print("Test 5 PASSED: User belum terhubung mendapatkan petunjuk /connect.")


def main():
    asyncio.run(test_voice_message_success())
    asyncio.run(test_voice_message_agent_error_fallback())
    asyncio.run(test_voice_message_duration_limit())
    asyncio.run(test_voice_message_empty_transcript())
    asyncio.run(test_voice_unlinked_user())
    print("\nALL VOICE TRANSCRIBER TESTS PASSED! (100% SUCCESS)")


if __name__ == "__main__":
    main()
