# Chromagora OS Base Build Blueprint Through Chapter 26 (Supabase Edition)

> CURRENT STATUS NOTE:
> This file is the base build blueprint through Chapter 26. It is not a fresh-start instruction set. Before implementing new chapters, inspect the current codebase and preserve the existing Supabase/FastAPI/Next/worker implementation.

> **This is the Supabase-adapted edition of the chapterbook.**
> All database references have been updated: SQLite is removed. Supabase (PostgreSQL + Auth + Realtime + RLS) is the only datastore.
> Original chapterbook saved as `docs/CHAPTERBOOK_ORIGINAL.md`.

## Build doctrine

Chromagora OS should be built as a multi-agent operating cell for SMBs. The system must not become:
* a chatbot with tools
* a CRM skin
* a generic automation dashboard
* a swarm of ungoverned agents
* a token-burning research toy
* a brittle prompt pile

The correct product architecture is:
```
Business Twin + Department Agents + Bounded Tactical Subagents + Workflow Engine + Policy Kernel + Tool Broker + Action Ledger + Operator Cockpit + Context Economy Layer
```

The additional runtime principle is:
```
Use the smallest sufficient context and model for the task, but never reduce context, model quality, evidence, or verification when business performance, trust, compliance, money, or external commitments are at stake.
```

This chapterbook assumes:
* local Docker is broken
* **Supabase (PostgreSQL + Auth + Realtime + Storage) is the primary and only datastore** — no SQLite, no local Postgres
* **Supabase Auth handles all identity** — no custom auth build in application code
* **Supabase Realtime powers the Command Feed and agent event streaming** — no custom WebSocket layer
* **Supabase Row Level Security (RLS) enforces tenant isolation** at the database level
* Edge functions (Deno) for lightweight backend logic; heavyweight workers are Python
* Local dev connects to a Supabase project URL via `.env`; Docker emulator optional, never required
* no Temporal at first
* no real external actions at first
* no uncontrolled LLM agents early
* dry-run execution before real execution
* mock tools before real integrations
* web cockpit before Android companion app
* Android readiness from day one
* GitHub repo as source of truth
* all code is Supabase-native; never database-agnostic SQL that hides PostGIS, JSONB, RLS, or array features

---

# Runtime token-efficiency doctrine

## What token efficiency means here

Token efficiency means the product avoids wasting model context and inference on tasks that do not need it.

Good token efficiency:
* structured state instead of dumping transcripts
* retrieval of only relevant Business Twin slices
* compact context packets per task
* model routing by task difficulty and risk
* cached summaries and evidence bundles
* deterministic code where reasoning is unnecessary
* bounded tactical subagents with strict output schemas
* event-based coordination instead of agents chatting endlessly
* memory write filtering
* progressive escalation from cheap/simple to expensive/deep only when justified

Bad token efficiency:
* using weak models for high-value reasoning
* stripping context needed for accurate decisions
* summarizing away legal/commercial constraints
* omitting evidence to save tokens
* routing everything to small models
* letting agents act with incomplete context
* compressing customer conversations so much that nuance is lost
* truncating policy or authority envelopes

## Runtime context hierarchy

Every agent run should receive context in this order:
```
1. Task instruction
2. Relevant authority envelope
3. Relevant Business Twin slice
4. Current workflow state
5. Recent events relevant to task
6. Evidence bundle
7. Retrieved artifacts only if needed
8. Full transcript/document only if needed
```

The system should not send the whole Business Twin to every agent.
The system should not send every customer conversation to every agent.
The system should build a **Context Packet** for each run.

## Model routing hierarchy

Use multiple model classes.

```
Tier 0 — No model
For deterministic CRUD, routing, status changes, policy checks, timers.

Tier 1 — Small/cheap model
For classification, extraction, formatting, simple drafting, note cleanup.

Tier 2 — Mid model
For opportunity scoring, customer nuance, bid/no-bid reasoning, SEO analysis.

Tier 3 — Strong model
For high-value negotiation prep, complex procurement analysis, ambiguous customer situations, strategic decisions.

Tier 4 — Human
For physical inspection, irreversible commitments, legal/commercial approval, unusual pricing, trust transfer.
```

The router should escalate when:
* confidence is low
* evidence is incomplete
* dollar exposure is high
* compliance sensitivity is high
* customer sentiment is negative
* action is irreversible
* opportunity value is high
* agent disagreement occurs
* policy requires approval

## Token budget rule

Every agent run should have:
```
context_budget
model_tier
max_iterations
allowed_tools
evidence_requirement
escalation_condition
```

A task should not spawn more agents or use more tokens just because it can.

---

# Supabase Architecture

## Database layer

Supabase provides PostgreSQL with:
* **Tables** — all domain models use PostgreSQL types (UUID, JSONB, TIMESTAMPTZ, TEXT, ARRAY)
* **Row Level Security** — tenant isolation enforced via RLS policies using `current_setting('app.current_tenant')`
* **Realtime** — event streaming for Command Feed, agent status, approval notifications
* **Auth** — Supabase Auth handles user identity; app uses `supabase.auth.getUser()` for API auth
* **Storage** — file artifacts (photos, documents) stored in Supabase Storage buckets
* **Edge Functions** — Deno-based functions for lightweight triggers (not primary compute)

## Environment variables

```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_JWT_SECRET=<jwt-secret>
DATABASE_URL=postgresql://postgres:postgres@db.<project>.supabase.co:5432/postgres
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
API_HOST=127.0.0.1
API_PORT=8000
CHROMAGORA_ENV=development
```

## Database conventions

* All primary keys use PostgreSQL `uuid` type (gen_random_uuid())
* `tenant_id` column on all tenant-scoped tables
* RLS enabled on all tenant-scoped tables
* `created_at` and `updated_at` use `timestamptz`
* JSON data stored as `jsonb`
* Status-like domains normally use CHECK constraints unless a true PostgreSQL enum is intentionally justified.
* Indexes on foreign keys and frequently queried columns
* No SQLite-compatible fallbacks — this is Postgres-only

## Authentication model

* Supabase Auth is the identity provider
* API validates JWT from `Authorization` header via Supabase
* `service_role_key` bypasses RLS for server-side operations (workers, migrations)
* `anon_key` used in web frontend with RLS enforced
* Multi-tenant: users belong to tenants via a `user_tenants` junction table

## Realtime event routing

Supabase Realtime channels:
* `tenant:{tenant_id}:events` — all events for a tenant
* `business:{business_id}:feed` — command feed for a business
* `agent:{agent_id}:runs` — agent run status updates
* `approvals:{tenant_id}` — new approval requests

---

# Chapter 0 — Repository Constitution

## Goal

Lock the architecture before code. Future OpenCode sessions must treat the repo as an engineered operating system, not an exploratory chatbot project.

## 0.1 Create core architecture docs

### Prompt

