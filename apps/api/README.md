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
  main.py          — FastAPI application entry
  core/            — config, supabase client, security
  routes/          — API route handlers
  db/              — database helpers, tenant context
  models/          — SQLAlchemy or raw SQL models
  schemas/         — Pydantic request/response schemas
  services/        — business logic services
  tests/           — unit tests
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
