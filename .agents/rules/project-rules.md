# Second Brain Agent — Project Rules

Aturan ini berasal dari bug yang **sudah pernah terjadi** di project ini, bukan preferensi gaya. Melanggarnya akan mengulang kegagalan yang sama.

Untuk aturan tentang **cara bekerja** (scope, urutan, penanganan secret), lihat `working-rules.md`. Konteks pribadi pemilik instance, kalau ada, ada di `personal-context.md` (tidak ikut repo).

## Tujuan Project

Asisten pribadi di Telegram untuk **memprioritaskan waktu** di antara beberapa area hidup, sambil tetap menjaga kesehatan. Tugas utamanya menjawab "apa yang harus saya kerjakan sekarang?", bukan sekadar mencatat.

Fitur baru harus kecil dan cepat dipakai. Aplikasi manajemen waktu yang menghabiskan waktu untuk dibangun berarti gagal di tujuannya sendiri.

## Model Distribusi: Self-Hosted

Repo ini open source. Setiap orang menjalankan **instance-nya sendiri**:

- Bot Telegram sendiri (dari @BotFather)
- Project Supabase sendiri (free tier cukup)
- Di perangkat sendiri — laptop, PC di rumah, atau mini PC

Tidak ada server pusat, dan pemilik repo tidak menyimpan data siapa pun.

Konsekuensinya untuk kode:

- **Tidak ada nilai pribadi di repo.** Nama area, jadwal, chat ID, atau preferensi apa pun milik satu orang tidak boleh muncul di kode, migrasi, atau dokumentasi.
- **Setup harus bisa diulang dari nol** oleh orang yang belum pernah melihat project ini.
- **Setiap langkah setup yang bisa dihilangkan, hilangkan.** Setiap langkah tambahan adalah tempat orang menyerah.

## Stack

Python 3.11 · FastAPI · SQLModel + SQLAlchemy async + asyncpg · Supabase PostgreSQL · `python-telegram-bot` · Google ADK + Gemini · Vue 3 + Vite + Tailwind v4 (dashboard)

Dependensi backend dikelola **uv**. Working directory backend: `apps/backend`. Dashboard: `apps/dashboard`.

---

## 1. Datetime wajib timezone-aware

Setiap field datetime di SQLModel **harus** pakai `sa_type=DateTime(timezone=True)`, termasuk field nullable.

```python
# BENAR
created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))
ended_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))

# SALAH — kolom di-cast TIMESTAMP WITHOUT TIME ZONE
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Tanpa `sa_type`, asyncpg melempar `DataError: can't subtract offset-naive and offset-aware datetimes` dan **seluruh insert ke tabel itu gagal**. Kegagalannya sering tidak terlihat karena tertangkap try/except di lapisan atas — gejalanya tabel terlihat kosong tanpa error yang jelas.

Jangan pernah mengakalinya dengan `.replace(tzinfo=None)`.

Kolom di Postgres harus `timestamptz`, bukan `timestamp`. Seluruh timestamp disimpan dalam UTC dan dikonversi ke `APP_TIMEZONE` hanya di lapisan tampilan.

**Deadline yang hanya berupa tanggal disimpan sebagai `date`**, bukan `timestamptz`. "Deadline Jumat" berarti hari Jumat di `APP_TIMEZONE`; menyimpannya sebagai tengah malam UTC akan menggesernya ke hari yang salah untuk zona di luar UTC.

## 2. Konfigurasi hanya lewat `app/config.py`

Semua konfigurasi dibaca dari objek `settings` di `app/config.py` (pydantic-settings).

- Jangan `os.getenv()` langsung di modul lain.
- Jangan hardcode token, API key, atau connection string.
- Jangan tulis nilai secret ke log, pesan error, atau komentar.

Nama variabel API key adalah **`GOOGLE_API_KEY`**, mengikuti nama yang dibaca pustaka `google-genai` dari environment. Bukan `GEMINI_API_KEY`.

