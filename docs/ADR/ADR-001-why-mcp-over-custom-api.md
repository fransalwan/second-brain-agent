# ADR-001: Standardisasi Model Context Protocol (MCP) untuk Interoperabilitas Multi-Agent

## Status
**Accepted / Implemented in Production (Phase 1)**

## Konteks & Masalah
Sebelum Fase 1, tools pada Second Brain dipanggil secara *tightly-coupled* melalui REST API internal atau fungsi Python langsung di `agent.py`. Pendekatan ini memiliki sejumlah keterbatasan:
1. Klien LLM eksternal terkemuka (seperti Claude Desktop, Cursor IDE, atau framework agen pihak ketiga) tidak dapat langsung mengonsumsi tools Second Brain tanpa custom adapter wrapper.
2. Setiap kali ada penambahan tool baru (misal: analisis visual VLM atau evaluasi radar sirkadian), skema parameter harus diduplikasi di Swagger docs, OpenAPI, dan prompt agen.
3. Ekosistem industri AI telah bergerak menuju standar terbuka yang diperkenalkan oleh Anthropic: **Model Context Protocol (MCP)**.

## Keputusan Arsitektur
Kami memutuskan untuk:
1. Membangun **Server MCP mandiri** di dalam FastAPI (`apps/backend/app/mcp_server.py`) yang mendukung transport **Server-Sent Events (SSE)** melalui rute `/mcp/sse` dan `/mcp/messages/`.
2. Mengekspos 8 skema tool berstandar JSON-RPC 2.0 (`save_note`, `search_notes`, `get_thesis_progress`, `log_habit`, `record_focus_session`, `evaluate_burnout_radar`, `upload_visual_document`, `run_rag_qa`).
3. Membangun adapter dwiarah di `apps/backend/app/agent.py` sehingga Google ADK Agent dapat mengimpor format tool MCP secara native (`adapt_mcp_tool`).
4. Menyediakan file konfigurasi siap pakai `mcp_client_config.json` di root repositori untuk koneksi satu-klik dari desktop clients.

## Konsekuensi & Evaluasi
### Positif
* **Ekosistem Terbuka:** Second Brain dapat bertindak sebagai *tool provider* bagi sembarang model frontier (Claude 3.7, GPT-4o, Gemini 2.0).
* **Kontrak Tipe Kuat:** Skema parameter divalidasi ketat oleh Pydantic dan JSON Schema standar, meminimalkan *malformed tool calls*.
* **Portabilitas:** Klien dapat terhubung via SSE (remote/network) maupun mode `stdio` (local subprocess).

### Negatif / Mitigasi
* *Overhead Protokol:* Format JSON-RPC 2.0 menambah sedikit overhead framing (~5–10ms) dibanding panggilan fungsi Python langsung. Mitigasi: Untuk agen internal internal in-process, adapter memotong serialisasi HTTP berlebih.