```
You are working inside a new GitHub repo for Chromagora OS. Create the following files:

/docs/ARCHITECTURE_CONSTITUTION.md
/docs/DOMAIN_GLOSSARY.md
/docs/RUNTIME_TOKEN_ECONOMY.md
/SUPABASE_ARCHITECTURE.md
/AGENTS.md

Chromagora OS is a multi-agent operating platform for SMBs. It is not a chatbot, CRM skin, marketing dashboard, or generic automation tool.

ARCHITECTURE_CONSTITUTION.md must define:
1. Product definition
2. Core architecture thesis
3. Business Cell concept
4. Business Twin concept
5. Department Agent concept
6. Tactical Subagent concept
7. Workflow Engine concept
8. Policy Kernel concept
9. Tool Broker concept
10. Action Ledger concept
11. Operator Cockpit concept
12. What must never be bypassed
13. What not to build yet
14. Supabase as the database layer (PostgreSQL, Auth, Realtime, RLS)
15. Migration path: no SQLite, no local Postgres — Supabase from day one

RUNTIME_TOKEN_ECONOMY.md must define:
1. Token efficiency as runtime architecture
2. Context Packet concept
3. Model routing tiers
4. Memory retrieval tiers
5. When to use no model
6. When to use small model
7. When to use stronger model
8. When to escalate to human
9. What token efficiency must never compromise
10. Examples of good and bad token efficiency

SUPABASE_ARCHITECTURE.md must define:
1. Supabase project structure
2. RLS policy patterns for tenant isolation
3. Realtime channel design
4. Auth flow (API + frontend)
5. Database type conventions
6. Migration strategy (no Alembic — Supabase migrations or hand-written DDL)
7. Edge function boundaries
8. Storage bucket design

AGENTS.md must instruct future AI coding agents:
- do not let agents call external tools directly
- do not bypass the Policy Kernel
- do not bypass the Tool Broker
- do not treat LLMs as workflow state
- do not store canonical truth only in vector memory
- do not build real external actions before dry-run actions
- keep context small but sufficient
- prefer typed schemas
- add tests for policy, workflow, tool execution, and agent behavior
- never optimize token use by reducing real-world correctness
- use Supabase PostgreSQL types, never generic SQL
- enable RLS on all tenant-scoped tables
- never add SQLite fallbacks

Do not implement application code yet.
```

---

# Chapter 1 — No-Docker Monorepo Scaffold

## Goal

Create a clean repo structure that runs on a Mac without Docker.

## 1.1 Scaffold the repo

### Prompt

```
Create the initial Chromagora OS monorepo structure. Use this structure:

/apps
  /web        — Next.js frontend
  /api        — FastAPI backend
  /mobile     — React Native / Expo (created in Chapter 24)
  /workers    — Python background workers (LLM, pipeline, scheduler)
/packages
  /schemas    — Shared Pydantic + TypeScript schemas
  /config     — Shared config, env, constants
  /shared     — Shared utilities
/docs
/infra
/migrations  — Supabase DDL migrations (not Alembic)
/scripts
/tests
  /unit
  /integration
  /evals

Add README.md files in each major directory explaining what belongs there.
Create a root README.md with:
- project name
- product definition
- architecture summary
- local development assumptions
- no-Docker development mode
- Supabase as the only database
- build sequence
- warning that agents cannot directly execute tools

Do not add Docker. Do not add Redis. Do not add Temporal. Do not add SQLite.
Do not add local Postgres. Do not add pgvector yet.
```

## 1.2 Scaffold FastAPI backend

### Prompt

```
Inside /apps/api, scaffold a minimal FastAPI backend.

Requirements:
- pyproject.toml (Python 3.12+)
- FastAPI app
- GET /health
- GET /version
- settings module (reads from .env)
- Supabase client initialization (supabase-py)
- folder structure:
  /apps/api/chromagora_api
    /core        — config, supabase client, security
    /routes
    /db
    /schemas      — Pydantic
    /services
    /tests
  main.py

The app must:
1. Initialize Supabase client from env on startup
2. Validate Supabase connection on /health
3. Use supabase-py for all database access
4. Support service_role_key bypass for admin operations

Add tests for /health and /version.
No database tables yet. No agent logic yet. No external services yet.
No SQLite. No local Postgres.
```

## 1.3 Scaffold Next.js frontend

### Prompt

```
Inside /apps/web, scaffold a minimal Next.js TypeScript app.

Requirements:
- App Router
- TypeScript
- basic layout
- simple global CSS
- home page
- status page placeholder
- Supabase client initialization (@supabase/supabase-js)
- navigation links: Command Feed, Businesses, Agents, Opportunities, Ledger, Settings
- dark mode support via CSS variables
- route groups: (app) for cockpit pages, (api) for API routes if needed

The app must:
1. Initialize Supabase client from env (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)
2. Support both anon and authenticated clients
3. Display Supabase connection status on /status

Do not add a heavy UI library yet unless minimal.
Do not connect data fetching yet. Keep the app clean and simple.
No SQLite. No localStorage hacks.
```

## 1.4 Add no-Docker local development docs

### Prompt

```
Create /docs/LOCAL_DEV_NO_DOCKER.md.

Explain how to run the project locally on a Mac without Docker. Include:
- backend setup (install deps, set .env with Supabase credentials)
- frontend setup (install deps, set .env with Supabase credentials)
- environment variables (all Supabase keys as documented in SUPABASE_ARCHITECTURE.md)
- Supabase CLI for migrations (no Alembic)
- how to reset local state
- why Docker, Redis, local Postgres, SQLite, and Temporal are intentionally deferred

Create .env.example with:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:postgres@db.your-project.supabase.co:5432/postgres
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
API_HOST=127.0.0.1
API_PORT=8000
CHROMAGORA_ENV=development

Do not add Docker files.
```

---

# Chapter 2 — Supabase Database Foundation

## Goal

Build the database layer on Supabase PostgreSQL with RLS, JSONB, UUID, and proper indexing.

## 2.1 Supabase schema and migrations

### Prompt

```
Set up database migrations for Chromagora OS using Supabase DDL (not Alembic).

Create the following migration files in /migrations:

000001_create_extensions.sql
000002_create_tenants.sql
000003_create_user_tenants.sql

Extensions:
- pgcrypto or pg_uuidv7 for UUID generation

Tenants table:
- id uuid primary key default gen_random_uuid()
- name text not null
- slug text unique not null
- status text not null default 'active'
- created_at timestamptz not null default now()
- updated_at timestamptz not null default now()

User tenants (auth from Supabase Auth):
- id uuid primary key default gen_random_uuid()
- user_id uuid not null references auth.users(id)
- tenant_id uuid not null references tenants(id)
- role text not null default 'operator'
- created_at timestamptz not null default now()
- updated_at timestamptz not null default now()
- unique(user_id, tenant_id)

For each table:
1. Create the table
2. Enable RLS
3. Create tenant isolation policy using current_setting('app.current_tenant', true)
4. Create indexes on foreign keys and status columns

Add a /scripts/apply_migrations.py script that uses SERVICE_ROLE_KEY to run migrations.
Add /docs/DATABASE.md explaining the migration approach.
Add tests that verify migration SQL is valid (parse check, no SQLite syntax).
No Alembic. No SQLAlchemy-core for migrations. No SQLite fallbacks.
```

## 2.2 Add base model conventions

### Prompt

