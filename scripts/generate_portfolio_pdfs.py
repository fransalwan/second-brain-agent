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
            self.drawString(54, 750, "Second Brain: Autonomous AI Engineering Platform — Frans Alwan Purba (UGM)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        
        footer_text = f"Halaman {self._pageNumber} dari {page_count}"
        confidential_text = "Dokumen Pendukung Portofolio AI Engineer & Panduan Teknis (Interview Preparation)"
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
    c_accent = colors.HexColor("#0284c7")    # Cyan/Sky
    c_emerald = colors.HexColor("#059669")   # Emerald

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_secondary,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_muted,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_secondary,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_dark,
        leftIndent=12,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=5,
        spaceAfter=5
    )

    story = []

    # Title & Header
    story.append(Paragraph("SECOND BRAIN: AUTONOMOUS AI ENGINEERING PLATFORM", title_style))
    story.append(Paragraph("Comprehensive Engineering Fundamentals, Architecture Blueprint & AI Systems Guide", subtitle_style))
    story.append(Paragraph("<b>Author:</b> Frans Alwan Purba &nbsp;|&nbsp; <b>Degree:</b> Master of Computer Science in AI Candidate, Universitas Gadjah Mada &nbsp;|&nbsp; <b>Stack:</b> Google ADK · Anthropic MCP · FastAPI · Go 1.22 · pgvector", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=8))

    # Section 1
    story.append(Paragraph("1. Executive Summary & Problem Space", h1_style))
    story.append(Paragraph(
        "Modern AI researchers and high-output software engineers face severe <i>cognitive thrashing</i>: juggling multi-model experimentation benchmarks, complex academic manuscripts, circadian sleep debt, and fragmented knowledge repositories. Conventional productivity tools (Notion, Trello, Obsidian) fail because they are passive silos requiring high manual maintenance without automated verification.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Second Brain</b> is architected as an <i>autonomous, event-driven AI Engineering Operating System & Distributed Multi-Agent Platform</i>. It standardizes agent tool interfaces via Anthropic's Model Context Protocol (MCP), eliminates semantic hallucinations using Corrective RAG (CRAG) + RAPTOR hierarchical tree summarization, extracts visual artifacts via Gemini 2.0 Flash VLM, calculates deterministic circadian burnout risks in &lt;2ms via Classical ML (Isolation Forest), and audits agent outputs with an automated LLM-as-a-Judge CI/CD Quality Flywheel (81.8/100 Composite Score).",
        body_style
    ))

    # Section 2
    story.append(Paragraph("2. Polyglot Architecture & Concurrency Model", h1_style))
    story.append(Paragraph(
        "A deliberate architectural choice is the <b>Polyglot Division of Concerns</b>, matching workload characteristics to language-level execution models:",
        body_style
    ))
    
    # Table of Polyglot Comparison
    table_data = [
        [Paragraph("<b>Domain / Layer</b>", bullet_style), Paragraph("<b>Technology</b>", bullet_style), Paragraph("<b>Rationale & Architectural Benefit</b>", bullet_style)],
        [
            Paragraph("<b>AI Reasoning & Tool Fleet</b>", bullet_style),
            Paragraph("Python 3.11 / FastAPI", bullet_style),
            Paragraph("Native integration with Google ADK, Anthropic MCP Server (SSE), PyTorch/CatBoost, scikit-learn, and async pgvector pipelines.", bullet_style)
        ],
        [
            Paragraph("<b>Background Telemetry Engine</b>", bullet_style),
            Paragraph("Golang 1.22+ Worker (:8085)", bullet_style),
            Paragraph("True OS-thread concurrency via Goroutines & Channels. 10x lower memory footprint (~14MB) than Python workers; zero GIL lockups during heavy continuous cron evaluations.", bullet_style)
        ],
        [
            Paragraph("<b>Knowledge Vector Store</b>", bullet_style),
            Paragraph("PostgreSQL + pgvector", bullet_style),
            Paragraph("Unified relational storage with 768-dimensional vector embeddings, HNSW graph indexing (m=16, ef_construction=64), and Row-Level Security (RLS).", bullet_style)
        ],
        [
            Paragraph("<b>Interactive Frontend</b>", bullet_style),
            Paragraph("Vue 3 + TypeScript + Vite", bullet_style),
            Paragraph("Reactive Bento Grid 2.0, Raycast-style Omnibar (Ctrl+K), sub-millisecond client-side routing, and 100% PWA offline capability.", bullet_style)
        ]
    ]
    t = Table(table_data, colWidths=[1.3*inch, 1.4*inch, 4.3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Section 3: Anthropic MCP
    story.append(Paragraph("3. Standard Model Context Protocol (Anthropic MCP SSE)", h1_style))
    story.append(Paragraph(
        "To avoid proprietary tool lock-in, Second Brain exposes its core capabilities as an <b>Anthropic Model Context Protocol (MCP) Server</b> over Server-Sent Events (SSE) at <code>/mcp/sse</code> and <code>/mcp/messages/</code>. This enables external LLM desktop clients (such as Claude Desktop and Cursor IDE) to seamlessly consume Second Brain tools via standardized JSON-RPC 2.0:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>8 Registered MCP Tool Schemas:</b> <code>save_note</code>, <code>search_notes</code>, <code>get_thesis_progress</code>, <code>log_habit</code>, <code>record_focus_session</code>, <code>evaluate_burnout_radar</code>, <code>upload_visual_document</code>, and <code>run_rag_qa</code>.<br/>"
        "• <b>Google ADK Bidirectional Adapter:</b> Internal ADK agents can import MCP-compliant tools dynamically, facilitating modular multi-agent collaboration.",
        bullet_style
    ))

    # Section 4: Next-Gen RAG & RAPTOR
    story.append(Paragraph("4. Next-Gen RAG: RAPTOR Knowledge Tree + Corrective RAG (CRAG)", h1_style))
    story.append(Paragraph(
        "Pure vector search suffers from semantic drift and technical token blindness. Second Brain implements a state-of-the-art <b>Hierarchical & Self-Corrective RAG Pipeline</b>:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>RAPTOR Hierarchical Clustering:</b> Document embeddings are grouped into semantic clusters using <b>Gaussian Mixture Models (GMM)</b> and KMeans. Gemini recursively synthesizes high-level summary nodes, constructing a multi-tier Knowledge Tree for macro-level conceptual retrieval.<br/>"
        "• <b>Corrective RAG (CRAG) Routing:</b> Evaluates context confidence dynamically:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;1. <b>CORRECT (&gt; 0.70):</b> High precision; passes context directly to the generator.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;2. <b>AMBIGUOUS (0.35 - 0.70):</b> Triggers <b>HyDE (Hypothetical Document Embeddings)</b> query expansion to retrieve missing contextual chunks.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;3. <b>INCORRECT (&lt; 0.35):</b> Activates Out-of-Distribution (OOD) guardrails, rejecting hallucinations with 100% adherence.<br/>"
        "• <b>Cross-Encoder Reranker:</b> Re-scores Top-10 pgvector candidates before injecting into context windows, balancing dense similarity (0.50), lexical BM25 matching (0.30), and token overlap (0.20).",
        bullet_style
    ))

    # Section 5: Multimodal VLM
    story.append(Paragraph("5. Multimodal Document Intelligence (Gemini 2.0 Flash VLM)", h1_style))
    story.append(Paragraph(
        "Technical engineering artifacts are rarely plain text. The <code>POST /api/v1/notes/upload-visual</code> endpoint leverages Gemini 2.0 Flash VLM to process complex visual documents:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Model Training Curve Analytics:</b> Analyzes training loss convergence, detects plateau/overfitting at specific epochs (e.g., CatBoost iteration 350), and extracts F1-Score / AUC-ROC metrics.<br/>"
        "• <b>Handwriting OCR & LaTeX Transcription:</b> Converts handwritten lecture slides and mathematical formulas into standard monospace LaTeX expressions.<br/>"
        "• <b>Automated Vector Ingestion:</b> Structured JSON outputs (summary, OCR, insights, tags) are vectorized into 768-D embeddings and linked to the RAPTOR tree in &lt;50ms.",
        bullet_style
    ))

    # Section 6: Classical ML Hybrid Radar
    story.append(Paragraph("6. Classical ML Hybrid: Circadian & Burnout Anomaly Radar", h1_style))
    story.append(Paragraph(
        "A key indicator of engineering maturity is knowing when <b>not</b> to use Generative AI. Calculating real-time health anomalies on every telemetry heartbeat with an LLM is wasteful and slow (&gt;500ms, costly tokens).",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Isolation Forest in &lt; 2ms:</b> Evaluates a 5-D feature vector (<code>sleep_hours</code>, <code>sleep_debt</code>, <code>midnight_sessions</code>, <code>overdue_tasks_ratio</code>, <code>water_intake</code>) in-memory with zero token spend.<br/>"
        "• <b>Conditional Autonomous LLM Intervention:</b> When the Anomaly Score drops below the critical decision boundary (&lt; -0.150), the system conditionally triggers Gemini 2.0 Flash to synthesize an empathetic, contextual energy recovery plan.",
        bullet_style
    ))

    # Section 7: Quality Flywheel & Evals
    story.append(Paragraph("7. Production Evals & CI/CD Observability (Quality Flywheel)", h1_style))
    story.append(Paragraph(
        "Every code commit is continuously audited against a 20-case curated Golden Dataset across 7 academic domains using <b>LLM-as-a-Judge RAG Triad</b> scoring:",
        body_style
    ))
    
    eval_table = [
        [Paragraph("<b>Evaluation Metric</b>", bullet_style), Paragraph("<b>Benchmark Score</b>", bullet_style), Paragraph("<b>CI/CD Gate Threshold</b>", bullet_style), Paragraph("<b>Status</b>", bullet_style)],
        [Paragraph("<b>Faithfulness (Groundedness)</b>", bullet_style), Paragraph("<b>85.0% (0.850)</b>", bullet_style), Paragraph(">= 80.0%", bullet_style), Paragraph("<font color='#059669'><b>PASSED</b></font>", bullet_style)],
        [Paragraph("<b>Context Recall</b>", bullet_style), Paragraph("<b>86.0% (0.860)</b>", bullet_style), Paragraph(">= 80.0%", bullet_style), Paragraph("<font color='#059669'><b>PASSED</b></font>", bullet_style)],
        [Paragraph("<b>Answer Relevancy</b>", bullet_style), Paragraph("<b>78.5% (0.785)</b>", bullet_style), Paragraph(">= 75.0%", bullet_style), Paragraph("<font color='#059669'><b>PASSED</b></font>", bullet_style)],
        [Paragraph("<b>Out-of-Distribution Refusal</b>", bullet_style), Paragraph("<b>100.0% (1.000)</b>", bullet_style), Paragraph(">= 90.0%", bullet_style), Paragraph("<font color='#059669'><b>PASSED</b></font>", bullet_style)],
        [Paragraph("<b>Composite AI Quality Index</b>", bullet_style), Paragraph("<b>81.8 / 100</b>", bullet_style), Paragraph(">= 75.0 / 100", bullet_style), Paragraph("<font color='#059669'><b>EXCELLENT</b></font>", bullet_style)],
    ]
    t_eval = Table(eval_table, colWidths=[2.2*inch, 1.5*inch, 1.8*inch, 1.5*inch])
    t_eval.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 6))

    # Section 8: Security & Testing
    story.append(Paragraph("8. Data Sovereignty & 117 Passing Automated Tests", h1_style))
    story.append(Paragraph(
        "All user data is partitioned at the database kernel level with PostgreSQL Row-Level Security (<code>auth.uid() = user_id</code>), ensuring zero cross-tenant leakage. The entire repository is covered by <b>117 passing automated unit tests</b> (pytest) with 0 errors.",
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
        fontSize=10,
        leading=14,
        textColor=c_secondary,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Header1_2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body2',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        spaceAfter=4
    )

    qa_q_style = ParagraphStyle(
        'QA_Q',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
        spaceBefore=4,
        spaceAfter=1,
        keepWithNext=True
    )

    qa_a_style = ParagraphStyle(
        'QA_A',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    story = []

    # Title
    story.append(Paragraph("SECOND BRAIN: LIVE DEMO CHEATSHEET & INTERVIEW DEFENSE", title_style))
    story.append(Paragraph("3-Minute Recruiter Walkthrough Script & High-Stakes AI Engineering Q&A Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=8))

    # Part 1: The Pitch
    story.append(Paragraph("PART 1: The 30-Second Elevator Pitch (AI Engineer Edition)", h1_style))
    story.append(Paragraph(
        "<i>\"Halo, perkenalkan saya Frans Alwan Purba, mahasiswa Magister Ilmu Komputer (Artificial Intelligence) di UGM. Proyek ini adalah <b>Second Brain</b>: platform autonomous AI engineering & distributed multi-agent system. Sistem ini membuktikan arsitektur AI produksi end-to-end: standardisasi Anthropic Model Context Protocol (MCP SSE), Corrective RAG (CRAG) dengan hierarki RAPTOR (GMM), Multimodal Vision AI (Gemini 2.0 VLM), deteksi anomali Classical ML (Isolation Forest &lt;2ms), dan Go Concurrency Telemetry (:8085)—seluruhnya terverifikasi dengan 117 automated unit tests dan skor evaluasi kualitas 81.8/100.\"</i>",
        body_style
    ))

    # Part 2: Step by Step Flow
    story.append(Paragraph("PART 2: Step-by-Step 3-Minute Live Demo Flow", h1_style))
    demo_steps = [
        [
            Paragraph("<b>Timestamp</b>", body_style),
            Paragraph("<b>Layar / Aksi yang Dilakukan</b>", body_style),
            Paragraph("<b>Narasi & Highlight Arsitektur AI</b>", body_style)
        ],
        [
            Paragraph("<b>0:00 - 0:30</b><br/>Halaman Login", body_style),
            Paragraph("Tunjukkan showcase 5 fase AI di kiri, klik tombol <b>'Masuk Mode Demo Instan (1-Click)'</b>.", body_style),
            Paragraph("\"Halaman login menyajikan arsitektur 5 fase AI secara transparan. Untuk recruiter, tersedia 1-Click Instant Demo tanpa perlu registrasi yang langsung memuat dataset riset AI terkurasi.\"", body_style)
        ],
        [
            Paragraph("<b>0:30 - 1:00</b><br/>Ringkasan AI", body_style),
            Paragraph("Buka tab <b>'Ringkasan AI'</b>. Tunjukkan AI Showcase Grid (Fase 1–5) & Go cluster telemetry.", body_style),
            Paragraph("\"Ini executive cockpit. Di bagian atas terlihat status klaster terdistribusi: FastAPI :8000 dan Go telemetry daemon :8085 dengan Goroutines pool P95 &lt; 2.5ms.\"", body_style)
        ],
        [
            Paragraph("<b>1:00 - 1:40</b><br/>Next-Gen RAG", body_style),
            Paragraph("Klik tab <b>'Next-Gen RAG'</b>. Klik preset <i>CatBoost Loss</i> lalu preset <i>Resep Martabak (OOD)</i>.", body_style),
            Paragraph("\"Di sini kita mendemonstrasikan Corrective RAG (CRAG) + RAPTOR Knowledge Tree. Kueri valid langsung menghasilkan grounded answer dengan Cross-Encoder rerank score 0.945; kueri out-of-distribution langsung ditolak guardrail demi 0% halusinasi.\"", body_style)
        ],
        [
            Paragraph("<b>1:40 - 2:10</b><br/>Multimodal VLM", body_style),
            Paragraph("Klik tab <b>'Multimodal VLM'</b>. Klik preset <i>Kurva Loss CatBoost (Epoch 350)</i>.", body_style),
            Paragraph("\"Fitur Multimodal Document AI menggunakan Gemini 2.0 Flash VLM. Menganalisis kurva konvergensi fungsi loss, mengekstrak formula LaTeX, dan langsung mengindeks tensor vektor ke pgvector 768-D secara otomatis.\"", body_style)
        ],
        [
            Paragraph("<b>2:10 - 2:35</b><br/>ML Radar", body_style),
            Paragraph("Klik tab <b>'ML Radar'</b>. Geser slider sleep debt ke 12 jam & midnight sessions ke 4 kali.", body_style),
            Paragraph("\"Ini bukti kedewasaan arsitektur: kami menggunakan Classical ML (Isolation Forest) untuk menghitung anomali sirkadian dalam &lt; 2ms tanpa membakar token LLM. Begitu skor drop &lt; -0.15, agen intervensi empatik LLM otomatis terpicu secara bersyarat.\"", body_style)
        ],
        [
            Paragraph("<b>2:35 - 3:00</b><br/>Evals & MCP", body_style),
            Paragraph("Klik tab <b>'AI Quality Flywheel'</b> lalu tab <b>'MCP & Telemetry'</b>.", body_style),
            Paragraph("\"Kualitas sistem diuji dengan LLM-as-a-Judge pada 20 Golden Dataset dengan skor 81.8/100 (Faithfulness 85%, Recall 86%). Dan di tab MCP, 8 tool schemas diekspos via SSE untuk Claude Desktop dan Cursor IDE.\"", body_style)
        ]
    ]
    t_demo = Table(demo_steps, colWidths=[1.1*inch, 2.1*inch, 3.8*inch])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 6))

    # Part 3: Anticipated Questions & Strong Answers
    story.append(Paragraph("PART 3: 7 Anticipated Technical Questions & Bulletproof Model Answers", h1_style))
    
    qas = [
        ("Q1: Mengapa menggunakan Classical ML (Isolation Forest) dipadukan dengan Generative AI (LLM)?",
         "<b>Jawaban:</b> Menjalankan LLM untuk memantau sinyal telemetri setiap detik sangat mahal biaya token dan memiliki latensi tinggi (&gt;500ms) serta non-deterministik. Isolation Forest mengevaluasi vektor 5-D secara deterministik dalam &lt; 2ms dengan zero token cost. LLM hanya di-trigger ketika anomali terdeteksi (&lt; -0.150) untuk mensintesis rekomendasi pemulihan empatik."),

        ("Q2: Bagaimana Corrective RAG (CRAG) dan RAPTOR Tree mencegah halusinasi secara signifikan?",
         "<b>Jawaban:</b> RAPTOR mengelompokkan dokumen menggunakan Gaussian Mixture Models (GMM) dan merangkumnya menjadi pohon hirarkis bertingkat. CRAG bertindak sebagai evaluator evaluator confidence: kueri ambigu (&lt;0.70) memicu ekspansi HyDE (Hypothetical Document Embeddings), sementara kueri out-of-distribution (&lt;0.35) langsung ditolak guardrail, menghasilkan 100% OOD Refusal."),

        ("Q3: Mengapa memilih standardisasi Anthropic Model Context Protocol (MCP)?",
         "<b>Jawaban:</b> Daripada membangun API tools proprietary yang tertutup, standar MCP SSE (/mcp/sse) memungkinkan agen eksternal industri (Claude Desktop, Cursor IDE) mengonsumsi tool Second Brain secara native melalui protokol JSON-RPC 2.0 yang interoperable."),

        ("Q4: Bagaimana metodologi Quality Flywheel diuji dan diotomasi?",
         "<b>Jawaban:</b> Kami menyusun 20 pasangan pertanyaan akademik, ground truth context, dan expected answer di Golden Dataset. Script eval_runner.py menguji RAG Triad (Context Recall 86%, Faithfulness 85%, Answer Relevancy 78.5%) via GitHub Actions CI/CD gate sebelum kode di-deploy ke production."),

        ("Q5: Bagaimana pembagian kerja polyglot antara Go Worker dan Python FastAPI?",
         "<b>Jawaban:</b> Python FastAPI menangani inferensi AI/ML, VLM, dan tool calling. Golang Worker (:8085) mengelola background telemetry via Goroutines pool dan Channels. Go menghemat memori 10x lipat (~14MB) dan menghilangkan bottleneck GIL Python saat polling telemetri konkurensi."),

        ("Q6: Bagaimana pipeline Multimodal VLM memproses kurva loss dan catatan tulisan tangan?",
         "<b>Jawaban:</b> Endpoint /api/v1/notes/upload-visual mengirim gambar ke Gemini 2.0 Flash VLM dengan prompt terstruktur. Model membaca konvergensi kurva loss dan OCR tulisan tangan, mengekstrak formula ke format LaTeX, dan mengindeks embedding vektornya ke pgvector 768-D dalam waktu &lt;50ms."),

        ("Q7: Bagaimana kedaulatan data dan isolasi multi-tenant dijamin?",
         "<b>Jawaban:</b> Setiap tabel dilindungi oleh PostgreSQL Row-Level Security (RLS) dengan aturan auth.uid() = user_id di level kernel database. Aplikasi tidak menggunakan tracker pihak ketiga dan zero advertising.")
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
