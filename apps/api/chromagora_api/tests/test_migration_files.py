"""Tests that migration files are valid SQL structure."""

import re
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "migrations"


def test_migrations_dir_exists():
    assert MIGRATIONS_DIR.exists(), f"Migrations dir not found: {MIGRATIONS_DIR}"


def test_migration_files_ordered():
    """Migration files should be numbered sequentially."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    assert len(files) >= 1, "No migration files found"

    for f in files:
        assert re.match(r"^\d{6}_", f.name), f"Migration file {f.name} doesn't follow NNNNNN_name.sql convention"


def test_migration_files_not_empty():
    """Migration files should not be empty."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for f in files:
        content = f.read_text().strip()
        assert len(content) > 0, f"Migration {f.name} is empty"


def test_first_migration_has_extensions():
    """First migration should create extensions."""
    first = sorted(MIGRATIONS_DIR.glob("*.sql"))[0]
    content = first.read_text().upper()
    assert "CREATE EXTENSION" in content, "First migration should create extensions"


def test_tenant_migration_has_rls():
    """Tenant migration should enable RLS."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    tenant_file = [f for f in files if "tenants" in f.name.lower() and "extension" not in f.name.lower()]
    assert len(tenant_file) > 0, "No tenant table migration found"
    content = tenant_file[0].read_text().upper()
    assert "ENABLE ROW LEVEL SECURITY" in content, "Tenant table should have RLS enabled"


def test_no_sqlite_syntax():
    """No migration should contain SQLite-specific syntax."""
    files = MIGRATIONS_DIR.glob("*.sql")
    sqlite_patterns = [r"AUTOINCREMENT", r"INTEGER PRIMARY KEY", r"strftime", r"DATE\("]
    for f in files:
        content = f.read_text()
        for pattern in sqlite_patterns:
            assert not re.search(pattern, content, re.IGNORECASE), \
                f"Migration {f.name} contains SQLite syntax: {pattern}"
