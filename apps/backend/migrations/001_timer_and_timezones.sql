-- 001_timer_and_timezones.sql
-- Jalankan sekali di Supabase SQL Editor. Aman dijalankan ulang.

-- 1) Samakan semua kolom waktu jadi timestamptz.
--    Kolom yang masih "timestamp without time zone" dianggap berisi waktu UTC
--    (sesuai datetime.utcnow() yang dipakai sebelumnya).
do $$
declare r record;
begin
  for r in
    select table_name, column_name
    from information_schema.columns
    where table_schema = 'public'
      and table_name in ('profiles', 'notes', 'time_logs', 'donations')
      and data_type = 'timestamp without time zone'
  loop
    execute format(
      'alter table public.%I alter column %I type timestamptz using %I at time zone ''UTC''',
      r.table_name, r.column_name, r.column_name
    );
  end loop;
end $$;

-- 2) Timer: tambah ended_at, durasi boleh kosong selama timer jalan
alter table public.time_logs add column if not exists ended_at timestamptz;
alter table public.time_logs alter column duration_minutes drop not null;

-- 3) Data lama yang sudah punya durasi dianggap sudah selesai
update public.time_logs
set ended_at = started_at + make_interval(mins => duration_minutes)
where ended_at is null and duration_minutes is not null;

-- 4) Maksimal satu timer aktif per user (dijaga di level database)
create unique index if not exists time_logs_one_running_per_user
  on public.time_logs (user_id)
  where ended_at is null;

-- 5) Index untuk query per user
create index if not exists notes_user_created_idx on public.notes (user_id, created_at desc);
create index if not exists time_logs_user_started_idx on public.time_logs (user_id, started_at desc);