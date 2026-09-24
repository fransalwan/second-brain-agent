# apps/backend/tests/test_ambient.py
"""Unit test untuk modul ambient tracking dan endpoint API."""

import asyncio
from datetime import datetime, time, timedelta
from pathlib import Path
import sys
from unittest.mock import AsyncMock
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ambient import (
    check_bedtime_status,
    get_ambient_status,
    handle_git_commit_event,
    start_ambient_timer,
    stop_ambient_timer,
)
from app.config import settings
from app.database import get_session
from app.main import app
from app.models import Area, Habit, Profile, Task, TimeLog, utcnow


@pytest.fixture
async def async_session():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    await test_engine.dispose()


async def test_ambient_start_and_idempotent(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="frans@example.com",
        full_name="Frans",
        telegram_chat_id=12345678,
    )
    async_session.add(profile)
    await async_session.commit()

    mock_bot = AsyncMock()

    # 1. Start timer pertama kali
    res1 = await start_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Second Brain Agent",
        source="vscode",
        notify_telegram=True,
        bot=mock_bot,
    )
    assert res1["status"] == "started"
    assert res1["project"] == "Second Brain Agent"
    assert mock_bot.send_message.called

    # 2. Start timer kedua kali dengan project yang sama (Idempotent)
    mock_bot.reset_mock()
    res2 = await start_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Second Brain Agent",
        source="vscode",
        notify_telegram=True,
        bot=mock_bot,
    )
    assert res2["status"] == "already_running"
    assert res2["project"] == "Second Brain Agent"
    assert not mock_bot.send_message.called  # Tidak mengirim pesan ganda


async def test_ambient_context_switch(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="frans@example.com",
        full_name="Frans",
        telegram_chat_id=12345678,
    )
    async_session.add(profile)
    await async_session.commit()

    mock_bot = AsyncMock()

    # Start project 1 (Usaha & Karir)
    await start_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Usaha & Karir",
        bot=mock_bot,
    )

    # Ubah started_at timer lama seolah-olah sudah jalan 30 menit
    res = await async_session.execute(select(TimeLog).where(TimeLog.user_id == user_id))
    old_timer = res.scalars().first()
    old_timer.started_at = utcnow() - timedelta(minutes=30)
    async_session.add(old_timer)
    await async_session.commit()

    # Start project 2 (Kuliah & Riset) -> harus auto switch
    res_switch = await start_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Kuliah & Riset",
        bot=mock_bot,
    )
    assert res_switch["status"] == "started"
    assert res_switch["project"] == "Kuliah & Riset"

    # Verifikasi timer lama selesai dengan durasi 30 menit
    await async_session.refresh(old_timer)
    assert old_timer.ended_at is not None
    assert old_timer.duration_minutes == 30


async def test_ambient_stop_discard_micro_session(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="frans@example.com",
        full_name="Frans",
    )
    async_session.add(profile)
    await async_session.commit()

    # Start timer
    await start_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Testing",
    )

    # Stop langsung (< 60 detik)
    res_stop = await stop_ambient_timer(
        session=async_session,
        email="frans@example.com",
        project_name="Testing",
        reason="window_closed",
    )
    assert res_stop["status"] == "discarded"
    assert res_stop["reason"] == "duration_too_short"

    # Verifikasi record dihapus agar tidak mengotori DB
    res_db = await async_session.execute(
        select(TimeLog).where(TimeLog.user_id == user_id)
    )
    assert res_db.scalars().first() is None


async def test_ambient_stop_meaningful_session(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="frans@example.com",
        full_name="Frans",
        telegram_chat_id=12345678,
    )
    async_session.add(profile)
    await async_session.commit()

    mock_bot = AsyncMock()

    # Buat timer yang sudah berjalan 45 menit
    timer = TimeLog(
        user_id=user_id,
        project_name="Second Brain Agent",
        started_at=utcnow() - timedelta(minutes=45),
    )
    async_session.add(timer)
    await async_session.commit()

    # Stop timer
    res_stop = await stop_ambient_timer(
        session=async_session,
        email="frans@example.com",
        reason="window_closed",
        notify_telegram=True,
        bot=mock_bot,
    )
    assert res_stop["status"] == "stopped"
    assert res_stop["duration_minutes"] == 45
    assert mock_bot.send_message.called


