#!/usr/bin/env python3
"""Unit tests for dynamic project detection and activity extraction in ambient_watcher."""

import json
from pathlib import Path
import pytest

from ambient_watcher import AmbientWatcher, extract_activity_context


@pytest.fixture
def watcher(tmp_path):
    config = {
        "backend_url": "http://localhost:8000",
        "api_key": "test-key",
        "user_email": "frans@example.com",
        "project_mappings": {
            "second-brain-agent": "Hobby / Open Source",
            "portfolio-opensource": "Hobby / Open Source",
            "thesis-manuscripts": "Thesis: Penulisan & Naskah",
            "thesis-experiments": "Thesis: Eksperimen & Model",
            "slp-iris": "Kuliah dan Riset",
            "tugas": "Kuliah",
            "scrap-yard-dashboard": "Karir",
            "upwork": "Karir",
            "CV PELANGI EFRATA": "Usaha",
            "default": "Hobby / Open Source",
        },
    }
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(config), encoding="utf-8")
    return AmbientWatcher(cfg_file)


def test_hobby_opensource_detection(watcher):
    # Explicit mapping
    title = "ambient_watcher.py - second-brain-agent - Visual Studio Code"
    assert watcher.match_project_name(title) == "Hobby / Open Source"
    assert "Pengembangan Fitur" in extract_activity_context(title, "Hobby / Open Source")

    # Dynamic hobby keyword
    title2 = "main.py - my-sideproject-tools - Visual Studio Code"
    assert watcher.match_project_name(title2) == "Hobby / Open Source"

    title3 = "test_core.py - awesome-opensource - Visual Studio Code"
    assert watcher.match_project_name(title3) == "Hobby / Open Source"
    assert "Unit Test" in extract_activity_context(title3, "Hobby / Open Source")


def test_kuliah_tugas_detection(watcher):
    # Dynamic tugas in folder
    title1 = "soal1.py - tugas-pemrograman-web - Visual Studio Code"
    assert watcher.match_project_name(title1) == "Kuliah"
    assert "Pengerjaan Tugas / Coding" in extract_activity_context(title1, "Kuliah")

    # Dynamic praktikum in folder
    title2 = "query.sql - praktikum-basis-data - Visual Studio Code"
    assert watcher.match_project_name(title2) == "Kuliah"
    assert "Praktikum Database" in extract_activity_context(title2, "Kuliah")

    # Dynamic tubes in folder
    title3 = "report.docx - tubes-jaringan - Visual Studio Code"
    assert watcher.match_project_name(title3) == "Kuliah"
    assert "Pengerjaan Laporan" in extract_activity_context(title3, "Kuliah")


def test_thesis_and_riset_detection(watcher):
    # Thesis manuscript
    title1 = "bab1.tex - thesis-manuscripts - Visual Studio Code"
    assert watcher.match_project_name(title1) == "Thesis: Penulisan & Naskah"
    assert "Draft" in extract_activity_context(title1, "Thesis: Penulisan & Naskah")

    # Thesis experiment
    title2 = "train.py - thesis-experiments - Visual Studio Code"
    assert watcher.match_project_name(title2) == "Thesis: Eksperimen & Model"
    assert "Model & Coding" in extract_activity_context(title2, "Thesis: Eksperimen & Model")

    # Dynamic research
    title3 = "model_eval.ipynb - slp-iris - Visual Studio Code"
    assert watcher.match_project_name(title3) == "Kuliah dan Riset"
    assert "Notebook" in extract_activity_context(title3, "Kuliah dan Riset")


def test_karir_detection(watcher):
    title1 = "proposal.md - upwork-client-task - Visual Studio Code"
    assert watcher.match_project_name(title1) == "Karir"
    assert "Project Client / Freelance" in extract_activity_context(title1, "Karir")

    title2 = "dashboard.tsx - scrap-yard-dashboard - Visual Studio Code"
    assert watcher.match_project_name(title2) == "Karir"


def test_usaha_detection(watcher):
    title = "invoice.pdf - CV PELANGI EFRATA - Visual Studio Code"
    assert watcher.match_project_name(title) == "Usaha"
    assert "Operasional Bisnis" in extract_activity_context(title, "Usaha")


def test_non_vscode_ignored(watcher):
    assert watcher.match_project_name("Google Chrome - Stack Overflow") is None
