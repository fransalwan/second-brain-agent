"""
Unit tests for Next-Gen RAG: RAPTOR Hierarchical Clustering, Corrective RAG (CRAG), and Cross-Encoder Reranking.
Tests deterministic pattern recognition, self-correction, query expansion, and out-of-distribution guardrails.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import numpy as np
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.rag import (
    rerank_candidates,
    corrective_rag_evaluate,
    expand_query_hyde,
    cluster_notes_raptor,
    advanced_crag_search,
    answer_with_second_brain,
)


def test_crag_evaluator_thresholds():
    """Validasi layer evaluasi Corrective RAG:
    - CORRECT (Confidence >= 0.70)
    - AMBIGUOUS (0.35 <= Confidence < 0.70)
    - INCORRECT (Confidence < 0.35)
    """
    # 1. Skenario High Precision (CORRECT)
    high_candidates = [{"note_id": 1, "similarity": 0.88, "content": "CatBoost loss convergence"}]
    res_high = corrective_rag_evaluate("CatBoost loss", high_candidates)
    assert res_high["action"] == "CORRECT"
    assert res_high["confidence"] >= 0.70
    assert res_high["status"] == "high_precision"

    # 2. Skenario Ambigu (AMBIGUOUS -> Trigger HyDE)
    ambig_candidates = [{"note_id": 2, "similarity": 0.55, "content": "Tinjauan pustaka bab 2"}]
    res_ambig = corrective_rag_evaluate("progres bab 2", ambig_candidates)
    assert res_ambig["action"] == "AMBIGUOUS"
    assert 0.35 <= res_ambig["confidence"] < 0.75
    assert res_ambig["status"] == "refine_query"

    # 3. Skenario Out-of-Distribution (INCORRECT -> Halusinasi Ditolak)
    low_candidates = [{"note_id": 3, "similarity": 0.22, "content": "Resep memasak pasta"}]
    res_low = corrective_rag_evaluate("Quantum computing teleportation", low_candidates)
    assert res_low["action"] == "INCORRECT"
    assert res_low["confidence"] < 0.35
    assert res_low["status"] == "out_of_distribution"

    # 4. Skenario Empty Retrieval
    res_empty = corrective_rag_evaluate("Empty query", [])
    assert res_empty["action"] == "INCORRECT"
    assert res_empty["confidence"] == 0.0


def test_hyde_query_expansion():
    """Validasi ekspansi kueri domain-spesifik untuk kueri ambigu."""
    # CatBoost & Metrik
    expanded_cat = expand_query_hyde("analisis catboost pada data")
    assert "gradient boosting" in expanded_cat.lower()
    assert "loss" in expanded_cat.lower()

    # Skripsi / Naskah
    expanded_skripsi = expand_query_hyde("revisi skripsi bab 4")
    assert "tesis" in expanded_skripsi.lower()
    assert "metodologi" in expanded_skripsi.lower()

    # Kesehatan & Sirkadian
    expanded_sleep = expand_query_hyde("jadwal tidur dan recovery")
    assert "sleep debt" in expanded_sleep.lower()
    assert "sirkadian" in expanded_sleep.lower()


def test_cross_encoder_reranker():
    """Validasi Cross-Encoder Reranker:
    Kandidat dengan kecocokan kata, bigram, dan tag yang tepat harus mendapat rerank score lebih tinggi,
    meskipun similarity vektor awalnya sedikit lebih rendah.
    """
    query = "evaluasi model catboost"

    candidates = [
        {
            "note_id": 1,
            "content": "Pengembangan arsitektur backend Go dan microservices",
            "tags": ["backend", "go"],
            "similarity": 0.72,
        },
        {
            "note_id": 2,
            "content": "Hasil evaluasi model CatBoost menunjukkan F1-Score 0.89 dan konvergensi loss optimal",
            "tags": ["catboost", "riset", "evaluasi"],
            "similarity": 0.70,  # Similarity vektor sedikit lebih rendah dari candidate 1
        },
        {
            "note_id": 3,
            "content": "Rencana liburan dan belanja bulanan",
            "tags": ["personal"],
            "similarity": 0.20,
        },
    ]

    reranked = rerank_candidates(query, candidates, top_n=3)

    assert len(reranked) == 3
    # Candidate 2 harus melonjak menjadi Top-1 karena kecocokan leksikal + bigram ("evaluasi model") + tag
    top_cand = reranked[0]
    assert top_cand["note_id"] == 2
    assert top_cand["rerank_score"] > reranked[1]["rerank_score"]
    assert top_cand["rerank_score"] > 0.65


@pytest.mark.asyncio
async def test_raptor_clustering_gmm():
    """Validasi RAPTOR hierarchical clustering menggunakan mock data embedding 768-D."""
    user_id = uuid4()

    # Generate 6 synthetic notes (3 clusters: AI, Skripsi, Kesehatan)
    mock_records = []
    topics = [
        ("Eksperimen CatBoost dengan 500 iterasi dan evaluasi F1-Score pada dataset medis", ["catboost", "ai"]),
        ("Hyperparameter tuning CatBoost learning rate 0.03 dan depth 6", ["catboost", "ml"]),
        ("Penyusunan naskah skripsi Bab 4 hasil analisis dan pembahasan", ["skripsi", "thesis"]),
        ("Bimbingan skripsi dengan dosen pembimbing mengenai format IEEE", ["skripsi", "dospem"]),
        ("Pola tidur sirkadian 8 jam dan monitoring sleep debt", ["tidur", "kesehatan"]),
        ("Rekomendasi hidrasi 2.5 liter air untuk mencegah dehidrasi saat begadang", ["tidur", "hidrasi"]),
    ]

    np.random.seed(42)
    for i, (content, tags) in enumerate(topics):
        # Buat vector 768-D dengan cluster separation buatan
        base_vec = np.zeros(768, dtype=np.float32)
        cluster_idx = i // 2
        base_vec[cluster_idx * 100 : (cluster_idx + 1) * 100] = 1.0
        noise = np.random.normal(0, 0.05, 768).astype(np.float32)
        vec = base_vec + noise
        vec = (vec / np.linalg.norm(vec)).tolist()

        mock_emb = MagicMock()
        mock_emb.embedding = vec
        mock_note = MagicMock()
        mock_note.id = i + 1
        mock_note.content = content
        mock_note.tags = tags

        mock_records.append((mock_emb, mock_note))

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = mock_records
    mock_session.execute.return_value = mock_result

    raptor_tree = await cluster_notes_raptor(mock_session, user_id, max_clusters=3)

    assert raptor_tree["total_notes"] == 6
    assert len(raptor_tree["clusters"]) >= 2
    assert raptor_tree["tree_depth"] == 2

    # Verifikasi bahwa tiap cluster memiliki label, summary, note_ids, dan coherence_score
    for cluster in raptor_tree["clusters"]:
        assert "cluster_id" in cluster
        assert "label" in cluster
        assert "summary" in cluster
        assert len(cluster["note_ids"]) > 0
        assert 0.0 <= cluster["coherence_score"] <= 1.0


@pytest.mark.asyncio
async def test_advanced_crag_search_ood_guardrail():
    """Validasi advanced_crag_search menolak halusinasi jika kueri out-of-distribution."""
    user_id = uuid4()
    mock_session = AsyncMock()

    # Mock hybrid search mengembalikan list kosong (OOD)
    with pytest.MonkeyPatch().context() as m:
        async def mock_hybrid(*args, **kwargs):
            return []

        m.setattr("app.rag.hybrid_search_notes", mock_hybrid)

        result = await advanced_crag_search(mock_session, user_id, "Quantum gravity wormholes", top_k=3)

        assert result["action"] == "INCORRECT"
        assert result["confidence"] == 0.0
        assert len(result["documents"]) == 0
        assert "Out of Distribution" in result["message"]


@pytest.mark.asyncio
async def test_answer_with_second_brain_grounding():
    """Validasi answer_with_second_brain membumikan jawaban pada dokumen yang di-rerank dan cluster metadata."""
    user_id = uuid4()
    mock_session = AsyncMock()

    candidate = {
        "note_id": 42,
        "content": "Hasil uji CatBoost menunjukkan nilai macro F1-score sebesar 0.912 pada data validasi.",
        "tags": ["catboost", "f1"],
        "similarity": 0.82,
        "rrf_score": 0.035,
    }

    with pytest.MonkeyPatch().context() as m:
        async def mock_hybrid(*args, **kwargs):
            return [candidate]

        async def mock_raptor(*args, **kwargs):
            return {
                "total_notes": 1,
                "clusters": [
                    {
                        "cluster_id": 1,
                        "label": "CatBoost & AI Evaluation Lab",
                        "summary": candidate["content"],
                        "note_ids": [42],
                        "coherence_score": 0.95,
                        "notes_count": 1,
                    }
                ],
                "tree_depth": 2,
            }

        m.setattr("app.rag.hybrid_search_notes", mock_hybrid)
        m.setattr("app.rag.cluster_notes_raptor", mock_raptor)

        response = await answer_with_second_brain(mock_session, user_id, "Bagaimana hasil evaluasi CatBoost?")

        assert response["crag_action"] == "CORRECT"
        assert response["context_sources"] == 1
        assert len(response["citations"]) == 1
        assert response["citations"][0]["note_id"] == 42
        assert "CatBoost & AI Evaluation Lab" in response["answer"]
        assert "F1-score sebesar 0.912" in response["answer"]
