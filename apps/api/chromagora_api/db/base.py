"""Database base utilities.

All database access uses Supabase via supabase-py.
No SQLAlchemy, no Alembic, no ORM for migrations.
Migrations are hand-written DDL in ../../migrations/.
"""

from supabase import Client

__all__ = ["get_supabase", "get_supabase_admin"]

# Import from core.supabase to avoid circular imports
# These are re-exported here for backward compatibility
from chromagora_api.core.supabase import get_supabase, get_supabase_admin  # noqa: F401


def execute_query(client: Client, table: str, filters: dict | None = None, select: str = "*", limit: int | None = None):
    """Build and execute a Supabase query with optional filters."""
    query = client.from_(table).select(select)
    if filters:
        for key, value in filters.items():
            if value is not None:
                query = query.eq(key, value)
    if limit:
        query = query.limit(limit)
    return query.execute()


def insert_record(client: Client, table: str, data: dict):
    """Insert a single record and return the result."""
    return client.from_(table).insert(data).execute()


def update_record(client: Client, table: str, id: str, data: dict):
    """Update a record by ID."""
    return client.from_(table).update(data).eq("id", id).execute()


def delete_record(client: Client, table: str, id: str):
    """Delete a record by ID."""
    return client.from_(table).delete().eq("id", id).execute()
