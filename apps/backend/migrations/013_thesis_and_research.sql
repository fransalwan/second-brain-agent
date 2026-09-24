-- 013_thesis_and_research.sql
-- Migrasi tabel untuk Modul Kuliah dan Riset (Thesis, Bimbingan Dospem, Metrik Eksperimen)

CREATE TABLE IF NOT EXISTS thesis_chapters (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    chapter_num INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Belum Mulai',
    progress INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_thesis_chapters_user_id ON thesis_chapters(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_thesis_chapters_user_num ON thesis_chapters(user_id, chapter_num);

CREATE TABLE IF NOT EXISTS supervision_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    notes TEXT NOT NULL,
    action_items TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supervision_logs_user_id ON supervision_logs(user_id);

CREATE TABLE IF NOT EXISTS experiment_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    metrics_summary TEXT NOT NULL,
    parameters TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experiment_metrics_user_id ON experiment_metrics(user_id);

-- Aktifkan Row Level Security (RLS)
ALTER TABLE thesis_chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervision_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_metrics ENABLE ROW LEVEL SECURITY;

-- Kebijakan RLS (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'thesis_chapters_user_isolation') THEN
        CREATE POLICY thesis_chapters_user_isolation ON thesis_chapters
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'supervision_logs_user_isolation') THEN
        CREATE POLICY supervision_logs_user_isolation ON supervision_logs
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'experiment_metrics_user_isolation') THEN
        CREATE POLICY experiment_metrics_user_isolation ON experiment_metrics
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

