# Demo Factory Runtime

This document describes the Demo Factory vertical: an operator-facing production line for private demo revamps for local service businesses.

## Business Condition

An operator has a ranked CSV or spreadsheet of local service-business leads. The system imports the rows, creates one isolated demo project per eligible row, processes the queue top-to-bottom, and publishes a private demo at `{slug}.demo.chromagora.com` after structured generation and QA pass.

## Loop Shape

```txt
CSV/spreadsheet lead queue
  -> normalized demo project rows
  -> sequential batch worker
  -> crawl public business site
  -> build evidence bundle
  -> generate BrandDoc
  -> retrieve conversion framework patterns
  -> generate conversion/page strategy
  -> curate assets and reviews
  -> assemble typed SiteSpec JSON
  -> deterministic Next.js renderer
  -> before/after reveal wrapper
  -> visual and adversarial QA
  -> auto-publish to {slug}.demo.chromagora.com
  -> cockpit review/send
```

Spreadsheet order is operationally meaningful. Rows are processed by valid numeric `Rank` when present, otherwise by CSV row order. The worker must not process row 25 before row 24 unless row 24 is terminally failed, skipped, or explicitly paused by operator policy.

## Architecture Commitments

Demo Factory is a vertical inside Chromagora OS. It reuses:

| Primitive | Usage |
|---|---|
| Supabase | Primary datastore for batches, projects, artifacts, specs, QA, deployments, events, and model-call records. |
| FastAPI | Service routes under `/demo-sites/*` for import, batch control, project inspection, and public SiteSpec resolution. |
| Next.js Operator Cockpit | Batch upload, batch progress, project detail, QA, deployment links, and model-call history. |
| Python workers | Sequential batch processing and project stage orchestration outside request threads. |
| `events` | Lifecycle events such as `demo_site.batch_imported`, `demo_site.site_spec_created`, and `demo_site.published`. |
| `agent_runs` | Major LLM agent stage traces where practical, with compact inputs and outputs. |
| Context packets | Each agent call receives a fresh compact packet for one business only. |
| Action ledger / trace IDs | Trace IDs connect batch, row, project, events, agent runs, and deployment actions. |
| Supabase Storage | Screenshots, scraped assets, rendered screenshots, and public demo assets. |

## Non-Goals

Demo Factory is not:

| Not This | Boundary |
|---|---|
| Standalone website builder | It is an OS vertical and uses existing tenants, API, workers, events, storage, and cockpit patterns. |
| Prompt-only demo generator | Agents produce structured artifacts; the renderer remains deterministic. |
| Arbitrary code generation per business | The canonical output is typed `SiteSpec` JSON, not generated React/CSS/HTML. |
| Autonomous outreach sender | Cockpit review/send remains operator controlled. |
| Direct client-domain deployment | v0.1 publishes private demos under `demo.chromagora.com`. |
| Quote follow-up replacement | It is a separate vertical after the quote follow-up runtime. |

## Tables Involved

| Table | Role |
|---|---|
| `demo_site_batches` | One imported CSV/spreadsheet batch with aggregate progress counters. |
| `demo_site_batch_rows` | Ordered normalized lead rows linked to projects. |
| `demo_site_projects` | One generation context per business/prospect. |
| `demo_site_source_snapshots` | Crawled pages, text summaries, and old-site screenshot references. |
| `demo_site_assets` | Scraped, selected, rejected, and published image/logo/screenshot assets. |
| `demo_site_brand_documents` | BrandDoc JSON produced from grounded evidence. |
| `demo_site_framework_sources` | Private/licensed framework source metadata only. |
| `demo_site_framework_patterns` | Searchable private pattern summaries/snippets, not raw committed corpus. |
| `demo_site_framework_retrievals` | Patterns selected for a project/stage. |
| `demo_site_reviews` | Verified or rejected exact-business reviews. |
| `demo_site_specs` | Renderer-safe canonical SiteSpec JSON. |
| `demo_site_qa_reports` | Visual/adversarial QA reports and screenshot references. |
| `demo_site_deployments` | Published demo host/URL state. |
| `demo_model_calls` | One row per OpenRouter/mock agent call. |
| `demo_factory_supervisor_events` | Rate-limit, timeout, stuck-job, retry, and pause/resume events. |
| `events` | OS-level lifecycle observability. |
| `agent_runs` | Agent stage traces and compact summaries. |

## Services Involved

