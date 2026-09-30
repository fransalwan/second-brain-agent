-- 018_verdion_leverage_engine.sql
-- Migrasi tabel untuk Verdion Leverage Engine:
-- 1. Penyesuaian Career Goals & Upwork Proposals untuk Brand Verdion & Whale Vetting
-- 2. Milestones & Escrow Sentinel
-- 3. Scope Creep & Change Request (CR) Addons
-- 4. Labor Arbitrage & Subcontractor Payouts (IDR)
-- 5. Monthly Retainer & Recurring Cashflow Engine

-- 1. Tambah kolom pada career_goals jika belum ada
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS company_name VARCHAR(100) NOT NULL DEFAULT 'Verdion';
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS min_project_budget_usd NUMERIC(10, 2) NOT NULL DEFAULT 800.00;
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS monthly_profit_target_idr NUMERIC(14, 2) NOT NULL DEFAULT 50000000.00;

-- 2. Tambah kolom pada upwork_proposals untuk Whale Vetting & Hook Engine
ALTER TABLE upwork_proposals ADD COLUMN IF NOT EXISTS client_spend_usd NUMERIC(12, 2) DEFAULT 0.00;
ALTER TABLE upwork_proposals ADD COLUMN IF NOT EXISTS client_hire_rate INT DEFAULT 0;
ALTER TABLE upwork_proposals ADD COLUMN IF NOT EXISTS client_rating NUMERIC(3, 2) DEFAULT 5.00;
ALTER TABLE upwork_proposals ADD COLUMN IF NOT EXISTS hook_text TEXT;
ALTER TABLE upwork_proposals ADD COLUMN IF NOT EXISTS proposal_score INT DEFAULT 0;

-- 3. Tabel Milestones untuk Kontrak Fixed-Price
CREATE TABLE IF NOT EXISTS upwork_milestones (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES upwork_contracts(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    amount_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    escrow_funded BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, in_progress, submitted, paid
    submitted_at TIMESTAMPTZ,
    auto_release_deadline TIMESTAMPTZ,
    deliverables_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upwork_milestones_contract_id ON upwork_milestones(contract_id);
CREATE INDEX IF NOT EXISTS idx_upwork_milestones_status ON upwork_milestones(status);

-- 4. Tabel Change Requests (CR) / Scope Creep Monetizer
CREATE TABLE IF NOT EXISTS verdion_change_requests (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES upwork_contracts(id) ON DELETE CASCADE,
    request_title VARCHAR(255) NOT NULL,
    estimated_hours NUMERIC(6, 2) DEFAULT 0.0,
    additional_price_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'quoted', -- quoted, accepted, declined
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verdion_cr_contract_id ON verdion_change_requests(contract_id);

-- 5. Tabel Subcontractor Logs (Labor Arbitrage)
CREATE TABLE IF NOT EXISTS verdion_subcontractor_logs (
    id SERIAL PRIMARY KEY,
    contract_id INT NOT NULL REFERENCES upwork_contracts(id) ON DELETE CASCADE,
    subdev_name VARCHAR(100) NOT NULL,
    task_scope VARCHAR(255) NOT NULL,
    payout_idr NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, completed, paid
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verdion_subdev_contract_id ON verdion_subcontractor_logs(contract_id);

-- 6. Tabel Retainer Bulanan (Recurring LTV)
CREATE TABLE IF NOT EXISTS verdion_retainers (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    client_name VARCHAR(255) NOT NULL,
    monthly_rate_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    billing_day INT NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, paused, cancelled
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verdion_retainers_user_id ON verdion_retainers(user_id);
CREATE INDEX IF NOT EXISTS idx_verdion_retainers_status ON verdion_retainers(status);

-- 7. Aktifkan Row Level Security (RLS)
ALTER TABLE upwork_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE verdion_change_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE verdion_subcontractor_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE verdion_retainers ENABLE ROW LEVEL SECURITY;

-- 8. Kebijakan RLS (Idempotent)
DO $$
BEGIN
    -- Milestones RLS (Join dengan upwork_contracts untuk mengecek auth.uid())
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'upwork_milestones_user_isolation') THEN
        CREATE POLICY upwork_milestones_user_isolation ON upwork_milestones
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM upwork_contracts c 
                    WHERE c.id = upwork_milestones.contract_id 
                    AND c.user_id = auth.uid()
                )
            );
    END IF;

    -- Change Requests RLS
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'verdion_cr_user_isolation') THEN
        CREATE POLICY verdion_cr_user_isolation ON verdion_change_requests
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM upwork_contracts c 
                    WHERE c.id = verdion_change_requests.contract_id 
                    AND c.user_id = auth.uid()
                )
            );
    END IF;

    -- Subcontractor Logs RLS
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'verdion_subdev_user_isolation') THEN
        CREATE POLICY verdion_subdev_user_isolation ON verdion_subcontractor_logs
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM upwork_contracts c 
                    WHERE c.id = verdion_subcontractor_logs.contract_id 
                    AND c.user_id = auth.uid()
                )
            );
    END IF;

    -- Retainers RLS
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'verdion_retainers_user_isolation') THEN
        CREATE POLICY verdion_retainers_user_isolation ON verdion_retainers
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;
