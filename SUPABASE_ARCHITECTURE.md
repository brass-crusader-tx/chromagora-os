# Chromagora OS — Supabase Architecture

## Supabase as Primary Datastore

Supabase provides the entire backend infrastructure:
- **PostgreSQL 15+** — all domain data, with UUID, JSONB, and array types
- **Supabase Auth** — userno custom auth)
- **Realtime** — live event streaming via websocket
- **Row Level Security (RLS)** — tenant isolation at the database engine level
- **Storage** — file artifacts (photos, PDFs) in buckets
- **Edge Functions** — lightweight Deno triggers (not primary compute)

## Project Architecture

```
https://<project-ref>.supabase.co
├── auth/                    # Supabase Auth (users, sessions)
├── rest/v1/                 # Auto-generated REST API from schema
├── realtime/v1/             # WebSocket realtime channels
├── storage/v1/              # File storage
└── functions/v1/            # Edge functions (Deno)
```

## Database Schema Conventions

### Primary Keys
```sql
id uuid PRIMARY KEY DEFAULT gen_random_uuid()
```

### Tenant Isolation
Every tenant-scoped table has:
```sql
tenant_id uuid NOT NULL REFERENCES tenants(id)
```

### Timestamps
```sql
created_at timestamptz NOT NULL DEFAULT now(),
updated_at timestamptz NOT NULL DEFAULT now()
```

### JSON Data
```sql
payload jsonb NOT NULL DEFAULT '{}',
evidence jsonb NOT NULL DEFAULT '{}'
```

### Enums (Database-Level)
```sql
CREATE TYPE agent_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE action_result_status AS ENUM ('dry_run', 'success', 'failed', 'blocked', 'approval_required', 'cancelled');
CREATE TYPE autonomy_level AS ENUM ('0_observe', '1_analyze', '2_draft', '3_internal_action', '4_low_risk_external', '5_bounded_negotiation', '6_binding_execution');
```

### Indexes
```sql
-- Every foreign key is indexed
CREATE INDEX idx_business_tenant ON businesses(tenant_id);
CREATE INDEX idx_events_tenant_business ON events(tenant_id, business_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_ledger_business ON action_executions(business_id, created_at DESC);
```

## Row Level Security (RLS) Pattern

All tenant-scoped tables follow this RLS pattern:

```sql
-- Enable RLS
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation ON businesses
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

-- Service role bypass (for workers, migrations)
-- Supabase service_role key bypasses RLS automatically
```

Setting the tenant context:
```sql
-- Set at connection start
SET app.current_tenant = '<tenant-uuid>';
```

Python (supabase-py):
```python
supabase.postgrest.session.headers.update({
    "Prefer": "count=exact"
})
# RPC to set tenant context
supabase.rpc('set_tenant_context', {'tenant_id': tenant_id}).execute()
```

TypeScript (supabase-js):
```ts
// RLS automatically filters based on JWT claims
// For admin operations, use service_role key
const supabaseAdmin = createClient(url, serviceRoleKey)
```

## Realtime Event Channels

| Channel | Purpose | Subscribers |
|---------|---------|-------------|
| `tenant:{tenant_id}:events` | All tenant events | Cockpit, workers |
| `business:{business_id}:feed` | Command feed for one business | Cockpit Command Feed UI |
| `agent:{agent_id}:runs` | Agent run status updates | Cockpit Agent page |
| `approvals:{tenant_id}` | New approval requests | Cockpit Approval Inbox |

Realtime is used for:
- Live Command Feed updates
- Approval notification popups
- Agent run status changes
- NOT for primary data access (REST queries via supabase-py / supabase-js)

## Authentication Flow

### Sign Up / Sign In
1. User signs in via Supabase Auth (GitHub OAuth, email/password, or magic link)
2. JWT token returned to client
3. All API requests include `Authorization: Bearer <jwt>`

### API Authentication
1. FastAPI middleware extracts JWT from Authorization header
2. JWT validated via Supabase JWKS endpoint
3. User identity and tenant claims extracted from JWT
4. RLS enforces tenant isolation automatically

### Service Role
1. Workers and migrations use `SUPABASE_SERVICE_ROLE_KEY`
2. Service role bypasses RLS — full access
3. Never exposed to frontend

## Environment Variables

```bash
# Backend (FastAPI, workers)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_JWT_SECRET=<jwt-secret>
DATABASE_URL=postgresql://postgres:postgres@db.<project>.supabase.co:5432/postgres

# Frontend (Next.js)
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>

# Workers
OPENROUTER_API_KEY=<key>
```

## Migration Strategy

No Alembic. No SQLAlchemy for migrations.

### Approach
1. Hand-written DDL in numbered files: `/migrations/000001_*.sql`, `000002_*.sql`, etc.
2. Applied via Supabase CLI: `supabase migration up`
3. Or via Python script using service role: `apply_migrations.py`
4. Each migration is idempotent (uses `IF NOT EXISTS`)

### Template
```sql
-- Migration: 000001_create_extensions
-- Created: 2026-06-24

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Rollback
```sql
-- Rollback file: 000001_create_extensions.rollback.sql
DROP EXTENSION IF EXISTS "uuid-ossp";
DROP EXTENSION IF EXISTS pgcrypto;
```

## Edge Function Boundaries

Edge functions are used ONLY for:
- Webhook receivers (CRM callbacks, payment webhooks)
- Lightweight triggers that don't need a full worker
- Auth-related hooks (user.created, user.deleted)

Edge functions are NOT used for:
- Primary API routes (FastAPI handles these)
- Agent execution (Python workers handle these)
- Workflow orchestration (database state machine)

## Storage Buckets

| Bucket | Purpose | Access |
|--------|---------|--------|
| `photos` | Job site photos, team photos | Authenticated |
| `documents` | Procurement PDFs, contracts | Authenticated |
| `public-assets` | Public marketing assets | Public read |

## Connection Management

### Python (supabase-py)
```python
from supabase import create_client, Client

supabase: Client = create_client(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # or ANON_KEY for RLS
)
```

### TypeScript (supabase-js)
```ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```
