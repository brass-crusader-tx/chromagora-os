# Chromagora OS — Architecture Constitution

## 1. Product Definition

Chromagora OS is a multi-agent operating platform for Small and Medium Businesses (SMBs). It is NOT:
- A chatbot
- A CRM skin
- A marketing dashboard
- A generic automation tool

It IS a structured operating cell where autonomous agents operate under explicit policies and authority, execute business workflows, maintain a live "Business Twin" mirror of real business state, and enable human-in-the-loop oversight through an Operator Cockpit.

## 2. Core Architecture Thesis

The platform is built around strict separation of concerns:

| Layer | Responsibility |
|-------|---------------|
| **Policy Kernel** | Defines what can and cannot be done. Authority envelopes, compliance rules. |
| **Tool Broker** | Mediates ALL interactions — external systems and internal tools. No agent calls tools directly. |
| **Workflow Engine** | Orchestrates sequences of agent actions. State machines backed by database. |
| **Business Twin** | Real-time, synchronized mirror of business state. Canonical structured truth. |
| **Department Agents** | Own domain-specific responsibilities (Sales, Reputation, Procurement, Operations, etc). |
| **Tactical Subagents** | Bounded sub-agents spawned for specific short-lived tasks under Spawn Contracts. |
| **Action Ledger** | Immutable record of every action proposed, approved, executed, or failed. |
| **Operator Cockpit** | Human oversight UI — Command Feed, Approval Inbox, Agent Runs, Ledger. |
| **Context Economy Layer** | Builds compact, task-specific Context Packets instead of dumping full state. |

## 3. Business Cell Concept

A **Business Cell** is the runtime container for one client business. It contains:
- Exactly one Business Twin
- One or more Department Agent instances
- Authority Envelopes governing agent autonomy
- Tool Broker with registered and permitted tools
- Workflow Lite engine state
- Action Ledger scope
- Event stream

**Principle:** A Business Cell is the smallest unit of operation. Everything is scoped to a Cell. No agent operates outside a Cell.

## 4. Business Twin Concept

The **Business Twin** is a structured, real-time mirror of a client business. It includes:
- **Profile:** legal name, business type, vertical, location, service areas
- **Services:** offered services with descriptions, categories, pricing notes
- **Service Areas:** geographic or zone-based coverage
- **Capacity Profile:** crew, equipment, scheduling constraints, max daily/weekly loads
- **Preferences:** key-value operational preferences with source and confidence
- **Approved Claims:** verified business claims (insured, licensed, warranty terms)
- **Forbidden Claims:** claims that must never be made

**Principle:** The Business Twin is canonical structured state in Supabase. Agent memory and vector embeddings are supplements, never replacements.

## 5. Department Agent Concept

**Department Agents** are persistent, named agents with domain responsibilities:
- Sales Agent — leads, quotes, follow-ups
- Reputation Agent — reviews, ratings, feedback
- Growth Agent — marketing, SEO, content
- Procurement Agent — tenders, opportunities, supplier scouting
- Supplier Agent — supplier relationships, credit checks
- Operations Agent — scheduling, dispatch, job status
- Compliance Agent — regulatory checks, CASL, privacy
- Operator Liaison Agent — human handoff, escalation

Each agent has an Authority Envelope that defines what it can and cannot do.

## 6. Tactical Subagent Concept

**Tactical Subagents** are short-lived, bounded agents spawned by Department Agents for specific tasks. They:
- Operate under a strict Spawn Contract
- Have scoped tools (never all tools)
- Have a token budget and TTL
- Cannot spawn their own subagents
- Cannot perform external actions unless explicitly permitted
- Return structured output and terminate

**Principle:** Subagents are tactical, not strategic. They execute a defined task and stop.

## 7. Workflow Engine Concept

