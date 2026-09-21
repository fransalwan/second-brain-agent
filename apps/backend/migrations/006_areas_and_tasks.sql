-- 006_areas_and_tasks.sql
-- Menambahkan tabel areas dan tasks beserta kebijakan RLS.
-- Aman dijalankan ulang (idempotent).

-- ---------------------------------------------------------------------------
-- 1. TABEL AREAS
-- ---------------------------------------------------------------------------
create table if not exists public.areas (
    id serial primary key,
    user_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    position int not null,
    created_at timestamptz not null default now(),
    constraint areas_user_name_unique unique (user_id, name)
);

create index if not exists idx_areas_user_position
    on public.areas (user_id, position asc);

-- ---------------------------------------------------------------------------
-- 2. TABEL TASKS
-- ---------------------------------------------------------------------------
create table if not exists public.tasks (
    id serial primary key,
    user_id uuid not null references public.profiles(id) on delete cascade,
    area_id int references public.areas(id) on delete set null,
    title text not null,
    deadline date,  -- Aturan 1: date murni untuk tanggal, bukan timestamptz
    is_urgent boolean not null default false,  -- Penanda pekerjaan mendesak untuk fungsi prioritas
    status text not null default 'pending' check (status in ('pending', 'completed')),
    completed_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_tasks_user_status_deadline
    on public.tasks (user_id, status, deadline asc nulls last);

create index if not exists idx_tasks_user_area
    on public.tasks (user_id, area_id);

create index if not exists idx_tasks_user_urgent
    on public.tasks (user_id, is_urgent)
    where status = 'pending';

-- ---------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (Aturan 8: SELECT-only untuk role authenticated)
-- ---------------------------------------------------------------------------
alter table public.areas enable row level security;
alter table public.tasks enable row level security;

-- Policy untuk tabel areas
drop policy if exists "Users can view own areas" on public.areas;
create policy "Users can view own areas"
    on public.areas
    for select
    to authenticated
    using (auth.uid() = user_id);

-- Policy untuk tabel tasks
drop policy if exists "Users can view own tasks" on public.tasks;
create policy "Users can view own tasks"
    on public.tasks
    for select
    to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 4. KONSISTENSI STATUS
-- ---------------------------------------------------------------------------
alter table public.tasks
    drop constraint if exists tasks_completed_consistent;

alter table public.tasks
    add constraint tasks_completed_consistent
    check ((status = 'completed') = (completed_at is not null));