```
Create /packages/schemas with shared database model conventions for Supabase PostgreSQL.

Document in /docs/DATABASE_CONVENTIONS.md:

- UUID primary keys (no serial, no auto-increment)
- tenant_id on all tenant-scoped tables
- created_at timestamptz default now()
- updated_at timestamptz default now() with trigger
- jsonb for flexible payloads
- text enums (CHECK constraints)
- arrays where appropriate (TEXT[], UUID[])
- generated columns where useful
- indexes on all foreign keys
- RLS policy patterns (permissive vs restrictive)
- naming conventions (snake_case tables, singular names)

Create Python helpers in /apps/api/chromagora_api/db/:
- base.py: Supabase client management
- tenant.py: Tenant context setting
- session.py: Request-scoped Supabase client with RLS session

Create TypeScript helpers in /apps/web/lib/:
- supabase-client.ts: Browser anon client
- supabase-admin.ts: Server-side service role client (API routes only)
- tenant.ts: Tenant-scoped queries

Do not create business domain tables yet.
Add tests verifying helpers load from .env.
```

---

# Chapter 3 — Core Business Domain

## Goal

Create the canonical structured state before agents exist.

## 3.1 Tenant and client business

### Prompt

```
Implement Tenant and ClientBusiness models via Supabase.

Tenant:
- id uuid pk
- name text
- slug text unique
- status text
- created_at, updated_at

ClientBusiness:
- id uuid pk
- tenant_id uuidFK
- legal_name text
- public_name text
- slug text
- business_type text
- primary_vertical text
- country text
- province_state text
- city text
- service_area_description text
- status text
- created_at, updated_at

Implementation:
1. Write DDL in /migrations/000004_create_businesses.sql
2. Enable RLS, tenant policy, indexes
3. Pydantic schemas in /packages/schemas/
4. CRUD service functions using supabase-py .from_().select/insert/update/delete
5. API routes in /apps/api/.../routes/businesses.py
6. TypeScript types in /packages/schemas/
7. Frontend API client functions

Add GET /tenants, POST /tenants, GET /businesses, POST /businesses, GET /businesses/{business_id}.
Add tests.
Use Supabase .from_() query builder, never raw SQL unless necessary.
```

## 3.2 Business Twin base

### Prompt

```
Implement Business Twin base models via Supabase.

BusinessTwin:
- id uuid pk, business_id uuid FK, version int, status text, summary text, created_at, updated_at

BusinessService:
- id uuid pk, business_id FK, name, description, category, is_active bool, base_price_notes, margin_notes

ServiceArea:
- id uuid pk, business_id FK, name, area_type, description, is_active bool

BusinessCapacityProfile:
- id uuid pk, business_id FK, crew_notes, equipment_notes, scheduling_notes, max_daily_estimates, max_weekly_jobs, seasonal_constraints

BusinessPreference:
- id uuid pk, business_id FK, key, value_json jsonb, source, confidence float, created_at, updated_at

Implementation:
1. DDL in /migrations/000005_create_business_twin.sql
2. RLS policies, indexes on business_id
3. Pydantic schemas, CRUD services, /businesses/{id}/twin routes
4. Supabase .from_() queries, never raw SQL
Add tests.
```

## 3.3 Business facts and claims

### Prompt

```
Add structured models for approved and forbidden business claims via Supabase.

ApprovedBusinessClaim:
- id uuid pk, business_id FK, claim_type, claim_text, evidence_json jsonb, approved_by, is_active bool, created_at, updated_at

ForbiddenBusinessClaim:
- id uuid pk, business_id FK, claim_type, claim_text, reason text, is_active bool, created_at, updated_at

Examples:
Approved: insured, licensed, 24-hour response, warranty terms, service guarantee, supplier relationship
Forbidden: do not claim emergency availability, do not claim licensed if unverified, do not guarantee bare pavement

DDL in /migrations/000006_create_claims.sql
Supabase .from_() CRUD routes.
Add tests.
These claims will later be injected into Context Packets and checked by Policy Kernel.
```

---

# Chapter 4 — Events and Action Ledger

## Goal

Everything important must become an event or ledger record before agents can act.

## 4.1 Event model

### Prompt

```
Implement Event model via Supabase.

Fields: id uuid pk, tenant_id uuid FK, business_id uuid FK nullable, event_type text, source_type text, source_id uuid nullable, payload_json jsonb, occurred_at timestamptz, created_at timestamptz, correlation_id uuid nullable, causation_id uuid nullable, workflow_run_id uuid nullable, trace_id text nullable.

Event type constants:
business.created, business_twin.updated, lead.created, lead.qualified, quote.sent, quote.stale, job.completed, review.requested, review.received, opportunity.detected, approval.required, action.proposed, action.approved, action.rejected, action.executed, action.failed, policy.violation_detected, agent.run_started, agent.run_completed, agent.run_failed

DDL: /migrations/000007_create_events.sql
Supabase enabled for realtime subscription via tenant:{tenant_id}:events channel.
emit_event service inserts row.
GET /events?business_id=&event_type= route.
Add tests.
```

## 4.2 Action proposal and approval request

### Prompt

```

Implement ActionProposal and ApprovalRequest via Supabase.

ActionProposal: id uuid pk, tenant_id FK, business_id FK, proposed_by_type text, proposed_by_id uuid nullable, action_type text, title, description, target_system nullable, proposed_payload_json jsonb, expected_value nullable float, confidence nullable float, risk_level text, autonomy_level_required int, status text, evidence_json jsonb, policy_decision_json jsonb nullable, created_at, updated_at, trace_id nullable.

Statuses: draft, proposed, approval_required, approved, rejected, executed, failed, cancelled, blocked.

ApprovalRequest: id uuid pk, tenant_id FK, business_id FK, action_proposal_id FK, status text, requested_by_type text, requested_by_id uuid nullable, requested_at, decided_by nullable, decided_at nullable, decision_notes nullable, expires_at nullable, trace_id nullable.

Statuses: pending, approved, rejected, cancelled, expired.

DDL: /migrations/000008_create_approvals.sql
Supabase CRUD services, routes: GET /approvals, POST /approvals, POST /approvals/{id}/approve, POST /approvals/{id}/reject.
Emit events for proposal, approval_required, approved, rejected.
Add tests.
```

## 4.3 Action execution ledger

### Prompt

```
Implement ActionExecution model via Supabase.

Fields: id uuid pk, tenant_id FK, business_id FK, action_proposal_id FK nullable, approval_request_id FK nullable, tool_name text, tool_action text, tool_args_hash text, tool_args_redacted_json jsonb, result_status text, result_json jsonb, error_message text nullable, executed_by_type text, executed_by_id uuid nullable, started_at, completed_at nullable, idempotency_key text nullable, reversibility text, rollback_status text nullable, evidence_json jsonb, trace_id text nullable.

Result statuses: dry_run, success, failed, blocked, approval_required, cancelled.

DDL: /migrations/000009_create_ledger.sql
record_action_execution service.
GET /ledger/actions?business_id= route.
Emit action.executed or action.failed events.
Add tests.
```

---

# Chapter 5 — Runtime Context Economy

## Goal

Build token efficiency into the architecture before LLM agents exist.

## 5.1 Context Packet schema

### Prompt

