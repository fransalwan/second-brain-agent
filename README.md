# Second Brain Agent

Bot Telegram yang berfungsi sebagai "otak kedua" — kirim pesan biasa, agent AI akan mengklasifikasi dan menyimpannya sebagai catatan terstruktur di database.

Contoh: kirim `ide: bikin fitur export notes ke markdown`, bot akan menyimpannya sebagai note dengan tag yang relevan dan membalas konfirmasi.

## Stack

| Komponen | Teknologi |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Bot | python-telegram-bot (mode webhook) |
| Agent | Google ADK + Gemini |
| Database | Supabase (PostgreSQL) via SQLModel + asyncpg |
| Tunneling (dev) | ngrok |

## Arsitektur

```
Telegram  ──POST──>  ngrok  ──>  FastAPI /telegram/webhook
                                        │
                                        │ validasi secret token
                                        ▼
                                  PTB update_queue
                                        │
                                        ▼
                                  bot.handle_message
                                        │
                                        ▼
                                  agent.run_agent  ──> Gemini (ADK)
                                        │                  │
                                        │                  └─> tools: simpan note, dll
                                        ▼
                                  Supabase (notes, chat_histories)
```

Webhook membalas `200 OK` secepatnya lalu memproses update di background, supaya Telegram tidak melakukan retry.

## Struktur

```
apps/backend/
├── app/
│   ├── main.py        # FastAPI app + endpoint webhook
│   ├── bot.py         # handler python-telegram-bot
│   ├── agent.py       # definisi ADK agent + tools
│   ├── models.py      # SQLModel: Profile, Note, ChatHistory, TimeLog, Donation
│   ├── database.py    # engine & session async
│   └── config.py      # settings dari .env (pydantic)
└── .env
```

## Setup

### 1. Prasyarat

- Python 3.11+
- Akun Supabase
- Bot Telegram (buat lewat [@BotFather](https://t.me/BotFather))
- Google AI Studio API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- ngrok (untuk development lokal)

### 2. Install

```bash
cd apps/backend
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 3. Konfigurasi

Salin `.env.example` menjadi `.env`, lalu isi:

```env
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
DATABASE_URL=              # Project > Connect > Session pooler (port 5432)

# Telegram
TELEGRAM_BOT_TOKEN=        # dari @BotFather, formatnya 123456:AAH...
TELEGRAM_WEBHOOK_SECRET=   # generate: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Google ADK / Gemini
GOOGLE_API_KEY=
GOOGLE_GENAI_USE_VERTEXAI=False
GEMINI_MODEL=gemini-3.6-flash

# Lain-lain
APP_TIMEZONE=Asia/Jakarta
```

> **Penting:** simpan `.env` dengan encoding **UTF-8 tanpa BOM** dan line ending **LF**. BOM akan membuat key pertama tidak terbaca oleh `python-dotenv`.

### 4. Jalankan

Tiga terminal:

```bash
# Terminal 1 — server
uvicorn app.main:app --reload --port 8000

# Terminal 2 — tunnel
ngrok http 8000
```

```bash
# Terminal 3 — daftarkan webhook
TOKEN=$(python -c "from app.config import settings; print(settings.TELEGRAM_BOT_TOKEN)" | tr -d '\r\n')
SECRET=$(python -c "from app.config import settings; print(settings.TELEGRAM_WEBHOOK_SECRET)" | tr -d '\r\n')
NGROK=$(curl -s http://127.0.0.1:4040/api/tunnels | python -c "import sys,json; print([t['public_url'] for t in json.load(sys.stdin)['tunnels'] if t['public_url'].startswith('https')][0])")

curl -s -X POST "https://api.telegram.org/bot$TOKEN/setWebhook" \
  -d "url=$NGROK/telegram/webhook" \
  -d "secret_token=$SECRET" \
  -d "drop_pending_updates=true"
```

> URL ngrok berubah setiap kali direstart. Ulangi blok terminal 3 setiap sesi baru.

Verifikasi:

```bash
curl -s "https://api.telegram.org/bot$TOKEN/getWebhookInfo" | python -m json.tool
```

Yang diharapkan: `url` menunjuk ke domain ngrok saat ini, `pending_update_count: 0`, dan tidak ada `last_error_message`.

## Endpoint

| Method | Path | Keterangan |
|---|---|---|
| GET | `/` | Health check |
| GET | `/test-db` | Cek koneksi Supabase |
| POST | `/telegram/webhook` | Menerima update dari Telegram (butuh header secret) |

## Troubleshooting

### Bot diam, tidak ada log di Uvicorn

Request belum sampai ke server lokal. Urutan pengecekan:

1. Buka `http://127.0.0.1:4040` (ngrok inspector). Kosong berarti Telegram tidak pernah memanggil URL tunnel — lanjut ke langkah 2. Ada request tapi statusnya 4xx/5xx berarti masalahnya di sisi aplikasi.
2. Cek `getWebhookInfo`. Pastikan `url` benar-benar domain ngrok aktif, bukan tunnel lama.
3. Pastikan URL berasal dari baris `Forwarding` di terminal ngrok, bukan dari halaman dashboard ngrok.

### `403 Invalid secret token`

Nilai `TELEGRAM_WEBHOOK_SECRET` yang dipegang Uvicorn berbeda dengan yang didaftarkan ke Telegram. Perubahan `.env` **tidak** terbaca oleh `--reload` — restart Uvicorn secara manual.

Bandingkan kedua nilai:

```bash
python -c "from app.config import settings; import hashlib; s=settings.TELEGRAM_WEBHOOK_SECRET; print(len(s), hashlib.sha256(s.encode()).hexdigest()[:12])"
```

### Port 8000 masih dipakai setelah Ctrl+C

```bash
netstat -ano | findstr LISTENING | findstr :8000
taskkill //PID <pid> //F
```

### `404 NOT_FOUND` dari Gemini

Model sudah dipensiunkan Google. Lihat model yang tersedia untuk API key kamu:

```bash
GKEY=$(python -c "from app.config import settings; print(settings.GOOGLE_API_KEY)" | tr -d '\r\n')
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GKEY" \
  | python -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models'] if 'generateContent' in m.get('supportedGenerationMethods',[])]"
```

Catatan: model bisa muncul di daftar ini tapi tetap ditolak untuk akun baru. Pesan error dari Google biasanya sudah menyebutkan model penggantinya. Gunakan `gemini-flash-latest` bila ingin alias yang mengikuti rilis stabil terbaru.

### `can't subtract offset-naive and offset-aware datetimes`

Kolom datetime di model kehilangan `sa_type=DateTime(timezone=True)`, sehingga di-cast sebagai `TIMESTAMP WITHOUT TIME ZONE` padahal nilainya timezone-aware. Samakan dengan model lain:

```python
created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))
```

Pastikan juga kolom di Postgres bertipe `timestamptz`:

```sql
ALTER TABLE chat_histories
ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';
```

## Keamanan

- `.env` tidak pernah di-commit. Pastikan tercantum di `.gitignore`.
- Endpoint webhook memvalidasi header `X-Telegram-Bot-Api-Secret-Token` menggunakan `secrets.compare_digest`.
- Bila bot token pernah terekspos, segera revoke lewat @BotFather → `/mybots` → API Token → Revoke current token.

## Status

Pipeline berjalan penuh: Telegram → ngrok → FastAPI → ADK/Gemini → Supabase.

Rencana berikutnya:

- [ ] Deploy ke host permanen (menghilangkan ketergantungan ngrok)
- [ ] Perintah pencarian & ringkasan catatan
- [ ] Integrasi tabel `time_logs` dan `donations`