`config.py` memakai `extra = "ignore"`, sehingga variabel di `.env` yang tidak dideklarasikan tidak menimbulkan error — dan juga tidak muncul di `settings`.

**Setting yang hanya dibutuhkan satu mode tidak boleh wajib di mode lain.** Contoh: `TELEGRAM_WEBHOOK_SECRET` hanya relevan di mode webhook. Pengguna mode polling tidak boleh dipaksa mengisinya. Validasi dilakukan sesuai mode yang aktif, dengan pesan error yang menyebut setting mana yang kurang.

## 3. `user_id` ditentukan server, bukan LLM

Identitas pengguna selalu berasal dari mapping `telegram_chat_id` → `profiles.id` yang dilakukan server sebelum agent dipanggil.

- Tool agent **tidak boleh** menerima `user_id` sebagai parameter yang diisi LLM.
- Setiap query dari backend ke tabel milik pengguna wajib difilter `user_id`.
- Backend connect sebagai role `postgres` sehingga **RLS ter-bypass** — isolasi data di backend sepenuhnya tanggung jawab lapisan query.
- Dashboard memakai anon key + JWT, sehingga isolasinya dijaga RLS. Query dashboard **tidak** memfilter `user_id` secara manual.

## 4. Prioritas dihitung kode, bukan LLM

Urutan tugas di brief harian dan jawaban "apa yang dikerjakan sekarang" ditentukan oleh fungsi deterministik di Python.

Keputusan yang menentukan hari seseorang tidak boleh bergantung pada model yang bisa memberi jawaban berbeda untuk input yang sama. LLM hanya merangkai kalimat dari urutan yang sudah jadi.

Fungsi prioritas harus bisa diuji tanpa memanggil Gemini dan tanpa database.

## 5. Mode Telegram: polling default, webhook opsional

Setting `TELEGRAM_MODE` menentukan cara bot menerima pesan.

**`polling` (default)** — bot menarik pesan dari Telegram. Tidak butuh URL publik, tunnel, domain, atau `setWebhook`. Bekerja di balik router rumah atau jaringan kampus. Ini mode untuk self-hosted di perangkat pribadi.

**`webhook`** — Telegram mendorong pesan ke URL publik. Hanya untuk instance yang di-deploy ke server dengan alamat publik.

Aturan untuk mode polling:

- Saat polling dimulai, webhook yang mungkin masih terdaftar harus dihapus. Verifikasi apakah `python-telegram-bot` melakukannya otomatis, jangan diasumsikan.
- Endpoint `POST /telegram/webhook` tidak aktif.
- **Satu token hanya boleh dipakai satu proses.** Dua proses yang polling dengan token yang sama menghasilkan error `409 Conflict` dan saling memutus.

Aturan untuk mode webhook:

1. Validasi header `X-Telegram-Bot-Api-Secret-Token` dengan `secrets.compare_digest`, tolak 403 kalau tidak cocok.
2. Masukkan update ke `ptb_app.update_queue`.
3. Langsung `return {"ok": True}` — jangan menunggu agent selesai. Gemini bisa butuh puluhan detik dan Telegram akan timeout lalu retry, menghasilkan pesan ganda.

Kode kedua mode harus tetap ada. Jangan hapus jalur webhook hanya karena polling jadi default.

## 6. Area dikonfigurasi pengguna, tidak di-hardcode

Area (misalnya "Kuliah", "Kerja", "Kesehatan") adalah milik pengguna, dibuat per pengguna, dan berbeda untuk setiap orang.

- **Tidak ada nama area di kode, migrasi, atau seed data.**
- Pengguna membuat dan mengurutkan areanya sendiri, lewat chat atau perintah.
- Urutan area menentukan bobot prioritas, dan pengguna bisa mengubahnya kapan saja.
- Pengguna baru yang belum punya area harus diarahkan untuk membuatnya — bukan diberi area default yang diam-diam dianggap benar.

## 7. Onboarding

Satu instance bisa dipakai lebih dari satu orang (misalnya keluarga), jadi alur undangan tetap ada:

