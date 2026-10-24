import os
from pathlib import Path
import sys
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Note, Profile
from app.rag import (
    answer_with_second_brain,
    cosine_similarity,
    generate_embedding,
    hybrid_search_notes,
    index_note_embedding,
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


def test_cosine_similarity_math():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(vec1, vec2), 0.0001) == 1.0

    vec_ortho = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(vec1, vec_ortho), 0.0001) == 0.0

    vec_neg = [-1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(vec1, vec_neg), 0.0001) == -1.0

    assert cosine_similarity([], vec1) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


@pytest.mark.asyncio
async def test_generate_embedding_deterministic():
    text = "Riset arsitektur state management dan vector database"
    emb1 = await generate_embedding(text)
    emb2 = await generate_embedding(text)

    assert len(emb1) == 768
    assert emb1 == emb2
    assert cosine_similarity(emb1, emb2) > 0.9999


@pytest.mark.asyncio
async def test_index_and_hybrid_search(async_session: AsyncSession):
    user_id = uuid4()
    profile = Profile(id=user_id, email="test.ai@ugm.ac.id", full_name="Frans AI")
    async_session.add(profile)
    await async_session.commit()

    note1 = Note(
        user_id=user_id,
        content="Bab 3 skripsi membahas metode hybrid search menggunakan Reciprocal Rank Fusion",
        tags=["skripsi", "ai"],
    )
    note2 = Note(
        user_id=user_id,
        content="Resep sarapan sehat oatmeal dan target tidur minimal 7 jam",
        tags=["kesehatan", "tidur"],
    )
    async_session.add(note1)
    async_session.add(note2)
    await async_session.commit()
    await async_session.refresh(note1)
    await async_session.refresh(note2)

    # Index embeddings
    emb1 = await index_note_embedding(async_session, note1.id, user_id, note1.content)
    emb2 = await index_note_embedding(async_session, note2.id, user_id, note2.content)

    assert emb1.id is not None
    assert emb2.id is not None

    # Hybrid Search
    results = await hybrid_search_notes(
        session=async_session,
        user_id=user_id,
        query="metode hybrid search skripsi",
        top_k=2,
    )

    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit["note_id"] == note1.id
    assert "skripsi" in top_hit["content"]
    assert top_hit["similarity"] > 0.0
    assert top_hit["rrf_score"] > 0.0


@pytest.mark.asyncio
async def test_answer_with_second_brain(async_session: AsyncSession):
    user_id = uuid4()
    profile = Profile(id=user_id, email="student@ugm.ac.id", full_name="Student UGM")
    async_session.add(profile)

    note = Note(
        user_id=user_id,
        content="Target revisi dospem: perbaiki tabel hasil eksperimen F1-score pada bab 4",
        tags=["skripsi"],
    )
    async_session.add(note)
    await async_session.commit()
    await async_session.refresh(note)

    await index_note_embedding(async_session, note.id, user_id, note.content)

    qa_result = await answer_with_second_brain(
        session=async_session,
        user_id=user_id,
        question="revisi dospem bab 4",
    )

    assert qa_result["question"] == "revisi dospem bab 4"
    assert "F1-score" in qa_result["answer"] or "catatan terkait" in qa_result["answer"]
    assert len(qa_result["citations"]) >= 1
    assert qa_result["confidence"] > 0.0

