-- 019_pgvector_and_semantic_embeddings.sql
-- Migrasi PostgreSQL untuk Semantic Search & RAG Knowledge Hub:
-- 1. Mengaktifkan ekstensi vector (pgvector)
-- 2. Membuat tabel note_embeddings untuk menyimpan vektor embeddings (Gemini text-embedding-004 / 768 dimensi)
-- 3. Membuat indeks HNSW (Hierarchical Navigable Small World) untuk pencarian cosine distance berkecepatan tinggi
-- 4. Mengaktifkan Row Level Security (RLS) untuk isolasi multi-tenant

-- 1. Aktifkan ekstensi vector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabel Note Embeddings
CREATE TABLE IF NOT EXISTS note_embeddings (
    id SERIAL PRIMARY KEY,
    note_id INT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    content_chunk TEXT NOT NULL,
    embedding vector(768), -- Dimensi representasi vektor Google Gemini text-embedding-004
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-004',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indeks relasional
CREATE INDEX IF NOT EXISTS idx_note_embeddings_user_id ON note_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_note_embeddings_note_id ON note_embeddings(note_id);

-- 3. Indeks HNSW (Hierarchical Navigable Small World) untuk Cosine Similarity
-- Memungkinkan pencarian semantik sub-milidetik pada skala ribuan hingga jutaan catatan
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_note_embeddings_hnsw_cosine ON note_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);';
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Fallback jika hardware/versi PostgreSQL belum mendukung spesifikasi HNSW tertentu
    RAISE NOTICE 'Gagal membuat HNSW index khusus, melanjutkan dengan fallback.';
END $$;

-- 4. Aktifkan Row-Level Security (RLS)
ALTER TABLE note_embeddings ENABLE ROW LEVEL SECURITY;

-- 5. Kebijakan RLS (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'note_embeddings_user_isolation') THEN
        CREATE POLICY note_embeddings_user_isolation ON note_embeddings
            FOR ALL USING (user_id = auth.uid())
            WITH CHECK (user_id = auth.uid());
    END IF;
END $$;