async def test_ambient_api_endpoints():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    async with async_session_factory() as session:
        profile = Profile(
            id=user_id,
            email="api_test@example.com",
            full_name="API Tester",
        )
        area = Area(
            user_id=user_id,
            name="Usaha",
            position=1,
        )
        session.add(profile)
        session.add(area)
        await session.commit()

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Request tanpa API Key -> 403
        resp_unauth = await client.post(
            "/api/v1/ambient/timer/start",
            json={"email": "api_test@example.com", "project_name": "Usaha"},
        )
        assert resp_unauth.status_code == 403

        # 2. Request dengan API Key yang benar -> 200
        headers = {"X-Ambient-Key": settings.AMBIENT_API_KEY}
        resp_start = await client.post(
            "/api/v1/ambient/timer/start",
            headers=headers,
            json={"email": "api_test@example.com", "project_name": "Usaha"},
        )
        assert resp_start.status_code == 200
        assert resp_start.json()["status"] == "started"

        # 3. Cek Status Endpoint
        resp_status = await client.get(
            "/api/v1/ambient/status?email=api_test@example.com",
            headers=headers,
        )
        assert resp_status.status_code == 200
        status_data = resp_status.json()
        assert status_data["active_timer"]["project_name"] == "Usaha"
        assert len(status_data["areas"]) == 1

        # 4. Stop Endpoint
        resp_stop = await client.post(
            "/api/v1/ambient/timer/stop",
            headers=headers,
            json={"email": "api_test@example.com", "reason": "window_closed"},
        )
        assert resp_stop.status_code == 200

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def test_ambient_focus_session_auto_checks_habit(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="habit_user@example.com",
        full_name="Habit User",
        telegram_chat_id=999888,
    )
    habit_coding = Habit(
        user_id=user_id,
        name="Ngoding / Deep Work",
        is_active=True,
    )
    habit_water = Habit(
        user_id=user_id,
        name="Minum Air Putih",
        is_active=True,
    )
    async_session.add(profile)
    async_session.add(habit_coding)
    async_session.add(habit_water)
    await async_session.commit()

    # Buat timer fokus yang sudah berjalan 25 menit (memenuhi syarat >= 15m)
    timer = TimeLog(
        user_id=user_id,
        project_name="Second Brain Agent",
        started_at=utcnow() - timedelta(minutes=25),
    )
    async_session.add(timer)
    await async_session.commit()

    mock_bot = AsyncMock()
    res_stop = await stop_ambient_timer(
        session=async_session,
        email="habit_user@example.com",
        reason="window_closed",
        notify_telegram=True,
        bot=mock_bot,
    )

    assert res_stop["status"] == "stopped"
    assert len(res_stop["auto_checked_habits"]) == 1
    assert res_stop["auto_checked_habits"][0]["name"] == "Ngoding / Deep Work"
    assert res_stop["auto_checked_habits"][0]["streak"] == 1


