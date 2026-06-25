# Vector Memory Plan (Optional)

Chromagora OS uses pgvector as an **optional** similarity search layer. Canonical business truth always remains in relational Supabase tables.

## Feature Flag

```
ENABLE_VECTOR_MEMORY=false  # default: off
```

When off, embedding tables are unused. The app starts without pgvector installed.

## Schema

### memory_artifacts
Stores source content that can be embedded:
- id, business_id, artifact_type, title, text_content, source_ref, created_at, updated_at

### memory_embeddings
Stores vector embeddings:
- id, artifact_fk, embedding_model, embedding vector(1536), created_at

## Usage

Vector memory is for:
- Similarity search across customer conversations
- Caching frequently retrieved evidence
- Finding related opportunities by description similarity

Vector memory is NOT for:
- Canonical Business Twin state
- Authority envelopes
- Policy rules
- Audit records

## Migration

DDL in `000021_create_memory.sql`. Only runs when ENABLE_VECTOR_MEMORY=true.

## Why Optional

- Not all deployments need vector search
- Embedding inference costs tokens
- Canonical data must remain structured and queryable
- pgvector requires PostgreSQL extension installation