```
Implement ContextPacket as typed schemas (Pydantic + TypeScript interfaces).

ContextPacket:
- packet_id, tenant_id, business_id, task_type, actor_type, actor_id nullable,
  model_tier int, context_budget, objective, authority_summary text,
  business_twin_slice jsonb, workflow_state jsonb, relevant_events jsonb,
  evidence_bundle jsonb, retrieved_artifacts jsonb, forbidden_claims jsonb,
  approved_claims jsonb, output_schema_name, escalation_conditions jsonb, created_at

ContextBudget: max_input_tokens, max_output_tokens, max_iterations, allow_retrieval, allow_full_artifacts, allow_subagents, escalation_model_tier

EvidenceBundle: evidence_items list, missing_evidence list, confidence, source_summary

EvidenceItem: source_type, source_id, title, snippet, url, timestamp, confidence

Store in /packages/schemas/ as Pydantic models and TypeScript types.
/docs/CONTEXT_PACKETS.md
Add tests for schema validation.
```

## 5.2 Context builder service

### Prompt

```
Implement ContextBuilder service using Supabase queries.

build_context_packet(business_id, task_type, actor_type, actor_id, objective, requested_model_tier, workflow_run_id=None, action_proposal_id=None, event_ids=None)

Behavior:
1. Supabase .from_('business_twin').select(...).eq('business_id', ...)
2. Load active claims from approved/forbidden tables
3. Load recent events (capped by context budget)
4. Build evidence bundle from event/action references
5. Return ContextPacket

No LLM. No vector retrieval. No full transcripts. No unrelated state.
Use supabase-py query builder.
Add tests verifying compactness.
```

## 5.3 Token budget policy

### Prompt

```
Implement TokenBudgetPolicy service.

ModelTier: 0 no_model, 1 small, 2 medium, 3 strong, 4 human
Task classes: deterministic_update, simple_classification, structured_extraction, customer_message_draft, approval_card_summary, opportunity_scoring, procurement_analysis, negotiation_prep, compliance_sensitive_action, binding_commitment

select_model_tier(task_type, risk_level, dollar_exposure, compliance_sensitive, confidence):
- deterministic_update -> tier 0
- simple extraction -> tier 1
- customer-facing draft -> tier 2+ if risk medium/high
- procurement -> tier 2 or 3 by dollar
- compliance -> tier 3 or human
- binding -> always human
- low confidence -> escalate one tier
- missing evidence -> escalate or require approval

Add tests for all routing rules.
```

---

# Chapter 6 — Authority Envelopes and Policy Kernel

## Goal

Agents can only act inside explicit authority.

## 6.1 Authority Envelope model

### Prompt

```
Implement AuthorityEnvelope via Supabase.

Fields: id uuid pk, business_id FK, name, description, agent_scope nullable, tool_scope nullable, action_type_scope nullable, autonomy_level int, max_dollar_exposure nullable, requires_approval bool, conditions_json jsonb, forbidden_conditions_json jsonb, is_active bool, created_at, updated_at.

Autonomy levels: 0 observe, 1 analyze, 2 draft, 3 internal_action, 4 low_risk_external_action, 5 bounded_negotiation, 6 binding_execution.

DDL: /migrations/000010_create_authority.sql
CRUD routes: /businesses/{id}/authority
Add tests.
```

## 6.2 Policy Kernel evaluator

### Prompt

```
Implement Policy Kernel evaluator (deterministic Python service).

evaluate_action_policy(business_id, actor_type, actor_id, action_type, target_system, autonomy_level_requested, dollar_exposure, risk_level, confidence, compliance_sensitive, payload_json) -> PolicyDecision

PolicyDecision: allowed, requires_approval, denied, denial_reasons, approval_reasons, matched_authority_envelope_ids, max_autonomy_level_allowed, model_tier_recommendation, decision_notes.

Rules:
1. Load active envelopes via Supabase query
2. Null scope = wildcard
3. No match -> require approval
4. Autonomy exceeds -> require approval
5. Dollar exceeds -> require approval
6. Low confidence -> escalate
7. Compliance sensitive -> require approval unless explicit
8. Level 6 -> always require approval
9. Forbidden conditions -> deny
10. Include model tier recommendation from TokenBudgetPolicy

Use supabase-py for all data access.
Add tests for all scenarios.
```

## 6.3 Compliance rule placeholders

### Prompt

```
Implement ComplianceRule via Supabase.

Fields: id uuid pk, tenant_id FK, business_id nullable FK, name, jurisdiction, rule_type, description, applies_to_action_type nullable, rule_config_json jsonb, is_active bool, created_at, updated_at.

Rule types: casl_commercial_message, privacy_personal_data, call_recording_notice, public_claims, review_request_policy, procurement_submission, supplier_credit_application.

DDL: /migrations/000011_create_compliance.sql
Update Policy Kernel to load active ComplianceRules.
If rule_config_json has {"blocking": true}, rule can require approval or deny.
Add tests.
```

---

# Chapter 7 — Tool Broker

## Goal

All real-world actions go through the broker. No agent gets raw power.

## 7.1 Tool registry

### Prompt

```
Implement ToolDefinition and BusinessToolPermission via Supabase.

ToolDefinition: id uuid pk, name, description, target_system, tool_action, input_schema_json jsonb, output_schema_json jsonb, risk_level_default, autonomy_level_required_default, is_external_action bool, is_active bool, created_at, updated_at.

BusinessToolPermission: id uuid pk, business_id FK, tool_definition_id FK, is_enabled bool, max_autonomy_level int, requires_approval_override nullable, config_json jsonb, created_at, updated_at.

DDL: /migrations/000012_create_tools.sql
Services: register_tool_definition, list_tools_for_business, check_tool_permission.
Add tests.
```

## 7.2 Dry-run Tool Broker

### Prompt

```
Implement dry-run Tool Broker (deterministic Python service).

request_tool_execution(business_id, actor_type, actor_id, tool_name, tool_action, tool_args_json, dry_run=True, dollar_exposure=None, risk_level=None, confidence=None, compliance_sensitive=False)

Behavior:
1. Look up ToolDefinition via Supabase
2. Check BusinessToolPermission via Supabase
3. Create ActionProposal
4. Evaluate policy
5. If denied -> blocked
6. If approval required -> ApprovalRequest
7. If allowed and dry_run=true -> ActionExecution with result_status="dry_run"
8. Emit events
9. Return structured result

No real external systems called.
Use supabase-py.
Add tests.
```

## 7.3 Mock tools

### Prompt

```
Add mock development tools and seed script via Supabase.

Mock tools: crm.create_lead, crm.update_lead_status, crm.create_followup_task, reputation.queue_review_request, procurement.create_opportunity_note, seo.create_content_draft, email.create_draft, supplier.create_supplier_note, message.create_draft

/scripts/seed_dev_tools.py — upserts ToolDefinitions via Supabase SERVICE_ROLE_KEY.
Document the Tool Broker behavior in the relevant service README or vertical runtime doc.
Add tests.
```

---

# Chapter 8 — Workflow-Lite Engine

## Goal

Use database-backed workflows before Temporal.

## 8.1 Workflow models

### Prompt

