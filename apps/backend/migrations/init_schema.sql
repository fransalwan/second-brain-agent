-- =============================================================================
-- Second Brain Agent - Initial Schema (Supabase PostgreSQL)
-- =============================================================================
-- Skema lengkap gabungan (Migrasi 001 - 011) untuk inisialisasi 1-klik instance baru.
-- Jalankan file ini sekali di Supabase SQL Editor.
-- Aman dijalankan ulang (idempotent).
-- =============================================================================

-- Extension UUID
create extension if not exists "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. TABEL PROFILES
-- -----------------------------------------------------------------------------
create table if not exists public.profiles (
    id                      uuid primary key references auth.users(id) on delete cascade,
    full_name               text,
    telegram_chat_id        bigint unique,
    brief_time              time not null default '07:00:00',
    last_brief_date         date,
    night_cutoff_time       time not null default '23:00:00',
    last_weekly_report_date date,
    created_at              timestamptz not null default now()
);

create index if not exists idx_profiles_brief_schedule
    on public.profiles (brief_time, last_brief_date);

-- -----------------------------------------------------------------------------
-- 2. TABEL NOTES
-- -----------------------------------------------------------------------------
create table if not exists public.notes (
    id         serial primary key,
    user_id    uuid not null references public.profiles(id) on delete cascade,
    content    text not null,
    source     text not null default 'web',
    tags       jsonb,
    created_at timestamptz not null default now()
);

create index if not exists notes_user_created_idx
    on public.notes (user_id, created_at desc);

-- -----------------------------------------------------------------------------
-- 3. TABEL TIME_LOGS
-- -----------------------------------------------------------------------------
create table if not exists public.time_logs (
    id                  serial primary key,
    user_id             uuid not null references public.profiles(id) on delete cascade,
    project_name        text not null,
    started_at          timestamptz not null default now(),
    ended_at            timestamptz,
    duration_minutes    int,
    break_reminder_sent boolean not null default false,
    night_warning_sent  boolean not null default false
);

create index if not exists time_logs_user_started_idx
    on public.time_logs (user_id, started_at desc);

create unique index if not exists time_logs_one_running_per_user
    on public.time_logs (user_id)
    where ended_at is null;

create index if not exists idx_time_logs_break_reminder
    on public.time_logs (ended_at, break_reminder_sent);

create index if not exists idx_time_logs_night_warning
    on public.time_logs (ended_at, night_warning_sent);

-- -----------------------------------------------------------------------------
-- 4. TABEL CHAT_HISTORIES
-- -----------------------------------------------------------------------------
create table if not exists public.chat_histories (
    id         serial primary key,
    user_id    uuid not null references public.profiles(id) on delete cascade,
    role       text not null,
    content    text not null,
    created_at timestamptz not null default now()
);

create index if not exists chat_histories_user_created_idx
    on public.chat_histories (user_id, created_at desc);

