-- 011_weekly_report.sql
-- Menambahkan kolom last_weekly_report_date ke tabel profiles.
-- Aman dijalankan ulang (idempotent).

alter table public.profiles
    add column if not exists last_weekly_report_date date;

create index if not exists idx_profiles_weekly_schedule
    on public.profiles (last_weekly_report_date);

