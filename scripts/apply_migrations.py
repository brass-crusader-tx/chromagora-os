"""Apply Supabase migrations from the migrations/ directory.

Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from environment.
Usage: python scripts/apply_migrations.py
"""

import os
import re
import sys
from pathlib import Path

from supabase import create_client


def get_migrations_dir() -> Path:
    """Get the migrations directory path."""
    return Path(__file__).resolve().parent.parent / "migrations"


def get_applied_migrations(supabase) -> set:
    """Get list of already applied migrations.

    In production, this would query a migration tracking table.
    For now, returns an empty set.
    """
    return set()


def apply_migration(supabase, filepath: Path) -> bool:
    """Apply a single migration file."""
    sql = filepath.read_text()

    # Basic validation
    if not sql.strip():
        print(f"  SKIP: {filepath.name} (empty)")
        return True

    # Remove comments for safety check
    clean_sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)

    try:
        # Execute via Supabase RPC (requires exec_sql function)
        # Or use supabase-py's postgrest API
        supabase.rpc("exec_sql", {"sql": clean_sql}).execute()
        print(f"  APPLIED: {filepath.name}")
        return True
    except Exception as e:
        print(f"  ERROR applying {filepath.name}: {e}")
        return False


def main():
    """Apply all pending migrations."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)

    migrations_dir = get_migrations_dir()
    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return

    applied = get_applied_migrations(supabase)

    print(f"Found {len(files)} migration files")
    print(f"Already applied: {len(applied)}")

    success_count = 0
    fail_count = 0

    for filepath in files:
        if filepath.name in applied:
            print(f"  SKIP (applied): {filepath.name}")
            continue
        if apply_migration(supabase, filepath):
            success_count += 1
        else:
            fail_count += 1

    print(f"\nDone. Applied: {success_count}, Failed: {fail_count}")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
