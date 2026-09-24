-- 014_health_module.sql
-- Migrasi tabel untuk Modul Kesehatan (Sleep Tracker, Hydration Tracker, Health Check & Burnout)

CREATE TABLE IF NOT EXISTS sleep_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hours NUMERIC(4, 1) NOT NULL,
    quality VARCHAR(50) NOT NULL DEFAULT 'Cukup',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sleep_logs_user_id ON sleep_logs(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sleep_logs_user_date ON sleep_logs(user_id, date);

CREATE TABLE IF NOT EXISTS hydration_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    glasses INT NOT NULL DEFAULT 1,
    target_glasses INT NOT NULL DEFAULT 8,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hydration_logs_user_id ON hydration_logs(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_hydration_logs_user_date ON hydration_logs(user_id, date);

CREATE TABLE IF NOT EXISTS health_check_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    took_vitamin BOOLEAN NOT NULL DEFAULT FALSE,
    did_stretch BOOLEAN NOT NULL DEFAULT FALSE,
    burnout_score INT NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_check_logs_user_id ON health_check_logs(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_health_check_logs_user_date ON health_check_logs(user_id, date);

-- Aktifkan Row Level Security (RLS)
ALTER TABLE sleep_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hydration_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_check_logs ENABLE ROW LEVEL SECURITY;

-- Kebijakan RLS (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'sleep_logs_user_isolation') THEN
        CREATE POLICY sleep_logs_user_isolation ON sleep_logs
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'hydration_logs_user_isolation') THEN
        CREATE POLICY hydration_logs_user_isolation ON hydration_logs
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'health_check_logs_user_isolation') THEN
        CREATE POLICY health_check_logs_user_isolation ON health_check_logs
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;
