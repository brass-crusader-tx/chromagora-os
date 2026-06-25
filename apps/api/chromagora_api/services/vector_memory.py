"""Vector memory service — optional pgvector similarity search.

Feature flag: ENABLE_VECTOR_MEMORY (default: false)
When off, only memory_artifacts CRUD works. Embeddings are no-op.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

ENABLE_VECTOR_MEMORY = os.environ.get("ENABLE_VECTOR_MEMORY", "false").lower() in ("true", "1", "yes")


def is_vector_memory_enabled() -> bool:
    """Check if vector memory feature is enabled."""
    return ENABLE_VECTOR_MEMORY


def _check_enabled() -> bool:
    """Log and return whether vector operations are available."""
    if not ENABLE_VECTOR_MEMORY:
        logger.debug("Vector memory is disabled (ENABLE_VECTOR_MEMORY=false)")
    return ENABLE_VECTOR_MEMORY


def create_artifact(
    business_id: UUID,
    title: str,
    text_content: str,
    artifact_type: str = "note",
    source_ref: str | None = None,
) -> dict[str, Any]:
    """Create a memory artifact. Works regardless of vector flag."""
    if not _check_enabled():
        logger.info("Creating memory artifact (vector flags=%s)", ENABLE_VECTOR_MEMORY)

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "business_id": str(business_id),
        "artifact_type": artifact_type,
        "title": title,
        "text_content": text_content,
        "source_ref": source_ref,
        "created_at": now,
        "updated_at": now,
    }
    resp = _table_admin("memory_artifacts").insert(data).execute()
    return resp.data[0] if resp.data else {}


def list_artifacts(business_id: UUID, artifact_type: str | None = None, limit: int = 50) -> list[dict]:
    """List memory artifacts for a business. Works regardless of vector flag."""
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    query = (
        sb.table("memory_artifacts")
        .select("id, artifact_type, title, text_content, source_ref, created_at, updated_at")
        .eq("business_id", str(business_id))
        .order("created_at", desc=True)
        .limit(limit)
    )
    if artifact_type:
        query = query.eq("artifact_type", artifact_type)

    resp = query.execute()
    return resp.data or []


def delete_artifact(artifact_id: UUID) -> bool:
    """Delete a memory artifact. Also cascades embeddings if table exists."""
    # Delete embeddings first if table exists and feature is on
    if ENABLE_VECTOR_MEMORY:
        _table_admin("memory_embeddings").delete().eq("artifact_fk", str(artifact_id)).execute()

    resp = _table_admin("memory_artifacts").delete().eq("id", str(artifact_id)).execute()
    return bool(resp.data)


def store_embedding(
    artifact_fk: UUID,
    embedding_vector: list[float],
    embedding_model: str = "text-embedding-3-small",
) -> Optional[dict]:
    """Store an embedding vector. Only works when ENABLE_VECTOR_MEMORY=true."""
    if not ENABLE_VECTOR_MEMORY:
        logger.warning("store_embedding called but ENABLE_VECTOR_MEMORY=false, skipping")
        return None

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "artifact_fk": str(artifact_fk),
        "embedding_model": embedding_model,
        "embedding_vector": embedding_vector,
        "created_at": now,
    }
    resp = _table_admin("memory_embeddings").insert(data).execute()
    return resp.data[0] if resp.data else None


def similarity_search(
    business_id: UUID,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict]:
    """Search similar embeddings using pgvector cosine distance.

    Only works when ENABLE_VECTOR_MEMORY=true and pgvector extension is installed.
    Returns empty list if feature is off.
    """
    if not ENABLE_VECTOR_MEMORY:
        logger.warning("similarity_search called but ENABLE_VECTOR_MEMORY=false, returning []")
        return []

    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    # Use Supabase raw SQL for vector similarity (RPC call preferred in production)
    resp = sb.rpc(
        "match_memory_artifacts",
        {
            "query_embedding": query_vector,
            "match_threshold": 0.5,
            "match_count": top_k,
            "p_business_id": str(business_id),
        },
    ).execute()
    return resp.data or []


def _get_supabase():
    """Get Supabase client. Late import to allow patching in tests."""
    from chromagora_api.db.base import get_supabase, get_supabase_admin
    return get_supabase()


def _table_admin(name: str):
    from chromagora_api.db.base import get_supabase_admin
    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Database not configured")
    return sb.table(name)
