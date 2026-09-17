# Second Brain Agent — Project Rules

Aturan ini berasal dari bug yang **sudah pernah terjadi** di project ini, bukan preferensi gaya. Melanggarnya akan mengulang kegagalan yang sama.

Untuk aturan tentang **cara bekerja** (scope, urutan, penanganan secret), lihat `working-rules.md`.

## Stack

Python 3.11 · FastAPI · SQLModel + SQLAlchemy async + asyncpg · Supabase PostgreSQL · `python-telegram-bot` (webhook) · Google ADK + Gemini · ngrok (dev)

Dijalankan di Windows 11 / Git Bash. Working directory: `apps/backend`.

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

Jangan pernah mengakalinya dengan `.replace(tzinfo=None)`. Timestamp kehilangan informasi zona dan perhitungan "hari ini" / "minggu ini" berdasarkan `APP_TIMEZONE` menjadi salah.

Kolom di Postgres harus `timestamptz`, bukan `timestamp`.

Seluruh timestamp disimpan dalam UTC dan dikonversi ke `APP_TIMEZONE` hanya di lapisan tampilan. Nilai di Supabase akan terlihat mundur 7 jam dari WIB — itu benar, bukan bug.

## 2. Secret hanya lewat `app/config.py`

Semua konfigurasi dibaca dari objek `settings` di `app/config.py` (pydantic-settings).

```python
from app.config import settings

model = settings.GEMINI_MODEL
```

- Jangan `os.getenv()` langsung di modul lain.
- Jangan hardcode token, API key, atau connection string.
- Jangan tulis nilai secret ke log, pesan error, atau komentar.

Nama variabel API key adalah **`GOOGLE_API_KEY`**, mengikuti nama yang dibaca pustaka `google-genai` dari environment. Bukan `GEMINI_API_KEY`. Pernah tidak konsisten antara `config.py`, `.env`, dan `.env.example`; jangan diubah lagi tanpa alasan kuat.

`config.py` memakai `extra = "ignore"`, sehingga variabel di `.env` yang tidak dideklarasikan **tidak** menimbulkan error — dan juga tidak muncul di `settings`. Kalau sebuah nilai terbaca di runtime tapi tidak ada di `Settings`, kemungkinan dibaca langsung dari environment oleh pustaka lain.

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

## 5. Onboarding: invite code terikat ke `auth.users`

Alur pendaftaran:

1. Admin mengirim `/invite <nama> <email>` dari Telegram
2. Backend membuat user di Supabase Auth lewat Admin API, mengambil UUID-nya
3. UUID itu disimpan di `invite_codes.auth_user_id` bersama kode acak
4. Pengguna mengirim `/connect <kode>`, `profiles` dibuat dengan `id = auth_user_id`

**`/connect` menolak invite code yang `auth_user_id`-nya sudah punya profil.** Ini mencegah sebuah kode memindahkan profil yang ada ke chat ID lain — jalur pembajakan akun. Jangan diubah menjadi upsert.

`/invite` memakai otorisasi diam: chat non-admin tidak mendapat respons apa pun, seolah perintahnya tidak ada.

## 6. Migrasi database manual

Perubahan skema ditulis sebagai file SQL bernomor di `apps/backend/migrations/`, dijalankan manual di Supabase SQL Editor. Tidak pakai Alembic.

Setiap migrasi harus aman dijalankan ulang (idempotent).

---

## Konvensi yang Sudah Ada

Ikuti pola di file yang sudah ada sebelum memperkenalkan pola baru:

- `app/main.py` — FastAPI app, lifespan PTB, endpoint
- `app/bot.py` — handler Telegram: `/start`, `/connect`, `/invite`, `handle_message()`
- `app/agent.py` — definisi ADK agent, tools, `run_agent()`
- `app/config.py` — pydantic Settings, objeknya bernama `settings`
- `app/models.py` — seluruh tabel SQLModel
- `app/database.py` — engine & session async

