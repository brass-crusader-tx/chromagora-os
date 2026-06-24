"""Tool Broker — dry-run tool execution with policy enforcement."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_schemas.authority import PolicyDecision
from chromagora_schemas.tools import ToolDefinition
from chromagora_api.services.policy_kernel import evaluate_action_policy

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db import get_supabase
    return get_supabase()


def _get_supabase_admin():
    """Get Supabase client using SERVICE_ROLE_KEY for admin operations (seed scripts)."""
    from chromagora_api.db import get_supabase_admin
    return get_supabase_admin()


# ---------------------------------------------------------------------------
# Tool registry helpers
# ---------------------------------------------------------------------------

def _lookup_tool(tool_name: str, tool_action: str) -> Optional[dict]:
    """Look up a ToolDefinition by name and action."""
    sb = _get_supabase()
    if not sb:
        return None
    resp = (
        sb.table("tool_definitions")
        .select("*")
        .eq("name", tool_name)
        .eq("tool_action", tool_action)
        .eq("is_active", True)
        .execute()
    )
    return resp.data[0] if resp.data else None


def _check_tool_permission(business_id: UUID, tool_definition_id: str) -> Optional[dict]:
    """Check BusinessToolPermission for a business + tool combo."""
    sb = _get_supabase()
    if not sb:
        return None
    resp = (
        sb.table("business_tool_permissions")
        .select("*")
        .eq("business_id", str(business_id))
        .eq("tool_definition_id", str(tool_definition_id))
        .eq("is_enabled", True)
        .execute()
    )
    return resp.data[0] if resp.data else None


def _redact_args(tool_args: dict) -> dict:
    """Redact sensitive fields before storage."""
    sensitive_keys = {"password", "token", "secret", "api_key", "authorization", "credit_card"}
    redacted = {}
    for key, value in tool_args.items():
        if key.lower() in sensitive_keys:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted


def _hash_args(tool_args: dict) -> str:
    """Create a hash of tool args for idempotency."""
    canonical = json.dumps(tool_args, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def request_tool_execution(
    business_id: UUID,
    actor_type: str,
    actor_id: Optional[UUID],
    tool_name: str,
    tool_action: str,
    tool_args_json: dict[str, Any],
    dry_run: bool = True,
    dollar_exposure: float = 0.0,
    risk_level: str = "low",
    confidence: Optional[float] = None,
    compliance_sensitive: bool = False,
) -> dict[str, Any]:
    """Request tool execution — always dry-run first.

    Flow:
    1. Look up ToolDefinition
    2. Check BusinessToolPermission
    3. Create ActionProposal
    4. Evaluate policy
    5. If denied -> blocked
    6. If approval required -> ApprovalRequest
    7. If allowed and dry_run -> ActionExecution with status "dry_run"
    8. Emit events
    9. Return structured result
    """
    sb = _get_supabase()
    result: dict[str, Any] = {
        "tool_name": tool_name,
        "tool_action": tool_action,
        "dry_run": dry_run,
        "status": "unknown",
        "action_proposal_id": None,
        "policy_decision": None,
        "execution_result": None,
        "events_emitted": [],
        "errors": [],
    }

    # 1. Look up ToolDefinition
    tool_def = _lookup_tool(tool_name, tool_action)
    if not tool_def:
        result["status"] = "blocked"
        result["errors"].append(f"Tool not found: {tool_name}/{tool_action}")
        return result

    tool_def_id = tool_def["id"]

    # 2. Check BusinessToolPermission
    permission = _check_tool_permission(business_id, tool_def_id)
    if not permission:
        # No permission record — default to blocked for external actions
        if tool_def.get("is_external_action"):
            result["status"] = "blocked"
            result["errors"].append(
                f"No permission for external tool: {tool_name}"
            )
            return result

    # 3. Create ActionProposal (persist for audit trail)
    proposal_id = uuid4()
    result["action_proposal_id"] = str(proposal_id)

    # 4. Evaluate policy
    # Determine effective autonomy level
    tool_autonomy = tool_def.get("autonomy_level_required_default", 1)
    permission_max = permission.get("max_autonomy_level", 1)
    effective_autonomy = min(tool_autonomy, permission_max)

    # Determine effective approval requirement
    approval_override = permission.get("requires_approval_override")
    if approval_override is not None:
        requires_approval = approval_override
    else:
        requires_approval = tool_def.get("risk_level_default") in ("medium", "high")

    policy = evaluate_action_policy(
        business_id=business_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action_type=tool_action,
        target_system=tool_def.get("target_system", tool_name),
        autonomy_level_requested=effective_autonomy,
        dollar_exposure=dollar_exposure,
        risk_level=risk_level,
        confidence=confidence,
        compliance_sensitive=compliance_sensitive,
    )

    result["policy_decision"] = policy.model_dump(mode="json")

    # 5. If denied -> blocked
    if policy.denied:
        result["status"] = "blocked"
        if sb:
            _persist_execution(
                business_id, proposal_id, None, tool_name, tool_action,
                tool_args_json, "blocked", policy.decision_notes, actor_type, actor_id,
            )
        return result

    # 6. If approval required -> ApprovalRequest
    if policy.requires_approval or requires_approval:
        result["status"] = "approval_required"
        if sb:
            _persist_execution(
                business_id, proposal_id, None, tool_name, tool_action,
                tool_args_json, "approval_required", policy.decision_notes, actor_type, actor_id,
            )
        return result

    # 7. If allowed and dry_run -> execute dry_run
    if dry_run:
        result["status"] = "dry_run"
        result["execution_result"] = {
            "mock": True,
            "tool": tool_name,
            "action": tool_action,
            "args_preview": {k: str(v)[:100] for k, v in tool_args_json.items()},
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        result["events_emitted"] = [
            {"event_type": "action.proposed", "source_type": "tool_broker"},
            {"event_type": "action.approved", "source_type": "tool_broker"},
            {"event_type": "action.executed", "source_type": "tool_broker"},
        ]
        if sb:
            _persist_execution(
                business_id, proposal_id, None, tool_name, tool_action,
                tool_args_json, "dry_run", "Dry run executed successfully",
                actor_type, actor_id,
            )
        return result

    # 8. Real execution (not implemented yet — always dry-run)
    result["status"] = "not_implemented"
    result["errors"].append("Real tool execution not yet implemented. Use dry_run=True.")
    return result


def _persist_execution(
    business_id: UUID,
    proposal_id: UUID,
    approval_id: Optional[UUID],
    tool_name: str,
    tool_action: str,
    tool_args: dict,
    result_status: str,
    notes: str,
    actor_type: str,
    actor_id: Optional[UUID],
) -> None:
    """Persist action execution to the ledger."""
    sb = _get_supabase()
    if not sb:
        return
    try:
        sb.table("action_executions").insert({
            "tenant_id": "00000000-0000-0000-0000-000000000000",  # filled by trigger
            "business_id": str(business_id),
            "action_proposal_id": str(proposal_id),
            "approval_request_id": str(approval_id) if approval_id else None,
            "tool_name": tool_name,
            "tool_action": tool_action,
            "tool_args_redacted": _redact_args(tool_args),
            "result_status": result_status,
            "error_message": notes if result_status == "blocked" else None,
            "executed_by_type": actor_type,
            "executed_by_id": str(actor_id) if actor_id else None,
            "reversibility": "reversible",
            "trace_id": str(proposal_id),  # for correlation
        }).execute()
    except Exception as exc:
        logger.warning("Failed to persist execution: %s", exc)


# ---------------------------------------------------------------------------
# Tool registration helpers
# ---------------------------------------------------------------------------

def register_tool_definition(
    name: str,
    description: str,
    target_system: str,
    tool_action: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    risk_level: str = "low",
    autonomy_level: int = 1,
    is_external: bool = False,
) -> Optional[str]:
    """Register a new tool definition. Returns the tool ID."""
    sb = _get_supabase_admin()
    if not sb:
        sb = _get_supabase()
    if not sb:
        return None

    payload = {
        "name": name,
        "description": description,
        "target_system": target_system,
        "tool_action": tool_action,
        "input_schema_json": input_schema or {},
        "output_schema_json": output_schema or {},
        "risk_level_default": risk_level,
        "autonomy_level_required_default": autonomy_level,
        "is_external_action": is_external,
    }
    resp = sb.table("tool_definitions").upsert(payload).execute()
    if resp.data:
        return resp.data[0]["id"]
    return None


def seed_dev_tools() -> list[str]:
    """Seed mock development tools. Returns list of tool IDs."""
    tools = [
        {
            "name": "crm.create_lead",
            "description": "Create a new lead in the CRM",
            "target_system": "crm",
            "tool_action": "create_lead",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"lead_id": {"type": "string"}}},
            "risk_level": "low",
            "autonomy_level": 3,
            "is_external": False,
        },
        {
            "name": "crm.update_lead_status",
            "description": "Update lead status",
            "target_system": "crm",
            "tool_action": "update_lead_status",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"success": {"type": "boolean"}}}},
            "risk_level": "low",
            "autonomy_level": 3,
            "is_external": False,
        },
        {
            "name": "crm.create_followup_task",
            "description": "Create a follow-up task for a lead",
            "target_system": "crm",
            "tool_action": "create_followup_task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "task_type": {"type": "string"},
                    "due_date": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"task_id": {"type": "string"}}},
            "risk_level": "low",
            "autonomy_level": 3,
            "is_external": False,
        },
        {
            "name": "reputation.queue_review_request",
            "description": "Queue a customer review request",
            "target_system": "reputation",
            "tool_action": "queue_review_request",
            "input_schema": {
                "type": "object",
                "properties": {
                    "business_id": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "customer_email": {"type": "string"},
                    "job_summary": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"request_id": {"type": "string"}}},
            "risk_level": "medium",
            "autonomy_level": 4,
            "is_external": False,
        },
        {
            "name": "procurement.create_opportunity_note",
            "description": "Create a procurement opportunity note",
            "target_system": "procurement",
            "tool_action": "create_opportunity_note",
            "input_schema": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "amount": {"type": "number"},
                    "description": {"type": "string"},
                    "deadline": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"note_id": {"type": "string"}}},
            "risk_level": "medium",
            "autonomy_level": 2,
            "is_external": False,
        },
        {
            "name": "seo.create_content_draft",
            "description": "Create an SEO content draft",
            "target_system": "seo",
            "tool_action": "create_content_draft",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "word_count": {"type": "integer"},
                },
            },
            "output_schema": {"type": "object", "properties": {"draft_id": {"type": "string"}}},
            "risk_level": "low",
            "autonomy_level": 2,
            "is_external": False,
        },
        {
            "name": "email.create_draft",
            "description": "Create an email draft",
            "target_system": "email",
            "tool_action": "create_draft",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "template_id": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"draft_id": {"type": "string"}}},
            "risk_level": "medium",
            "autonomy_level": 2,
            "is_external": False,
        },
        {
            "name": "supplier.create_supplier_note",
            "description": "Create a supplier note",
            "target_system": "supplier",
            "tool_action": "create_supplier_note",
            "input_schema": {
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "string"},
                    "note": {"type": "string"},
                    "rating": {"type": "integer"},
                },
            },
            "output_schema": {"type": "object", "properties": {"note_id": {"type": "string"}}},
            "risk_level": "low",
            "autonomy_level": 3,
            "is_external": False,
        },
        {
            "name": "message.create_draft",
            "description": "Create a message draft (SMS/notification)",
            "target_system": "message",
            "tool_action": "create_draft",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "recipient": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            "output_schema": {"type": "object", "properties": {"draft_id": {"type": "string"}}},
            "risk_level": "medium",
            "autonomy_level": 4,
            "is_external": False,
        },
    ]

    ids = []
    for tool in tools:
        tool_id = register_tool_definition(**tool)
        if tool_id:
            ids.append(tool_id)

    return ids
