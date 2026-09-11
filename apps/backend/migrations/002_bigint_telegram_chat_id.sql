-- 002_bigint_telegram_chat_id.sql
-- Chat ID Telegram bisa lebih dari 2.147.483.647 (batas kolom integer).
-- Jalankan sekali di Supabase SQL Editor. Aman dijalankan ulang.
alter table public.profiles
  alter column telegram_chat_id type bigint;