Tabel: `profiles`, `notes`, `chat_histories`, `time_logs`, `donations`, `invite_codes`.

Tool agent: `save_note`, `search_notes`, `start_timer`, `stop_timer`, `get_summary`.

---

## Jebakan Lingkungan Dev

Jangan menyarankan hal-hal berikut — sudah terbukti bermasalah di setup ini:

| Jangan | Alasan | Gantinya |
|---|---|---|
| `python` polos di terminal agent | Terminal agent tidak mewarisi venv | `venv/Scripts/python.exe` |
| `source .env` | Tidak kebal BOM; variabel lama di shell tidak ditimpa | Baca lewat `app.config` |
| Asumsi `--reload` membaca ulang `.env` | Uvicorn hanya memantau file `.py` | Restart manual setiap ubah `.env` |
| Command berisi placeholder `<TOKEN>`, `<PID>` | Pernah diketik apa adanya | Set variabel dulu, lalu pakai `$VAR` |
| Model Gemini dari ingatan | `gemini-1.5-flash` dan `gemini-2.5-flash` sudah tidak tersedia | Pakai `settings.GEMINI_MODEL` |
| Supabase Direct connection | IPv6, timeout di jaringan rumah | Session pooler, port 5432 |
| Kolom chat ID sebagai `integer` | Chat ID Telegram melebihi int32 | `bigint` / `sa_type=BigInteger` |
| Menjalankan `uvicorn --reload` sendiri | Proses foreground, menggantung terminal agent | Minta saya yang menjalankan |

`.env` harus UTF-8 **tanpa BOM**, line ending LF. BOM membuat key di baris pertama tidak terbaca `python-dotenv`.

Catatan ngrok: URL berganti setiap restart, jadi `setWebhook` perlu diulang tiap sesi. Ambil URL dari `http://127.0.0.1:4040/api/tunnels`, bukan dari halaman dashboard ngrok — mendaftarkan `app.ngrok.ai` membuat bot diam total tanpa log.

---

## Keputusan yang Sudah Mengikat

Jangan usulkan membatalkan ini tanpa informasi baru yang benar-benar mengubah perhitungan:

- **`profiles.id` terikat ke `auth.users.id`** (Opsi A), bukan UUID mandiri. Dipilih sadar agar dashboard Fase 3 tidak butuh alur "tautkan akun" untuk data yang sudah tersebar di `notes`, `time_logs`, dan `chat_histories`.
- **Webhook membalas 200 sebelum memproses agent.**
- **Migrasi database manual dan bernomor**, bukan Alembic.
- **`user_id` ditentukan server**, tidak pernah dari output LLM.
- **`/connect` menolak, bukan upsert**, kalau profil sudah ada.
- **`GOOGLE_API_KEY`**, bukan `GEMINI_API_KEY`.

---

## Status & Prioritas

**Sudah jalan:** pipeline Telegram → ngrok → FastAPI → ADK/Gemini → Supabase, end-to-end. Seluruh agent tool terverifikasi. Onboarding penuh lewat Telegram — `/invite` membuat user Supabase Auth beserta invite code, `/connect` menautkan chat ke profil.

**Belum diuji:** `/connect` dengan kode valid dari akun yang belum punya profil (butuh akun Telegram kedua).

**Prioritas berikutnya, berurutan:**

1. Migrasi dependensi ke `uv` (sebelum menambah aplikasi Vue, supaya sisi Python sudah rapi)
2. Dashboard Vue 3 (Fase 3)
3. Kebijakan RLS, dikerjakan bareng dashboard karena konsumennya di sana
4. Deploy backend ke Railway/Render, lepas dari ngrok


| Menjalankan ngrok tanpa memastikan portnya | `ngrok http 8080` menghasilkan 502 dalam ~2ms di inspector, terlihat seperti server mati | Verifikasi `"addr"` di `127.0.0.1:4040/api/tunnels` cocok dengan port uvicorn |
