# Chromagora OS — Database Documentation

## Overview

All data is stored in Supabase PostgreSQL. No SQLite, no local Postgres.

## Tables

### tenants
Top-level organizational unit. Each tenant is isolated via RLS.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | gen_random_uuid() |
| name | text | Display name |
| slug | text UNIQUE | URL-safe identifier |
| status | text | active, suspended, archived |
| created_at | timestamptz | |
| updated_at | timestamptz | Auto-updated via trigger |

### user_tenants
Junction between Supabase Auth users and tenants.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid | References auth.users |
| tenant_id | uuid FK | References tenants |
| role | text | owner, admin, operator, viewer |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## Row Level Security

All tenant-scoped tables use RLS with tenant isolation:
```sql
USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
```

The tenant context is set at the start of each request via a database function.

## Migrations

Numbered SQL files in `/migrations/`. Applied via:
- Supabase CLI: `supabase migration up`
- Python script: `python scripts/apply_migrations.py`

## Conventions

- UUID primary keys (never serial/auto-increment)
- tenant_id on all tenant-scoped tables
- timestamptz for all timestamps
- jsonb for flexible payloads
- CHECK constraints for enums
- Indexes on all foreign keys and status columns
- Triggers for updated_at
