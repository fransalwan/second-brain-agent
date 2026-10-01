-- 018_milestones_and_freelance.sql
-- Migrasi tabel untuk Freelance & Milestones Engine:
-- 1. Penyesuaian Career Goals & Upwork Proposals
-- 2. Milestones & Escrow Sentinel

-- 1. Tambah kolom pada career_goals jika belum ada
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS company_name VARCHAR(100) NOT NULL DEFAULT 'Student Freelancer';
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS min_project_budget_usd NUMERIC(10, 2) NOT NULL DEFAULT 800.00;
ALTER TABLE career_goals ADD COLUMN IF NOT EXISTS monthly_profit_target_idr NUMERIC(14, 2) NOT NULL DEFAULT 50000000.00;

-- 2. Tambah kolom pada upwork_proposals untuk Client Vetting & Hook
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

-- 4. Aktifkan Row Level Security (RLS)
ALTER TABLE upwork_milestones ENABLE ROW LEVEL SECURITY;

-- 5. Kebijakan RLS (Idempotent)
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
END $$;
