# Chromagora OS Development Instructions

## Project Overview

Chromagora OS is a multi-tenant business platform. You are an AI coding agent contributing to this project.

## Development Guidelines

### Tools
Use all available tools freely:
- **exec** — Run shell commands (Python, npm, git, etc.)
- **read/write/edit** — Modify source code files
- **glob/grep** — Search and find files

### Code Style
- Python 3.12+ with FastAPI
- TypeScript/Next.js for frontend
- Supabase PostgreSQL for database
- Pydantic for data validation

### Testing
- Write tests for new functionality
- Run tests before committing
- Use pytest for Python tests

### Git
- Commit working increments
- Use conventional commit messages
- Push to GitHub regularly

### Architecture
- Treat `docs/CHAPTERBOOK.md` as a historical baseline through Chapter 26, not a fresh-start build order
- Reference `docs/ARCHITECTURE_CONSTITUTION.md` for rules
- Use Supabase Auth for authentication
- Enable RLS on all tenant-scoped tables

## Context Priority

When files conflict, follow this order:
1. Current source code and migrations
2. `docs/CURRENT_STATE.md`
3. Active vertical docs under `docs/verticals/`
4. `docs/CHAPTERBOOK.md` as historical baseline through Chapter 26
5. Archived docs only when explicitly requested

Do not treat archived chapterbooks or v0.1 acceptance docs as active build instructions.

## Key Files

- `docs/CURRENT_STATE.md` — Current implementation summary
- `docs/CHAPTERBOOK.md` — Historical base build blueprint
- `docs/ARCHITECTURE_CONSTITUTION.md` — Architecture rules
- `SUPABASE_ARCHITECTURE.md` — Database layer
- `docs/DOMAIN_GLOSSARY.md` — Domain language