```
Implement workflow-lite.

WorkflowDefinition: id uuid pk, name, description, workflow_type, version int, config_json jsonb, is_active bool, created_at, updated_at.

WorkflowRun: id uuid pk, tenant_id FK, business_id FK, workflow_definition_id FK nullable, workflow_type text, status text, current_step nullable, input_json jsonb, state_json jsonb, result_json jsonb nullable, started_at, updated_at, completed_at nullable, correlation_id nullable uuid, trace_id nullable text.

Statuses: pending, running, waiting_for_approval, waiting_for_external_event, completed, failed, cancelled.

WorkflowStepLog: id uuid pk, workflow_run_id FK, step_name, status text, input_json jsonb, output_json jsonb nullable, error_message nullable, started_at, completed_at nullable.

DDL: /migrations/000013_create_workflows.sql
Services: create_workflow_run, log_workflow_step, update_workflow_state, mark_waiting_for_approval, complete_workflow, fail_workflow.
Emit events on major state changes.
Add tests.
```

## 8.2 Review request workflow

### Prompt

```
Implement completed_job_review_request workflow in dry-run mode via Supabase.

Input: business_id, customer_name, customer_contact, job_summary, completed_at

Steps:
1. Create WorkflowRun
2. Create ActionProposal for reputation.queue_review_request via Tool Broker
3. If approval required -> mark waiting_for_approval
4. If allowed -> dry-run ActionExecution
5. Complete if no approval required

POST /workflows/review-request/dry-run
Add tests for allowed, approval-required paths, event emission, trace propagation.
```

## 8.3 Stale quote workflow

### Prompt

```
Implement stale_quote_followup workflow in dry-run mode via Supabase.

Input: business_id, quote_id nullable, customer_name, customer_contact, quote_amount nullable, service_type, quote_sent_at, last_contact_at nullable.

Steps:
1. Create WorkflowRun
2. Determine stale (default 3 days)
3. If not stale -> complete with no action
4. If stale -> emit quote.stale, build ContextPacket, request crm.create_followup_task
5. Pause for approval if required
6. Complete if allowed

POST /workflows/stale-quote-followup/dry-run
Add tests.
```

---

# Chapter 9 — Operator Cockpit v0

## Goal

Build the command surface around the control spine.

## 9.1 Connect frontend to backend

### Prompt

```
Connect Next.js frontend to FastAPI.

Requirements:
- API client helper
- NEXT_PUBLIC_API_BASE_URL support
- page calling GET /health and /version
- clear loading/error states
- basic TypeScript types
- Supabase JWT passed as Bearer token

Do not overbuild. Do not add auth UI yet (auth comes later).
```

## 9.2 Businesses and Business Twin UI

### Prompt

```
Build frontend pages using Supabase data:

/businesses — list, create
/businesses/[id] — view details
/businesses/[id]/twin — view and edit Business Twin basics, services, areas, capacity, preferences, approved/forbidden claims

Use Supabase .from_() queries via API routes or direct anon client.
Keep UI utilitarian. Dark mode.
```

## 9.3 Command Feed

### Prompt

```
Build /command page displaying Event records from Supabase.

Features: newest first, filter by business_id, event_type badge, timestamp, source_type, payload preview.
Use Supabase realtime subscription on tenant:{tenant_id}:events channel for live updates.
```

## 9.4 Approval Inbox

### Prompt

```
Build /approvals page.

Backend: GET /approvals?status=pending, POST /approvals/{id}/approve, POST /approvals/{id}/reject (Supabase mutations).
Frontend: list pending, show ActionProposal details, approve/reject buttons.
Approval/rejection emits events.
Add tests.
```

## 9.5 Action Ledger page

### Prompt

```
Build /ledger page showing ActionExecution records from Supabase.
Filter by business_id. Readable, audit-oriented. Dark mode.
```

---

# Chapter 10 — Agent Registry and Agent Runs

## Goal

Introduce agents as tracked actors, not vague prompt calls.

## 10.1 Agent definitions

### Prompt

```
Implement AgentDefinition and BusinessAgentInstance via Supabase.

AgentDefinition: id, name, agent_type, description, standing_mission, default_subscribed_events jsonb, default_allowed_tools jsonb, default_authority_level int, default_model_tier int, is_active, created_at, updated_at.

BusinessAgentInstance: id, business_id FK, agent_definition_id FK, display_name, status, config_json jsonb, authority_envelope_id FK nullable, created_at, updated_at.

Seed MVP agents: Sales, Reputation, Growth, Procurement, Supplier, Operations, Compliance, Operator Liaison.

DDL: /migrations/000014_create_agents.sql
Routes: GET /agents/definitions, GET /businesses/{id}/agents, POST /businesses/{id}/agents.
Add tests.
```

## 10.2 AgentRun model

### Prompt

```
Implement AgentRun via Supabase.

Fields: id, tenant_id FK, business_id FK, agent_instance_id FK nullable, agent_type text, trigger_type text, trigger_event_id FK nullable, workflow_run_id FK nullable, status text, input_json jsonb, context_packet_json jsonb nullable, output_json jsonb nullable, error_message nullable, started_at, completed_at nullable, cost_estimate nullable float, model_name nullable, model_tier nullable int, trace_id nullable.

Statuses: pending, running, completed, failed, cancelled.

DDL: /migrations/000015_create_agent_runs.sql
Services: start_agent_run, complete_agent_run, fail_agent_run.
GET /agent-runs?business_id=
Add tests.
```

## 10.3 Agent Workforce UI

### Prompt

```
Build /agents and /businesses/[id]/agents pages using Supabase data.
Show agent name, type, mission, status, model tier, envelope, recent runs.
```

---

# Chapter 11 — Rules-Based Agents v0

## Goal

Start with deterministic rules agents. No LLM required.

## 11.1 Reputation Agent v0

### Prompt

```
Implement Reputation Agent v0 as non-LLM service using Supabase.

Input: business_id, customer_name, customer_contact, job_summary, completed_at.

1. Start AgentRun (Supabase insert)
2. Build ContextPacket (Supabase queries)
3. Validate fields
4. Request reputation.queue_review_request via Tool Broker (dry-run)
5. Complete AgentRun

POST /agents/reputation/run-review-request-dry-run
Add tests. No LLM. No external calls.
```

## 11.2 Sales Agent v0

### Prompt

```
Implement Sales Agent v0 as non-LLM service using Supabase.

Input: business_id, quote_id nullable, customer_name, customer_contact, quote_amount nullable, service_type, quote_sent_at, last_contact_at nullable.

1. Start AgentRun
2. Build ContextPacket
3. Determine stale
4. If stale -> request crm.create_followup_task via Tool Broker
5. Complete AgentRun

POST /agents/sales/run-stale-quote-dry-run
Add tests.
```

---

# Chapter 12 — Authority and Tool Configuration UI

## Goal

Operators must be able to configure autonomy before agents become more capable.

## 12.1 Authority Envelope editor

### Prompt

```
Build Authority Envelope UI at /businesses/[id]/authority.
Supabase CRUD. List, create, edit, deactivate. Autonomy level selector 0-6.
Dark mode. Explain autonomy levels.
```

## 12.2 Tool Permissions UI

### Prompt

```
Build Tool Permissions UI at /businesses/[id]/tools.
Supabase .from_('tool_definitions') queries. Enable/disable per business.
Dark mode.
```

---

# Chapter 13 — Opportunity Intelligence v0

## Goal

Create first version of market/procurement intelligence without scraping.

