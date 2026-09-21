-- 009_timer_break_reminder.sql
-- Menambahkan kolom break_reminder_sent ke tabel time_logs.
-- Aman dijalankan ulang (idempotent).

alter table public.time_logs
    add column if not exists break_reminder_sent boolean not null default false;

create index if not exists idx_time_logs_break_reminder
    on public.time_logs (ended_at, break_reminder_sent);

