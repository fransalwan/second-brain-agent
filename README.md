# Second Brain Agent

Asisten pribadi di Telegram yang membantu menjawab satu pertanyaan setiap hari: **"apa yang harus saya kerjakan sekarang?"**

Tangkap ide, catat tugas beserta deadline-nya, lacak sesi fokus, dan atur prioritas di antara beberapa area hidup — kuliah, pekerjaan, project pribadi — cukup lewat chat biasa.

> **Status:** ✅ Siap pakai & open-source. Semua fitur inti (tugas, area, timer, prioritas deterministik, brief pagi, habit, dan bedtime guardian) telah terimplementasi dan teruji.

---

## Kenapa project ini ada

Daftar tugas biasa punya masalah yang sama: semakin panjang daftarnya, semakin bingung mulai dari mana. Second Brain Agent tidak mencoba menampilkan lebih banyak tugas — tujuannya menampilkan **lebih sedikit**, dengan urutan yang jelas dan alasan yang bisa dipahami.

Prinsip yang dipegang:

- **Tanpa hambatan.** Kirim pesan seperti ngobrol biasa. Tidak ada form, tidak ada aplikasi yang harus dibuka.
- **Keputusan penting dihitung kode, bukan AI.** Urutan prioritas ditentukan fungsi yang bisa diuji. AI hanya membantu memahami bahasa sehari-hari.
- **Tetap jalan saat AI tidak tersedia.** Fitur inti tidak bergantung pada kuota API.
- **Data milikmu sendiri.** Kamu menjalankan instance-mu sendiri. Tidak ada server pusat.

---

## Fitur

| Fitur | Status |
| --- | --- |
| Tangkap ide dan catatan dari chat | ✅ |
| Timer deep work per project, rekap harian dan mingguan | ✅ |
| Area hidup yang bisa diatur dan diurutkan sendiri | ✅ |
| Tugas dengan deadline dari bahasa sehari-hari ("deadline jumat") | ✅ |
| Penanda tugas mendesak | ✅ |
| Perintah cepat tanpa AI (`/areas`, `/tasks`, `/done`, `/habits`, `/timer`, `/night`) | ✅ |
| Dashboard web read-only dengan login magic link | ✅ |
| Undangan untuk pengguna lain di instance yang sama | ✅ |
| Fungsi prioritas: tiga tugas teratas beserta alasannya (3-tier deterministik) | ✅ |
| Brief pagi otomatis (0 kuota LLM, susulan instan saat online) | ✅ |
| Pelacakan kebiasaan harian (streak & integrasi ke brief pagi) | ✅ |
| Pengingat istirahat saat fokus & batas jam kerja malam (*bedtime guardian*) | ✅ |

---

## Cara pakai

Kirim pesan ke bot seperti biasa. Agent yang menentukan aksinya.

| Kirim | Yang terjadi |
| --- | --- |
| `ide: bikin fitur export notes ke markdown` | Disimpan sebagai catatan dengan tag otomatis |
| `area saya: Kuliah, Kerja, Project` | Membuat area, urutannya jadi bobot prioritas |
| `tambah area Kesehatan` | Menambah area di urutan terakhir |
| `ubah urutan area: Kerja, Kuliah, Project` | Mengubah urutan prioritas |
| `tugas kuliah: revisi bab 2 deadline jumat` | Menyimpan tugas di area Kuliah dengan deadline Jumat terdekat |
| `tandai mendesak #3` | Menandai tugas #3 sebagai mendesak |
| `mulai ngoding second brain` | Memulai timer deep work |
| `udahan dulu` | Menghentikan timer, durasi dicatat |
| `rekap hari ini` | Ringkasan waktu fokus dan catatan hari ini |
| `cari catatan soal vue` | Mencari catatan berdasarkan kata kunci |

### Perintah cepat

Perintah berikut **tidak memakai AI** — responsnya instan dan tetap bekerja saat kuota Gemini habis.

