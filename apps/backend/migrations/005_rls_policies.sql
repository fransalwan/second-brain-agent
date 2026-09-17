-- 005_rls_policies.sql
-- Mengaktifkan Row Level Security (RLS) dan kebijakan akses SELECT untuk Fase 3 (Dashboard).
--
-- Konteks:
-- Dashboard web mengakses data langsung ke Supabase menggunakan anon key + JWT user.
-- RLS memastikan setiap user hanya bisa membaca datanya sendiri (auth.uid() = id / user_id).
--
-- Catatan:
-- 1. Versi pertama ini murni READ-ONLY (hanya SELECT policy). INSERT, UPDATE, dan DELETE
--    secara default ditolak untuk client web (authenticated role).
-- 2. Backend bot Telegram terhubung sebagai role postgres (superuser DB), sehingga
--    kebijakan RLS ini di-bypass sepenuhnya dan tidak memengaruhi operasi bot.
-- 3. Tabel invite_codes sudah di-enable RLS pada migrasi 004 tanpa policy.
--    Tabel donations di-enable RLS di sini tanpa policy agar terlindung dari akses anon key.
--
-- Aman dijalankan ulang (idempotent).

-- ---------------------------------------------------------------------------
-- 1. PROFILES
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;

drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
    on public.profiles
    for select
    to authenticated
    using (auth.uid() = id);

-- ---------------------------------------------------------------------------
-- 2. NOTES
-- ---------------------------------------------------------------------------
alter table public.notes enable row level security;

drop policy if exists "Users can view own notes" on public.notes;
create policy "Users can view own notes"
    on public.notes
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 3. TIME LOGS
-- ---------------------------------------------------------------------------
alter table public.time_logs enable row level security;

drop policy if exists "Users can view own time logs" on public.time_logs;
create policy "Users can view own time logs"
    on public.time_logs
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 4. CHAT HISTORIES
-- ---------------------------------------------------------------------------
alter table public.chat_histories enable row level security;

drop policy if exists "Users can view own chat histories" on public.chat_histories;
create policy "Users can view own chat histories"
    on public.chat_histories
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 5. DONATIONS
-- ---------------------------------------------------------------------------
-- Belum dipakai di Fase 3, tetapi RLS wajib aktif agar tidak terbuka dari
-- anon key. Dibiarkan tanpa policy sehingga ditolak untuk seluruh client publik.
alter table public.donations enable row level security;