| Service | File | Role |
|---|---|---|
| CSV Importer | `apps/api/chromagora_api/services/demo_factory_importer.py` | Parses lead CSVs, normalizes URLs/domains/slugs, creates batch rows and projects. |
| Framework Retrieval | `apps/api/chromagora_api/services/demo_frameworks.py` | Retrieves private framework patterns without committing corpus material. |
| Deployment Service | `apps/api/chromagora_api/services/demo_deployment_service.py` | Marks a passing SiteSpec current and creates/updates deployment rows. |
| Batch Processor | `apps/workers/chromagora_workers/demo_factory/batch_processor.py` | Selects rows in processing order and updates counters. |
| Orchestrator | `apps/workers/chromagora_workers/demo_factory/orchestrator.py` | Runs the project stage machine. |
| Model Gateway | `apps/workers/chromagora_workers/demo_factory/model_gateway.py` | Makes isolated OpenRouter/mock calls and persists model-call telemetry. |
| Supervisor | `apps/workers/chromagora_workers/demo_factory/supervisor.py` | Handles rate limits, timeouts, cooldowns, and stuck-stage events. |
| SiteSpec Assembler | `apps/workers/chromagora_workers/demo_factory/site_spec_assembler.py` | Enforces the renderer contract and removes unsupported claims. |
| Visual QA | `apps/workers/chromagora_workers/demo_factory/visual_qa.py` | Checks local renders before publish. |

## Workers

| Worker | Role |
|---|---|
| `demo_factory_worker.py` | Polling worker with `--once`, `--interval`, heartbeats, and sequential row processing. |
| Future crawler/QA workers | May split heavy stages later, but v0.1 keeps one active row lane for predictable ordering. |

## Routes

| Route | Purpose |
|---|---|
| `POST /demo-sites/import-csv` | Import a CSV body and create a batch, rows, and projects. |
| `GET /demo-sites/batches` | List recent batches. |
| `GET /demo-sites/batches/{batch_id}` | Return batch detail with rows in processing order. |
| `POST /demo-sites/batches/{batch_id}/start` | Mark a queued/paused batch running. |
| `POST /demo-sites/batches/{batch_id}/pause` | Pause a running batch. |
| `POST /demo-sites/batches/{batch_id}/resume` | Resume a paused batch. |
| `GET /demo-sites/projects/{project_id}` | Project detail. |
| `POST /demo-sites/projects/{project_id}/retry` | Reset retryable project/row state. |
| `POST /demo-sites/projects/{project_id}/archive` | Archive a project. |
| `GET /demo-sites/projects/{project_id}/artifacts` | BrandDoc, SiteSpec, assets, reviews, model calls, and supervisor events. |
| `GET /demo-sites/projects/{project_id}/qa` | QA reports. |
| `GET /demo-sites/projects/{project_id}/deployment` | Current deployment. |
| `GET /demo-sites/public/{slug}/site-spec` | Public renderer resolution by slug. |

## Events Emitted

| Event Type | When |
|---|---|
| `demo_site.batch_imported` | CSV import creates a batch. |
| `demo_site.batch_started` | Batch starts or resumes. |
| `demo_site.project_queued` | Import creates a project. |
| `demo_site.crawl_started` | Crawl begins. |
| `demo_site.crawl_completed` | Crawl evidence is persisted. |
| `demo_site.brand_doc_created` | BrandDocument is saved. |
| `demo_site.copy_strategy_created` | ConversionStrategy is saved. |
| `demo_site.site_spec_created` | SiteSpec is assembled. |
| `demo_site.qa_failed` | Blocking QA issue prevents publish. |
| `demo_site.qa_passed` | QA passes. |
| `demo_site.published` | Deployment is verified and marked published. |
| `demo_site.project_failed` | Project fails retryably or terminally. |
| `demo_site.batch_completed` | No queued/retryable rows remain. |

## Failure Modes

| Failure | Behavior |
|---|---|
| CSV parse error | Import fails without creating partial rows. |
| Missing website URL | Row may still create a project if business name/domain evidence is sufficient; otherwise it is skipped. |
| Crawl timeout | Project becomes `failed_retryable`; later rows continue when policy allows. |
| OpenRouter 429 | Project moves to `waiting_rate_limit`, supervisor records cooldown, and the same stage retries after cooldown. |
| Agent invalid JSON | Stage retries through the model gateway; repeated failure becomes retryable, not terminal by default. |
| Unsupported claim | SiteSpec assembler removes it or adversarial QA blocks publish. |
| Unverified reviews | Review section is omitted. |
| Visual QA blocking issue | Deployment is not published and row becomes retryable. |
| Publish verification failure | Deployment remains `failed`; project/row are retryable. |
| Ordinary row failure | Batch records failure and continues after the row is terminal/skipped, without killing the whole batch. |
