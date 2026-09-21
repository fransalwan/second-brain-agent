# apps/backend/tests/test_recharge.py
import asyncio
from pathlib import Path
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Profile
import app.bot as bot_module
import app.agent as agent_module
from app.recharge import (
    YOUTUBE_MUSIC_PLAYLISTS,
    COFFEE_PRESETS,
    FEEL_GOOD_MOVIES,
    OFFLINE_ACTIVITIES,
    build_shopeefood_url,
    get_random_movie,
    get_random_activity,
    build_chill_menu_keyboard,
    build_music_keyboard,
    build_coffee_keyboard,
    build_movie_keyboard,
    build_hangout_keyboard,
    build_break_reminder_keyboard,
)


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
        self.callback_query = None


class MockCallbackQuery:
    def __init__(self, data: str):
        self.data = data
        self.answered = False
        self.edited_messages = []

    async def answer(self):
        self.answered = True

    async def edit_message_text(
        self, text: str, parse_mode: str = None, reply_markup=None
    ):
        self.edited_messages.append(
            {"text": text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        )


class MockContext:
    def __init__(self, args=None):
        self.args = args or []


class MockToolContext:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = str(user_id)


def test_recharge_data_structures():
    # 1. YouTube Music
    assert len(YOUTUBE_MUSIC_PLAYLISTS) >= 5
    for p in YOUTUBE_MUSIC_PLAYLISTS:
        assert p["url"].startswith("https://music.youtube.com/")
        assert p["title"] and p["desc"]

    # 2. ShopeeFood URL builder
    url_aren = build_shopeefood_url("kopi susu gula aren")
    assert "shopee.co.id/now-food/search?keyword=kopi" in url_aren
    assert "gula%20aren" in url_aren or "gula+aren" in url_aren

    # 3. Kopi Presets
    assert len(COFFEE_PRESETS) >= 4
    for c in COFFEE_PRESETS:
        preset_url = build_shopeefood_url(c["keyword"])
        assert preset_url.startswith("https://shopee.co.id/now-food/search?keyword=")

    # 4. Feel Good Movies & Activities
    assert len(FEEL_GOOD_MOVIES) >= 5
    m = get_random_movie()
    assert "title" in m and "platform" in m and "reason" in m

    assert len(OFFLINE_ACTIVITIES) >= 5
    act = get_random_activity()
    assert "title" in act and "detail" in act

    # 5. Keyboards
    chill_kb = build_chill_menu_keyboard()
    assert len(chill_kb.inline_keyboard) == 2
    assert chill_kb.inline_keyboard[0][0].callback_data == "chill:music"
    assert chill_kb.inline_keyboard[0][1].callback_data == "chill:coffee"

    music_kb = build_music_keyboard()
    assert any(
        btn.url and "music.youtube.com" in btn.url
        for row in music_kb.inline_keyboard
        for btn in row
    )

    coffee_kb = build_coffee_keyboard()
    assert any(
        btn.url and "shopee.co.id" in btn.url
        for row in coffee_kb.inline_keyboard
        for btn in row
    )

    break_kb = build_break_reminder_keyboard()
    assert len(break_kb.inline_keyboard) >= 2

    print("Test 1 PASSED: Struktur data dan URL kurasi Mode Jeda valid.")


async def test_bot_chill_and_coffee_commands():
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
        prof = Profile(id=u_id, full_name="Tester Chill", telegram_chat_id=chat_id)
        session.add(prof)
        await session.commit()

    # 1. Jalankan /chill
    u1 = MockUpdate(chat_id)
    await bot_module.chill_cmd(u1, MockContext())
    reply1 = u1.effective_message.replies[-1]
    assert "Mode Jeda" in reply1["text"]
    assert reply1["reply_markup"] is not None
    assert reply1["reply_markup"].inline_keyboard[0][0].callback_data == "chill:music"
    print(
        "Test 2 PASSED: Perintah /chill menampilkan menu Mode Jeda dengan Inline Keyboard."
    )

    # 2. Jalankan /kopi
    u2 = MockUpdate(chat_id)
    await bot_module.coffee_cmd(u2, MockContext())
    reply2 = u2.effective_message.replies[-1]
    assert "ShopeeFood" in reply2["text"]
    assert reply2["reply_markup"] is not None
    assert any(
        "shopee.co.id" in btn.url
        for row in reply2["reply_markup"].inline_keyboard
        for btn in row
        if btn.url
    )
    print("Test 3 PASSED: Perintah /kopi langsung memunculkan preset ShopeeFood.")

    # 3. Callback chill:music
    u3 = MockUpdate(chat_id)
    cb_music = MockCallbackQuery("chill:music")
    u3.callback_query = cb_music
    await bot_module.chill_callback(u3, MockContext())
    assert cb_music.answered is True
    edited_music = cb_music.edited_messages[-1]
    assert "YouTube Music" in edited_music["text"]
    assert any(
        "music.youtube.com" in btn.url
        for row in edited_music["reply_markup"].inline_keyboard
        for btn in row
        if btn.url
    )
    print("Test 4 PASSED: Callback chill:music menampilkan playlist YouTube Music.")

    # 4. Callback chill:coffee
    u4 = MockUpdate(chat_id)
    cb_coffee = MockCallbackQuery("chill:coffee")
    u4.callback_query = cb_coffee
    await bot_module.chill_callback(u4, MockContext())
    edited_coffee = cb_coffee.edited_messages[-1]
    assert "ShopeeFood" in edited_coffee["text"]
    print("Test 5 PASSED: Callback chill:coffee menampilkan pilihan kopi.")

    # 5. Callback chill:movie
    u5 = MockUpdate(chat_id)
    cb_movie = MockCallbackQuery("chill:movie")
    u5.callback_query = cb_movie
    await bot_module.chill_callback(u5, MockContext())
    edited_movie = cb_movie.edited_messages[-1]
    assert "Rekomendasi Tontonan" in edited_movie["text"]
    assert "Platform:" in edited_movie["text"]
    print(
        "Test 6 PASSED: Callback chill:movie menampilkan rekomendasi tontonan feel-good."
    )

    # 6. Callback chill:hangout
    u6 = MockUpdate(chat_id)
    cb_hangout = MockCallbackQuery("chill:hangout")
    u6.callback_query = cb_hangout
    await bot_module.chill_callback(u6, MockContext())
    edited_hangout = cb_hangout.edited_messages[-1]
    assert "Reset Pikiran & Hangout" in edited_hangout["text"]
    print("Test 7 PASSED: Callback chill:hangout menampilkan ide aktivitas offline.")

    # 7. Callback kembali ke main
    u7 = MockUpdate(chat_id)
    cb_main = MockCallbackQuery("chill:main")
    u7.callback_query = cb_main
    await bot_module.chill_callback(u7, MockContext())
    edited_main = cb_main.edited_messages[-1]
    assert "Mode Jeda" in edited_main["text"]
    print("Test 8 PASSED: Callback chill:main kembali ke menu utama Mode Jeda.")


async def test_agent_recharge_tool():
    u_id = uuid.uuid4()
    tool_ctx = MockToolContext(u_id)

    res = await agent_module.get_recharge_suggestion("all", tool_ctx)
    assert res["status"] == "success"
    assert "youtube_music" in res
    assert "shopeefood_coffee" in res
    assert "recommended_movie" in res
    assert "offline_activity" in res
    assert "music.youtube.com" in res["youtube_music"]["url"]
    assert "shopee.co.id" in res["shopeefood_coffee"]["url"]
    print(
        "Test 9 PASSED: Tool agen get_recharge_suggestion mengembalikan paket rekomendasi lengkap."
    )


async def main():
    test_recharge_data_structures()
    await test_bot_chill_and_coffee_commands()
    await test_agent_recharge_tool()
    print("\nALL RECHARGE & MOOD BOOSTER TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