## 13.1 Opportunity model

### Prompt

```
Implement Opportunity via Supabase.

Fields: id, tenant_id FK, business_id FK, opportunity_type, source_name, source_url nullable, title, description, location, published_at nullable, deadline_at nullable, estimated_value_min nullable, estimated_value_max nullable, fit_score nullable, urgency_score nullable, capacity_fit nullable, margin_confidence nullable, strategic_value nullable, status text, required_documents jsonb, missing_documents jsonb, evidence_json jsonb, recommended_next_action nullable, agent_owner nullable, workflow_run_id FK nullable, created_at, updated_at, trace_id nullable.

Statuses: detected, qualifying, qualified, rejected, approval_required, pursuing, submitted, won, lost, archived.

DDL: /migrations/000016_create_opportunities.sql
Add CRUD routes and tests.
```

## 13.2 Opportunity War Room UI

### Prompt

```
Build /opportunities page using Supabase data.
Filter by business_id, status. Simple list. Dark mode.
```

## 13.3 Procurement Scout v0

### Prompt

```
Implement Procurement Scout v0 as non-LLM dry-run agent via Supabase.

Input: business_id, opportunity_type, source_name, source_url nullable, title, description, location, deadline_at nullable, estimated_value_min/max nullable.

1. Start AgentRun
2. Create Opportunity (Supabase insert)
3. Score fit (rules: service match, area match, deadline present, value present, docs known)
4. Create ActionProposal via Tool Broker
5. Complete AgentRun

POST /agents/procurement/evaluate-opportunity-dry-run
No scraping. No LLM. Add tests.
```

---

# Chapter 14 — LLM Integration Layer

## Goal

Add LLMs only after schemas, policy, workflows, ledger, and context economy exist.

## 14.1 Model router interface

### Prompt

```
Implement model router abstraction in /apps/workers.

/apps/workers/chromagora_workers/llm/model_router.py

Interface:
complete_text(prompt, model_hint=None, model_tier=None, temperature=0)
complete_structured(prompt, schema, model_hint=None, model_tier=None, temperature=0)

Requirements:
- Provider calls routed to OpenRouter (base URL from env)
- Models selected by tier from config
- Tier 0: no model (deterministic code)
- Tier 1: openrouter/google/gemma-4-26b-it:free
- Tier 2: openrouter/qwen/qwen3-coder:free
- Tier 3: openrouter/nvidia/nemotron-3-super-120b-a12b:free or similar free tier
- Tier 4: not applicable (human)
- Base router uses OpenRouter `:free` models for ordinary OS agent runs.
- No hardcoded API keys
- Timeout, error handling, structured logging
- Mock provider for provider-agnostic tests

Note: the base model router is for ordinary OS agent runs. Specialized verticals may define their own model gateway, timeout policy, and model selection, while still recording model calls and respecting tenant scoping, traceability, and cost controls.

Do not wire to agents yet.
Add tests for mock provider.
```

## 14.2 LLM policy for runtime token efficiency

### Prompt

```
Create /docs/MODEL_ROUTING_POLICY.md.

Document tier assignments, escalation triggers, downgrade rules.
Emphasize: the base router uses free models by default for ordinary OS agent runs.
No model for Tier 0. Base/free models for Tier 1-3. Human for Tier 4.
Clarify that specialized verticals may define their own model gateway, timeout policy, and model selection, while still recording model calls and respecting tenant scoping, traceability, and cost controls.
Add code constants.
No real provider calls yet.
```

## 14.3 Structured tender extraction

### Prompt

```
Implement optional LLM structured extraction.

extract_tender_fields(text, mode="deterministic" | "llm_structured")

Output: title, buyer_name, deadline, location, service_keywords, required_documents, insurance_requirements, estimated_value, submission_method, disqualifying_requirements, unknowns, confidence.

Rules: parser does NOT save to database, create actions, or execute tools.
Uses the base OpenRouter model gateway unless a specialized vertical gateway is explicitly designed.
Mock LLM tests.
```

## 14.4 Approval card summary generator

### Prompt

```
Implement LLM-assisted approval card summary generator using free OpenRouter models.

Input: ActionProposal, PolicyDecision, ContextPacket, EvidenceBundle
Output: plain_language_summary, why_this_matters, expected_value, risk_summary, what_has_been_checked, missing_evidence, what_happens_if_approved, what_happens_if_ignored, suggested_operator_decision, confidence.

Rules: drafts display copy only. Cannot approve/reject/execute/mutate DB.
Must mention missing evidence. Must not invent facts.
Mock LLM tests.
```

---

# Chapter 15 — Tactical Subagents and Spawn Contracts

## Goal

Add recursive subagents safely.

## 15.1 Spawn Contract model

### Prompt

```
Implement SpawnContract schema via Supabase.

Fields: id uuid pk, parent_agent_run_id FK, business_id FK, subagent_type, objective, scope, input_refs jsonb, allowed_tools jsonb, forbidden_tools jsonb, source_boundaries jsonb, max_side_effects, ttl_seconds, token_budget jsonb, output_schema_name, evidence_requirements jsonb, success_condition, kill_condition, authority_level int, memory_write_policy text, status text, created_at, updated_at.

Rules: default memory_write_policy = "no_durable_write", default max_side_effects = "none", default authority_level = analyze/draft, external tools forbidden by default.

DDL: /migrations/000017_create_spawn_contracts.sql
```

## 15.2 Tactical subagent runner v0

### Prompt

```
Implement tactical subagent runner v0.

run_tactical_subagent(spawn_contract):
1. Validate SpawnContract
2. Build scoped ContextPacket
3. Enforce token budget
4. Use mock or deterministic handler
5. Return structured output
6. No external tools
7. No durable memory unless policy allows
8. Record AgentRun linked to parent

Initial types: seo_gap_scout_mock, tender_requirement_extractor_mock
Add tests.
```

---

# Chapter 16 — End-to-End Demo Loops

## Goal

Make the first loops feel like real Chromagora.

## 16.1 Review request simulation

### Prompt

```
Create POST /demo/review-request-simulation using Supabase.

Input: business_id, customer_name, customer_contact, job_summary.

1. Emit job.completed event
2. Trigger Reputation Agent v0
3. Build ContextPacket
4. Create ActionProposal
5. Evaluate Policy Kernel
6. Tool Broker
7. ApprovalRequest or dry-run ActionExecution
8. Return all IDs

Frontend: /demo/review-request with links to cockpit pages.
```

## 16.2 Stale quote simulation

### Prompt

```
Create POST /demo/stale-quote-simulation using Supabase.

Input: business_id, customer_name, customer_contact, quote_amount, service_type, quote_sent_at.

1. Emit quote.sent or quote.stale
2. Sales Agent v0
3. ContextPacket, ActionProposal, Policy, Tool Broker
4. Return all IDs

Frontend: /demo/stale-quote
```

## 16.3 Opportunity simulation

### Prompt

```
Create POST /demo/opportunity-simulation using Supabase.

Input: business_id, opportunity_type, source_name, source_url, title, description, location, deadline_at, estimated_value_min/max.

1. Emit opportunity.detected
2. Procurement Scout v0
3. Create Opportunity, score, propose
4. Policy, Tool Broker
5. Return all IDs

Frontend: /demo/opportunity
```

