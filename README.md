# Second Brain & Time Management Agent

Sistem multi-user berbasis AI untuk menangkap ide tanpa hambatan (*frictionless capture*) dan melacak waktu *deep work*, langsung dari Telegram.

Dibuat sebagai utilitas pribadi dan untuk lingkaran terbatas. Tanpa gamifikasi, tanpa fitur sosial. Fokusnya efisiensi, kejernihan pikiran, dan pelacakan progres kerja.

> **Status:** 🚧 Fase 2 — bot Telegram (webhook) dan AI agent sudah terintegrasi, sedang diuji di lingkungan lokal. Belum siap dipakai publik.

## Tujuan

1. **Zero-friction capture** — rekam ide, tugas, atau catatan mentah kapan saja lewat Telegram.
2. **Deep work tracking** — lacak durasi sesi fokus (coding, menulis, belajar) tanpa distraksi.
3. **AI-driven synthesis** — AI agent memahami maksud pesan, merapikan catatan, dan membuat ringkasan.
4. **Privasi & isolasi data** — data setiap pengguna terisolasi (lihat [Catatan Keamanan](#catatan-keamanan)).
5. **Keberlanjutan** — mekanisme donasi sederhana untuk menutup biaya server.

## Cara Pakai (Telegram)

Cukup kirim pesan dengan bahasa sehari-hari. Agent yang menentukan aksinya.

| Contoh pesan | Yang terjadi |
| --- | --- |
| `ide: bikin fitur export notes ke markdown` | Disimpan sebagai catatan + tag otomatis |
| `mulai ngoding second brain` | Timer deep work dimulai |
| `udahan dulu` | Timer dihentikan, durasi dicatat |
| `rekap hari ini` / `rekap minggu ini` | Ringkasan waktu fokus per proyek + catatan terbaru |
| `cari catatan soal vue` | Mencari catatan berdasarkan kata kunci |

Kalau AI sedang gagal (misalnya limit API), pesan tetap disimpan sebagai catatan mentah sehingga tidak ada ide yang hilang.

## Tech Stack

| Lapisan | Teknologi |
| --- | --- |
| Backend & API | Python 3.11+, FastAPI, SQLModel, SQLAlchemy (async) + asyncpg |
| Database & Auth | Supabase (PostgreSQL, Auth, Row Level Security) |
| AI Agent | Google ADK (Agent Development Kit) + Gemini (`gemini-3.5-flash`) |
| Bot | Telegram Bot API via webhook (`python-telegram-bot`) |
| Dashboard | Vue 3 (Composition API), Vite, Tailwind CSS v4, `shadcn-vue` |
| Infrastruktur | Cloudflare Tunnel (dev lokal), Railway/Render (backend), Vercel/Netlify (dashboard) |

## Arsitektur

```mermaid
flowchart LR
    U([User])
    TG[Telegram]
    VUE[Vue Dashboard]
    AUTH[Supabase Auth]
    DB[(Supabase PostgreSQL)]

    subgraph BE[FastAPI Backend]
        WH[POST /telegram/webhook]
        MAP[Cari user dari telegram_chat_id]
        AG[Google ADK Agent<br/>+ Gemini]
        API[REST API /api/*]
    end

    U -->|chat| TG
    TG -->|webhook + secret token| WH
    WH --> MAP
    MAP --> AG
    AG -->|"save_note, search_notes,<br/>start_timer, stop_timer, get_summary"| DB
    U --> VUE
    VUE -->|login| AUTH
    VUE -->|request + JWT| API
    API --> DB
```

**Alur pesan Telegram:**

1. Telegram mengirim update ke `POST /telegram/webhook`. Request tanpa secret token yang benar ditolak (403).
2. Backend mencari profil berdasarkan `telegram_chat_id`. Chat yang belum terhubung tidak diproses.
3. Pesan diteruskan ke ADK agent bersama `user_id` milik pengirim. `user_id` ini ditentukan server, bukan oleh LLM.
4. Agent memanggil tool yang sesuai, lalu balasannya dikirim ke Telegram.

Dashboard (Fase 3) belum dibuat.

## Struktur Proyek

```text
second-brain-agent/
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── main.py          # FastAPI app, lifespan bot, endpoint webhook
│       │   ├── bot.py           # Handler Telegram (/start, pesan teks, fallback)
│       │   ├── agent.py         # ADK agent, tools, dan runner
│       │   ├── database.py      # Async engine & session
│       │   └── models.py        # Tabel: profiles, notes, time_logs, donations
│       ├── migrations/          # SQL yang dijalankan manual di Supabase
│       ├── requirements.txt
│       └── .env.example
├── .gitignore
└── README.md
```

## Roadmap MVP (v1.0)

### Fase 1 — Fondasi & Isolasi Data
- [x] Struktur monorepo (`apps/backend`)
- [x] Project Supabase (Database & Auth)
- [x] Koneksi FastAPI ↔ Supabase (SQLModel + asyncpg, session pooler)
- [x] Tabel `profiles`, `notes`, `time_logs`
- [x] Timestamp timezone-aware (`timestamptz`)
- [ ] Kebijakan RLS untuk akses via Supabase API (dashboard)

### Fase 2 — Telegram Bridge & AI Agent
- [x] Bot Telegram via webhook FastAPI (dengan `secret_token`)
- [x] Cloudflare Tunnel untuk dev lokal
- [x] Integrasi Google ADK + Gemini
- [x] Agent tools: `save_note`, `search_notes`, `start_timer`, `stop_timer`, `get_summary`
- [x] Fallback: simpan pesan mentah saat agent gagal
- [ ] Uji end-to-end semua tool di Telegram
- [ ] Fitur "Connect Account" otomatis (saat ini masih manual lewat SQL)
- [ ] Riwayat percakapan persisten (saat ini in-memory, hilang saat restart)

### Fase 3 — Dashboard & Visualisasi
- [ ] Setup Vue 3 + Vite + Tailwind v4 + `shadcn-vue`
- [ ] Login dengan Supabase Auth
- [ ] Halaman *time logs* (grafik) dan *notes* (list & search)

### Fase 4 — Donasi & Deployment
- [ ] Halaman donasi (QRIS statis / Saweria / Trakteer)
- [ ] Deploy backend (Railway/Render) dan dashboard (Vercel/Netlify)
- [ ] Set webhook Telegram ke URL production

## Rencana Setelah v1.0

- **Knowledge graph** — visualisasi hubungan antar catatan.
- **Transkripsi voice note** — agent mentranskrip dan merangkum voice note dari Telegram.
- **Laporan mingguan** — ringkasan otomatis pola *deep work* dan produktivitas.
- **Integrasi payment gateway** (mis. Midtrans) jika donasi butuh pencatatan otomatis.

## Menjalankan Secara Lokal

### Prasyarat

- Python 3.11+
- Project [Supabase](https://supabase.com)
- Token bot Telegram dari [@BotFather](https://t.me/BotFather)
- Gemini API key dari [Google AI Studio](https://aistudio.google.com/apikey)
- [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) — Windows: `winget install --id Cloudflare.cloudflared`

### 1. Clone & install

```bash
git clone https://github.com/fransalwan/second-brain-agent.git
cd second-brain-agent/apps/backend

python -m venv venv
source venv/Scripts/activate     # Windows (Git Bash)
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cp .env.example .env             # lalu isi nilainya
```

### 2. Environment variables

| Variabel | Keterangan |
| --- | --- |
| `DATABASE_URL` | Supabase → **Connect** → **Session pooler**. Format `postgresql://postgres.<project-ref>:<password>@<host>.pooler.supabase.com:5432/postgres` |
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | String acak buatan sendiri: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `GOOGLE_API_KEY` | Gemini API key dari Google AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | `FALSE` |
| `GEMINI_MODEL` | Default `gemini-3.5-flash` |
| `APP_TIMEZONE` | Default `Asia/Jakarta` (untuk "hari ini" / "minggu ini") |

> Gunakan **Session pooler**, bukan Direct connection. Direct connection hanya lewat IPv6 dan akan timeout di kebanyakan jaringan rumah. Buat password database yang hanya berisi huruf dan angka supaya tidak merusak URL.

### 3. Migrasi database

Jalankan file di `apps/backend/migrations/` secara berurutan di **Supabase → SQL Editor**:

1. `001_timer_and_timezones.sql`
2. `002_bigint_telegram_chat_id.sql`

Semua migrasi aman dijalankan ulang.

### 4. Jalankan (butuh 3 terminal)

**Terminal 1 — server**
```bash
uvicorn app.main:app --reload --port 8000
```
Cek koneksi database: `curl -s http://localhost:8000/test-db` harus mengembalikan `"status":"success"`.

**Terminal 2 — tunnel** (biarkan tetap terbuka; URL berganti setiap kali restart)
```bash
cloudflared tunnel --url http://localhost:8000
```

**Terminal 3 — daftarkan webhook**
```bash
set -a; source <(tr -d '\r' < .env); set +a
TUNNEL_URL="https://xxxx.trycloudflare.com"   # dari output Terminal 2

curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${TUNNEL_URL}/telegram/webhook" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d "drop_pending_updates=true"
```

> Jangan jalankan `source .env` di terminal yang dipakai untuk uvicorn. Variabel yang sudah ada di terminal tidak ditimpa oleh `.env`, sehingga server bisa memakai nilai lama.

### 5. Hubungkan akun Telegram

1. Kirim `/start` ke bot, catat **Chat ID** yang dibalas.
2. Buat user di **Supabase → Authentication → Users → Add user** (centang *Auto Confirm User*).
3. Jalankan di SQL Editor:

```sql
insert into public.profiles (id, full_name, telegram_chat_id, created_at)
select id, 'Nama Kamu', 123456789, now()
from auth.users
where email = 'email@contoh.com'
on conflict (id) do update set telegram_chat_id = excluded.telegram_chat_id;
```

Kirim `/start` lagi. Bot akan membalas "Akun kamu sudah terhubung".

## Troubleshooting

Cek status webhook: `curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"`

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `last_error_message: 530` | Tunnel cloudflared mati / URL berganti | Jalankan ulang tunnel, lalu `setWebhook` dengan URL baru |
| `last_error_message: 404` | Server yang jalan versi lama, atau ada proses lama di port 8000 | `netstat -ano \| grep ":8000"`, matikan PID lama (`taskkill //F //T //PID <pid>`), start ulang uvicorn |
| `last_error_message: 403` | Secret di `.env` beda dengan yang didaftarkan | Restart uvicorn, ulangi `setWebhook` |
| Bot membalas "Gagal memproses pesan" | Error di handler | Lihat traceback di terminal uvicorn |
| `password authentication failed` | Password/username `DATABASE_URL` salah, atau terminal masih memegang nilai lama | Salin ulang URI Session pooler; buka terminal baru |
| `[Errno 10060] ... 2406:...` | Memakai Direct connection (IPv6) | Ganti ke Session pooler |
| `value out of int32 range` | Kolom `telegram_chat_id` masih `integer` | Jalankan migrasi `002` |
| Bot membalas "AI sedang bermasalah" | API key salah, kena limit (`429`), atau nama model salah | Cek traceback, `GOOGLE_API_KEY`, dan `GEMINI_MODEL` |

## Catatan Keamanan

- **RLS tidak berlaku untuk query dari backend.** Backend terhubung dengan role `postgres`, yang mem-bypass RLS. Karena itu setiap query dan tool agent memfilter berdasarkan `user_id` yang ditentukan server (dari mapping `telegram_chat_id`), bukan dari input LLM.
- **Webhook divalidasi** dengan header `X-Telegram-Bot-Api-Secret-Token`.
- Bot hanya memproses **chat pribadi**; pesan grup dan pesan yang di-edit diabaikan.
- Jangan pernah commit `.env`, dan jangan menaruh `service_role` key atau `DATABASE_URL` di kode frontend.
- Jika sebuah secret sempat terekspos (log, screenshot, chat), segera rotasi: reset password database, buat API key baru, atau `/revoke` token di @BotFather.

## Dukung Pengembangan

Jika alat ini bermanfaat dan kamu ingin membantu biaya server, silakan kunjungi halaman donasi di dashboard (setelah Fase 4) atau hubungi maintainer.

## Lisensi

Belum ditentukan.
