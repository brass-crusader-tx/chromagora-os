# Tests — Test Suite

## Structure
- `unit/` — unit tests for services, schemas, policy
- `integration/` — integration tests for API endpoints, database
- `evals/` — deterministic eval fixtures and runner```bash
# Unit tests
pytest tests/unit

# Integration tests (requires Supabase credentials)
pytest tests/integration

# Evals
pytest tests/evals
```