**Workflow Lite** is a database-backed state machine engine (no Temporal in v0.1):
- Workflows are defined by config (steps, transitions, conditions)
- Workflow runs persist state in Supabase
- Human approval pauses are first-class (waiting_for_approval state)
- External event waits are supported
- All state transitions emit Events

 Business operations are long-running and stateful. Deterministic state machines over a database are sufficient for v0.1.

## 8. Policy Kernel Concept

The **Policy Kernel** is the deterministic evaluation layer:
- Every proposed action passes through it
- Loads Authority Envelopes for the acting agent
- Checks compliance rules
- Returns PolicyDecision: allowed, requires_approval, denied
- Recommends model tier from TokenBudgetPolicy
- Never bypassed

**Principle:** Authority must exist before power. No agent acts without policy evaluation.

## 9. Tool Broker Concept

The **Tool Broker** is the single gateway for all real-world actions:
- No agent or subagent calls tools directly
- All tool calls are registered in a ToolDefinition catalog
- BusinessToolPermission enables/disables tools per business
- Every execution routes through: Policy Check → Proposal → Approval (if needed) → Execution → Ledger
- Dry-run mode is the default for development
- Feature flags gate real external actions

**Principle:** All real-world actions are gated, recorded, and auditable.

## 10. Action Ledger Concept

The **Action Ledger** is an immutable audit trail:
- Every proposal, approval, execution, and failure is recorded
- Records include: tool used, redacted args, result, actor, timestamps, trace_id
- Reversibility classification for every action
- Idempency keys prevent duplicate execution
- Used for replay, debugging, and compliance audits

**Principle:** If it isn't in the ledger, it didn't happen.

## 11. Operator Cockpit Concept

The **Operator Cockpit** is the web-based command surface:
- **Command Feed:** real-time event stream (powered by Supabase Realtime)
- **Approval Inbox:** pending human decisions with context summaries
- **Business Manager:** create/edit businesses and Business Twins
- **Agent Workforce:** view agents, their status, recent runs
- **Opportunity War Room:** procurement opportunities
- **Action Ledger:** audit trail viewer
- **Authority & Tool Config:** autonomy and tool permissions

**Principle:** Humans must have full visibility and control before any autonomy increases.

## 12. What Must Never Be Bypass

1. **Policy Kernel** — every action proposal must be evaluated
2. **Tool Broker** — no direct tool calls from agents
3. **Action Ledger** — every execution must be recorded
4. **RLS (Row Level Security)** — all tenant data isolated at database level
5. **Supabase Auth** — no custom auth, no backdoors
6. **Dry-run before real** — test execution before actual external actions
7. **Context Packets** — never dump full state to agents

## 13. What Not to Build Yet

- Real external integrations (email, telephony, CRM)
- Temporal workflow engine
- pgvector semantic memory (optional later)
- Native Android companion app
- Real procurement scraping
- Real voice agent
- Custom auth or identity system
- Docker or containerized local dev
- Local Postgres or SQLite
- Paid model inference

## 14. Supabase as the Database Layer

Supabase provides the entire database and auth layer:
- **PostgreSQL** — all domain data with UUID PKs, JSONB fields, proper indexes
- **Auth** — Supabase Auth for all identity (no custom auth)
- **Realtime** — event streaming for Command Feed and agent status
- **RLS** — tenant isolation enforced at database level via RLS policies
- **Storage** — file artifacts (photos, documents) in Supabase Storage buckets
- **Edge Functions** — lightweight Deno functions for triggers (not primary compute)
- **Migrations** — hand-written DDL files, no Alembic

## 15. Migration Path

There is no migration path from SQLite or local Postgres. Supabase is the primary and only database from day one:
- Local development connects to a Supabase project URL via `.env`
- All DDL targets PostgreSQL types (uuid, jsonb, timestamptz, text arrays)
- No database-agnostic SQL
- RLS policies written from the start
- Supabase CLI for local emulator (optional, never required)

---

_This constitution is binding for all future development sessions._
