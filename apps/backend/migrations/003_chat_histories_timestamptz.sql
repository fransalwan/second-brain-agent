-- 003_chat_histories_timestamptz.sql
-- Memastikan chat_histories.created_at bertipe timestamptz.
--
-- Konteks: field created_at di model ChatHistory sempat tidak memakai
-- sa_type=DateTime(timezone=True), sehingga SQLModel memetakannya ke
-- TIMESTAMP WITHOUT TIME ZONE. Asyncpg menolak menyimpan objek datetime
-- timezone-aware ke kolom tersebut dan seluruh insert gagal.
--
-- Aman dijalankan ulang.

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name   = 'chat_histories'
          and column_name  = 'created_at'
          and data_type    = 'timestamp without time zone'
    ) then
        alter table public.chat_histories
            alter column created_at type timestamptz
            using created_at at time zone 'UTC';
    end if;
end $$;

alter table public.chat_histories
    alter column created_at set default now();