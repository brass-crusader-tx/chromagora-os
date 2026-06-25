# Hosted Infrastructure

Chromagora OS is designed to run without Docker. Workers can be hosted on platforms like fly.io, Railway, or Render.

## Workers

Python workers need:
- Python 3.12+
- `supabase>=2.10.0`
- `httpx>=0.28.0`
- `pydantic>=2.0`

Workers connect to the same Supabase project via environment variables.

## Hosting Options

### fly.io
- Push to fly.io with `fly launch`
- Dockerfile optional (Python can run without it using nixpacks)
- Set secrets via `fly secrets set`

### Railway
- Connect GitHub repo, auto-deploy on push
- Set environment variables in dashboard
- No Dockerfile needed if `pyproject.toml` present

### Render
- Connect GitHub repo as Web Service
- Uses `pyproject.toml` for build detection

## Notes

- Workers do NOT run inside Docker by default
- Container is optional, never required
- All state is in Supabase — workers are stateless
- Multiple worker instances can run concurrently (idempotency keys prevent duplicates)

## Architecture

```
Frontend (Next.js) ──── Supabase (anon client + RLS)
                            │
API (FastAPI) ───────────── Supabase (service_role client)
                            │
Workers (Python) ────────── Supabase (service_role client)
```