| Perintah | Fungsi |
| --- | --- |
| `/start` | Sapaan, atau menampilkan Chat ID kalau akun belum terhubung |
| `/areas` | Daftar area terurut berdasarkan prioritas |
| `/tasks` | Daftar tugas pending terurut algoritma prioritas (3-tier) beserta ID-nya |
| `/done <id>` | Menandai tugas selesai secara instan |
| `/habits` | Melihat daftar habit aktif dan streak saat ini |
| `/check <id>` | Mencentang habit yang sudah diselesaikan hari ini |
| `/timer` | Melihat status timer aktif beserta durasi berjalan |
| `/stop` | Menghentikan timer aktif secara langsung |
| `/night [HH:MM]` | Melihat atau mengubah batas jam kerja malam (*bedtime guardian*) |
| `/connect <kode>` | Menghubungkan akun Telegram dengan kode undangan |
| `/invite <nama> <email>` | Membuat kode undangan (khusus admin) |

Setiap balasan tentang tugas selalu menyebut area, nama hari, dan tanggal deadline. Kalau AI salah menangkap maksudmu, kesalahannya langsung terlihat dan bisa dikoreksi.

Pesan yang dikirim saat backend mati **tidak hilang** — akan diproses begitu backend menyala kembali.

---

## Arsitektur

```mermaid
flowchart LR
    U([Kamu])
    TG[Telegram]
    DB[(Supabase PostgreSQL)]
    G[Gemini]

    subgraph BE[Backend di perangkatmu]
        BOT[python-telegram-bot<br/>mode polling]
        CMD[Perintah cepat<br/>/areas /tasks /done]
        AG[Google ADK Agent]
    end

    subgraph WEB[Dashboard]
        VUE[Vue 3]
    end

    U -->|chat| TG
    BOT -->|menarik pesan| TG
    BOT --> CMD
    BOT --> AG
    AG <--> G
    CMD --> DB
    AG -->|tools| DB
    U --> VUE
    VUE -->|anon key + JWT, dijaga RLS| DB
```

Backend memakai **long polling**: bot menarik pesan dari Telegram, bukan menerima kiriman ke URL publik. Artinya tidak perlu tunnel, domain, atau IP publik — backend bisa berjalan di laptop, PC rumah, atau mini PC, di balik router mana pun.

