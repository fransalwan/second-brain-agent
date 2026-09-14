# Second Brain Agent — Project Rules

Aturan ini berasal dari bug yang **sudah pernah terjadi** di project ini, bukan preferensi gaya. Melanggarnya akan mengulang kegagalan yang sama.

## Stack

Python 3.11 · FastAPI · SQLModel + SQLAlchemy async + asyncpg · Supabase PostgreSQL · `python-telegram-bot` (webhook) · Google ADK + Gemini · ngrok (dev)

Dijalankan di Windows 11 / Git Bash. Working directory: `apps/backend`.

---

## 1. Datetime wajib timezone-aware

Setiap field datetime di SQLModel **harus** pakai `sa_type=DateTime(timezone=True)`.

```python
# BENAR
created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))

# SALAH — kolom di-cast TIMESTAMP WITHOUT TIME ZONE
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Tanpa `sa_type`, asyncpg melempar `DataError: can't subtract offset-naive and offset-aware datetimes` dan **seluruh insert ke tabel itu gagal**. Kegagalannya sering tidak terlihat karena tertangkap try/except di lapisan atas — gejalanya tabel terlihat kosong tanpa error yang jelas.

Jangan pernah mengakalinya dengan `.replace(tzinfo=None)`. Timestamp kehilangan informasi zona dan perhitungan "hari ini" / "minggu ini" berdasarkan `APP_TIMEZONE` menjadi salah.

Kolom di Postgres harus `timestamptz`, bukan `timestamp`.

## 2. Secret hanya lewat `app/config.py`

Semua konfigurasi dibaca dari objek `settings` di `app/config.py` (pydantic-settings).

```python
from app.config import settings
model = settings.GEMINI_MODEL
```

- Jangan `os.getenv()` langsung di modul lain.
- Jangan hardcode token, API key, atau connection string.
- Jangan tulis nilai secret ke log, pesan error, atau komentar.

Kalau butuh membandingkan dua nilai secret saat debugging, bandingkan panjang dan hash-nya, jangan nilainya.

## 3. `user_id` ditentukan server, bukan LLM

Identitas pengguna selalu berasal dari mapping `telegram_chat_id` → `profiles.id` yang dilakukan server sebelum agent dipanggil.

- Tool agent **tidak boleh** menerima `user_id` sebagai parameter yang diisi LLM.
- Setiap query ke `notes`, `time_logs`, `chat_histories` wajib difilter `user_id`.
- Backend connect sebagai role `postgres` sehingga **RLS ter-bypass** — isolasi data sepenuhnya tanggung jawab lapisan query.

## 4. Webhook membalas dulu, proses belakangan

Endpoint `POST /telegram/webhook`:

1. Validasi header `X-Telegram-Bot-Api-Secret-Token` dengan `secrets.compare_digest`, tolak 403 kalau tidak cocok.
2. Masukkan update ke `ptb_app.update_queue`.
3. Langsung `return {"ok": True}`.

Jangan menunggu agent selesai sebelum membalas. Gemini bisa butuh puluhan detik dan Telegram akan timeout lalu retry, menghasilkan pesan ganda.

## 5. Migrasi database manual

Perubahan skema ditulis sebagai file SQL bernomor di `apps/backend/migrations/`, dijalankan manual di Supabase SQL Editor. Tidak pakai Alembic.

Setiap migrasi harus aman dijalankan ulang (idempotent).

---

## Konvensi yang Sudah Ada

Ikuti pola di file yang sudah ada sebelum memperkenalkan pola baru:

- `app/main.py` — FastAPI app, lifespan PTB, endpoint
- `app/bot.py` — handler Telegram, `handle_message()`
- `app/agent.py` — definisi ADK agent, tools, `run_agent()`
- `app/models.py` — seluruh tabel SQLModel
- `app/database.py` — engine & session async

Tabel: `profiles`, `notes`, `chat_histories`, `time_logs`, `donations`.

Tool agent yang sudah ada: `save_note`, `search_notes`, `start_timer`, `stop_timer`, `get_summary`.

---

## Jebakan Lingkungan Dev

Jangan menyarankan hal-hal berikut — sudah terbukti bermasalah di setup ini:

| Jangan | Alasan | Gantinya |
|---|---|---|
| `source .env` | Tidak kebal BOM; variabel lama di shell tidak ditimpa | Baca lewat `app.config` |
| Asumsi `--reload` membaca ulang `.env` | Uvicorn hanya memantau file `.py` | Restart manual setiap ubah `.env` |
| Command berisi placeholder `<TOKEN>`, `<PID>` | Pernah diketik apa adanya | Set variabel dulu, lalu pakai `$VAR` |
| Model Gemini dari ingatan | `gemini-1.5-flash` dan `gemini-2.5-flash` sudah tidak tersedia | Pakai `settings.GEMINI_MODEL` |
| Supabase Direct connection | IPv6, timeout di jaringan rumah | Session pooler, port 5432 |
| `telegram_chat_id` sebagai `integer` | Chat ID Telegram melebihi int32 | `bigint` |

Catatan ngrok: URL berganti setiap restart, jadi `setWebhook` perlu diulang tiap sesi. Ambil URL dari `http://127.0.0.1:4040/api/tunnels`, bukan dari halaman dashboard ngrok.

---

## Status & Prioritas

**Sudah jalan:** pipeline Telegram → ngrok → FastAPI → ADK/Gemini → Supabase, end-to-end. `save_note` terverifikasi, `chat_histories` terisi.

**Prioritas berikutnya, berurutan:**

1. Verifikasi `start_timer` / `stop_timer` / `get_summary` lewat Telegram
2. Fitur `/connect` otomatis (sekarang masih SQL manual)
3. Deploy backend ke Railway/Render, lepas dari ngrok
4. Dashboard Vue 3

Jangan mulai dashboard sebelum tiga item pertama selesai.

---

## Cara Bekerja di Project Ini

- Diagnosis sebelum solusi. Kalau penyebabnya belum pasti, usulkan cara mengeceknya dulu.
- Satu perubahan per langkah. Jangan menyentuh banyak file sekaligus tanpa diminta.
- Jelaskan mekanismenya, bukan cuma perintahnya. Ini project belajar.
- Bahasa Indonesia santai, istilah teknis tetap bahasa Inggris.
