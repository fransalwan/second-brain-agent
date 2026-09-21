-- 010_night_cutoff.sql
-- Menambahkan batas jam kerja malam pada tabel profiles dan flag pengingat malam pada time_logs.
-- Aman dijalankan ulang (idempotent).

alter table public.profiles
    add column if not exists night_cutoff_time time not null default '23:00:00';

alter table public.time_logs
    add column if not exists night_warning_sent boolean not null default false;

create index if not exists idx_time_logs_night_warning
    on public.time_logs (ended_at, night_warning_sent);

