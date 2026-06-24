# Migrations — Supabase DDL

Database migrations as numbered SQL files.

## Convention
- Files numbered: `NNNNNN_descriptive_name.sql`
- Each migration is idempotent (`IF NOT EXISTS`)
- No Alembic, no SQLAlchemy migrations
- Applied via Supabase CLI or `scripts/apply_migrations.py`

## Format
```sql
-- Migration: 000001_create_extensions
-- Created: YYYY-MM-DD
-- Description: What this migration does

CREATE EXTENSION IF NOT EXISTS ...
```
