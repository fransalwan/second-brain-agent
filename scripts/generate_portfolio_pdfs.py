import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Second Brain: Autonomous AI Productivity Agent — Frans Alwan Purba (UGM)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        
        footer_text = f"Halaman {self._pageNumber} dari {page_count}"
        confidential_text = "Dokumen Pendukung Portofolio & Panduan Teknis (Confidential / Interview Preparation)"
        self.drawString(54, 32, confidential_text)
        self.drawRightString(558, 32, footer_text)
        self.restoreState()

def build_pdf_fundamentals(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom palette
    c_primary = colors.HexColor("#1e1b4b")   # Deep indigo
    c_secondary = colors.HexColor("#4338ca") # Indigo
    c_dark = colors.HexColor("#0f172a")      # Slate 900
    c_muted = colors.HexColor("#475569")     # Slate 600
    c_card_bg = colors.HexColor("#f8fafc")   # Slate 50
    c_accent = colors.HexColor("#0284c7")    # Cyan/Sky

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceAfter=14
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=c_muted,
        spaceAfter=16
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_dark,
        leftIndent=14,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceAfter=6
    )

    story = []

    # Title & Header
    story.append(Paragraph("SECOND BRAIN: AUTONOMOUS AI PRODUCTIVITY AGENT", title_style))
    story.append(Paragraph("Comprehensive Engineering Fundamentals & Architectural Blueprint", subtitle_style))
    story.append(Paragraph("<b>Author:</b> Frans Alwan Purba &nbsp;|&nbsp; <b>Degree:</b> Master's Student in Computer Science (Artificial Intelligence), Universitas Gadjah Mada &nbsp;|&nbsp; <b>Focus:</b> Polyglot Distributed Systems & Applied AI", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=12))

    # Section 1
    story.append(Paragraph("1. Executive Summary & Problem Space", h1_style))
    story.append(Paragraph(
        "Modern researchers and high-output software engineers face severe <i>cognitive thrashing</i>: juggling complex graduate coursework, thesis experimental benchmarks, circadian sleep debt, and personal health. Traditional productivity tools (Notion, Trello, Google Calendar) fail because they are passive silos requiring high manual maintenance.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Second Brain</b> is architected as an <i>ambient, event-driven, autonomous productivity operating system</i>. It eliminates manual logging through edge Git hooks, concurrent Go telemetry workers, and hybrid pgvector (768-D) semantic RAG, enabling zero-cognitive-overhead task triaging and automated research documentation.",
        body_style
    ))

    # Section 2
    story.append(Paragraph("2. Polyglot Architecture: FastAPI (Python) + Telemetry Engine (Golang)", h1_style))
    story.append(Paragraph(
        "A deliberate architectural design choice of this project is its <b>Polyglot Division of Concerns</b>, matching technical requirements to language-level execution models:",
        body_style
    ))
    
    # Table of Polyglot Comparison
    table_data = [
        [Paragraph("<b>Domain / Layer</b>", bullet_style), Paragraph("<b>Technology</b>", bullet_style), Paragraph("<b>Rationale & Architectural Benefit</b>", bullet_style)],
        [
            Paragraph("<b>AI Reasoning & RAG</b>", bullet_style),
            Paragraph("Python 3.11 / FastAPI", bullet_style),
            Paragraph("Native integration with Google Gemini ADK, NumPy, PyTorch/CatBoost, and asynchronous vector embeddings pipeline.", bullet_style)
        ],
        [
            Paragraph("<b>Background Telemetry</b>", bullet_style),
            Paragraph("Golang 1.22+ Worker (:8085)", bullet_style),
            Paragraph("True OS-thread concurrency via Goroutines & Channels. 10x lower memory footprint than Python worker pools; zero GIL lockups during heavy cron evaluation.", bullet_style)
        ],
        [
            Paragraph("<b>Storage & RLS</b>", bullet_style),
            Paragraph("PostgreSQL + pgvector", bullet_style),
            Paragraph("Unified ACID relational storage with 768-dimensional vector embeddings, HNSW indexing, and database-kernel Row-Level Security.", bullet_style)
        ],
        [
            Paragraph("<b>Frontend & UI</b>", bullet_style),
            Paragraph("Vue 3 + TypeScript + Vite", bullet_style),
            Paragraph("Reactive Bento Grid 2.0, Raycast-style Omnibar (Ctrl+K), sub-millisecond client-side routing, and zero-runtime bundle overhead.", bullet_style)
        ]
    ]
    t = Table(table_data, colWidths=[1.3*inch, 1.4*inch, 4.3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 3
    story.append(Paragraph("3. Hybrid Vector RAG & Reciprocal Rank Fusion (RRF)", h1_style))
    story.append(Paragraph(
        "Pure vector search suffers from semantic drift on keyword-exact technical tokens (such as 'Bab 3', 'CatBoost', 'F1-Score'), while pure keyword search fails on intent and conceptual queries. Second Brain solves this by implementing a <b>Hybrid Retrieval Engine with Reciprocal Rank Fusion (RRF)</b>:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Mathematical Formulation:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>RRF(d) = (w<sub>kw</sub> / (60 + rank<sub>kw</sub>(d))) + (w<sub>vec</sub> / (60 + rank<sub>vec</sub>(d)))</b>",
        code_style
    ))
    story.append(Paragraph(
        "• <b>Dense Vector Component:</b> Notes and academic artifacts are transformed into 768-dimensional dense vectors using <code>text-embedding-004</code> and indexed with <b>Hierarchical Navigable Small World (HNSW)</b> cosine distance graphs for sub-50ms retrieval.<br/>"
        "• <b>Sparse Lexical Component:</b> PostgreSQL full-text search (tsvector) extracts exact keywords and morphological matches.<br/>"
        "• <b>Smoothing Factor (k=60):</b> Mitigates outlier domination from either channel, ensuring balanced relevance ordering.",
        bullet_style
    ))

    # Section 4
    story.append(Paragraph("4. Automated Academic Git Pipeline (Edge Event Triggers)", h1_style))
    story.append(Paragraph(
        "Rather than forcing researchers to switch contexts to log updates, Second Brain uses <b>ambient Git hooks and cloud webhooks</b> across three primary academic repositories:",
        body_style
    ))
    story.append(Paragraph("• <b>materi-kuliah:</b> Captures assignment completions and lectures. Regex parsing detects course tags and updates streak counts automatically.", bullet_style))
    story.append(Paragraph("• <b>thesis-manuscripts:</b> Monitors progress on thesis Chapters 1–5. Detects supervisor feedback keywords ('bimbingan', 'revisi') and resets the anti-ghosting timer.", bullet_style))
    story.append(Paragraph("• <b>thesis-experiments:</b> Evaluates ML commit messages (e.g., <code>eval CatBoost: acc=94.2% f1=93.8% loss=0.14</code>), extracting metrics into PostgreSQL to immediately generate IEEE LaTeX comparative tables for Bab 4.", bullet_style))

    # Section 5
    story.append(Paragraph("5. Data Sovereignty & Row-Level Security (RLS)", h1_style))
    story.append(Paragraph(
        "In compliance with academic privacy and data ethics, Second Brain operates on a <b>Zero-Trust Database Kernel Architecture</b>. Every table (profiles, tasks, notes, habits, time_logs) is fortified with PostgreSQL Row-Level Security: <code>auth.uid() = user_id</code>. No user or recruiter can read or mutate another student's data. In addition, the application enforces <b>Zero Third-Party Trackers and Zero Ads</b>.",
        body_style
    ))

    # Section 6
    story.append(Paragraph("6. Quality Flywheel & Rigorous Testing Suite", h1_style))
    story.append(Paragraph(
        "System reliability is maintained using Google's <b>Quality Flywheel</b> methodology: 90 automated tests (100% passing) across intent classification benchmarks (>=90% threshold), p95 latency verification (<50ms), and semantic cluster separation.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated {filename}")

def build_pdf_cheatsheet(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor("#0f172a")   # Slate 900
    c_secondary = colors.HexColor("#4338ca") # Indigo
    c_dark = colors.HexColor("#1e293b")      # Slate 800
    c_muted = colors.HexColor("#64748b")     # Slate 500
    c_gold = colors.HexColor("#d97706")      # Amber

    title_style = ParagraphStyle(
        'DocTitle2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSub2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_secondary,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Header1_2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body2',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        spaceAfter=5
    )

    qa_q_style = ParagraphStyle(
        'QA_Q',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=c_primary,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    qa_a_style = ParagraphStyle(
        'QA_A',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    story = []

    # Title
    story.append(Paragraph("SECOND BRAIN: LIVE DEMO CHEATSHEET & INTERVIEW DEFENSE", title_style))
    story.append(Paragraph("3-Minute Recruiter Walkthrough Script & High-Stakes Technical Q&A Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=10))

    # Part 1: The Pitch
    story.append(Paragraph("PART 1: The 30-Second Elevator Pitch", h1_style))
    story.append(Paragraph(
        "<i>\"Halo, perkenalkan saya Frans Alwan Purba, mahasiswa Magister Ilmu Komputer (Artificial Intelligence) di UGM. Proyek ini adalah <b>Second Brain</b>: Autonomous AI Productivity Agent berbasis web mobile-first dengan arsitektur polyglot (FastAPI dan Go Worker). Sistem ini menyelesaikan problem nyata mahasiswa S2 dan engineer: menjaga riset skripsi dan tubes tetap tepat waktu melalui sinkronisasi Git otomatis, pencarian semantik hybrid pgvector (768-D), dan background telemetry real-time, dengan tetap menjaga kesehatan sirkadian tanpa burnout.\"</i>",
        body_style
    ))

    # Part 2: Step by Step Flow
    story.append(Paragraph("PART 2: Step-by-Step 3-Minute Live Demo Flow", h1_style))
    demo_steps = [
        [
            Paragraph("<b>Timestamp</b>", body_style),
            Paragraph("<b>Layar / Aksi yang Dilakukan</b>", body_style),
            Paragraph("<b>Narasi yang Diucapkan</b>", body_style)
        ],
        [
            Paragraph("<b>0:00 - 0:30</b><br/>Halaman Login", body_style),
            Paragraph("Tunjukkan tombol <b>'Masuk Mode Demo Instan (1-Click)'</b> dan klik.", body_style),
            Paragraph("\"Untuk mempermudah recruiter dan reviewer, saya sediakan 1-Click Instant Demo Mode. Cukup satu klik tanpa perlu registrasi, sistem langsung memuat lingkungan simulasi lengkap data tesis saya di UGM.\"", body_style)
        ],
        [
            Paragraph("<b>0:30 - 1:15</b><br/>Bento Grid & Omnibar", body_style),
            Paragraph("Tekan <b>Ctrl+K</b>, ketik <code>? evaluasi f1-score</code> lalu Enter. Buka tab Ringkasan Bento Grid.", body_style),
            Paragraph("\"Ini Bento Grid 2.0. Di tengah ada Raycast-style Omnibar (Ctrl+K). Dengan mode tanda tanya, kita langsung memicu semantic vector search (RAG) ke pgvector atas catatan kuliah dan eksperimen riset saya.\"", body_style)
        ],
        [
            Paragraph("<b>1:15 - 2:00</b><br/>Agent Ops Tab", body_style),
            Paragraph("Klik tab <b>'Agent Ops (Telemetry)'</b>. Klik tombol simulasi commit CatBoost.", body_style),
            Paragraph("\"Di tab ini terlihat arsitektur polyglot: service Go di port 8085 bertugas menangani evaluasi telemetri konkurensi tinggi. Terintegrasi dengan 3 repo GitHub saya: materi-kuliah, thesis-manuscripts, dan thesis-experiments.\"", body_style)
        ],
        [
            Paragraph("<b>2:00 - 2:45</b><br/>Tanya AI & Tour", body_style),
            Paragraph("Klik <b>'Tanya AI'</b> atau klik pill <b>'✨ Demo (Tour 60s)'</b> di navbar.", body_style),
            Paragraph("\"Fitur Tanya AI ini murni RAG grounded tanpa halusinasi, menggabungkan cosine similarity dense embedding 768-D dengan keyword BM25 via Reciprocal Rank Fusion (RRF).\"", body_style)
        ],
        [
            Paragraph("<b>2:45 - 3:00</b><br/>Closing & Specs", body_style),
            Paragraph("Buka modal <b>'Tech Specs'</b> dan tunjukkan diagram arsitektur.", body_style),
            Paragraph("\"Seluruh backend terverifikasi dengan 90 unit tests (100% pass), database terisolasi via PostgreSQL Row-Level Security, dan 0 tracker. Siap diuji secara live.\"", body_style)
        ]
    ]
    t_demo = Table(demo_steps, colWidths=[1.1*inch, 2.3*inch, 3.6*inch])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 8))

    # Part 3: Anticipated Questions & Strong Answers
    story.append(Paragraph("PART 3: 6 Anticipated Technical Questions & Model Answers", h1_style))
    
    qas = [
        ("Q1: Kenapa memilih arsitektur Polyglot (Go + Python)? Kenapa tidak Python murni?",
         "<b>Jawaban:</b> Python sangat unggul untuk ekosistem AI/ML (FastAPI, Google ADK, PyTorch, CatBoost), namun memiliki batasan Global Interpreter Lock (GIL) dan konsumsi memori tinggi jika dipakai untuk polling telemetri konkurensi ribuan pengguna. Golang memiliki model Goroutines yang ringan (hanya 2KB stack) dan channel concurrency, sehingga Go worker (:8085) menghemat memori 10x lipat dan mengeksekusi evaluasi jam malam/sleep debt tanpa memblokir thread inferensi AI."),

        ("Q2: Bagaimana cara kerja Reciprocal Rank Fusion (RRF) pada pencarian semantik kamu?",
         "<b>Jawaban:</b> Dense vector search (768-D) sangat baik memahami konteks umum, tapi sering luput pada nomor bab atau akronim teknis spesifik. Sebaliknya, keyword search unggul pada kecocokan eksak tapi buta konteks. RRF menggabungkan keduanya dengan formula: RRF(d) = sum(w / (60 + rank(d))). Konstanta 60 berfungsi sebagai peredam agar peringkat atas dari salah satu metode tidak mendominasi secara tidak adil."),

        ("Q3: Mengapa menggunakan Git hook lokal selain GitHub Webhook?",
         "<b>Jawaban:</b> Mahasiswa dan engineer sering koding secara offline atau di jaringan kampus yang terbatas. Git post-commit hook lokal mengeksekusi trigger di level edge seketika saat commit terjadi tanpa delay jaringan, dan otomatis sinkron saat push ke cloud via Webhook."),

        ("Q4: Bagaimana jaminan privasi data antar pengguna jika diakses oleh publik?",
         "<b>Jawaban:</b> Keamanan tidak hanya dijaga di level aplikasi, melainkan langsung di kernel database menggunakan PostgreSQL Row-Level Security (RLS). Setiap query ke tabel apapun dipaksa memfilter: auth.uid() = user_id. Pengguna A tidak mungkin bisa mem-fetch data pengguna B meskipun tahu ID-nya."),

        ("Q5: Bagaimana kamu mengukur reliabilitas agen ini (Quality Flywheel)?",
         "<b>Jawaban:</b> Saya menerapkan Quality Flywheel dengan 90 automated test cases (pytest). Evaluasi mencakup Intent Classification Accuracy dengan target minimal 90%, p95 latency benchmark di bawah 50 milidetik, dan evaluasi separasi ruang embedding antar domain."),

        ("Q6: Bagaimana korelasi proyek ini dengan studi S2 AI kamu di UGM?",
         "<b>Jawaban:</b> Proyek ini adalah implementasi nyata dari riset saya: menggabungkan representasi embedding berdimensi tinggi, optimasi algoritma evaluasi CatBoost, dan software engineering kelas produksi untuk mendongkrak efisiensi riset akademik.")
    ]

    for q, a in qas:
        story.append(Paragraph(q, qa_q_style))
        story.append(Paragraph(a, qa_a_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated {filename}")

if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    pdf1 = os.path.join(docs_dir, "Second_Brain_Engineering_Fundamentals.pdf")
    pdf2 = os.path.join(docs_dir, "Second_Brain_Live_Demo_Cheatsheet.pdf")
    build_pdf_fundamentals(pdf1)
    build_pdf_cheatsheet(pdf2)
