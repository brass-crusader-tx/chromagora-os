#!/usr/bin/env python3
"""Apply SQL migrations through DATABASE_URL.

This is the fallback when Supabase Management API access is unavailable. It
loads the root .env with python-dotenv, normalizes raw special characters in the
database password in memory, then executes migration statements in order.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import psycopg
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MIGRATIONS_DIR = REPO_ROOT / "migrations"

sys.path.insert(0, str(SCRIPT_DIR))


def _database_url() -> str:
    load_dotenv(REPO_ROOT / ".env", override=True)
    dsn = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
    if not dsn:
        raise SystemExit("DATABASE_URL is empty")
    return _normalize_url_password(dsn)


def _normalize_url_password(dsn: str) -> str:
    if "://" not in dsn or "@" not in dsn:
        return dsn
    scheme, rest = dsn.split("://", 1)
    creds, host_rest = rest.rsplit("@", 1)
    if ":" not in creds:
        return _strip_unsupported_query_params(dsn)
    user, password = creds.split(":", 1)
    normalized = f"{scheme}://{user}:{quote(password, safe='')}@{host_rest}"
    return _strip_unsupported_query_params(normalized)


def _strip_unsupported_query_params(dsn: str) -> str:
    parts = urlsplit(dsn)
    allowed = {
        "application_name",
        "connect_timeout",
        "gssencmode",
        "keepalives",
        "keepalives_count",
        "keepalives_idle",
        "keepalives_interval",
        "sslcert",
        "sslcompression",
        "sslcrl",
        "sslkey",
        "sslmode",
        "sslrootcert",
        "target_session_attrs",
    }
    query = urlencode([(key, value) for key, value in parse_qsl(parts.query) if key in allowed])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def apply(files: list[str]) -> None:
    selected = [Path(file) for file in files] if files else sorted(MIGRATIONS_DIR.glob("*.sql"))
    with psycopg.connect(_database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for migration in selected:
                if not migration.is_absolute():
                    migration = REPO_ROOT / migration
                statements = _extract_statements(migration.read_text())
                print(f"{migration.name}: {len(statements)} statements")
                applied = 0
                for statement in statements:
                    clean = statement.strip()
                    if not clean:
                        continue
                    cur.execute(clean)
                    applied += 1
                print(f"  applied {applied}")


def _extract_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    dollar_tag: str | None = None
    i = 0
    while i < len(sql):
        char = sql[i]
        current.append(char)
        if char == "$":
            end = sql.find("$", i + 1)
            if end != -1:
                token = sql[i : end + 1]
                tag_body = token[1:-1]
                if tag_body.replace("_", "").isalnum() or tag_body == "":
                    if dollar_tag is None:
                        dollar_tag = token
                    elif dollar_tag == token:
                        dollar_tag = None
                    for extra in sql[i + 1 : end + 1]:
                        current.append(extra)
                    i = end
        elif char == ";" and dollar_tag is None:
            statement = "".join(current).strip()
            if statement and not _comment_only(statement):
                statements.append(statement)
            current = []
        i += 1
    remainder = "".join(current).strip()
    if remainder and not _comment_only(remainder):
        statements.append(remainder)
    return statements


def _comment_only(statement: str) -> bool:
    lines = [line.strip() for line in statement.splitlines()]
    return all(not line or line.startswith("--") for line in lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply SQL migrations through DATABASE_URL")
    parser.add_argument("files", nargs="*", help="Specific migration files to apply")
    args = parser.parse_args()
    apply(args.files)
