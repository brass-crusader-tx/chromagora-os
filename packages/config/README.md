# Config — Shared Configuration

Placeholder for shared configuration that needs to be reused across apps and workers.

Current reality:
- API settings live in `apps/api/chromagora_api/core/config.py`.
- Worker model routing constants live in `apps/workers/chromagora_workers/llm/model_router.py`.
- Frontend runtime settings are read from Next.js environment variables.

Move configuration here only when it is genuinely shared by multiple runtime surfaces.