-- -----------------------------------------------------------------------------
-- 5. TABEL DONATIONS (Opsional / Tertutup dari web client)
-- -----------------------------------------------------------------------------
create table if not exists public.donations (
    id             serial primary key,
    user_id        uuid references public.profiles(id) on delete set null,
    amount         int not null,
    message        text,
    payment_method text not null,
    created_at     timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- 6. TABEL INVITE_CODES
-- -----------------------------------------------------------------------------
create table if not exists public.invite_codes (
    code            text primary key,
    auth_user_id    uuid not null,
    full_name       text,
    used_at         timestamptz,
    used_by_chat_id bigint,
    expires_at      timestamptz not null,
    created_at      timestamptz not null default now()
);

create index if not exists idx_invite_codes_unused
    on public.invite_codes (code)
    where used_at is null;

-- -----------------------------------------------------------------------------
-- 7. TABEL AREAS (Area Hidup Pengguna)
-- -----------------------------------------------------------------------------
create table if not exists public.areas (
    id         serial primary key,
    user_id    uuid not null references public.profiles(id) on delete cascade,
    name       text not null,
    position   int not null,
    created_at timestamptz not null default now(),
    constraint areas_user_name_unique unique (user_id, name)
);

create index if not exists idx_areas_user_position
    on public.areas (user_id, position asc);

-- -----------------------------------------------------------------------------
-- 8. TABEL TASKS (Daftar Tugas & Deadline)
-- -----------------------------------------------------------------------------
create table if not exists public.tasks (
    id           serial primary key,
    user_id      uuid not null references public.profiles(id) on delete cascade,
    area_id      int references public.areas(id) on delete set null,
    title        text not null,
    deadline     date,
    is_urgent    boolean not null default false,
    status       text not null default 'pending' check (status in ('pending', 'completed')),
    completed_at timestamptz,
    created_at   timestamptz not null default now()
);

create index if not exists idx_tasks_user_status_deadline
    on public.tasks (user_id, status, deadline asc nulls last);

create index if not exists idx_tasks_user_area
    on public.tasks (user_id, area_id);

create index if not exists idx_tasks_user_urgent
    on public.tasks (user_id, is_urgent)
    where status = 'pending';

alter table public.tasks
    drop constraint if exists tasks_completed_consistent;

alter table public.tasks
    add constraint tasks_completed_consistent
    check ((status = 'completed') = (completed_at is not null));

-- -----------------------------------------------------------------------------
-- 9. TABEL HABITS & HABIT_LOGS (Kebiasaan Harian)
-- -----------------------------------------------------------------------------
create table if not exists public.habits (
    id         serial primary key,
    user_id    uuid not null references public.profiles(id) on delete cascade,
    name       text not null,
    is_active  boolean not null default true,
    position   int not null default 1,
    created_at timestamptz not null default now(),
    constraint habits_user_name_unique unique (user_id, name)
);

create index if not exists idx_habits_user_position
    on public.habits (user_id, position asc);

create index if not exists idx_habits_user_active
    on public.habits (user_id, is_active);

create table if not exists public.habit_logs (
    id             serial primary key,
    habit_id       int not null references public.habits(id) on delete cascade,
    user_id        uuid not null references public.profiles(id) on delete cascade,
    completed_date date not null,
    created_at     timestamptz not null default now(),
    constraint habit_logs_habit_date_unique unique (habit_id, completed_date)
);

create index if not exists idx_habit_logs_user_date
    on public.habit_logs (user_id, completed_date desc);

create index if not exists idx_habit_logs_habit_date
    on public.habit_logs (habit_id, completed_date desc);

-- -----------------------------------------------------------------------------
-- 10. ROW LEVEL SECURITY (RLS) POLICIES
-- -----------------------------------------------------------------------------
-- Seluruh tabel mengaktifkan RLS. Client web (authenticated) hanya memiliki izin SELECT.
-- Backend FastAPI terhubung via postgres role (BYPASSRLS native).

alter table public.profiles enable row level security;
alter table public.notes enable row level security;
alter table public.time_logs enable row level security;
alter table public.chat_histories enable row level security;
alter table public.donations enable row level security;
alter table public.invite_codes enable row level security;
alter table public.areas enable row level security;
alter table public.tasks enable row level security;
alter table public.habits enable row level security;
alter table public.habit_logs enable row level security;

-- Policy Profiles
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
    on public.profiles for select to authenticated
    using (auth.uid() = id);

-- Policy Notes
drop policy if exists "Users can view own notes" on public.notes;
create policy "Users can view own notes"
    on public.notes for select to authenticated
    using (auth.uid() = user_id);

-- Policy Time Logs
drop policy if exists "Users can view own time logs" on public.time_logs;
create policy "Users can view own time logs"
    on public.time_logs for select to authenticated
    using (auth.uid() = user_id);

-- Policy Chat Histories
drop policy if exists "Users can view own chat histories" on public.chat_histories;
create policy "Users can view own chat histories"
    on public.chat_histories for select to authenticated
    using (auth.uid() = user_id);

-- Policy Areas
drop policy if exists "Users can view own areas" on public.areas;
create policy "Users can view own areas"
    on public.areas for select to authenticated
    using (auth.uid() = user_id);

-- Policy Tasks
drop policy if exists "Users can view own tasks" on public.tasks;
create policy "Users can view own tasks"
    on public.tasks for select to authenticated
    using (auth.uid() = user_id);

-- Policy Habits
drop policy if exists "Users can view own habits" on public.habits;
create policy "Users can view own habits"
    on public.habits for select to authenticated
    using (auth.uid() = user_id);

-- Policy Habit Logs
drop policy if exists "Users can view own habit logs" on public.habit_logs;
create policy "Users can view own habit logs"
    on public.habit_logs for select to authenticated
    using (auth.uid() = user_id);

-- Catatan: Tabel 'donations' dan 'invite_codes' sengaja tidak memiliki policy publik/authenticated,
-- sehingga tertutup penuh dari akses browser (hanya backend service role / postgres yang bisa mengakses).

