# apps/backend/tests/test_thesis_module.py
"""Unit tests untuk Modul Kuliah dan Riset:
- /thesis & callback thesis:select, thesis:set, thesis:main
- /bimbingan (catat & riwayat log bimbingan dospem + anti-ghosting alert)
- /metric (catat & riwayat metrik eksperimen model)
- /paper (catat & riwayat bank literatur riset)
- /matkul (countdown deadline tugas kuliah & 1-tap done)
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import (
    Area,
    ExperimentMetric,
    Note,
    Profile,
    SupervisionLog,
    Task,
    ThesisChapter,
    utcnow,
)
import app.bot as bot_module


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

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 112233

    async with TestSessionLocal() as session:
        profile = Profile(
            id=user_id,
            email="academic@example.com",
            full_name="Mahasiswa Riset",
            telegram_chat_id=chat_id,
        )
        session.add(profile)
        await session.commit()

    yield {"user_id": user_id, "chat_id": chat_id, "session_factory": TestSessionLocal}
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_thesis_cmd_and_interactive_updates(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. Jalankan /thesis pertama kali -> harus auto-generate 5 bab
    update = MockUpdate(chat_id)
    await bot_module.thesis_cmd(update, MockContext())

    assert len(update.effective_message.replies) == 1
    reply = update.effective_message.replies[0]
    assert "Status & Progres Naskah Thesis" in reply
    assert "Bab 1: Pendahuluan" in reply
    assert "Bab 5: Kesimpulan & Saran" in reply

    # Verifikasi bab tersimpan di DB
    async with Session() as session:
        res = await session.execute(
            select(ThesisChapter).where(ThesisChapter.user_id == user_id)
        )
        chapters = res.scalars().all()
        assert len(chapters) == 5

    # 2. Callback pilih Bab 1
    update_cb1 = MockUpdate(chat_id, callback_data="thesis:select:1")
    await bot_module.thesis_callback(update_cb1, MockContext())
    assert update_cb1.callback_query.answered is True
    assert "Update Status Bab 1" in update_cb1.callback_query.edited_text

    # 3. Callback update status Bab 1 -> Drafting (35%)
    update_cb2 = MockUpdate(chat_id, callback_data="thesis:set:1:Drafting:35")
    await bot_module.thesis_callback(update_cb2, MockContext())
    assert "Bab 1 diperbarui" in update_cb2.callback_query.answer_text
    assert "Drafting" in update_cb2.callback_query.edited_text

    # 4. Verifikasi di DB bahwa Bab 1 statusnya Drafting
    async with Session() as session:
        res = await session.execute(
            select(ThesisChapter).where(
                ThesisChapter.user_id == user_id, ThesisChapter.chapter_num == 1
            )
        )
        ch1 = res.scalars().first()
        assert ch1.status == "Drafting"
        assert ch1.progress == 35

    # 5. Callback thesis:main kembali ke ringkasan
    update_cb3 = MockUpdate(chat_id, callback_data="thesis:main")
    await bot_module.thesis_callback(update_cb3, MockContext())
    assert "Status & Progres Naskah Thesis" in update_cb3.callback_query.edited_text


@pytest.mark.asyncio
async def test_bimbingan_cmd(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. /bimbingan saat masih kosong
    update1 = MockUpdate(chat_id)
    await bot_module.bimbingan_cmd(update1, MockContext())
    assert (
        "Belum ada catatan bimbingan tersimpan" in update1.effective_message.replies[0]
    )

    # 2. Catat notulensi bimbingan
    notes_text = "Dospem minta perjelas batasan masalah Bab 1 dan perbandingan model F1"
    update2 = MockUpdate(chat_id)
    await bot_module.bimbingan_cmd(update2, MockContext(args=notes_text.split()))
    assert (
        "Notulensi Bimbingan Berhasil Dicatat" in update2.effective_message.replies[0]
    )
    assert "batasan masalah Bab 1" in update2.effective_message.replies[0]

    # 3. Cek kembali riwayat bimbingan
    update3 = MockUpdate(chat_id)
    await bot_module.bimbingan_cmd(update3, MockContext())
    reply3 = update3.effective_message.replies[0]
    assert "Riwayat Bimbingan Dosen Pembimbing" in reply3
    assert "Hari ini!" in reply3
    assert "batasan masalah Bab 1" in reply3

    # 4. Tes anti-ghosting alert jika sudah > 14 hari
    async with Session() as session:
        res = await session.execute(
            select(SupervisionLog).where(SupervisionLog.user_id == user_id)
        )
        log = res.scalars().first()
        # Set tanggal 20 hari yang lalu
        log.created_at = utcnow() - timedelta(days=20)
        session.add(log)
        await session.commit()

    update4 = MockUpdate(chat_id)
    await bot_module.bimbingan_cmd(update4, MockContext())
    reply4 = update4.effective_message.replies[0]
    assert "Peringatan Anti-Ghosting" in reply4
    assert "20 hari" in reply4


@pytest.mark.asyncio
async def test_metric_cmd(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. Saat belum ada metrik
    update1 = MockUpdate(chat_id)
    await bot_module.metric_cmd(update1, MockContext())
    assert "Belum ada catatan metrik eksperimen" in update1.effective_message.replies[0]

    # 2. Tambah metrik baru
    args = "BiLSTM-Attn Akurasi: 93.2%, F1: 92.5% | Epoch: 50, LR: 0.001".split()
    update2 = MockUpdate(chat_id)
    await bot_module.metric_cmd(update2, MockContext(args=args))
    reply2 = update2.effective_message.replies[0]
    assert "Metrik Eksperimen Berhasil Dicatat" in reply2
    assert "BiLSTM-Attn" in reply2
    assert "Epoch: 50, LR: 0.001" in reply2

    # 3. Cek riwayat
    update3 = MockUpdate(chat_id)
    await bot_module.metric_cmd(update3, MockContext())
    reply3 = update3.effective_message.replies[0]
    assert "Riwayat Metrik Eksperimen Model" in reply3
    assert "BiLSTM-Attn" in reply3
    assert "93.2%" in reply3


@pytest.mark.asyncio
async def test_paper_cmd(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. Saat belum ada paper
    update1 = MockUpdate(chat_id)
    await bot_module.paper_cmd(update1, MockContext())
    assert (
        "Belum ada catatan paper/jurnal tersimpan"
        in update1.effective_message.replies[0]
    )

    # 2. Simpan paper baru
    args = "Vaswani et al. (2017) Attention Is All You Need | Multi-head self-attention".split()
    update2 = MockUpdate(chat_id)
    await bot_module.paper_cmd(update2, MockContext(args=args))
    reply2 = update2.effective_message.replies[0]
    assert "Paper Tersimpan di Bank Literatur" in reply2
    assert "#paper" in reply2

    # 3. Verifikasi tersimpan sebagai Note dengan tags
    async with Session() as session:
        res = await session.execute(select(Note).where(Note.user_id == user_id))
        notes = res.scalars().all()
        assert len(notes) == 1
        assert "Vaswani" in notes[0].content
        assert "paper" in notes[0].tags
        assert "literatur" in notes[0].tags

    # 4. Cek riwayat paper
    update3 = MockUpdate(chat_id)
    await bot_module.paper_cmd(update3, MockContext())
    reply3 = update3.effective_message.replies[0]
    assert "Bank Literatur & Intisari Paper" in reply3
    assert "Vaswani et al." in reply3


@pytest.mark.asyncio
async def test_matkul_cmd(setup_test_db):
    user_id = setup_test_db["user_id"]
    chat_id = setup_test_db["chat_id"]
    Session = setup_test_db["session_factory"]

    # 1. Belum ada area Kuliah dan Riset atau belum ada tugas
    update1 = MockUpdate(chat_id)
    await bot_module.matkul_cmd(update1, MockContext())
    assert "Tidak Ada Tugas Kuliah Pending" in update1.effective_message.replies[0]

    # 2. Buat area "Kuliah dan Riset" dan tambahkan tugas
    today = date.today()
    async with Session() as session:
        area = Area(user_id=user_id, name="Kuliah dan Riset", position=2)
        session.add(area)
        await session.commit()
        await session.refresh(area)

        # Tugas 1: Hari ini
        t1 = Task(
            user_id=user_id,
            area_id=area.id,
            title="Submit Laporan Tugas Akhir Bab 3",
            deadline=today,
            status="pending",
            is_urgent=True,
        )
        # Tugas 2: Besok
        t2 = Task(
            user_id=user_id,
            area_id=area.id,
            title="Presentasi Seminar Proposal",
            deadline=today + timedelta(days=1),
            status="pending",
        )
        # Tugas 3: Sisa 5 hari
        t3 = Task(
            user_id=user_id,
            area_id=area.id,
            title="Review Paper Jurnal",
            deadline=today + timedelta(days=5),
            status="pending",
        )
        session.add_all([t1, t2, t3])
        await session.commit()

    # 3. Jalankan /matkul
    update2 = MockUpdate(chat_id)
    await bot_module.matkul_cmd(update2, MockContext())
    reply2 = update2.effective_message.replies[0]

    assert "Daftar Tugas Perkuliahan & Countdown" in reply2
    assert "Submit Laporan Tugas Akhir Bab 3" in reply2
    assert "HARI INI!" in reply2
    assert "Presentasi Seminar Proposal" in reply2
    assert "BESOK!" in reply2
    assert "Review Paper Jurnal" in reply2
    assert "Sisa 5 hari" in reply2

    # Verifikasi ada inline buttons untuk mark completed
    assert len(update2.effective_message.reply_markups) == 1
    markup = update2.effective_message.reply_markups[0]
    button_datas = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert any("task:done:" in bd for bd in button_datas)
