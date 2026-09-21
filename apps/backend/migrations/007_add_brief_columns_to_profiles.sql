-- 007_add_brief_columns_to_profiles.sql
-- Menambahkan kolom brief_time dan last_brief_date ke tabel profiles.
-- Aman dijalankan ulang (idempotent).

alter table public.profiles
    add column if not exists brief_time time not null default '07:00:00',
    add column if not exists last_brief_date date;

create index if not exists idx_profiles_brief_schedule
    on public.profiles (brief_time, last_brief_date);

