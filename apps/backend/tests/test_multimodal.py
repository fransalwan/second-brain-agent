"""
Unit tests for Multimodal Document Intelligence (VLM) Pipeline.
Tests OCR handwriting extraction, research chart visual insights (CatBoost loss/F1-score),
FastAPI visual upload endpoint, and automatic pgvector/RAG integration.
"""

import io
import os
import sys
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.database import get_session
from app.main import app
from app.models import Note, Profile
from app.multimodal import analyze_visual_document, process_and_save_visual_document
from app.rag import advanced_crag_search


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


@pytest.mark.asyncio
async def test_analyze_visual_document_research_chart():
    """Validasi VLM parsing grafik kurva konvergensi model AI (CatBoost loss/F1-score)."""
    mock_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    result = await analyze_visual_document(
        file_bytes=mock_image_bytes,
        filename="catboost_loss_f1_epoch350.png",
        mime_type="image/png",
    )

    assert result["document_type"] == "research_chart"
    assert "catboost" in result["title"].lower()
    assert "0.892" in result["transcription"] or "0.892" in str(result["visual_insights"])
    assert any("catboost" in t.lower() for t in result["tags"])
    assert any("loss" in t.lower() or "f1" in t.lower() for t in result["tags"])
    assert len(result["visual_insights"]) >= 2


@pytest.mark.asyncio
async def test_analyze_visual_document_lecture_notes():
    """Validasi VLM parsing catatan kuliah tulisan tangan / slide praktikum."""
    mock_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    result = await analyze_visual_document(
        file_bytes=mock_image_bytes,
        filename="catatan_kuliah_sistem_cerdas.jpg",
        mime_type="image/jpeg",
    )

    assert result["document_type"] == "handwritten_note"
    assert "Catatan Kuliah" in result["title"]
    assert any("kuliah" in t.lower() for t in result["tags"])
    assert any("catatan-tangan" in t.lower() for t in result["tags"])
    assert len(result["transcription"]) > 20


@pytest.mark.asyncio
async def test_process_and_save_visual_document(async_session: AsyncSession):
    """Validasi pipeline lengkap: analisa visual -> pembuatan Note -> auto-indexing RAG."""
    user_id = uuid4()
    profile = Profile(id=user_id, email="researcher@ugm.ac.id", full_name="AI Researcher")
    async_session.add(profile)
    await async_session.commit()

    mock_image_bytes = b"fake_png_binary_data"
    result = await process_and_save_visual_document(
        session=async_session,
        user_id=user_id,
        file_bytes=mock_image_bytes,
        filename="evaluasi_model_catboost_bab4.png",
        mime_type="image/png",
    )

    assert result["status"] == "success"
    assert result["note_id"] is not None
    assert "multimodal" in result["tags"]

    # Pastikan Note tersimpan di database
    note_in_db = await async_session.get(Note, result["note_id"])
    assert note_in_db is not None
    assert "Transkripsi & OCR Cerdas" in note_in_db.content
    assert "CatBoost" in note_in_db.content
    assert "multimodal" in note_in_db.tags


@pytest.mark.asyncio
async def test_api_upload_visual_endpoint(async_session: AsyncSession):
    """Validasi endpoint HTTP POST /api/v1/notes/upload-visual menggunakan AsyncClient."""
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            files = {
                "file": (
                    "catboost_training_curve.png",
                    io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRmock"),
                    "image/png",
                )
            }
            response = await client.post(
                "/api/v1/notes/upload-visual",
                files=files,
                data={"email": "student@ugm.ac.id"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "note_id" in data["data"]
            assert data["data"]["document_type"] == "research_chart"
            assert any("catboost" in t.lower() for t in data["data"]["tags"])
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_upload_visual_unsupported_format(async_session: AsyncSession):
    """Validasi penolakan format file yang tidak didukung (misal: .exe atau .txt)."""
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            files = {
                "file": (
                    "script.exe",
                    io.BytesIO(b"MZ executable binary data"),
                    "application/x-dosexec",
                )
            }
            response = await client.post(
                "/api/v1/notes/upload-visual",
                files=files,
            )

            assert response.status_code == 400
            assert "tidak didukung" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_multimodal_rag_retrievability(async_session: AsyncSession):
    """Validasi bahwa dokumen visual yang diupload langsung dapat dicari secara semantik oleh CRAG."""
    user_id = uuid4()
    profile = Profile(id=user_id, email="student@ugm.ac.id", full_name="Student UGM")
    async_session.add(profile)
    await async_session.commit()

    # Upload & save visual chart note
    mock_bytes = b"\x89PNG\r\n\x1a\n"
    save_res = await process_and_save_visual_document(
        session=async_session,
        user_id=user_id,
        file_bytes=mock_bytes,
        filename="catboost_hyperparameter_f1_loss.png",
        mime_type="image/png",
    )

    # Lakukan pencarian via CRAG
    search_res = await advanced_crag_search(
        session=async_session,
        user_id=user_id,
        query="konvergensi loss catboost iterasi 350",
        top_k=3,
    )

    assert len(search_res["documents"]) >= 1
    top_doc = search_res["documents"][0]
    assert top_doc["note_id"] == save_res["note_id"]
    assert "CatBoost" in top_doc["content"]
