#!/usr/bin/env python3
"""Apply Supabase migrations via the Management API.

Requires a Supabase Personal Access Token (PAT) set as SUPABASE_ACCESS_TOKEN.
Generate one at: https://supabase.com/dashboard/account/tokens

Usage: python scripts/apply_migrations.py [--dry-run] [migration_file...]
Without arguments, applies all migrations in order.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load env from apps/api/.env (two levels up from scripts/)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_ENV = REPO_ROOT / "apps" / "api" / ".env"

# Also check scripts/.env
ENV_PATH = SCRIPT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
elif API_ENV.exists():
    load_dotenv(API_ENV)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0] if "//" in SUPABASE_URL else ""
ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")

MIGRATIONS_DIR = REPO_ROOT / "migrations"

API_BASE = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"


def extract_statements(sql_text: str) -> list[str]:
    """Split SQL into individual statements, respecting $$ quoting."""
    statements = []
    current = []
    in_dollar_quote = False
    dollar_tag = ""
    lines = sql_text.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not current and (stripped.startswith("--") or not stripped):
            continue

        if not in_dollar_quote:
            # Check for $$ opening
            match = re.search(r"\$\$(\w*)", line)
            if match:
                in_dollar_quote = True
                dollar_tag = match.group(1) or ""
                tag_end = line.find(f"$${dollar_tag}", match.end() - len(dollar_tag) - 2)
                if tag_end != -1:
                    # Opening and closing on same line
                    pass
                else:
                    current.append(line)
                    continue
            else:
                current.append(line)
                if stripped.endswith(";"):
                    stmt = "\n".join(current).strip()
                    statements.append(stmt)
                    current = []
        else:
            current.append(line)
            if f"$${dollar_tag}" in line:
                in_dollar_quote = False
                stmt = "\n".join(current).strip()
                statements.append(stmt)
                current = []

    if current:
        remaining = "\n".join(current).strip()
        if remaining and not all(
            l.strip().startswith("--") or not l.strip() for l in current
        ):
            statements.append(remaining)

    return [s for s in statements if s and not s.startswith("--")]


def apply_migrations(dry_run: bool = False, files: list[str] | None = None):
    """Apply migration files to the Supabase database."""
    if not ACCESS_TOKEN:
        print("ERROR: SUPABASE_ACCESS_TOKEN not set.")
        print("Generate one at: https://supabase.com/dashboard/account/tokens")
        print("Then set it in scripts/.env or as an environment variable.")
        sys.exit(1)

    if not PROJECT_REF:
        print("ERROR: Could not extract project ref from SUPABASE_URL")
        sys.exit(1)

    if files:
        migration_files = [Path(f) for f in files]
    else:
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    total = 0
    failed = 0

    with httpx.Client(timeout=30) as client:
        for mf in migration_files:
            if not mf.exists():
                print(f"  SKIP (not found): {mf.name}")
                continue

            sql = mf.read_text()
            statements = extract_statements(sql)

            if not statements:
                print(f"  SKIP (empty): {mf.name}")
                continue

            print(f"\n{'[DRY RUN] ' if dry_run else ''}{mf.name}: {len(statements)} statements")

            for stmt in statements:
                # Skip RLS policies that require table to exist (will fail if table not created yet)
                clean = stmt.strip()
                if not clean:
                    continue

                if dry_run:
                    print(f"  [DRY] {clean[:80]}...")
                    total += 1
                    continue

                try:
                    r = client.post(API_BASE, headers=headers, json={"query": clean})
                    if r.status_code == 200:
                        total += 1
                    else:
                        err = r.text[:200]
                        print(f"  FAIL: {clean[:80]}...")
                        print(f"        {err}")
                        failed += 1
                except Exception as e:
                    print(f"  ERROR: {clean[:80]}...")
                    print(f"         {e}")
                    failed += 1

    print(f"\n{'='*50}")
    print(f"Migration {'dry run' if dry_run else 'apply'} complete:")
    print(f"  Statements executed: {total}")
    print(f"  Failures: {failed}")
    if failed > 0:
        sys.exit(1)
    else:
        print("  All migrations applied successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply Supabase migrations")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    parser.add_argument("files", nargs="*", help="Specific migration files to apply")
    args = parser.parse_args()
    apply_migrations(dry_run=args.dry_run, files=args.files or None)
