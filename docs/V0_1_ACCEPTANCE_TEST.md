# Chromagora OS v0.1 Acceptance Test

This document defines when Chromagora OS v0.1 is considered complete.

## Core Criteria

A successful v0.1 must allow:

### Data Model
1. Create tenant
2. Create client business
3. Define Business Twin (services, areas, capacity, preferences)
4. Define approved/forbidden claims

### Authority & Policy
5. Configure authority envelopes (autonomy levels 0-6)
6. Enable mock tools per business
7. Policy Kernel evaluates proposals correctly

### Agent Workforce
8. Run review request simulation (Reputation Agent v0)
9. Run stale quote simulation (Sales Agent v0)
10. Run opportunity evaluation (Procurement Scout v11. Generate action proposals via agents

### Workflow & Approval
12. Trigger approval required for out-of-scope actions
13. Approve/reject from cockpit (web + mobile endpoints)
14. Dry-run execution records in Action Ledger

### CRM-lite
15. Create and manage leads, quotes, jobs
16. Create message drafts (no sending)

### Observability
17. See events in Command Feed
18. See executions in Action Ledger
19. See agent runs20. Trace IDs propagate across workflow
21. Run deterministic evals and verify outcomes

### Infrastructure
22. Run without Docker
23. Run without real external integrations
24. Run on Supabase (not SQLite)
25. RLS enforced on all tenant tables
26. Free models only (no paid API costs)

## Explicitly NOT in v0.1

- Real voice telephony
- Real email sending (feature-flagged off)
- Web scraping or real opportunity detection
- Temporal workflow engine (workflow-lite only)
- pgvector required (optional, feature-flagged off)
- Native Android companion app (React Native scaffold only if Chapter 24 built)
- Autonomous contract submission
- Autonomous binding negotiation

## How to Verify

1. Start API: `cd apps/api && uvicorn chromagora_api.main:app --reload`
2. Run all tests: `cd apps/api && python -m pytest chromagora_api/tests/ -v`
3. Run demo script: see `docs/V0_1_DEMO_SCRIPT.md`
4. Open frontend: `cd apps/web && npm run dev`
5. Navigate to http://localhost:3010/businesses

## Test Count Target

- 206+ existing tests must continue to pass
- New tests added in Chapters 20-26 should push total to 250+
- Zero test failures