1. Admin mengirim `/invite <nama> <email>`
2. Backend membuat user di Supabase Auth lewat Admin API, mengambil UUID-nya
3. UUID disimpan di `invite_codes.auth_user_id` bersama kode acak
4. Pengguna mengirim `/connect <kode>`, `profiles` dibuat dengan `id = auth_user_id`

**`/connect` menolak invite code yang `auth_user_id`-nya sudah punya profil.** Ini mencegah pemindahan profil ke chat ID lain — jalur pembajakan akun. Jangan diubah menjadi upsert.

`/invite` memakai otorisasi diam: chat non-admin tidak mendapat respons apa pun.

## 8. Skema database

Perubahan skema ditulis sebagai file SQL bernomor di `apps/backend/migrations/`, dijalankan manual di Supabase SQL Editor. Tidak pakai Alembic.

Setiap migrasi harus aman dijalankan ulang (idempotent).

**Tabel baru berisi data pengguna wajib disertai RLS di migrasi yang sama**: `enable row level security` plus policy `SELECT` untuk role `authenticated` dengan `auth.uid() = user_id`. Policy yang dibuat terpisah lewat dashboard Supabase tidak tercatat di repo, sehingga instance baru mendapat tabel tanpa perlindungan.

## 9. Dependensi lewat uv

`pyproject.toml` dan `uv.lock` adalah sumber kebenaran. Tidak ada `requirements.txt`.

- Menambah paket: `uv add <nama>`
- Menjalankan sesuatu: `uv run <perintah>`
- Menyiapkan environment dari nol: `uv sync`

`pyproject.toml` hanya mendaftarkan **dependensi langsung**. Jangan pernah mengimpor hasil `pip freeze` — itu mengunci ratusan paket transitif dan pernah menahan `google-adk` di versi yang belum punya `ToolContext.user_id`.

`uv.lock` wajib ke-commit.

## 10. Scheduler berjalan di proses yang sama

Pesan yang dikirim bot tanpa diminta (brief pagi, pengingat) memakai **JobQueue** bawaan `python-telegram-bot`, bukan pustaka scheduler terpisah dan bukan cron eksternal.

Instance self-hosted sering berjalan di perangkat yang tidak selalu menyala. Setiap job harian **wajib** punya mekanisme susulan: saat startup, periksa apakah job hari ini sudah terkirim; kalau belum dan waktunya sudah lewat, kirim sekarang. Catat pengiriman di database supaya restart tidak mengirim ulang.

`--reload` me-restart proses setiap file `.py` berubah. Tanpa pencatatan di database, setiap simpan file akan mengirim brief lagi.

Jam pengiriman adalah preferensi pengguna, bukan konstanta di kode.

---

## Konvensi yang Sudah Ada

Ikuti pola di file yang sudah ada sebelum memperkenalkan pola baru:

- `app/main.py` — FastAPI app, lifespan PTB, endpoint
- `app/bot.py` — handler Telegram: `/start`, `/connect`, `/invite`, `handle_message()`
- `app/agent.py` — definisi ADK agent, tools, `run_agent()`
- `app/config.py` — pydantic Settings, objeknya bernama `settings`
- `app/models.py` — seluruh tabel SQLModel
- `app/database.py` — engine & session async
- `pyproject.toml` / `uv.lock` — dependensi
- `apps/dashboard/src/lib/supabase.ts` — client Supabase tunggal untuk dashboard

Tabel: `profiles`, `notes`, `chat_histories`, `time_logs`, `donations`, `invite_codes`.

Tool agent: `save_note`, `search_notes`, `start_timer`, `stop_timer`, `get_summary`.

---

## Jebakan Lingkungan Dev

Jangan menyarankan hal-hal berikut — sudah terbukti bermasalah:

