-- 005_rls_policies.sql
-- Membersihkan policy manual lama dan menerapkan kebijakan RLS baru (SELECT-only untuk role authenticated).
--
-- Konteks:
-- Sebelumnya ada policy manual yang dibuat dari Supabase Dashboard dengan cakupan CRUD (ALL)
-- dan target role {public}. Migrasi ini menghapus seluruh policy lama tersebut dan menggantinya
-- dengan policy read-only (SELECT) khusus untuk role authenticated (Fase 3 Dashboard).
--
-- Catatan:
-- 1. Versi ini murni READ-ONLY untuk client web. Seluruh operasi INSERT, UPDATE, dan DELETE
--    secara default ditolak untuk client web (authenticated).
-- 2. Policy lama "Backend full access" pada chat_histories dihapus karena redundan:
--    backend FastAPI connect sebagai role postgres yang memiliki hak BYPASSRLS secara native di PostgreSQL.
-- 3. Tabel donations dan invite_codes diaktifkan RLS tanpa policy (tertutup penuh dari client web).
--
-- Aman dijalankan ulang (idempotent).

-- ---------------------------------------------------------------------------
-- 1. PROFILES
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;

-- Hapus policy lama (manual & draft sebelumnya)
drop policy if exists "Users can update own profile" on public.profiles;
drop policy if exists "Users can view own profile" on public.profiles;

-- Pasang policy baru: SELECT only untuk authenticated
create policy "Users can view own profile"
    on public.profiles
    for select
    to authenticated
    using (auth.uid() = id);

-- ---------------------------------------------------------------------------
-- 2. NOTES
-- ---------------------------------------------------------------------------
alter table public.notes enable row level security;

-- Hapus policy lama (manual & draft sebelumnya)
drop policy if exists "Users can CRUD own notes" on public.notes;
drop policy if exists "Users can view own notes" on public.notes;

-- Pasang policy baru: SELECT only untuk authenticated
create policy "Users can view own notes"
    on public.notes
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 3. TIME LOGS
-- ---------------------------------------------------------------------------
alter table public.time_logs enable row level security;

-- Hapus policy lama (manual & draft sebelumnya)
drop policy if exists "Users can CRUD own time logs" on public.time_logs;
drop policy if exists "Users can view own time logs" on public.time_logs;

-- Pasang policy baru: SELECT only untuk authenticated
create policy "Users can view own time logs"
    on public.time_logs
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 4. CHAT HISTORIES
-- ---------------------------------------------------------------------------
alter table public.chat_histories enable row level security;

-- Hapus policy lama (manual & draft sebelumnya)
-- "Backend full access" dihapus karena role postgres sudah otomatis mem-bypass RLS
drop policy if exists "Backend full access" on public.chat_histories;
drop policy if exists "Users can delete own chat history" on public.chat_histories;
drop policy if exists "Users can insert own chat history" on public.chat_histories;
drop policy if exists "Users can view own chat history" on public.chat_histories;
drop policy if exists "Users can view own chat histories" on public.chat_histories;

-- Pasang policy baru: SELECT only untuk authenticated
create policy "Users can view own chat histories"
    on public.chat_histories
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 5. DONATIONS
-- ---------------------------------------------------------------------------
alter table public.donations enable row level security;

-- Hapus policy CRUD lama
drop policy if exists "Users can CRUD own donations" on public.donations;
drop policy if exists "Users can view own donations" on public.donations;

-- Tanpa policy baru: akses ditolak untuk seluruh client web (authenticated maupun anon)
