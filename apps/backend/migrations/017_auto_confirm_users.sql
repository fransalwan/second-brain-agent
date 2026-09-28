-- Migration 017: Auto confirm users on signup for zero-friction student onboarding
-- Allows students from university emails (ugm.ac.id, ui.ac.id, etc.) and personal emails
-- to immediately access their dashboard without waiting for external SMTP relays.

UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;

CREATE OR REPLACE FUNCTION public.handle_auto_confirm_user()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.email_confirmed_at IS NULL THEN
    NEW.email_confirmed_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created_auto_confirm ON auth.users;
CREATE TRIGGER on_auth_user_created_auto_confirm
  BEFORE INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_auto_confirm_user();
