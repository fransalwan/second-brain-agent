# Second Brain & Time Management Agent

Sistem multi-user berbasis AI untuk menangkap ide tanpa hambatan (*frictionless capture*) dan melacak waktu *deep work*, langsung dari Telegram.

Dibuat sebagai utilitas pribadi dan untuk lingkaran terbatas. Tanpa gamifikasi, tanpa fitur sosial. Fokusnya efisiensi, kejernihan pikiran, dan pelacakan progres kerja.

> **Status:** 🚀 Fase 3 selesai (Agent ADK, Onboarding Auth /invite & /connect, RLS 005, Dashboard Vue 3). Fase 4 (Deployment ke cloud) ditunda sementara karena kendala verifikasi kartu di Render; backend tetap berjalan lokal via tunnel domain statis ngrok.

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

> Batas "hari ini" mengikuti tengah malam waktu `APP_TIMEZONE`. Sesi yang dimulai pukul 23:35 dan rekap yang diminta pukul 00:10 dihitung sebagai dua hari berbeda.

## Tech Stack

| Lapisan | Teknologi |
| --- | --- |
| Backend & API | Python 3.11, FastAPI, SQLModel, SQLAlchemy (async) + asyncpg, uv |
| Database & Auth | Supabase (PostgreSQL, Auth, Row Level Security) |
| AI Agent | Google ADK (Agent Development Kit) + Gemini (`gemini-3.6-flash`) |
| Bot | Telegram Bot API via polling (default self-hosted) / webhook (`python-telegram-bot`) |
| Dashboard | Vue 3 (Composition API), Vite, TypeScript, Tailwind CSS v4, vue-router |
| Infrastruktur | ngrok domain statis (backend lokal), Render (rencana deployment cloud) |
| Tooling development | Antigravity IDE (agent-first, membaca `.agents/`) |

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
2. Endpoint memasukkan update ke `update_queue` milik `python-telegram-bot` lalu langsung membalas `200 OK`, supaya Telegram tidak melakukan retry saat agent butuh waktu lama.
3. Backend mencari profil berdasarkan `telegram_chat_id`. Chat yang belum terhubung tidak diproses.
4. Pesan diteruskan ke ADK agent bersama `user_id` milik pengirim. `user_id` ini ditentukan server, bukan oleh LLM.
5. Agent memanggil tool yang sesuai, balasannya dikirim ke Telegram, dan percakapan dicatat di `chat_histories`.

Seluruh timestamp disimpan dalam UTC (`timestamptz`) dan dikonversi ke `APP_TIMEZONE` hanya di lapisan tampilan. Artinya nilai di Supabase akan terlihat mundur 7 jam dari WIB — itu perilaku yang benar, bukan bug.

Dashboard (Fase 3) berada di `apps/dashboard`, dibangun dengan Vue 3, Vite, TypeScript, dan Tailwind CSS v4. Dashboard mengakses Supabase secara langsung menggunakan Supabase Client dengan RLS (Row Level Security) yang membatasi hak baca pengguna terautentikasi (SELECT-only).

## Struktur Proyek

```text
second-brain-agent/
├── .agents/
│   ├── rules/               # Aturan project untuk AI coding agent
│   └── skills/              # Panduan Google ADK
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py      # FastAPI app, lifespan bot, endpoint webhook
│   │   │   ├── bot.py       # Handler Telegram (/start, /invite, /connect, fallback)
│   │   │   ├── agent.py     # ADK agent, tools, dan runner
│   │   │   ├── config.py    # Settings dari .env (pydantic-settings)
│   │   │   ├── database.py  # Async engine & session
│   │   │   └── models.py    # Tabel: profiles, notes, chat_histories, time_logs, donations, invite_codes
│   │   ├── migrations/      # SQL manual di Supabase (001 s.d. 005)
│   │   ├── pyproject.toml   # Dependensi backend (uv)
│   │   ├── uv.lock          # Kunci dependensi transitif
│   │   └── .env.example     # Template env development
│   └── dashboard/
│       ├── src/             # Vue 3 SPA (Login OTP/Magic link, HomeView notes & timers)
│       ├── package.json
│       ├── vite.config.ts
│       └── .env.example     # VITE_SUPABASE_URL & VITE_SUPABASE_ANON_KEY
├── .gitignore
└── README.md
```

