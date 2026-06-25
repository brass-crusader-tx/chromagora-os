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
- Follow `docs/CHAPTERBOOK.md` for build order
- Reference `docs/ARCHITECTURE_CONSTITUTION.md` for rules
- Use Supabase Auth for authentication
- Enable RLS on all tenant-scoped tables

## Key Files

- `docs/CHAPTERBOOK.md` — Build blueprint
- `docs/ARCHITECTURE_CONSTITUTION.md` — Architecture rules
- `SUPABASE_ARCHITECTURE.md` — Database layer
- `docs/DOMAIN_GLOSSARY.md` — Domain language
