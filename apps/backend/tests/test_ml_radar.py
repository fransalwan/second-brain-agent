"""
Unit tests for Classical ML Hybrid: Burnout & Circadian Anomaly Radar.
Tests Isolation Forest inference speed (<10ms), threshold boundary classification,
deterministic feature extraction from database, and conditional LLM intervention.
"""

import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.database import get_session
from app.main import app
from app.ml_radar import (
    compute_burnout_anomaly_score,
    evaluate_user_burnout_radar,
    extract_circadian_features,
    generate_autonomous_burnout_intervention,
)
from app.models import HydrationLog, Profile, SleepLog, Task, TimeLog


@pytest.fixture
async def async_session():
    import asyncio
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_factory() as session:
        yield session
        await session.close()

    await test_engine.dispose()
    await asyncio.sleep(0.01)


def test_burnout_radar_latency_under_10ms():
    """Validasi Acceptance Criteria: Komputasi Anomaly Score harus deterministik & selesai dalam < 10ms."""
    healthy_features = {
        "sleep_hours": 7.5,
        "sleep_debt_hours": 1.5,
        "midnight_sessions_count": 0.0,
        "overdue_tasks_ratio": 0.05,
        "water_intake_liters": 2.2,
    }

    # Warmup
    compute_burnout_anomaly_score(healthy_features)

    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        score, is_anomaly = compute_burnout_anomaly_score(healthy_features)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 10.0, f"Rata-rata latensi {avg_latency:.2f}ms melebihi batas 10ms"
    assert not is_anomaly


def test_burnout_radar_healthy_student_profile():
    """Validasi profil mahasiswa sehat (tidur cukup, hidrasi baik, tugas terkontrol).
    Menghasilkan score positif (inlier), flag burnout_alert = False, dan TIDAK memanggil LLM.
    """
    healthy_features = {
        "sleep_hours": 8.0,
        "sleep_debt_hours": 0.0,
        "midnight_sessions_count": 0.0,
        "overdue_tasks_ratio": 0.0,
        "water_intake_liters": 2.5,
    }

    score, is_anomaly = compute_burnout_anomaly_score(healthy_features)
    assert score > -0.15, f"Skor mahasiswa sehat harus di atas threshold normal, got {score}"
    assert not is_anomaly


def test_burnout_radar_critical_burnout_anomaly():
    """Validasi profil mahasiswa burnout (tidur <4h, begadang berulang, hutang tidur tinggi, dehidrasi).
    Menghasilkan anomaly_score < -0.15 dan flag burnout_alert = True.
    """
    burnout_features = {
        "sleep_hours": 3.2,
        "sleep_debt_hours": 19.5,
        "midnight_sessions_count": 4.0,
        "overdue_tasks_ratio": 0.85,
        "water_intake_liters": 0.75,
    }

    score, is_anomaly = compute_burnout_anomaly_score(burnout_features)
    assert is_anomaly, "Pola hidup ekstrem wajib terdeteksi sebagai anomali sirkadian"
    assert score < -0.15, f"Anomaly score harus < -0.15, got {score}"


@pytest.mark.asyncio
async def test_llm_intervention_only_on_anomaly():
    """Validasi arsitektur hybrid: LLM intervensi hanya digenerate jika Isolation Forest mendeteksi anomali."""
    # Skenario 1: Sehat -> intervensi None (hemat token, no LLM call)
    healthy_features = {
        "sleep_hours": 7.8,
        "sleep_debt_hours": 1.0,
        "midnight_sessions_count": 0.0,
        "overdue_tasks_ratio": 0.1,
        "water_intake_liters": 2.2,
    }
    mock_session = None
    res_healthy = await evaluate_user_burnout_radar(mock_session, uuid4(), custom_features=healthy_features)
    assert not res_healthy["burnout_alert"]
    assert res_healthy["intervention"] is None
    assert res_healthy["risk_level"] == "HEALTHY_OPTIMAL"

    # Skenario 2: Anomali -> intervensi dihasilkan
    burnout_features = {
        "sleep_hours": 3.0,
        "sleep_debt_hours": 20.0,
        "midnight_sessions_count": 5.0,
        "overdue_tasks_ratio": 0.9,
        "water_intake_liters": 0.5,
    }
    res_burnout = await evaluate_user_burnout_radar(mock_session, uuid4(), custom_features=burnout_features)
    assert res_burnout["burnout_alert"]
    assert res_burnout["intervention"] is not None
    assert "Bedtime Guardian" in res_burnout["intervention"] or "istirahat" in res_burnout["intervention"].lower()
    assert res_burnout["risk_level"] in ["CRITICAL_BURNOUT", "ELEVATED_RISK"]


@pytest.mark.asyncio
async def test_feature_extraction_from_db(async_session: AsyncSession):
    """Validasi feature extraction engine mengambil data riil dari tabel database."""
    user_id = uuid4()
    profile = Profile(id=user_id, email="burnout_test@ugm.ac.id", full_name="Tester")
    async_session.add(profile)

    today = date.today()
    # 1. Tambah Sleep Log 5 jam (kurang)
    async_session.add(SleepLog(user_id=user_id, date=today, hours=5.0, quality="Kurang"))
    # 2. Tambah Hydration 4 gelas = 1.0 liter
    async_session.add(HydrationLog(user_id=user_id, date=today, glasses=4))
    # 3. Tambah Task overdue
    past_dl = today - timedelta(days=2)
    async_session.add(Task(user_id=user_id, title="Revisi Bab 4", deadline=past_dl, status="pending"))
    async_session.add(Task(user_id=user_id, title="Siapkan Slide", deadline=today + timedelta(days=3), status="pending"))
    # 4. Tambah TimeLog tengah malam
    midnight_time = datetime.now(timezone.utc).replace(hour=2, minute=15)
    async_session.add(TimeLog(user_id=user_id, project_name="Eksperimen CatBoost Malam", started_at=midnight_time, night_warning_sent=True))

    await async_session.commit()

    features = await extract_circadian_features(async_session, user_id, target_date=today)

    assert features["sleep_hours"] == 5.0
    assert features["sleep_debt_hours"] > 0
    assert features["water_intake_liters"] == 1.0
    assert features["overdue_tasks_ratio"] == 0.5  # 1 dari 2 task pending overdue
    assert features["midnight_sessions_count"] >= 1.0


@pytest.mark.asyncio
async def test_api_burnout_radar_endpoint(async_session: AsyncSession):
    """Validasi endpoint HTTP GET /api/v1/ml/burnout-radar."""
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/v1/ml/burnout-radar", params={"email": "student@ugm.ac.id"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert "anomaly_score" in data
            assert "burnout_alert" in data
            assert "features" in data
            assert "sleep_hours" in data["features"]
    finally:
        app.dependency_overrides.clear()

