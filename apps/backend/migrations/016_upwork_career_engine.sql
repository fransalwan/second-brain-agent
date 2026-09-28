-- 016_upwork_career_engine.sql
-- Migrasi tabel untuk Upwork Career Engine: Target Pendapatan, Pipeline Proposal, & Kontrak Kerja

CREATE TABLE IF NOT EXISTS career_goals (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    month VARCHAR(10) NOT NULL, -- Format YYYY-MM
    target_revenue_usd NUMERIC(10, 2) NOT NULL DEFAULT 1000.00,
    target_proposals_count INT NOT NULL DEFAULT 20,
    current_badge VARCHAR(50) NOT NULL DEFAULT 'Rising Talent',
    usd_to_idr_rate NUMERIC(10, 2) NOT NULL DEFAULT 16200.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_career_goals_user_id ON career_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_career_goals_month ON career_goals(month);

CREATE TABLE IF NOT EXISTS upwork_proposals (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    job_title VARCHAR(255) NOT NULL,
    bid_amount_usd NUMERIC(10, 2),
    connects_spent INT NOT NULL DEFAULT 8,
    client_country VARCHAR(100),
    job_url TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'submitted',
    notes TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upwork_proposals_user_id ON upwork_proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_upwork_proposals_status ON upwork_proposals(status);
CREATE INDEX IF NOT EXISTS idx_upwork_proposals_submitted_at ON upwork_proposals(submitted_at);

CREATE TABLE IF NOT EXISTS upwork_contracts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    proposal_id INT REFERENCES upwork_proposals(id) ON DELETE SET NULL,
    client_name VARCHAR(255) NOT NULL,
    project_title VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50) NOT NULL DEFAULT 'fixed',
    rate_or_budget_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_earned_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    rating NUMERIC(3, 2),
    feedback TEXT,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upwork_contracts_user_id ON upwork_contracts(user_id);
CREATE INDEX IF NOT EXISTS idx_upwork_contracts_status ON upwork_contracts(status);

-- Aktifkan Row Level Security (RLS)
ALTER TABLE career_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE upwork_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE upwork_contracts ENABLE ROW LEVEL SECURITY;

-- Kebijakan RLS (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'career_goals_user_isolation') THEN
        CREATE POLICY career_goals_user_isolation ON career_goals
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'upwork_proposals_user_isolation') THEN
        CREATE POLICY upwork_proposals_user_isolation ON upwork_proposals
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'upwork_contracts_user_isolation') THEN
        CREATE POLICY upwork_contracts_user_isolation ON upwork_contracts
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;