## Development dengan AI Agent

Project ini dikembangkan dengan bantuan [Antigravity](https://antigravity.google), IDE agent-first dari Google. Folder `.agents/` berisi konteks yang dibaca otomatis oleh AI coding agent:

| Folder | Isi | Fungsi |
| --- | --- | --- |
| `.agents/skills/` | Dokumentasi Google ADK | Pengetahuan domain: cara membuat agent, tools, dan runner yang benar |
| `.agents/rules/` | Aturan project | Standar yang wajib diikuti saat menulis kode di repo ini |

Aturan di `.agents/rules/` **tidak berisi preferensi gaya**, melainkan invariant yang berasal dari bug yang sudah pernah terjadi:

1. Field datetime wajib `sa_type=DateTime(timezone=True)`
2. Secret hanya diakses lewat `app/config.py`, tidak pernah hardcode
3. `user_id` ditentukan server dari `telegram_chat_id`, bukan dari output LLM
4. Webhook membalas 200 sebelum memproses agent
5. Migrasi database manual dan idempotent

Setelah membuka project di Antigravity, verifikasi rules terbaca dengan bertanya di panel agent (`Ctrl+L`):

> Apa aturan project ini soal field datetime di SQLModel, dan kenapa aturan itu ada?

Jawaban yang benar menyebut `sa_type=DateTime(timezone=True)` beserta alasannya (penolakan asyncpg, insert gagal). Jawaban generik tentang timezone berarti rules belum aktif.

Manfaat konkret di project ini: audit statis seluruh field datetime dan perhitungan durasi selesai dalam hitungan detik, menggantikan trial-and-error lewat Telegram yang butuh berkali-kali percobaan.

## Roadmap MVP (v1.0)

### Fase 1 — Fondasi & Isolasi Data ✅
- [x] Struktur monorepo (`apps/backend`)
- [x] Project Supabase (Database & Auth)
- [x] Koneksi FastAPI ↔ Supabase (SQLModel + asyncpg, session pooler)
- [x] Tabel `profiles`, `notes`, `chat_histories`, `time_logs`
- [x] Timestamp timezone-aware (`timestamptz`) di seluruh model
- [x] Kebijakan RLS untuk akses via Supabase API (migrasi 005)

### Fase 2 — Telegram Bridge & AI Agent ✅
- [x] Bot Telegram via webhook FastAPI (dengan `secret_token`)
- [x] Tunnel untuk dev lokal (ngrok)
- [x] Integrasi Google ADK + Gemini
- [x] Agent tools: `save_note`, `search_notes`, `start_timer`, `stop_timer`, `get_summary`
- [x] Fallback: simpan pesan mentah saat agent gagal
- [x] Riwayat percakapan persisten di tabel `chat_histories`
- [x] Uji end-to-end seluruh tool di Telegram
- [x] Setup `.agents/` untuk AI-assisted development

### Fase 2.5 — Onboarding ✅
- [x] Perintah `/invite <nama> <email>` khusus admin untuk mendaftarkan user ke Supabase Auth
- [x] Perintah `/connect <kode>` aman dari pembajakan akun (menolak kode yang sudah bertaut)

### Fase 3 — Dashboard & Visualisasi ✅
- [x] Setup Vue 3 + Vite + TypeScript + Tailwind CSS v4 + vue-router
- [x] Login via Magic Link / OTP Supabase Auth (bebas kebocoran password di chat)
- [x] Navigation guard & pembersihan token hash dari URL browser
- [x] Halaman dashboard: daftar notes, active timer, rekap time logs dengan waktu lokal

### Fase 4 — Deployment & Donasi (Ditunda Sementara)
- [ ] Deploy backend FastAPI ke cloud (ditunda: verifikasi kartu Render)
- [ ] Deploy dashboard ke cloud
- [ ] Halaman donasi (QRIS statis / Saweria / Trakteer)

## Rencana Setelah v1.0

- **Knowledge graph** — visualisasi hubungan antar catatan.
- **Transkripsi voice note** — agent mentranskrip dan merangkum voice note dari Telegram.
- **Laporan mingguan** — ringkasan otomatis pola *deep work* dan produktivitas.
- **Logical day start** — opsi `DAY_START_HOUR` supaya sesi dini hari dihitung sebagai hari sebelumnya.
- **Integrasi payment gateway** (mis. Midtrans) jika donasi butuh pencatatan otomatis.

## Arsitektur Dual Bot (Rencana Deployment Masa Depan)

Saat ini di lingkungan lokal, sistem berjalan dengan satu bot Telegram. Namun saat backend dideploy ke cloud nanti, Telegram Bot API hanya mengizinkan **satu URL webhook aktif per bot token**. Jika lingkungan lokal dan produksi memakai token bot yang sama, mendaftarkan webhook ngrok lokal saat coding akan langsung menimpa webhook produksi di server — akibatnya seluruh pesan pengguna di Telegram akan dialihkan ke laptop Anda (atau gagal total jika laptop mati).

Oleh karena itu, ketika siap deploy ke cloud, sistem akan memisahkan dua bot Telegram di [@BotFather](https://t.me/BotFather):
1. **Bot Produksi (`@SecondBrainBot`)**:
   - Token & secret disetel di Environment Variables server cloud.
   - Webhook terdaftar permanen ke URL server cloud.
   - Melayani pengguna sehari-hari tanpa pernah disentuh oleh sesi coding lokal.
2. **Bot Development (`@SecondBrainDevBot`)**:
   - Token & secret disetel di `apps/backend/.env` lokal.
   - Webhook didaftarkan ke tunnel ngrok saat sesi pengujian lokal.

---

## Menjalankan Secara Lokal

### Prasyarat

- Python 3.11 (dikelola lewat `uv`)
- Node.js 20+ & npm (untuk dashboard)
- Project [Supabase](https://supabase.com)
- Token bot Telegram dari [@BotFather](https://t.me/BotFather)
- Akun [ngrok](https://ngrok.com) dengan **1 domain statis gratis** (klaim di Dashboard ngrok → menu **Domains** → **Create Domain**, misal `<domain-statis-kamu>.ngrok-free.app` atau `.ngrok-free.dev`)
- Gemini API key dari [Google AI Studio](https://aistudio.google.com/apikey)
- Opsional: [Antigravity](https://antigravity.google) untuk development dengan AI agent

### 1. Clone & install

**Backend:**
```bash
git clone https://github.com/fransalwan/second-brain-agent.git
cd second-brain-agent/apps/backend
uv sync
cp .env.example .env
```

**Dashboard:**
```bash
cd ../dashboard
npm install
cp .env.example .env
```

### 2. Environment variables backend (`apps/backend/.env`)

| Variabel | Keterangan |
| --- | --- |
| `DATABASE_URL` | Supabase → **Connect** → **Session pooler**. Format `postgresql://postgres.<project-ref>:<password>@<host>.pooler.supabase.com:5432/postgres` (port 5432) |
| `TELEGRAM_MODE` | Default `polling` (untuk self-hosted lokal tanpa tunnel). Opsi: `webhook` |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram dari @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | String acak, **hanya wajib** jika `TELEGRAM_MODE=webhook`: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ADMIN_CHAT_ID` | Telegram Chat ID admin untuk otorisasi perintah `/invite` |
| `GOOGLE_API_KEY` | Gemini API key dari Google AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | `FALSE` |
| `GEMINI_MODEL` | Default `gemini-3.6-flash` |
| `APP_TIMEZONE` | Default `Asia/Jakarta` (untuk "hari ini" / "minggu ini") |
| `SUPABASE_URL` | URL project Supabase (`https://<project-ref>.supabase.co`) |
| `SUPABASE_ANON_KEY` | Anon key Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key Supabase (khusus backend untuk pembuatan user auth via `/invite`) |

> Gunakan **Session pooler**, bukan Direct connection. Direct connection hanya lewat IPv6 dan akan timeout di kebanyakan jaringan rumah. Buat password database yang hanya berisi huruf dan angka supaya tidak merusak URL.

> **Simpan `.env` dengan encoding UTF-8 tanpa BOM dan line ending LF.** BOM membuat key di baris pertama tidak terbaca oleh `python-dotenv`.

Verifikasi konfigurasi backend:
```bash
uv run python -c "
from app.config import settings
for k in ('TELEGRAM_MODE','TELEGRAM_BOT_TOKEN','TELEGRAM_WEBHOOK_SECRET','GOOGLE_API_KEY','GEMINI_MODEL','DATABASE_URL'):
    v = getattr(settings, k, '') or ''
    print(k, 'OK' if v else 'KOSONG (OPSIONAL)' if k == 'TELEGRAM_WEBHOOK_SECRET' and settings.TELEGRAM_MODE == 'polling' else 'KOSONG', len(str(v)))
"
```

### 3. Migrasi database

Jalankan file di `apps/backend/migrations/` secara berurutan di **Supabase → SQL Editor**:

1. `001_timer_and_timezones.sql`
2. `002_bigint_telegram_chat_id.sql`
3. `003_chat_histories_timestamptz.sql`
4. `004_invite_codes.sql`
5. `005_rls_policies.sql`

Semua migrasi aman dijalankan ulang (idempotent).

### 4. Menjalankan Backend & Bot

Secara default, bot berjalan dalam **mode polling** (`TELEGRAM_MODE=polling`). Anda **tidak membutuhkan ngrok**, domain publik, atau registrasi webhook.

#### A. Mode Polling (Default — Self-Hosted Lokal)

Cukup jalankan 1 terminal untuk server backend:

```bash
cd apps/backend
uv run uvicorn app.main:app --reload --port 8000
```
Cek koneksi database: `curl -s http://localhost:8000/test-db` harus mengembalikan `"status":"success"`.

> **Catatan drop_pending_updates=False:** Pada mode polling, pesan Telegram yang dikirim saat server/komputer mati akan otomatis ditarik dan diproses begitu backend menyala kembali. Untuk instalasi *self-hosted* di perangkat pribadi, ini perilaku yang diharapkan agar tidak ada ide atau catatan yang terlewat.

> **Catatan error `409 Conflict` saat `--reload`:** Saat file `.py` disimpan dan uvicorn me-reload proses, proses baru bisa mulai berjalan sesaat sebelum proses lama selesai memutus koneksi polling. Telegram akan merespons `409 Conflict` selama beberapa detik. Begitu proses lama benar-benar berhenti, proses baru akan otomatis tersambung normal tanpa perlu tindakan manual.

Verifikasi status polling (memastikan webhook lama sudah terhapus):
```bash
uv run python -c "
from app.bot import ptb_app
import asyncio
async def check():
    async with ptb_app.bot:
        info = await ptb_app.bot.get_webhook_info()
        print(f'Webhook URL: {info.url!r} (kosong = polling aktif)')
        print(f'Pending updates: {info.pending_update_count}')
asyncio.run(check())
"
```
*(Skrip di atas aman digunakan karena mengecek via client bot tanpa mencetak URL request mentah atau token ke terminal).*

#### B. Mode Webhook (Opsional — Server Publik)

Jika dideploy ke server publik (seperti Render atau VPS):
1. Set `TELEGRAM_MODE=webhook` dan isi `TELEGRAM_WEBHOOK_SECRET` di `.env`.
2. Daftarkan URL webhook sekali saja:
   ```bash
   cd apps/backend
   TOKEN=$(uv run python -c "from app.config import settings; print(settings.TELEGRAM_BOT_TOKEN)" | tr -d '\r\n')
   SECRET=$(uv run python -c "from app.config import settings; print(settings.TELEGRAM_WEBHOOK_SECRET)" | tr -d '\r\n')
   curl -s -X POST "https://api.telegram.org/bot$TOKEN/setWebhook" \
     -d "url=https://<domain-kamu>/telegram/webhook" \
     -d "secret_token=$SECRET" \
     -d "drop_pending_updates=true"
   ```

### 5. Menjalankan Dashboard Lokal

```bash
cd apps/dashboard
npm run dev
```
Dashboard berjalan di `http://localhost:5173`.

### 6. Onboarding Pengguna

1. Dari chat Telegram admin (sesuai `ADMIN_CHAT_ID`), kirim ke bot:
   ```text
   /invite Nama Pengguna email@contoh.com
   ```
   Backend akan membuat akun di Supabase Auth dan membalas dengan **kode invite 8 karakter**.
2. Pengguna mengirimkan perintah tautan ke bot:
   ```text
   /connect <KODE_INVITE>
   ```
   Bot akan menautkan Telegram Chat ID pengguna ke profil akun Supabase Auth tersebut.
3. Pengguna dapat membuka dashboard (`/login`), memasukkan email yang sama, lalu mengklik Magic Link yang dikirim ke email untuk masuk ke dashboard.

---

## Panduan Deployment ke Render (Ditunda — Referensi Masa Depan)

> **Catatan Status:** Deployment ke Render saat ini ditunda karena Free Tier Render mewajibkan verifikasi kartu kredit dan menolak kartu virtual. Backend dan bot tetap dijalankan secara lokal dengan domain statis ngrok. Panduan di bawah ini dipertahankan sebagai referensi teknis saat siap melakukan deployment ke cloud atau berpindah provider.

Deployment menggunakan Render Free Tier untuk backend dan static site dashboard:

### 1. Backend (Render Web Service)

1. Buat service baru di [Render Dashboard](https://dashboard.render.com): **New +** → **Web Service**.
2. Hubungkan repository GitHub dan konfigurasikan:
   - **Name**: `second-brain-backend` (atau sesuaikan)
   - **Root Directory**: `apps/backend`
   - **Runtime**: `Python`
   - **Instance Type**: `Free`
   - **Build Command**: `uv sync --frozen` *(Render mendukung uv secara native jika terdapat `uv.lock` di root service)*
   - **Start Command**: `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Tambahkan **Environment Variables** di Render:
   - `PYTHON_VERSION`: `3.11.11` *(Wajib disetel! Default Render saat ini adalah Python 3.14 yang tidak kompatibel dengan `requires-python = ">=3.11,<3.13"`)*
   - `DATABASE_URL`: URI Supabase Session pooler (port 5432)
   - `TELEGRAM_BOT_TOKEN`: Token **Bot Produksi** (@SecondBrainBot)
   - `TELEGRAM_WEBHOOK_SECRET`: String acak secret produksi (buat baru lewat `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - `ADMIN_CHAT_ID`: Chat ID Telegram admin
   - `GOOGLE_API_KEY`: API key Google Gemini
   - `GOOGLE_GENAI_USE_VERTEXAI`: `FALSE`
   - `GEMINI_MODEL`: `gemini-3.6-flash`
   - `APP_TIMEZONE`: `Asia/Jakarta`
   - `SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `SUPABASE_ANON_KEY`: Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
4. Simpan dan tunggu deploy selesai hingga log menunjukkan `Application startup complete`.

### 2. Daftarkan Webhook Bot Produksi

Setelah backend aktif dan memiliki URL Render (misal `https://second-brain-backend.onrender.com`), daftarkan webhook bot produksi sekali saja via terminal:

```bash
PROD_TOKEN="<TOKEN_BOT_PRODUKSI>"
PROD_SECRET="<SECRET_TOKEN_PRODUKSI>"
RENDER_URL="https://second-brain-backend.onrender.com"

curl -s -X POST "https://api.telegram.org/bot$PROD_TOKEN/setWebhook" \
  -d "url=$RENDER_URL/telegram/webhook" \
  -d "secret_token=$PROD_SECRET" \
  -d "drop_pending_updates=true"
```

Verifikasi:
```bash
curl -s "https://api.telegram.org/bot$PROD_TOKEN/getWebhookInfo" | python -m json.tool
```

### 3. Dashboard (Render Static Site)

1. Buat service baru di Render: **New +** → **Static Site**.
2. Hubungkan repository GitHub dan konfigurasikan:
   - **Name**: `second-brain-dashboard`
   - **Root Directory**: `apps/dashboard`
   - **Build Command**: `npm run build`
   - **Publish Directory**: `dist`
3. Tambahkan **Environment Variables**:
   - `VITE_SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `VITE_SUPABASE_ANON_KEY`: Supabase anon key
4. Tambahkan **Redirect / Rewrite Rules** di menu pengaturan static site Render:
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Action**: `Rewrite` *(Bukan Redirect — ini wajib agar Vue Router History Mode tidak menghasilkan 404 saat halaman di-refresh)*.

### 4. Whitelist Supabase Auth Redirect URLs

Buka **Supabase Dashboard** → **Authentication** → **URL Configuration**:
- **Site URL**: Isi dengan domain dashboard produksi (misal `https://second-brain-dashboard.onrender.com`).
- **Redirect URLs**: Tambahkan entri berikut agar login Magic Link bekerja di lokal maupun produksi:
  - `http://localhost:5173/**`
  - `https://second-brain-dashboard.onrender.com/**`

## Troubleshooting

Cek status webhook: `curl -s "https://api.telegram.org/bot$TOKEN/getWebhookInfo" | python -m json.tool`

### Aturan pertama: restart uvicorn

Sebelum menduga ada bug di kode, pastikan server yang berjalan memuat versi terbaru. `--reload` hanya memantau file `.py` — perubahan `.env` tidak terbaca, dan proses lama bisa tertinggal memegang port.

Tiga bug yang tampak berbeda di project ini (`403 Invalid secret token`, konfigurasi yang seolah tidak berpengaruh, dan `get_summary` yang mengembalikan nol) semuanya berakar pada hal yang sama. Restart bersih lebih murah daripada debugging spekulatif.

### Bot diam total, tidak ada log apa pun di uvicorn

Request tidak sampai ke server lokal. Alat pemisah paling tajam adalah **ngrok inspector** di `http://127.0.0.1:4040`, dashboard lokal yang mencatat semua request yang masuk ke tunnel.

- **Inspector kosong** saat pesan dikirim → Telegram tidak pernah memanggil URL tunnel. Masalahnya di konfigurasi webhook: cek `url` di `getWebhookInfo`, pastikan itu domain `.ngrok-free.app` yang aktif, bukan tunnel lama.
- **Inspector berisi request** → traffic sampai. Lihat status code-nya lalu lanjut ke tabel di bawah.

### Tabel gejala

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `last_error_message: 404` + `ip_address` asing | Webhook menunjuk ke `app.ngrok.ai` (halaman dashboard ngrok), bukan ke tunnel | `setWebhook` ulang dengan URL dari baris `Forwarding` |
| `last_error_message: 530` / `Connection refused` | Tunnel ngrok belum berjalan di lokal | Jalankan Terminal 2: `ngrok http 8000 --url=<domain-statis-kamu>` |
| `403 Invalid secret token` | Nilai secret yang dipegang uvicorn ≠ yang didaftarkan ke Telegram | Restart uvicorn — `.env` **tidak** dibaca ulang oleh `--reload` |
| `403` tetap muncul walau sudah restart | Ada proses uvicorn zombie memegang port 8000 | Lihat bagian *Port 8000* di bawah |
| `{"ok":false,"error_code":404}` dari `getMe` | `$TOKEN` kosong, atau placeholder terketik apa adanya | `echo "${#TOKEN}"` — harus 45–46 |
| `Read timeout expired` | Handler menunggu operasi lama sebelum membalas | Pastikan endpoint membalas 200 sebelum memproses agent |
| Bot lambat merespons setelah lama tidak dipakai (1–5 menit) | Cold start Render Free Tier setelah 15 menit idle | Perilaku normal Render, bukan bug. Lihat bagian *Cold start Render* di bawah |
| Bot membalas "AI sedang bermasalah" | Model salah/pensiun, API key salah, atau kena limit (`429`) | Lihat bagian *Gemini 404* di bawah |
| `can't subtract offset-naive and offset-aware datetimes` | Kolom datetime tidak timezone-aware | Lihat bagian *Timezone* di bawah |
| Rekap mengembalikan 0 padahal data ada | Server belum di-restart, atau batas hari sudah lewat tengah malam | Restart uvicorn; cek `mulai_wib` di `time_logs` |
| `password authentication failed` | Kredensial `DATABASE_URL` salah, atau terminal memegang nilai lama | Salin ulang URI Session pooler; buka terminal baru |
| `[Errno 10060] ... 2406:...` | Memakai Direct connection (IPv6) | Ganti ke Session pooler |
| `value out of int32 range` | Kolom `telegram_chat_id` masih `integer` | Jalankan migrasi `002` |

### Port 8000 masih dipakai setelah Ctrl+C

Proses uvicorn bisa tertinggal dan tetap memegang port. Yang menjawab request adalah instance lama dengan `.env` versi sebelumnya, sehingga perubahan konfigurasi seolah-olah tidak berpengaruh.

```bash
netstat -ano | findstr LISTENING | findstr :8000
taskkill //PID <pid> //F     # ganti <pid> dengan angka di kolom terakhir
```

Normalnya hanya ada satu atau dua baris (parent + child dari `--reload`). Lebih dari itu, matikan semuanya lalu start ulang.

### Gemini `404 NOT_FOUND`

Model sudah dipensiunkan. Lihat model yang tersedia untuk API key kamu:

```bash
GKEY=$(python -c "from app.config import settings; print(settings.GOOGLE_API_KEY)" | tr -d '\r\n')
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GKEY" \
  | python -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models'] if 'generateContent' in m.get('supportedGenerationMethods',[])]"
```

Daftar ini **tidak sepenuhnya akurat** — sebuah model bisa terdaftar tapi tetap ditolak untuk akun baru (`no longer available to new users`). Pesan error dari Google biasanya sudah menyebutkan model penggantinya; ikuti saja. Alternatifnya pakai alias `gemini-flash-latest` yang selalu menunjuk rilis flash stabil terbaru.

Tes model sebelum mengubah `.env`:

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key=$GKEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"halo"}]}]}' | head -c 300
```

### Timezone: `can't subtract offset-naive and offset-aware datetimes`

Terjadi saat field datetime di SQLModel tidak diberi `sa_type`, sehingga di-cast sebagai `TIMESTAMP WITHOUT TIME ZONE` padahal nilainya membawa `tzinfo=utc`. Asyncpg menolaknya dengan `DataError` dan seluruh insert ke tabel itu gagal. Kegagalan ini mudah terlewat karena sering tertangkap error handling di lapisan atas — gejalanya tabel terlihat kosong sementara alur lain tetap berjalan normal.

```python
# Salah
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Benar
created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))
```

Berlaku juga untuk field nullable seperti `TimeLog.ended_at`.

Jangan mengakalinya dengan `.replace(tzinfo=None)` — timestamp kehilangan informasi zona dan perhitungan "hari ini" / "minggu ini" berdasarkan `APP_TIMEZONE` menjadi salah.

Pastikan juga kolom di Postgres bertipe `timestamptz`:

```sql
ALTER TABLE chat_histories
ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';
```

### Memeriksa data dalam waktu lokal

Kolom `timestamptz` disimpan dalam UTC. Untuk melihatnya dalam WIB tanpa mengubah data:

```sql
select project_name,
       duration_minutes,
       started_at at time zone 'Asia/Jakarta' as mulai_wib,
       ended_at   at time zone 'Asia/Jakarta' as selesai_wib
from time_logs
order by started_at desc;
```

Berguna saat rekap terasa tidak sesuai — sering kali penyebabnya batas tengah malam, bukan bug.

### Cold start Render (Bot lambat merespons setelah lama tidak dipakai)

> *Catatan: Bagian ini merupakan referensi perilaku saat backend dideploy ke cloud platform gratis seperti Render yang memiliki mekanisme idle spin-down.*

Jika bot tidak menerima request selama **15 menit**, Render Free Tier akan otomatis mematikan (*spin-down*) instance kontainer untuk menghemat kuota komputasi.

Ketika pesan pertama dikirim setelah masa idle tersebut:
1. Permintaan webhook memicu Render melakukan *spin-up*. Proses booting container, inisialisasi FastAPI, database pooler, dan bot membutuhkan waktu **30–60 detik**.
2. Karena batas *connection timeout* pengiriman webhook dari Telegram cukup ketat (sekitar 5–10 detik), percobaan pertama Telegram akan gagal / timeout.
3. Telegram Bot API otomatis menjadwalkan pengiriman ulang (*retry*) dengan mekanisme *exponential backoff*. Percobaan retry pertama biasanya tiba dalam **1–5 menit**.
4. Begitu service backend Render selesai aktif, Telegram berhasil mengirimkan retry tersebut, backend membalas `200 OK`, dan pesan diproses.

> **Penting:** Ini adalah perilaku bawaan platform gratis Render, **bukan bug dan pesan tidak pernah hilang**. Telegram terus menyimpan dan mencoba mengirim antrean pesan hingga 24 jam. Pesan-pesan berikutnya yang dikirim selama service masih terjaga (dalam jendela 15 menit) akan direspons secara instan.

## Catatan Keamanan

- **RLS tidak berlaku untuk query dari backend.** Backend terhubung dengan role `postgres`, yang mem-bypass RLS. Karena itu setiap query dan tool agent memfilter berdasarkan `user_id` yang ditentukan server (dari mapping `telegram_chat_id`), bukan dari input LLM.
- **Webhook divalidasi** dengan header `X-Telegram-Bot-Api-Secret-Token` menggunakan `secrets.compare_digest` (perbandingan constant-time).
- Bot hanya memproses **chat pribadi**; pesan grup dan pesan yang di-edit diabaikan.
- Jangan pernah commit `.env`, dan jangan menaruh `service_role` key atau `DATABASE_URL` di kode frontend. Verifikasi dengan `git check-ignore -v .env` dan `git log --all --oneline -- "*.env"`.
- Saat menempelkan output terminal ke mana pun (issue, chat, screenshot), **sensor token**. Untuk membandingkan dua nilai tanpa mengeksposnya, bandingkan hash-nya:
  ```bash
  python -c "import hashlib,sys; s=sys.argv[1]; print(len(s), hashlib.sha256(s.encode()).hexdigest()[:12])" "$SECRET"
  ```
- Jika sebuah secret sempat terekspos (log, screenshot, chat), segera rotasi: reset password database, buat API key baru, atau revoke token di @BotFather → `/mybots` → **API Token** → **Revoke current token**.

## Dukung Pengembangan

Jika alat ini bermanfaat dan kamu ingin membantu biaya server, silakan kunjungi halaman donasi di dashboard (setelah Fase 4) atau hubungi maintainer.

## Lisensi

Belum ditentukan.
