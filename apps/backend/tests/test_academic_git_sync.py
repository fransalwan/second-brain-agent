import os
from pathlib import Path
import sys
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.ambient import handle_git_commit_event
from app.database import get_session
from app.main import app
from app.models import (
    CourseAssignment,
    ExperimentMetric,
    Habit,
    Profile,
    SupervisionLog,
    Task,
    ThesisChapter,
)


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


@pytest.fixture
async def sample_user(async_session: AsyncSession) -> Profile:
    user = Profile(
        id=uuid4(),
        email="fransalwanpurba@mail.ugm.ac.id",
        full_name="Frans Alwan Purba",
        telegram_chat_id=12345678,
    )
    async_session.add(user)

    # Tambahkan habit skripsi & kuliah
    h1 = Habit(user_id=user.id, name="Menulis Skripsi", is_active=True, position=1)
    h2 = Habit(user_id=user.id, name="Eksperimen Riset", is_active=True, position=2)
    h3 = Habit(user_id=user.id, name="Belajar Kuliah", is_active=True, position=3)
    async_session.add_all([h1, h2, h3])

    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_thesis_manuscripts_chapter_progress(async_session: AsyncSession, sample_user: Profile):
    """Test sinkronisasi commit di repo thesis-manuscripts mengupdate Bab 3 ke 80%."""
    res = await handle_git_commit_event(
        session=async_session,
        email="fransalwanpurba@mail.ugm.ac.id",
        commit_message="feat(bab 3): metodologi penelitian eksperimen EJOR progres 80%",
        repo_name="thesis-manuscripts",
        branch="main",
        notify_telegram=False,
    )

    assert res["status"] == "success"
    assert res["academic_sync"]["repo_type"] == "thesis-manuscripts"
    assert res["academic_sync"]["chapter_updated"] is not None
    assert res["academic_sync"]["chapter_updated"]["chapter_num"] == 3
    assert res["academic_sync"]["chapter_updated"]["progress"] == 80

    # Cek di database
    chap_res = await async_session.execute(
        select(ThesisChapter).where(
            ThesisChapter.user_id == sample_user.id,
            ThesisChapter.chapter_num == 3,
        )
    )
    chap = chap_res.scalars().first()
    assert chap is not None
    assert chap.progress == 80
    assert chap.status == "Drafting"


@pytest.mark.asyncio
async def test_thesis_manuscripts_supervision_log(async_session: AsyncSession, sample_user: Profile):
    """Test sinkronisasi commit naskah yang mencatat arahan bimbingan dospem."""
    res = await handle_git_commit_event(
        session=async_session,
        email="fransalwanpurba@mail.ugm.ac.id",
        commit_message="catatan bimbingan dospem: perbaiki trade-off waktu komputasi SRA di bab 4",
        repo_name="thesis-manuscripts",
        branch="main",
        notify_telegram=False,
    )

    assert res["status"] == "success"
    assert res["academic_sync"]["supervision_logged"] is not None

    # Cek log tersimpan di database
    sup_res = await async_session.execute(
        select(SupervisionLog).where(SupervisionLog.user_id == sample_user.id)
    )
    logs = sup_res.scalars().all()
    assert len(logs) >= 1
    assert "perbaiki trade-off" in logs[0].notes


@pytest.mark.asyncio
async def test_thesis_experiments_metric_sync(async_session: AsyncSession, sample_user: Profile):
    """Test sinkronisasi metrik evaluasi model machine learning dari repo thesis-experiments."""
    commit_msg = "eval XGBoost: acc=94.5% f1=93.8% loss=0.12 epoch=100 lr=0.001 batch=32"
    res = await handle_git_commit_event(
        session=async_session,
        email="fransalwanpurba@mail.ugm.ac.id",
        commit_message=commit_msg,
        repo_name="thesis-experiments",
        branch="main",
        notify_telegram=False,
    )

    assert res["status"] == "success"
    assert res["academic_sync"]["repo_type"] == "thesis-experiments"
    mr = res["academic_sync"]["metric_recorded"]
    assert mr is not None
    assert mr["model_name"] == "XGBoost"
    assert "Akurasi: 94.5%" in mr["metrics_summary"]
    assert "F1: 93.8%" in mr["metrics_summary"]
    assert "Epoch: 100" in mr["parameters"]
    assert "LR: 0.001" in mr["parameters"]

    # Cek di database
    metric_res = await async_session.execute(
        select(ExperimentMetric).where(
            ExperimentMetric.user_id == sample_user.id,
            ExperimentMetric.model_name == "XGBoost",
        )
    )
    em = metric_res.scalars().first()
    assert em is not None
    assert "Akurasi: 94.5%" in em.metrics_summary


@pytest.mark.asyncio
async def test_materi_kuliah_assignment_sync(async_session: AsyncSession, sample_user: Profile):
    """Test commit repo materi-kuliah otomatis menandai CourseAssignment sebagai done."""
    # Buat assignment tugas kriptografi
    assignment = CourseAssignment(
        user_id=sample_user.id,
        course_name="Kriptografi",
        title="Tugas 2 Implementasi Enkripsi RSA",
        assignment_type="Individu",
        status="pending",
    )
    async_session.add(assignment)
    await async_session.commit()

    res = await handle_git_commit_event(
        session=async_session,
        email="fransalwanpurba@mail.ugm.ac.id",
        commit_message="selesaikan tugas 2 kriptografi implementasi enkripsi rsa",
        repo_name="materi-kuliah",
        branch="main",
        notify_telegram=False,
    )

    assert res["status"] == "success"
    assert res["academic_sync"]["repo_type"] == "materi-kuliah"
    assert res["academic_sync"]["assignment_completed"] is not None

    # Cek status assignment di DB
    await async_session.refresh(assignment)
    assert assignment.status == "done"
    assert assignment.completed_at is not None


@pytest.mark.asyncio
async def test_github_webhook_endpoint(async_session: AsyncSession, sample_user: Profile):
    """Test endpoint GitHub Webhook /api/v1/github/webhook untuk event ping dan push."""
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Test Ping Event
            ping_resp = await client.post(
                "/api/v1/github/webhook",
                headers={"X-GitHub-Event": "ping"},
                json={"zen": "Non-blocking is better than blocking."},
            )
            assert ping_resp.status_code == 200
            assert ping_resp.json()["status"] == "pong"

            # 2. Test Push Event
            push_payload = {
                "ref": "refs/heads/main",
                "repository": {
                    "name": "thesis-manuscripts",
                    "full_name": "fransalwan/thesis-manuscripts",
                },
                "pusher": {
                    "name": "fransalwan",
                    "email": "fransalwanpurba@mail.ugm.ac.id",
                },
                "commits": [
                    {
                        "id": "c1a2b3",
                        "message": "feat(bab 1): pendahuluan latar belakang riset selesai 90%",
                        "author": {
                            "email": "fransalwanpurba@mail.ugm.ac.id",
                        },
                    }
                ],
            }
            push_resp = await client.post(
                "/api/v1/github/webhook",
                headers={"X-GitHub-Event": "push"},
                json={**push_payload},
            )
            assert push_resp.status_code == 200
            data = push_resp.json()
            assert data["status"] == "success"
            assert data["processed_commits"] == 1
            assert data["repo"] == "thesis-manuscripts"
    finally:
        app.dependency_overrides.clear()

