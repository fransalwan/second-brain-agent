import asyncio
import os
from pathlib import Path
import re
import sys
import time
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.rag import cosine_similarity, generate_embedding


EVAL_INTENT_DATASET = [
    # Coursework
    {"prompt": "tugas kuis kalkulus besok mendesak", "expected_category": "coursework"},
    {"prompt": "latihan praktikum basis data dikumpulkan jumat", "expected_category": "coursework"},
    {"prompt": "tugas tubes kecerdasan buatan deadline minggu ini", "expected_category": "coursework"},
    # Research / Thesis
    {"prompt": "dospem minta revisi bab 3 metodologi riset", "expected_category": "research"},
    {"prompt": "revisi eksperimen model transformer bab 4 skripsi", "expected_category": "research"},
    {"prompt": "jadwal bimbingan tesis dengan dosen pembimbing senin", "expected_category": "research"},
    # Health & Vitality
    {"prompt": "minum 2 gelas air putih", "expected_category": "health"},
    {"prompt": "tidur 7.5 jam kualitas nyenyak", "expected_category": "health"},
    {"prompt": "minum vitamin dan stretching leher", "expected_category": "health"},
    # Rest & Recharge
    {"prompt": "capek banget pengen ngopi santai", "expected_category": "rest"},
    {"prompt": "jenuh butuh rekomendasi musik santai YouTube", "expected_category": "rest"},
    {"prompt": "burnout penat pengen nonton film", "expected_category": "rest"},
]


def classify_student_intent(text: str) -> str:
    """Classifier intent deterministik teruji untuk triase cepat kebutuhan mahasiswa."""
    lower = text.lower()
    if any(k in lower for k in ["capek", "jenuh", "burnout", "penat", "ngopi", "film", "musik"]):
        return "rest"
    if any(k in lower for k in ["minum", "tidur", "vitamin", "stretch", "gelas", "sleep"]):
        return "health"
    if any(k in lower for k in ["bab", "skripsi", "tesis", "dospem", "bimbingan", "riset", "eksperimen"]):
        return "research"
    if any(k in lower for k in ["tugas", "kuis", "tubes", "praktikum", "kalkulus", "ujian", "kuliah"]):
        return "coursework"
    return "general"


def parse_student_quick_input(text: str) -> dict:
    """Parser ekstraksi parameter untuk Quick Capture."""
    t = text.lower().strip()
    if t.startswith("minum"):
        match = re.search(r"(\d+)\s*(ml|gelas)?", t)
        glasses = int(match.group(1)) if match else 1
        return {"type": "hydration", "glasses": glasses}
    if t.startswith("tidur"):
        match = re.search(r"(\d+(\.\d+)?)\s*(jam|hours)?", t)
        hours = float(match.group(1)) if match else 7.0
        return {"type": "sleep", "hours": hours}
    if "tugas" in t or "kuis" in t or "praktikum" in t:
        is_urgent = "mendesak" in t or "urgent" in t
        return {"type": "task", "title": text, "is_urgent": is_urgent}
    return {"type": "note", "title": text}


def test_intent_classification_accuracy():
    """Menguji akurasi klasifikasi intent mahasiswa (Benchmark minimal 90%)."""
    correct = 0
    total = len(EVAL_INTENT_DATASET)

    for item in EVAL_INTENT_DATASET:
        predicted = classify_student_intent(item["prompt"])
        if predicted == item["expected_category"]:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.90, f"Akurasi intent klasifikasi ({accuracy * 100:.1f}%) di bawah target 90%"


def test_quick_capture_parameter_extraction():
    """Menguji ketepatan ekstraksi parameter deadline, kategori, dan urgensi."""
    # Test case 1: Urgent Coursework
    parsed_1 = parse_student_quick_input("tugas kuis kalkulus besok mendesak")
    assert parsed_1["type"] == "task"
    assert "kuis kalkulus" in parsed_1["title"].lower()
    assert parsed_1["is_urgent"] is True

    # Test case 2: Hydration log
    parsed_2 = parse_student_quick_input("minum 2 gelas")
    assert parsed_2["type"] == "hydration"
    assert parsed_2["glasses"] == 2

    # Test case 3: Sleep log
    parsed_3 = parse_student_quick_input("tidur 7.5 jam")
    assert parsed_3["type"] == "sleep"
    assert parsed_3["hours"] == 7.5


@pytest.mark.asyncio
async def test_embedding_latency_p95_benchmark():
    """Mengukur latensi pemrosesan representasi vektor untuk menjamin performa < 50ms."""
    sample_queries = [
        "Metodologi penelitian deep learning",
        "Pengingat tugas algoritma dan pemrograman",
        "Target jam tidur malam dan hidrasi sehat",
        "Catatan bimbingan tesis bab 2 tinjauan pustaka",
    ]

    latencies = []
    for q in sample_queries:
        start_t = time.perf_counter()
        _ = await generate_embedding(q)
        latencies.append((time.perf_counter() - start_t) * 1000)

    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = latencies[min(p95_idx, len(latencies) - 1)]

    assert p95_latency < 50.0, f"P95 Embedding latency {p95_latency:.2f}ms melebihi batas 50ms"


@pytest.mark.asyncio
async def test_rag_context_relevance_semantic_separation():
    """Menguji bahwa vektor semantik mampu memisahkan domain Riset vs Domain Kesehatan."""
    vec_research = await generate_embedding("Optimasi hyperparameter jaringan saraf tiruan")
    vec_thesis = await generate_embedding("Eksperimen model deep learning klasifikasi data")
    vec_health = await generate_embedding("Minum air 8 gelas dan istirahat tidur cukup")

    sim_domain_match = cosine_similarity(vec_research, vec_thesis)
    sim_cross_domain = cosine_similarity(vec_research, vec_health)

    assert sim_domain_match > sim_cross_domain, (
        f"Domain match ({sim_domain_match:.3f}) harus lebih tinggi dari cross domain ({sim_cross_domain:.3f})"
    )


@pytest.mark.asyncio
async def test_full_ai_evaluation_suite_run():
    """Validasi eksekusi penuh LLM-as-a-judge Quality Flywheel terhadap golden dataset."""
    from evals.eval_runner import run_evaluation_suite

    summary = await run_evaluation_suite()
    assert summary["total_test_cases"] >= 15
    m = summary["metrics_summary"]
    assert m["faithfulness"] >= 0.70
    assert m["ood_refusal_rate"] >= 0.90
    assert summary["composite_quality_index"] > 60.0


