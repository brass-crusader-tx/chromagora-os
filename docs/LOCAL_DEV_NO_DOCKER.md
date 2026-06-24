# Local Development Without Docker

Chromagora OS is designed to run locally on a Mac without Docker.

## Prerequisites

- Python 3.11+ (install via Homebrew: `brew install python@3.11`)
- Node.js 20+ (install via Homebrew: `brew install node`)
- Supabase account (free tier works)
- Supabase CLI (optional, for migrations: `npm install -g supabase`)

## Backend Setup

```bash
cd apps/api

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your Supabase project credentials

# Run tests
pytest chromagora_api/tests/

# Start development server
uvicorn chromagora_api.main:app --reload --port 8000
```

## Frontend Setup (when scaffolded)

```bash
cd apps/web
npm install
npm run dev
```

Available at http://localhost:3000

## Database

Supabase is the database. Create a project at https://supabase.com, then:

1. Copy project URL and keys to `.env`
2. Use Supabase CLI to push migrations: `supabase migration up`
3. Or run: `python scripts/apply_migrations.py`

## Resetting Local State

Since data is in Supabase:
- Use Supabase Dashboard table editor to delete rows
- Or run SQL via Supabase SQL Editor

## Why No Docker?

Docker on Mac can be unreliable. Chromagora OS uses:
- **Supabase** — runs remotely, no local database container
- **Python venv** — local virtual environment
- **Node.js** — local installation
- **Supabase CLI** — optional, for local emulator

## Why No Redis?

Redis is not needed for v0.1. Realtime is handled by Supabase.
Worker state is stored in PostgreSQL.

## Why No Postgres Locally?

Supabase is PostgreSQL. Running a local Postgres for dev is unnecessary
when you can connect to a free Supabase project.

## Why No Temporal?

Workflow Lite uses database-backed state machines. No separate orchestration
engine needed for v0.1.
