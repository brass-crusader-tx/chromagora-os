# Supabase as Primary Database

Chromagora OS uses Supabase as its **sole datastore**. There is no SQLite fallback, no local Postgres, and no migration path from another database.

## Why Supabase

- **PostgreSQL** — full SQL support, JSONB, arrays, PostGIS (if needed)
- **Row Level Security** — tenant isolation enforced at the database level
- **Realtime** — event streaming for Command Feed, agent events, approval notifications
- **Auth** — Supabase Auth handles all user identity
- **Storage** — file artifacts (photos, documents) in Supabase Storage buckets
- **Edge Functions** — Deno-based lightweight triggers (not primary compute)

## No Other Database

- No SQLite
- No local PostgreSQL
- No Docker requirement for any database
- No database-agnostic SQL that hides PostgreSQL-specific features
- All migrations are hand-written DDL or Supabase Migration UI

## Connection

Local dev connects to a Supabase project URL via `.env`. The Supabase CLI manages migrations.

```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=***
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

- `service_role_key` bypasses RLS for server-side operations (workers, migrations)
- `anon_key` used in web frontend with RLS enforced

## Tenant Isolation

All tenant-scoped tables:
1. Have a `tenant_id` column
2. Have RLS enabled
3. Have a tenant isolation policy: `USING (tenant_id = current_setting('app.current_tenant', true)::uuid)`

## Migration Approach

- Hand-written DDL files in `/migrations/`
- Applied via `scripts/apply_migrations.py` using SERVICE_ROLE_KEY
- No Alembic, no SQLAlchemy-core for migrations
- Migration files are prefixed with a sequence number
