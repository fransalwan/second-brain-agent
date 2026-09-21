# apps/backend/tests/test_task_tools.py
import asyncio
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Area, Task
import app.agent as agent_module


class MockToolContext:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = str(user_id)


async def run_all_tests():
    # Gunakan SQLite in-memory murni (Aturan 13: tidak menyentuh database asli)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    agent_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_a_id = uuid.uuid4()
    ctx_a = MockToolContext(user_a_id)

    user_b_id = uuid.uuid4()
    ctx_b = MockToolContext(user_b_id)

    # -----------------------------------------------------------------------
    # Tes 1: Pengguna tanpa area ditolak saat menambah tugas
    # -----------------------------------------------------------------------
    res_no_area = await agent_module.add_task(
        title="Belajar Python",
        area_name="Kuliah",
        deadline="2026-09-25",
        tool_context=ctx_a,
    )
    assert res_no_area["status"] == "error"
    assert res_no_area["reason"] == "no_areas_configured"
    assert "belum membuat area hidup" in res_no_area["message"]
    print(
        "Test 1 PASSED: Pengguna tanpa area ditolak dengan pesan panduan membuat area."
    )

    # Siapkan area untuk User A
    async with TestSessionLocal() as session:
        area_kuliah = Area(user_id=user_a_id, name="Kuliah", position=1)
        area_usaha = Area(user_id=user_a_id, name="Usaha", position=2)
        session.add(area_kuliah)
        session.add(area_usaha)
        await session.commit()

    # -----------------------------------------------------------------------
    # Tes 2: Format tanggal selain ISO ditolak
    # -----------------------------------------------------------------------
    invalid_dates = ["jumat", "25-09-2026", "2026/09/25", "besok", "25 Sep 2026"]
    for bad_date in invalid_dates:
        res_bad_date = await agent_module.add_task(
            title="Tugas Uji Format",
            area_name="Kuliah",
            deadline=bad_date,
            tool_context=ctx_a,
        )
        assert res_bad_date["status"] == "error"
        assert res_bad_date["reason"] == "invalid_date_format"
        assert "Gunakan format ISO YYYY-MM-DD" in res_bad_date["message"]
    print(f"Test 2 PASSED: Semua {len(invalid_dates)} format tanggal non-ISO ditolak.")

    # -----------------------------------------------------------------------
    # Tes 3: Area tidak ditemukan ditolak
    # -----------------------------------------------------------------------
    res_bad_area = await agent_module.add_task(
        title="Tugas Random",
        area_name="Liburan",
        deadline="2026-09-25",
        tool_context=ctx_a,
    )
    assert res_bad_area["status"] == "error"
    assert res_bad_area["reason"] == "area_not_found"
    assert "Area 'Liburan' tidak ditemukan" in res_bad_area["message"]
    print("Test 3 PASSED: Area yang tidak ada dalam daftar pengguna ditolak.")

    # -----------------------------------------------------------------------
    # Tes 4: Berhasil menambah tugas dengan deadline ISO dan is_urgent
    # -----------------------------------------------------------------------
    res_success = await agent_module.add_task(
        title="Revisi Bab 2 Skripsi",
        area_name="Kuliah",
        deadline="2026-09-25",
        is_urgent=True,
        tool_context=ctx_a,
    )
    assert res_success["status"] == "success"
    task_info = res_success["task"]
    assert task_info["title"] == "Revisi Bab 2 Skripsi"
    assert task_info["area_name"] == "Kuliah"
    assert task_info["deadline"] == "2026-09-25"
    assert task_info["is_urgent"] is True
    task_a_id = task_info["id"]

    # Verifikasi langsung di database
    async with TestSessionLocal() as session:
        t_db = (
            await session.execute(select(Task).where(Task.id == task_a_id))
        ).scalar_one()
        assert t_db.deadline == date(2026, 9, 25)
        assert t_db.is_urgent is True
        assert t_db.status == "pending"
    print(
        "Test 4 PASSED: add_task sukses menyimpan ke DB dengan deadline date dan is_urgent."
    )

    # -----------------------------------------------------------------------
    # Tes 5: mark_urgent milik orang lain ditolak dengan pesan IDENTIK
    # -----------------------------------------------------------------------
    # User B mencoba mark_urgent tugas milik User A (task_a_id)
    res_unauth = await agent_module.mark_urgent(
        task_id=task_a_id, is_urgent=True, tool_context=ctx_b
    )
    # User B mencoba mark_urgent tugas yang benar-benar tidak ada (ID 99999)
    res_nonexistent = await agent_module.mark_urgent(
        task_id=99999, is_urgent=True, tool_context=ctx_b
    )

    assert res_unauth["status"] == "error"
    assert res_unauth["reason"] == "not_found"
    assert res_nonexistent["status"] == "error"
    assert res_nonexistent["reason"] == "not_found"

    # Pesan penolakan harus identik tanpa membocorkan eksistensi ID
    assert res_unauth["message"] == f"Tugas #{task_a_id} tidak ditemukan."
    assert res_nonexistent["message"] == "Tugas #99999 tidak ditemukan."
    print(
        "Test 5 PASSED: mark_urgent milik orang lain ditolak identik dengan task non-existent."
    )

    # -----------------------------------------------------------------------
    # Tes 6: Pemilik asli berhasil mark_urgent
    # -----------------------------------------------------------------------
    res_urgent_toggle = await agent_module.mark_urgent(
        task_id=task_a_id, is_urgent=False, tool_context=ctx_a
    )
    assert res_urgent_toggle["status"] == "success"
    assert res_urgent_toggle["is_urgent"] is False

    async with TestSessionLocal() as session:
        t_check = (
            await session.execute(select(Task).where(Task.id == task_a_id))
        ).scalar_one()
        assert t_check.is_urgent is False
    print("Test 6 PASSED: Pemilik asli berhasil mengubah status mendesak tugas.")

    # -----------------------------------------------------------------------
    # Tes 7: Verifikasi get_instruction dihitung dinamis dan menyuntikkan tanggal APP_TIMEZONE
    # -----------------------------------------------------------------------
    instruction_text = agent_module.get_instruction()
    tz = ZoneInfo(agent_module.settings.APP_TIMEZONE)
    now_local = datetime.now(tz)
    today_iso = now_local.strftime("%Y-%m-%d")
    today_day_name = agent_module.INDO_DAYS[now_local.weekday()]

    assert today_iso in instruction_text
    assert today_day_name in instruction_text
    assert "Aturan Pengelolaan Tugas:" in instruction_text
    assert "add_task" in instruction_text
    assert "mark_urgent" in instruction_text
    assert "Format deadline HANYA boleh ISO YYYY-MM-DD" in instruction_text
    assert f"JANGAN gunakan minggu depan" in instruction_text
    print(
        f"Test 7 PASSED: get_instruction menyuntikkan tanggal lokal ({today_day_name}, {today_iso}) dan aturan tanggal relatif."
    )


if __name__ == "__main__":
    asyncio.run(run_all_tests())
