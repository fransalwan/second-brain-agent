-- 015_coursework_and_exams.sql
-- Migrasi tabel untuk Modul Tugas Kuliah, Persiapan Ujian (UTS/UAS), dan Final Project

CREATE TABLE IF NOT EXISTS course_assignments (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    assignment_type VARCHAR(50) NOT NULL DEFAULT 'Individu',
    deadline TIMESTAMPTZ,
    weight_percent INT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_course_assignments_user_id ON course_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_course_assignments_course_name ON course_assignments(course_name);
CREATE INDEX IF NOT EXISTS idx_course_assignments_status ON course_assignments(status);

CREATE TABLE IF NOT EXISTS course_exams (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    exam_type VARCHAR(50) NOT NULL DEFAULT 'UTS',
    exam_date TIMESTAMPTZ NOT NULL,
    room_or_link VARCHAR(255),
    rules VARCHAR(100) DEFAULT 'Closed Book',
    topics JSONB,
    target_score INT DEFAULT 85,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_course_exams_user_id ON course_exams(user_id);
CREATE INDEX IF NOT EXISTS idx_course_exams_course_name ON course_exams(course_name);

CREATE TABLE IF NOT EXISTS course_projects (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    deadline TIMESTAMPTZ,
    milestones JSONB,
    deliverables JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_course_projects_user_id ON course_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_course_projects_course_name ON course_projects(course_name);

-- Aktifkan Row Level Security (RLS)
ALTER TABLE course_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_projects ENABLE ROW LEVEL SECURITY;

-- Kebijakan RLS (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'course_assignments_user_isolation') THEN
        CREATE POLICY course_assignments_user_isolation ON course_assignments
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'course_exams_user_isolation') THEN
        CREATE POLICY course_exams_user_isolation ON course_exams
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'course_projects_user_isolation') THEN
        CREATE POLICY course_projects_user_isolation ON course_projects
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;
