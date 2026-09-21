-- =============================================================================
-- Migrasi 012: Izinkan Pengguna Authenticated Mengelola Profil & Tambah Kolom Email
-- =============================================================================

-- 1. Tambah kolom email di tabel profiles jika belum ada
alter table public.profiles
    add column if not exists email text;

create index if not exists idx_profiles_lower_email
    on public.profiles (lower(email));

-- 2. Kebijakan RLS agar pengguna authenticated dapat membuat dan mengedit profil sendiri
drop policy if exists "Users can insert own profile" on public.profiles;
create policy "Users can insert own profile"
    on public.profiles for insert to authenticated
    with check (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
    on public.profiles for update to authenticated
    using (auth.uid() = id);