---

# Chapter 17 — CRM-Lite and Draft Artifacts

## Goal

Add internal business records before integrating external CRMs.

## 17.1 CRM-lite models

### Prompt

```
Implement CRM-lite models via Supabase.

Lead: id, business_id FK, customer_name, customer_contact, source, service_type, status, notes, created_at, updated_at.
Quote: id, business_id FK, lead_id FK nullable, quote_amount nullable, service_type, status, sent_at nullable, last_followup_at nullable, notes, created_at, updated_at.
Job: id, business_id FK, lead_id FK nullable, quote_id FK nullable, customer_name, service_type, status, scheduled_at nullable, completed_at nullable, notes, created_at, updated_at.

DDL: /migrations/000018_create_crm.sql
CRUD routes, frontend pages, tests.
Update agents to optionally use these records.
```

## 17.2 Email/SMS draft table, no sending

### Prompt

```
Implement MessageDraft via Supabase.

Fields: id, business_id FK, channel text, recipient, subject nullable, body, status text, related_action_proposal_id FK nullable, related_workflow_run_id FK nullable, created_at, updated_at.

Channels: email, sms. Statuses: draft, approval_required, approved, sent, cancelled.
Tool: message.create_draft via Tool Broker. No sending.
UI, tests.
```

---

# Chapter 18 — Observability and Evals

## Goal

Trust the system before increasing autonomy.

## 18.1 Trace ID propagation

### Prompt

```
Add trace_id propagation via Supabase.

All records: Event, WorkflowRun, WorkflowStepLog, ActionProposal, ApprovalRequest, ActionExecution, AgentRun.

Requirements:
1. Generate trace_id at entry if missing
2. Pass through all created records
3. Include in API responses
4. Structured logging with trace_id

Add tests proving propagation across full demo workflow.
```

## 18.2 Deterministic eval fixtures

### Prompt

```
Create deterministic eval fixtures in /tests/evals.

Fixtures:
1. review request allowed
2. review request approval required
3. stale quote allowed
4. stale quote approval required
5. opportunity high fit
6. opportunity low fit
7. binding execution blocked
8. low confidence escalates
9. forbidden claim blocks message

Eval runner test loading fixtures and verifying expected outcomes.
No real LLM.
```

## 18.3 LLM structured output evals

### Prompt

```
Add LLM output validation tests using mock provider.

Evaluate: tender extraction schema, approval card schema, missing evidence handling, no invented facts, confidence field, unknown fields rejected.
Strict Pydantic validation. Mock LLM only.
```

---

# Chapter 19 — Mobile Readiness, Not Android App Yet

## Goal

Architect mobile support without building the native app too early.

## 19.1 Mobile API surface

### Prompt

```
Add mobile-oriented API endpoints via FastAPI.

GET /mobile/today?business_id=
GET /mobile/approvals?business_id=
POST /mobile/approvals/{id}/approve
POST /mobile/approvals/{id}/reject
GET /mobile/command-feed?business_id=
GET /mobile/jobs/today?business_id=
POST /mobile/capture/note
POST /mobile/capture/photo-metadata

Response includes: urgent approvals, high-priority events, active workflow waits, upcoming jobs, opportunity deadlines, blocked agents.
Add tests.
```

## 19.2 Responsive field mode in web

### Prompt

```
Add responsive mobile-friendly field mode at /field.
Thin, API-driven. Dark mode. Not the native app.
```

---

# Chapter 20 — Infrastructure Upgrade Path

## Goal

Prepare for hosted infrastructure without Docker.

## 20.1 Supabase as primary (already done)

### Prompt

```
Document /docs/SUPABASE_AS_PRIMARY.md.

Explain why Supabase is the primary and only database:
- No SQLite fallback
- No local Postgres
- RLS for tenant isolation
- Realtime for event streaming
- Auth for identity
- Edge functions for lightweight logic
- Workers hosted separately (fly.io, Railway, or similar)

This file replaces the old POSTGRES_MIGRATION_PLAN.md since there is no migration path needed.
```

## 20.2 Hosted workers

### Prompt

```
Add support for hosting Python workers on a platform without Docker.

Options: fly.io, Railway, Render, or similar.
Document setup in /docs/HOSTED_INFRA.md.
Workers need: supabase-py, httpx, pydantic, Python 3.12+.
No Docker requirement documented as the default path. Container optional.
```

## 20.3 pgvector optional memory layer

### Prompt

```
Add optional pgvector support via Supabase.

Feature flag: ENABLE_VECTOR_MEMORY.
Canonical Business Twin remains relational.
Vector memory optional. App starts without pgvector.

Tables via Supabase:
MemoryArtifact: id, business_id FK, artifact_type, title, text_content, source_ref, created_at, updated_at.
MemoryEmbedding: id, artifact_fk FK, embedding_model, embedding_vector vector(1536), created_at.

If feature flag off, embeddings table unused.
DDL: /migrations/000019_create_memory.sql (conditional)
/docs/VECTOR_MEMORY_PLAN.md
```

---

# Chapter 21 — Temporal Upgrade Plan

## Goal

Move from workflow-lite to durable workflows only after product loops are proven.

## 21.1 Temporal upgrade document

### Prompt

```
Create /docs/TEMPORAL_UPGRADE_PLAN.md.

Explain which workflows move to Temporal, which stay as db state machines.
Approval pauses ->signals. Timers/retries -> Temporal.
Tool Broker calls remain outside deterministic workflow logic.
Use Temporal Cloud (no local Docker).
Migration strategy from WorkflowRun to Temporal IDs.
No Temporal code yet.
```

## 21.2 Temporal adapter interface

### Prompt

```
Create workflow engine abstraction.

Interface: start_workflow, signal_workflow, get_workflow_status, cancel_workflow.
Current adapter: WorkflowLiteAdapter.
TemporalAdapter documented but not implemented.
Add tests for WorkflowLiteAdapter.
```

---

# Chapter 22 — Real Integrations, Narrowly

## Goal

Add real actions only after dry-run loops, policy, approval, and ledger work.

## 22.1 Real email sending behind approval

### Prompt

```
Add real email sending via API behind feature flag.

ENABLE_REAL_EMAIL_SENDING.
MessageDraft must be approved before sending.
Routes through Tool Broker. Policy Kernel approves. ActionExecution records.
Idempotency key required. No bulk sending. No CASL outreach without compliance.
Abstract provider. Mock + tests. No hardcoded credentials.
```

## 22.2 External CRM integration placeholder

### Prompt

```
Create CRM integration abstraction.

Interface: create_lead, update_lead, create_task, get_lead, list_recent_leads.
InternalCrmLiteProvider uses Supabase tables.
Future: HubSpot, GoHighLevel, Zoho providers.
No external credentials yet.
```

---

# Chapter 23 — Voice Agent Preparation

## Goal

Prepare for inbound voice without building a fragile voice agent too early.

## 23.1 Call transcript and call summary models

### Prompt

```
Implement via Supabase.

CallRecord: id, business_id FK, caller_phone, caller_name nullable, call_status, started_at, ended_at nullable, recording_url nullable, transcript_text nullable, consent_recorded bool, created_at, updated_at.

CallSummary: id, call_record_id FK, intent, service_type, address_or_area nullable, urgency, lead_quality, escalation_required bool, escalation_reason nullable, structured_notes jsonb, confidence, created_at.

Routes for CRUD. No telephony yet. Add tests.
```

