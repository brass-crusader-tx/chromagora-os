"""Authority Envelope CRUD routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_backend_supabase, get_business_tenant_id
from chromagora_schemas.authority import (
    AuthorityEnvelopeCreate,
    AuthorityEnvelopeResponse,
    AuthorityEnvelopeUpdate,
)

router = APIRouter(prefix="/businesses/{business_id}/authority", tags=["authority"])


def _coerce_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _normalize_envelope(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["conditions_json"] = _coerce_json_object(row.get("conditions_json"))
    row["forbidden_conditions_json"] = _coerce_json_object(
        row.get("forbidden_conditions_json")
    )
    return row


def _scoped_client(business_id: UUID):
    try:
        sb = get_backend_supabase()
        if not get_business_tenant_id(str(business_id), sb):
            raise HTTPException(status_code=404, detail="Business not found")
        return sb
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("", response_model=list[AuthorityEnvelopeResponse])
async def list_authority_envelopes(business_id: UUID):
    sb = _scoped_client(business_id)
    resp = (
        sb.table("authority_envelopes")
        .select("*")
        .eq("business_id", str(business_id))
        .execute()
    )
    return [_normalize_envelope(row) for row in (resp.data or [])]


@router.post("", response_model=AuthorityEnvelopeResponse, status_code=status.HTTP_201_CREATED)
async def create_authority_envelope(business_id: UUID, body: AuthorityEnvelopeCreate):
    sb = _scoped_client(business_id)
    payload = body.model_dump(mode="json")
    payload["business_id"] = str(business_id)
    resp = sb.table("authority_envelopes").insert(payload).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create envelope")
    return _normalize_envelope(resp.data[0])


@router.get("/{envelope_id}", response_model=AuthorityEnvelopeResponse)
async def get_authority_envelope(business_id: UUID, envelope_id: UUID):
    sb = _scoped_client(business_id)
    resp = (
        sb.table("authority_envelopes")
        .select("*")
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Envelope not found")
    return _normalize_envelope(resp.data[0])


@router.patch("/{envelope_id}", response_model=AuthorityEnvelopeResponse)
async def update_authority_envelope(
    business_id: UUID,
    envelope_id: UUID,
    body: AuthorityEnvelopeUpdate,
):
    sb = _scoped_client(business_id)
    update_data = body.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = (
        sb.table("authority_envelopes")
        .update(update_data)
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Envelope not found")
    return _normalize_envelope(resp.data[0])


@router.delete("/{envelope_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authority_envelope(business_id: UUID, envelope_id: UUID):
    sb = _scoped_client(business_id)
    resp = (
        sb.table("authority_envelopes")
        .delete()
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    return None
