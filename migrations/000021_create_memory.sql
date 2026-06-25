-- Migration: 000021_create_memory
-- Created: 2026-06-24
-- Description: Memory artifacts table + optional pgvector embeddings
-- Chapter 20.3 — pgvector optional memory layer

-- Memory artifacts: store source content for embedding
CREATE TABLE IF NOT EXISTS memory_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES client_businesses(id),
    artifact_type text NOT NULL DEFAULT 'note',
    title text NOT NULL DEFAULT '',
    text_content text NOT NULL DEFAULT '',
    source_ref text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memory_artifacts_business ON memory_artifacts(business_id);
CREATE INDEX IF NOT EXISTS idx_memory_artifacts_type ON memory_artifacts(artifact_type);
ALTER TABLE memory_artifacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_memory_artifacts ON memory_artifacts
    USING (
        business_id IN (
            SELECT id FROM client_businesses
            WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
        )
    );

-- Memory embeddings: only created when ENABLE_VECTOR_MEMORY=true
-- Requires: CREATE EXTENSION IF NOT EXISTS vector;
-- Uncomment when pgvector is available:
--
-- CREATE TABLE IF NOT EXISTS memory_embeddings (
--     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     artifact_fk uuid NOT NULL REFERENCES memory_artifacts(id) ON DELETE CASCADE,
--     embedding_model text NOT NULL DEFAULT 'text-embedding-3-small',
--     embedding_vector vector(1536) NOT NULL,
--     created_at timestamptz NOT NULL DEFAULT now()
-- );
--
-- CREATE INDEX IF NOT EXISTS idx_memory_embeddings_artifact ON memory_embeddings(artifact_fk);
-- CREATE INDEX IF NOT EXISTS idx_memory_embeddings_model ON memory_embeddings(embedding_model);
-- -- IVFFlat index for similarity search (requires data to be present)
-- -- CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector ON memory_embeddings
-- --     USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