| Jangan | Alasan | Gantinya |
|---|---|---|
| `python` polos | Menunjuk ke Python sistem, tanpa dependensi project | `uv run python` |
| `pip install`, `requirements.txt`, `venv/` | Sudah tidak dipakai sejak migrasi ke uv | `uv add`, `uv sync` |
| `source .env` | Tidak kebal BOM; variabel lama di shell tidak ditimpa | Baca lewat `app.config` |
| Asumsi `--reload` membaca ulang `.env` | Uvicorn hanya memantau file `.py` | Restart manual setiap ubah `.env` |
| Command berisi placeholder `<TOKEN>`, `<PID>` | Pernah diketik apa adanya | Set variabel dulu, lalu pakai `$VAR` |
| Model Gemini dari ingatan | Model lama dipensiunkan tanpa pemberitahuan | Pakai `settings.GEMINI_MODEL` |
| Supabase Direct connection | IPv6, timeout di banyak jaringan rumah | Session pooler, port 5432 |
| Kolom chat ID sebagai `integer` | Chat ID Telegram melebihi int32 | `bigint` / `sa_type=BigInteger` |
| Menjalankan `uvicorn --reload` sendiri | Proses foreground, menggantung terminal agent | Minta pemilik yang menjalankan |
| Menjalankan uvicorn berulang tanpa mematikan yang lama | Instance lama tetap hidup; di mode polling menyebabkan `409 Conflict` | Satu proses saja; cek dengan `netstat` |

`.env` harus UTF-8 **tanpa BOM**, line ending LF. BOM membuat key di baris pertama tidak terbaca `python-dotenv`.

Perintah backend dijalankan dari `apps/backend`, bukan dari root repo.

**Khusus mode webhook:** tunnel harus mengarah ke port yang benar (`ngrok http 8080` terhadap uvicorn di 8000 menghasilkan 502 dalam ~2ms), dan URL yang didaftarkan harus URL tunnel, bukan domain dashboard penyedianya.

---

## Keputusan yang Sudah Mengikat

Jangan usulkan membatalkan ini tanpa informasi baru yang benar-benar mengubah perhitungan:

- **Self-hosted, open source.** Tidak ada server pusat.
- **Polling sebagai mode default**, webhook tetap didukung.
- **Area dibuat pengguna**, tidak pernah di-hardcode.
- **`profiles.id` terikat ke `auth.users.id`**, bukan UUID mandiri.
- **`user_id` ditentukan server**, tidak pernah dari output LLM.
- **Urutan prioritas dihitung kode**, tidak pernah dari output LLM.
- **`/connect` menolak, bukan upsert**, kalau profil sudah ada.
- **Migrasi database manual dan bernomor**, bukan Alembic.
- **`GOOGLE_API_KEY`**, bukan `GEMINI_API_KEY`.
- **uv sebagai package manager.**
- **RLS dashboard read-only** — hanya `SELECT` untuk `authenticated`. Izin tulis ditambahkan hanya kalau fiturnya dibuat.
- **Login dashboard memakai magic link.**
- **Scheduler memakai JobQueue PTB**, dengan susulan saat startup.

---

## Status & Prioritas

**Sudah jalan:**
- Bot Telegram → FastAPI → ADK/Gemini → Supabase, mode webhook
- Seluruh agent tool terverifikasi
- Onboarding `/invite` dan `/connect`
- Dashboard Vue 3 dengan magic link, menampilkan notes dan time_logs lewat RLS

**Belum diuji:** `/connect` dengan kode valid dari akun yang belum punya profil.

**Prioritas berikutnya, berurutan:**

1. **Mode polling** — jadikan default, pertahankan webhook
2. **Area** — tabel dan alur pembuatan oleh pengguna
3. **Tugas** — tabel `tasks` dan tool agent untuk menambah dan menyelesaikan lewat chat
4. **Fungsi prioritas** — deterministik, dapat diuji, memilih maksimal tiga tugas
5. **Brief pagi** — JobQueue dengan susulan saat startup
6. Habit harian
7. Pengingat istirahat saat timer berjalan terlalu lama
8. Batas jam kerja malam

**Pendukung open source, bisa dikerjakan kapan saja:** file lisensi, file skema gabungan untuk instalasi baru.
