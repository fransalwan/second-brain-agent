-- 008_habits.sql
-- Menambahkan tabel habits dan habit_logs beserta kebijakan RLS.
-- Aman dijalankan ulang (idempotent).

-- ---------------------------------------------------------------------------
-- 1. TABEL HABITS
-- ---------------------------------------------------------------------------
create table if not exists public.habits (
    id serial primary key,
    user_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    is_active boolean not null default true,
    position int not null default 1,
    created_at timestamptz not null default now(),
    constraint habits_user_name_unique unique (user_id, name)
);

create index if not exists idx_habits_user_position
    on public.habits (user_id, position asc);

create index if not exists idx_habits_user_active
    on public.habits (user_id, is_active);

-- ---------------------------------------------------------------------------
-- 2. TABEL HABIT_LOGS
-- ---------------------------------------------------------------------------
create table if not exists public.habit_logs (
    id serial primary key,
    habit_id int not null references public.habits(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    completed_date date not null,  -- Aturan 1: date murni untuk tanggal lokal
    created_at timestamptz not null default now(),
    constraint habit_logs_habit_date_unique unique (habit_id, completed_date)
);

create index if not exists idx_habit_logs_user_date
    on public.habit_logs (user_id, completed_date desc);

create index if not exists idx_habit_logs_habit_date
    on public.habit_logs (habit_id, completed_date desc);

-- ---------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (Aturan 8: SELECT-only untuk role authenticated)
-- ---------------------------------------------------------------------------
alter table public.habits enable row level security;
alter table public.habit_logs enable row level security;

drop policy if exists "Users can view own habits" on public.habits;
create policy "Users can view own habits"
    on public.habits
    for select
    to authenticated
    using (auth.uid() = user_id);

drop policy if exists "Users can view own habit logs" on public.habit_logs;
create policy "Users can view own habit logs"
    on public.habit_logs
    for select
    to authenticated
    using (auth.uid() = user_id);

