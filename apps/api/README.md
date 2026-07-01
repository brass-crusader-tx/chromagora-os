# API — FastAPI Backend

The Chromagora OS backend API.

## Stack
- Python 3.12+
- FastAPI
- Supabase (supabase-py) for all database access
- Pydantic v2

## Structure
```
chromagora_api/
  main.py          — FastAPI app and router registration
  core/            — config, Supabase client, auth, errors, rate limit
  db/              — Supabase admin helpers and tenant scoping
  routes/          — API route handlers
  services/        — business logic and runtime services
  tests/           — API tests
```

## Running
```bash
cd apps/api
pip install -r requirements.txt
uvicorn chromagora_api.main:app --reload --port 8000
```

## Key Endpoints
- `GET /health` — health check with Supabase connection status
- `GET /version` — API version
