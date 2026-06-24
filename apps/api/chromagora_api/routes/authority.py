"""Authority Envelope CRUD routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_schemas.authority import (
    AuthorityEnvelopeCreate,
    AuthorityEnvelopeResponse,
    AuthorityEnvelopeUpdate,
)

router = APIRouter(prefix="/businesses/{business_id}/authority", tags=["authority"])


@router.get("", response_model=list[AuthorityEnvelopeResponse])
async def list_authority_envelopes(business_id: UUID):
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("authority_envelopes")
        .select("*")
        .eq("business_id", str(business_id))
        .execute()
    )
    return resp.data or []


@router.post("", response_model=AuthorityEnvelopeResponse, status_code=status.HTTP_201_CREATED)
async def create_authority_envelope(business_id: UUID, body: AuthorityEnvelopeCreate):
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    payload = body.model_dump()
    payload["business_id"] = str(business_id)
    resp = sb.table("authority_envelopes").insert(payload).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create envelope")
    return resp.data[0]


@router.get("/{envelope_id}", response_model=AuthorityEnvelopeResponse)
async def get_authority_envelope(business_id: UUID, envelope_id: UUID):
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("authority_envelopes")
        .select("*")
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Envelope not found")
    return resp.data[0]


@router.patch("/{envelope_id}", response_model=AuthorityEnvelopeResponse)
async def update_authority_envelope(
    business_id: UUID,
    envelope_id: UUID,
    body: AuthorityEnvelopeUpdate,
):
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = "now()"
    resp = (
        sb.table("authority_envelopes")
        .update(update_data)
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Envelope not found")
    return resp.data[0]


@router.delete("/{envelope_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authority_envelope(business_id: UUID, envelope_id: UUID):
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("authority_envelopes")
        .delete()
        .eq("id", str(envelope_id))
        .eq("business_id", str(business_id))
        .execute()
    )
    return None
