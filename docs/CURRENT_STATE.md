# Chromagora OS Current State

Chromagora OS is currently a Supabase-first monorepo with a FastAPI backend, a Next.js cockpit, Python workers, and hand-written Supabase/PostgreSQL migrations.

## Runtime Surfaces

- `apps/api` contains the FastAPI backend, route handlers, Supabase helpers, auth/rate-limit/error middleware, and runtime services.
- `apps/web` contains the Next.js operator cockpit.
- `apps/workers` contains Python worker code, including the base model router and quote follow-up worker entrypoints.
- `packages/schemas` contains shared Python/Pydantic schema models.
- `migrations` contains numbered SQL migrations through `000025_quote_runtime_hardening.sql`.

## Implemented Vertical

The quote follow-up runtime is the primary implemented vertical and the best current template for future vertical integration. It includes migrations, schema updates, services, API routes, worker code, events, approvals, execution records, traceability, and tests.

See `docs/verticals/quote-follow-up-runtime.md` for the intended loop shape.

## Demo Route Naming

The existing `/demo/*` API route means internal runtime simulations:

- `/demo/review-request-simulation`
- `/demo/stale-quote-simulation`
- `/demo/opportunity-simulation`

These are not prospect website demo endpoints. Future Demo Factory work should use `/demo-sites/*` and `/demo-site-batches/*`, not `/demo/*`.

## Model Routing

The existing worker model router is the base OS router for ordinary agent runs. It is not sufficient as-is for heavy demo-generation pipelines. Specialized verticals may define their own model gateway, timeout policy, and model selection, while still recording model calls and respecting tenant scoping, traceability, and cost controls.

## New Vertical Pattern

New verticals should follow the quote follow-up integration pattern:

1. Add migrations and tenant-scoped tables/columns.
2. Add Pydantic schemas and service-layer business logic.
3. Add route handlers for operator/API access.
4. Add worker or dispatcher entrypoints when asynchronous processing is needed.
5. Emit events and preserve trace IDs across the loop.
6. Record proposals, approvals, executions, and ledger/trace data where relevant.
7. Add focused API/service/worker tests.
8. Add or update cockpit pages only after backend behavior exists.

Do not use archived chapterbooks or historical v0.1 acceptance docs as active implementation instructions unless explicitly requested.