async def test_ambient_direct_habit_check_api():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    async with async_session_factory() as session:
        profile = Profile(
            id=user_id,
            email="direct_habit@example.com",
            full_name="Direct Habit Tester",
        )
        habit = Habit(
            user_id=user_id,
            name="Membaca Buku 15 Menit",
            is_active=True,
        )
        session.add(profile)
        session.add(habit)
        await session.commit()

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-Ambient-Key": settings.AMBIENT_API_KEY}
        resp = await client.post(
            "/api/v1/ambient/habit/check",
            headers=headers,
            json={
                "email": "direct_habit@example.com",
                "habit_keyword": "membaca",
                "notify_telegram": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["habit_name"] == "Membaca Buku 15 Menit"
        assert data["streak"] == 1
        assert data["already_completed"] is False

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def test_git_commit_auto_done_by_id(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="git_user@example.com",
        full_name="Git User",
        telegram_chat_id=554433,
    )
    task1 = Task(
        id=10,
        user_id=user_id,
        title="Bikin sistem autentikasi mandiri",
        status="pending",
    )
    task2 = Task(
        id=11,
        user_id=user_id,
        title="Perbarui dokumentasi README",
        status="pending",
    )
    async_session.add(profile)
    async_session.add(task1)
    async_session.add(task2)
    await async_session.commit()

    mock_bot = AsyncMock()
    res = await handle_git_commit_event(
        session=async_session,
        email="git_user@example.com",
        commit_message="feat(auth): selesaikan login page #10 dan fix #11",
        repo_name="second-brain-agent",
        branch="main",
        notify_telegram=True,
        bot=mock_bot,
    )

    assert res["status"] == "success"
    assert len(res["completed_tasks"]) == 2

    # Verifikasi status di DB
    await async_session.refresh(task1)
    await async_session.refresh(task2)
    assert task1.status == "completed"
    assert task1.completed_at is not None
    assert task2.status == "completed"
    assert task2.completed_at is not None
    assert mock_bot.send_message.called


async def test_git_commit_auto_done_by_keyword(async_session: AsyncSession):
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="git_kw_user@example.com",
        full_name="Git Keyword User",
        telegram_chat_id=778899,
    )
    task = Task(
        id=25,
        user_id=user_id,
        title="Kirim revisi invoice tagihan klien",
        status="pending",
    )
    async_session.add(profile)
    async_session.add(task)
    await async_session.commit()

    mock_bot = AsyncMock()
    # Pesan commit tanpa ID eksplisit tapi cocok dengan kata kunci judul
    res = await handle_git_commit_event(
        session=async_session,
        email="git_kw_user@example.com",
        commit_message="fix: kirim revisi invoice klien",
        repo_name="usaha-karir",
        branch="main",
        notify_telegram=True,
        bot=mock_bot,
    )

    assert res["status"] == "success"
    assert len(res["completed_tasks"]) == 1
    assert res["completed_tasks"][0]["id"] == 25

    await async_session.refresh(task)
    assert task.status == "completed"
    assert task.completed_at is not None


async def test_git_commit_api_endpoint():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    async with async_session_factory() as session:
        profile = Profile(
            id=user_id,
            email="git_api@example.com",
            full_name="Git API Tester",
        )
        task = Task(
            id=99,
            user_id=user_id,
            title="Setup ambient git hook",
            status="pending",
        )
        session.add(profile)
        session.add(task)
        await session.commit()

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-Ambient-Key": settings.AMBIENT_API_KEY}
        resp = await client.post(
            "/api/v1/ambient/git/commit",
            headers=headers,
            json={
                "email": "git_api@example.com",
                "commit_message": "feat: finish task #99",
                "repo_name": "second-brain-agent",
                "branch": "main",
                "notify_telegram": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["completed_tasks"]) == 1
        assert data["completed_tasks"][0]["id"] == 99

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def test_bedtime_status_past_cutoff(async_session: AsyncSession):
    """Verifikasi check_bedtime_status mengembalikan is_past_bedtime=True saat lewat cutoff."""
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="bedtime_user@example.com",
        full_name="Bedtime User",
        night_cutoff_time=time(22, 30),
    )
    async_session.add(profile)
    await async_session.commit()

    # Mock waktu lokal ke 23:15 (sudah lewat cutoff 22:30)
    from unittest.mock import patch

    fake_now = datetime(2026, 9, 22, 23, 15, 0)
    with patch("app.ambient.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        res = await check_bedtime_status(
            session=async_session,
            email="bedtime_user@example.com",
        )

    assert res["status"] == "ok"
    assert res["is_past_bedtime"] is True
    assert res["cutoff_time"] == "22:30"
    assert res["current_time"] == "23:15"
    assert "🌙" in res["message"]


async def test_bedtime_status_before_cutoff(async_session: AsyncSession):
    """Verifikasi check_bedtime_status mengembalikan is_past_bedtime=False sebelum cutoff."""
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        email="early_user@example.com",
        full_name="Early User",
        night_cutoff_time=time(22, 30),
    )
    async_session.add(profile)
    await async_session.commit()

    # Mock waktu lokal ke 20:00 (belum lewat cutoff 22:30)
    from unittest.mock import patch

    fake_now = datetime(2026, 9, 22, 20, 0, 0)
    with patch("app.ambient.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        res = await check_bedtime_status(
            session=async_session,
            email="early_user@example.com",
        )

    assert res["status"] == "ok"
    assert res["is_past_bedtime"] is False
    assert res["cutoff_time"] == "22:30"
    assert "✅" in res["message"]


async def test_bedtime_status_api_endpoint():
    """Verifikasi endpoint GET /api/v1/ambient/bedtime-status mengembalikan data yang benar."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    async with async_session_factory() as session:
        profile = Profile(
            id=user_id,
            email="bedtime_api@example.com",
            full_name="Bedtime API Tester",
            night_cutoff_time=time(23, 0),
        )
        session.add(profile)
        await session.commit()

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-Ambient-Key": settings.AMBIENT_API_KEY}

        # 1. Tanpa API key -> 403
        resp_unauth = await client.get(
            "/api/v1/ambient/bedtime-status?email=bedtime_api@example.com",
        )
        assert resp_unauth.status_code == 403

        # 2. Dengan API key -> 200
        resp = await client.get(
            "/api/v1/ambient/bedtime-status?email=bedtime_api@example.com",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "is_past_bedtime" in data
        assert "cutoff_time" in data
        assert "current_time" in data
        assert "message" in data
        assert data["cutoff_time"] == "23:00"

        # 3. User tidak ditemukan -> 404
        resp_404 = await client.get(
            "/api/v1/ambient/bedtime-status?email=notfound@example.com",
            headers=headers,
        )
        assert resp_404.status_code == 404

    app.dependency_overrides.clear()
    await test_engine.dispose()