Mode webhook tetap tersedia untuk instance yang di-deploy ke server (lihat [Mode webhook](#mode-webhook)).

**Tech stack:** Python 3.11 · FastAPI · SQLModel + asyncpg · Supabase (PostgreSQL, Auth, RLS) · python-telegram-bot · Google ADK + Gemini · Vue 3 + Vite + Tailwind CSS v4 · uv

---

## Menjalankan instance sendiri

### Yang dibutuhkan

- [uv](https://docs.astral.sh/uv/) — mengurus Python dan semua dependensi
- Project [Supabase](https://supabase.com) (free tier cukup)
- Bot Telegram dari [@BotFather](https://t.me/BotFather)
- Gemini API key dari [Google AI Studio](https://aistudio.google.com/apikey)
- Node.js, kalau ingin menjalankan dashboard

### 1. Clone dan install

```bash
git clone https://github.com/fransalwan/second-brain-agent.git
cd second-brain-agent/apps/backend
uv sync
cp .env.example .env
```

### 2. Siapkan database

#### Opsi A: Instance Baru (1-Klik via SQL Editor)
Jalankan file [`apps/backend/migrations/init_schema.sql`](apps/backend/migrations/init_schema.sql) langsung di **Supabase → SQL Editor**. Skema lengkap tabel, relasi, indeks, dan kebijakan RLS akan dibuat secara otomatis sekaligus.

#### Opsi B: Migrasi Bertahap (Instance Berjalan)
Jalankan file di `apps/backend/migrations/` secara berurutan di **Supabase → SQL Editor**:

1. `001_timer_and_timezones.sql`
2. `002_bigint_telegram_chat_id.sql`
3. `003_chat_histories_timestamptz.sql`
4. `004_invite_codes.sql`
5. `005_rls_policies.sql`
6. `006_areas_and_tasks.sql`
7. `007_add_brief_columns_to_profiles.sql`
8. `008_habits.sql`
9. `009_timer_break_reminder.sql`
10. `010_night_cutoff.sql`

Semua file migrasi dan file inisialisasi aman dijalankan ulang (*idempotent*).

### 3. Isi `.env`

| Variabel | Keterangan |
| --- | --- |
| `DATABASE_URL` | Supabase → **Connect** → **Session pooler** (port 5432) |
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `GOOGLE_API_KEY` | Gemini API key dari Google AI Studio |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → `service_role` (untuk `/invite`) |
| `ADMIN_CHAT_ID` | Chat ID Telegram-mu — cara mendapatkannya ada di langkah 5 |
| `TELEGRAM_MODE` | `polling` (default) atau `webhook` |
| `GEMINI_MODEL` | Nama model Gemini yang dipakai |
| `APP_TIMEZONE` | Zona waktumu, misalnya `Asia/Jakarta` |

> Gunakan **Session pooler**, bukan Direct connection — Direct connection hanya lewat IPv6 dan sering timeout di jaringan rumah.

> Simpan `.env` sebagai **UTF-8 tanpa BOM**. BOM membuat variabel di baris pertama tidak terbaca.

### 4. Jalankan

```bash
uv run uvicorn app.main:app --port 8000
```

Satu terminal saja. Tidak perlu ngrok.

### 5. Hubungkan akunmu

1. Kirim `/start` ke bot. Karena akunmu belum terhubung, bot akan menampilkan **Chat ID**-mu.
2. Isi `ADMIN_CHAT_ID` di `.env` dengan angka itu, lalu restart backend (`Ctrl+C`, jalankan lagi).
3. Kirim `/invite NamaKamu email@kamu.com` — bot membalas dengan kode undangan.
4. Kirim `/connect <kode>` — akunmu terhubung.
5. Buat area pertamamu: `area saya: Kuliah, Kerja, Project`.

Untuk mengundang orang lain ke instance yang sama, ulangi langkah 3 dengan nama dan email mereka, lalu kirimkan kodenya. Kode berlaku tujuh hari dan hanya bisa dipakai sekali.

### 6. Dashboard (opsional)

```bash
cd apps/dashboard
npm install
cp .env.example .env
```

Isi `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` (anon key aman untuk browser — isolasi data dijaga RLS). Lalu:

```bash
npm run dev
```

Di Supabase → **Authentication → URL Configuration**, isi **Site URL** dengan `http://localhost:5173` dan tambahkan `http://localhost:5173/**` ke **Redirect URLs**, supaya tautan login magic link kembali ke dashboard.

---

## Tentang kuota Gemini

Free tier Gemini dibatasi per hari dan per menit untuk setiap model. Satu pesan chat bisa memakai dua sampai tiga request — satu untuk memilih aksi, satu lagi untuk merangkai balasan.

Kalau kuota habis:

- Pesan bahasa bebas tetap **disimpan sebagai catatan mentah**, tidak ada yang hilang
- Perintah cepat (`/areas`, `/tasks`, `/done`) tetap bekerja normal
- Kuota pulih otomatis setelah reset harian

Cek batas dan pemakaianmu di [ai.dev/rate-limit](https://ai.dev/rate-limit). Model varian *lite* biasanya punya batas lebih longgar.

---

## Mode webhook

Untuk instance di server dengan URL publik, set di `.env`:

```
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_SECRET=<string acak>
```

Buat secret dengan `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"`, lalu daftarkan webhook ke `https://<domainmu>/telegram/webhook` dengan parameter `secret_token` yang sama.

Saat kembali ke mode polling, webhook dihapus otomatis.

---

## Troubleshooting

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| Bot tidak membalas sama sekali | Backend mati, atau menjalankan kode lama | Restart backend. Di mode polling, pesan **tidak** muncul di log uvicorn — itu normal |
| Perintah `/xxx` diabaikan | Perintah belum ada di versi yang berjalan | Restart backend setelah menarik kode baru |
| `409 Conflict` di log | Dua proses memakai token bot yang sama | Hentikan semua proses, jalankan satu saja. Muncul sesaat saat restart itu normal |
| "AI sedang bermasalah" | Kuota Gemini habis (429) atau server Gemini sibuk (503) | Tunggu; pesanmu sudah tersimpan sebagai catatan |
| `404 NOT_FOUND` dari Gemini | Model sudah dipensiunkan | Ganti `GEMINI_MODEL`; pesan error biasanya menyebut penggantinya |
| `uv trampoline failed to canonicalize script path` | Folder project dipindah bersama `.venv` | `rm -rf .venv` lalu `uv sync` |
| `password authentication failed` / timeout IPv6 | `DATABASE_URL` salah atau memakai Direct connection | Salin ulang URI Session pooler |
| Variabel `.env` tidak terbaca | File tersimpan dengan BOM, atau backend belum di-restart | Simpan ulang sebagai UTF-8 tanpa BOM; restart |
| Dashboard kosong padahal data ada | Migrasi 005/006 belum dijalankan, atau akun belum `/connect` | Jalankan migrasi; hubungkan akun |
| Magic link tidak kembali ke dashboard | Redirect URL belum didaftarkan | Tambahkan URL dashboard di Supabase → URL Configuration |

Catatan waktu: semua timestamp disimpan dalam UTC. Nilai di Supabase akan tampak berbeda beberapa jam dari waktu lokalmu — itu benar, konversi dilakukan saat ditampilkan.

---

## Keamanan

- **Isolasi data.** Backend memfilter setiap query berdasarkan pengguna yang ditentukan server dari Chat ID Telegram, tidak pernah dari output AI. Dashboard dilindungi Row Level Security dengan akses baca saja.
- **Undangan aman.** `/connect` menolak kode yang akunnya sudah terhubung, sehingga kode tidak bisa dipakai untuk memindahkan akun orang lain. `/invite` tidak merespons sama sekali untuk selain admin.
- **ID tidak bocor.** Mencoba menyelesaikan tugas milik orang lain menghasilkan pesan yang identik dengan ID yang tidak ada.
- **Jangan commit `.env`.** Periksa dengan `git check-ignore -v apps/backend/.env`.
- **Kalau secret terekspos** (di screenshot, chat, atau log), rotasi segera: revoke token di @BotFather, buat API key baru, reset password database.

---

## Pengembangan

Tes otomatis memakai SQLite di memori (Rule 13) dan tidak menyentuh database asli Supabase:

```bash
cd apps/backend
uv run python tests/test_priority.py          # Logika prioritas 3-tier
uv run python tests/test_brief_scheduler.py   # Formatter & scheduler brief pagi
uv run python tests/test_direct_commands.py   # Perintah cepat non-LLM & isolasi user
uv run python tests/test_task_tools.py        # Validasi tool tugas & injeksi tanggal
uv run python tests/test_habits.py            # Habit, streak, & idempotent check
uv run python tests/test_break_reminder.py    # Pengingat istirahat & /timer /stop
uv run python tests/test_night_cutoff.py      # Batas jam kerja malam & /night
```

Project ini dikembangkan dengan bantuan AI coding agent. Folder `.agents/rules/` berisi aturan yang dibaca otomatis oleh agent — setiap aturan berasal dari bug yang pernah terjadi, bukan preferensi gaya. Membacanya adalah cara tercepat memahami keputusan desain di project ini.

Menambah dependensi: `uv add <paket>`. Perubahan skema: file SQL bernomor baru di `migrations/`, lengkap dengan kebijakan RLS.

---

## Roadmap

**Selesai**

- [x] Fungsi prioritas — tiga tugas teratas beserta alasannya (3-tier deterministik)
- [x] Brief pagi otomatis, dengan susulan kalau perangkat baru dinyalakan setelah jadwal
- [x] Pelacakan kebiasaan harian (streak, idempotent check, ringkasan brief)
- [x] Pengingat istirahat saat sesi fokus terlalu lama (>= 90 menit, anti-spam)
- [x] Batas jam kerja malam (*bedtime guardian*, /night, dan soft warning)
- [x] File skema gabungan untuk instalasi baru (`init_schema.sql`)

**Ide berikutnya**

- [ ] Transkripsi voice note
- [ ] Laporan mingguan pola kerja
- [ ] Visualisasi hubungan antar catatan

---

## Lisensi

MIT — lihat [LICENSE](LICENSE).