create table if not exists public.invite_codes (
    code             text primary key,
    auth_user_id     uuid not null,
    full_name        text,
    used_at          timestamptz,
    used_by_chat_id  bigint,
    expires_at       timestamptz not null,
    created_at       timestamptz not null default now()
);

create index if not exists idx_invite_codes_unused
    on public.invite_codes (code)
    where used_at is null;

alter table public.invite_codes enable row level security;