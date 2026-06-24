# AGENTS.md — Chromagora OS Development Agent Instructions

You are an AI coding agent contributing to **Chromagora OS v0.1**.

Read these files FIRST:
1. `docs/CHAPTERBOOK.md` — the 26-chapter build blueprint
2. `docs/ARCHITECTURE_CONSTITUTION.md` — binding architecture rules
3. `docs/RUNTIME_TOKEN_ECONOMY.md` — model routing and context rules
4. `SUPABASE_ARCHITECTURE.md` — database layer rules
5. `docs/DOMAIN_GLOSSARY.md` — domain language

## Binding Rules (Never Break)

1. **No direct tool calls from agents.** Every tool call routes through the Tool Broker.
2. **Never bypass Policy Kernel.** Every action proposal is evaluated before execution.
3. **Never treat LLMs as workflow state.** Deterministic state lives in Supabase.
4. **Never store canonical truth in vector memory.** Business Twin is canonical; vector is supplement.
5. **Never build real external actions before dry-run.** Every tool has dry-run mode first.
6. **Keep context small but sufficient.** Use Context Packets, never full database dumps.
7. **Prefer typed schemas.** Pydantic in Python, Zod/TypeScript types in frontend.
8. **Never optimize token use by reducing correctness.** Spend more when stakes are high.
9. **Use Supabase PostgreSQL types.** uuid, jsonb, timestamptz, text arrays — never generic SQL.
10. **Enable RLS on all tenant-scoped tables.** No exceptions.
11. **No SQLite fallbacks.** Supabase is the only database.
12. **No custom auth.** Use Supabase Auth exclusively.
13. **Write tests** for: policy, workflow, tool execution, agent behavior, schema validation.
14. **Push commits to GitHub often.** Every working increment is a commit.

## Supabase is the Only Database

- PostgreSQL with UUID PKs, JSONB fields, proper indexes
- RLS enforces tenant isolation
- Realtime powers live event streaming
- No SQLite, no local Postgres, no alternative database

## Model Routing

Free models only. Never pay for inference.
- Tier 0: No model (deterministic code)
- Tier 1: `openrouter/google/gemma-4-26b-a4b-it:free` — classification, extraction
- Tier 2: `openrouter/qwen/qwen3-coder:free` — scoring, drafting, content
- Tier 3: `openrouter/nvidia/nemotron-3-super-120b-a12b:free` — complex analysis, negotiation prep
- Tier 4: Human

Base URL: `https://openrouter.ai/api/v1`
API Key: from environment variable `OPENROUTER_API_KEY`

## Project Structure

```
chromagora-os/
├── apps/
│   ├── api/          — FastAPI backend (Python 3.12+)
│   ├── web/          — Next.js frontend (TypeScript)
│   ├── mobile/       — React Native / Expo (Chapter 24)
│   └── workers/      — Python background workers
├── packages/
│   ├── schemas/      — Shared Pydantic + TypeScript schemas
│   ├── config/       — Shared config, env, constants
│   └── shared/       — Shared utilities
├── docs/             — Architecture, chapterbook, READMEs
├── infra/            — Infrastructure configuration
├── migrations/       — Supabase DDL migration files
├── scripts/          — Utility scripts (seed, apply_migrations)
└── tests/
    ├── unit/         — Unit tests
    ├── integration/  — Integration tests
    └── evals/        — Deterministic eval fixtures
```

## Build Order

Follow `docs/CHAPTERBOOK.md` implementation order. Current chapter: see git log for last completed chapter.

## Commit Convention

```
chore: scaffold — initial repo structure
docs:  architecture constitution and domain glossary
feat:  database — tenant and client business models
feat:  events — event model and action ledger
...
```

## What Not to Build Yet

Real external integrations, Temporal, pgvector (optional), native Android app, real voice agent, real procurement scraping, Docker, paid models.