## 23.2 Voice qualification schema

### Prompt

```
Create VoiceQualificationResult schema.

Fields: caller_intent, service_type, address_or_area, service_area_match, timeline, urgency, budget_signal, photos_requested, estimate_booking_recommended, escalation_required, escalation_reason, bad_fit_signals, next_action, confidence, missing_information.

Document voice-agent design in an active vertical or service doc before implementation.
No real voice.
```

---

# Chapter 24 — Native Android Companion App

## Goal

Build Android only after the mobile API and web field mode prove the surface.

## 24.1 Create mobile app scaffold

### Prompt

```
Create /apps/mobile as React Native / Expo TypeScript app.

Tabs: Today, Approvals, Jobs, Capture, Settings.
No business logic in mobile app. Consumes backend APIs only. Supabase anon client for auth.
Connect to /mobile endpoints.
```

## 24.2 Mobile approval flow

### Prompt

```
Implement mobile Approval flow.
GET /mobile/approvals, POST /mobile/approvals/{id}/approve, POST /mobile/approvals/{id}/reject.
Fast, simple UX. Dark mode.
```

## 24.3 Mobile field capture

### Prompt

```
Implement Capture screen: text note, attach to optional job_id/lead_id, type selector.
POST /mobile/capture/note. No photo upload yet. No local canonical state.
```

---

# Chapter 25 — Autonomy Increase

## Goal

Only now start increasing actual autonomy.

## 25.1 Allow low-risk external actions

### Prompt

```
Implement controlled low-risk external action support.

Scope: actions marked low_risk_external_action + enabled in BusinessToolPermission.
Rules: Policy Kernel allows, Tool Broker executes, ActionExecution records, idempotency key, rollback status.
Approval required if low confidence or compliance sensitive.
Add tests proving unauthorized blocked.
```

## 25.2 Autonomy scorecard

### Prompt

```
Add Autonomy Scorecard per business via Supabase.

Metrics: total proposals, approvals required/accepted/rejected, dry-run/real executions, blocked, violations, failures, avg confidence, value proposed/approved.

GET /businesses/{id}/autonomy-scorecard
Frontend: /businesses/[id]/autonomy
```

---

# Chapter 26 — Final v0.1 Acceptance Test

## Goal

Define when Chromagora OS v0.1 is real.

## 26.1 Create acceptance test document

### Prompt

```
Create /docs/V0_1_ACCEPTANCE_TEST.md.

Successful v0.1 must allow:
1. Create tenant
2. Create client business
3. Define Business Twin
4. Define approved/forbidden claims
5. Configure authority envelopes
6. Enable mock tools
7. Run review request simulation
8. Run stale quote simulation
9. Run opportunity simulation
10. Generate action proposals
11. Trigger approval required
12. Approve/reject from cockpit
13. See events in Command Feed
14. See executions in Action Ledger
15. See agent runs
16. See context packet summaries
17. Trace IDs across workflow
18. Run deterministic evals
19. Run without Docker
20. Run without real external integrations
21. Run on Supabase (not SQLite)
22. RLS enforced on all tenant tables
23. Base router cost controls

Explicitly NOT in v0.1: real voice, real email by default, real scraping, Temporal, pgvector required, native Android, autonomous contract submission, autonomous negotiation.
```

## 26.2 Create v0.1 demo script

### Prompt

```
Create /docs/V0_1_DEMO_SCRIPT.md.

Scenario: landscaping/snow removal business.
1. Business creation
2. Business Twin config
3. Authority envelope setup
4. Mock tools enabled
5. Completed job -> review request
6. Stale quote -> follow-up
7. Commercial snow opportunity -> evaluation
8. Approval inbox
9. Approve/reject
10. Action ledger
11. Command feed
12. Trace links
Practical, founder-demo ready.
```

---

# Implementation order summary

Build in this order:
```
0.  Repo Constitution
1.  No-Docker Scaffold
2.  Supabase Database Foundation
3.  Core Business Domain
4.  Events + Action Ledger
5.  Runtime Context Economy
6.  Policy Kernel
7.  Tool Broker
8.  Workflow-Lite
9.  Operator Cockpit
10. Agent Registry
11. Rules-Based Agents
12. Authority + Tool UI
13. Opportunity Intelligence
14. LLM Integration (base router)
15. Tactical Subagents
16. End-to-End Simulations
17. CRM-lite + Drafts
18. Observability + Evals
19. Mobile Readiness
20. Hosted Infra (workers)
21. Temporal Plan
22. Narrow Real Integrations
23. Voice Prep
24. Android Companion
25. Autonomy Increase
26. v0.1 Acceptance Test
```

# Core sequencing rationale

## Why docs first
Because AI coding agents drift. The repo needs architectural law before implementation.

## Why no Docker first
Because the machine constraint is real, and Docker is not needed for v0.1.

## Why Supabase before anything
Because all data lives there. No SQLite, no local Postgres, no migration path needed.

## Why database before agents
Because agents need structured state.

## Why ledger before tools
Because actions must be auditable before anything can act.

## Why policy before tool execution
Because authority must exist before power.

## Why context economy before LLMs
Because runtime token efficiency must be designed before model calls become scattered.

## Why workflows before agents
Because business operations are long-running and stateful.

## Why rules-based agents before LLM agents
Because the system should prove the action path before adding nondeterministic reasoning.

## Why cockpit before autonomy
Because humans need visibility and control before agents become aggressive.

## Why mobile readiness before Android
Because the Android app should consume clean APIs, not create its own logic.

## Why Temporal later
Because workflow-lite is enough for v0.1 and does not require Docker.

## Why pgvector later
Because canonical Business Twin state must be structured first.

## Why real integrations later
Because dry-run tool execution must be safe and observable first.

# Runtime token-efficiency architecture summary

Chromagora OS should save tokens by:
* using deterministic code for policy, routing, CRUD, status changes, and timers
* using compact Context Packets instead of full state dumps
* using structured Business Twin slices
* retrieving only relevant artifacts
* caching summaries
* routing simple tasks to smaller models
* escalating complex/high-risk tasks to stronger models
* forcing subagents to operate under spawn contracts
* preventing endless agent chat
* using typed events instead of conversational coordination
* writing compact evidence bundles
* measuring cost per workflow and agent run
* **using the base OpenRouter free-tier models for ordinary OS agent runs, with specialized vertical gateways documented separately when needed**

Chromagora OS must not save tokens by:
* using weak models for high-value judgment
* dropping authority constraints
* dropping policy context
* dropping customer nuance when customer risk is high
* compressing away evidence
* ignoring missing information
* preventing escalation
* limiting context for procurement or negotiation when stakes are high
* allowing agents to act from incomplete context
* treating summaries as canonical truth

Final rule:
```
Spend fewer tokens by default. Spend whatever tokens are required when correctness, trust, money, compliance, or customer experience depends on it. The base OS router defaults to free-tier inference; specialized vertical gateways must define timeout, model-selection, traceability, tenant-scoping, and cost controls explicitly.
```
