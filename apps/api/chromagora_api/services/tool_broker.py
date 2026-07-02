"""Tool Broker — tool execution with policy enforcement.

For the quote follow-up loop, the handler creates its own action_proposal,
then calls request_tool_execution with the existing proposal_id.

If approval is required, a REAL approval_request is created.
If allowed, execution is triggered via the action_executor service.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_schemas.authority import PolicyDecision
from chromagora_api.services.policy_kernel import evaluate_action_policy
from chromagora_api.services.runtime_utils import parse_json_field, to_jsonable

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


def _get_supabase_admin():
    """Get Supabase client using SERVICE_ROLE_KEY for admin operations (seed scripts)."""
    return _get_supabase()


def _table_admin(name: str):
    return _get_supabase().table(name)


def _tenant_for_business(sb, business_id: UUID) -> str:
    from chromagora_api.db.tenant import get_business_tenant_id

    tenant_id = get_business_tenant_id(str(business_id), sb)
    if not tenant_id:
        raise TenantError("Business not found")
    return tenant_id


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

class TenantError(Exception):
    """Business/tenant resolution error."""
    pass


def _find_existing_approval(sb, tenant_id: str, idempotency_key: str) -> Optional[dict[str, Any]]:
    """Return an existing approval request for an idempotency key."""
    try:
        resp = (
            sb.table("approval_requests")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("idempotency_key", idempotency_key)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def request_tool_execution(
    tenant_id: Optional[UUID] = None,
    business_id: Optional[UUID] = None,
    action_proposal_id: Optional[UUID] = None,
    actor_type: str = "agent",
    actor_id: Optional[UUID] = None,
    tool_name: str = "",
    tool_action: str = "",
    tool_args_json: Optional[dict[str, Any]] = None,
    dry_run: bool = True,
    dollar_exposure: float = 0.0,
    risk_level: str = "low",
    confidence: Optional[float] = None,
    compliance_sensitive: bool = False,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Request tool execution with policy enforcement.

    Two calling modes:

    1. Legacy mode (no action_proposal_id): Creates a new ActionProposal,
       evaluates policy, and proceeds as before.

    2. Quote-follow-up mode (action_proposal_id provided): The caller
       (quote_stale_handler) has already created the ActionProposal.
       This function evaluates policy, creates a real approval_request
       if needed, and triggers execution if allowed.

    Flow:
    1. Load or create ActionProposal
    2. Evaluate policy
    3. If denied -> blocked
    4. If approval required -> create real ApprovalRequest
    5. If allowed -> execute via action_executor
    6. Return structured result
    """
    sb = _get_supabase()

    # Resolve tenant_id
    if not tenant_id and business_id:
        tenant_id_str = _tenant_for_business(sb, business_id)
        tenant_id = UUID(tenant_id_str)
    elif not tenant_id:
        return {"outcome": "failed", "error": "Cannot resolve tenant_id"}

    if not trace_id:
        trace_id = str(uuid4())

    result: dict[str, Any] = {
        "outcome": "unknown",
        "action_proposal_id": None,
        "approval_request_id": None,
        "policy_decision": None,
        "execution_result": None,
        "trace_id": trace_id,
    }

    # ── Mode 2: Existing proposal (quote follow-up path) ───────────────
    if action_proposal_id:
        try:
            resp = sb.table("action_proposals").select("*").eq("id", str(action_proposal_id)).execute()
            if not resp.data:
                return {"outcome": "failed", "error": "Action proposal not found"}
            proposal = resp.data[0]
        except Exception as exc:
            return {"outcome": "failed", "error": f"Failed to load proposal: {exc}"}

        proposal_id = action_proposal_id
        result["action_proposal_id"] = str(proposal_id)

        if not business_id:
            business_id = UUID(proposal["business_id"]) if proposal.get("business_id") else None

        action_type = proposal.get("action_type", "")
        proposal_risk = proposal.get("risk_level", "low")
        proposal_requires_approval = proposal.get("requires_approval", True)
        proposed_payload = parse_json_field(proposal.get("proposed_payload", {}), default={})

        # Evaluate policy
        policy = evaluate_action_policy(
            business_id=business_id,
            actor_type="agent",
            actor_id=UUID(proposal["proposed_by_id"]) if proposal.get("proposed_by_id") else None,
            action_type=action_type,
            target_system="crm",
            autonomy_level_requested=2,
            dollar_exposure=0.0,
            risk_level=proposal_risk,
            confidence=None,
            compliance_sensitive=False,
            tenant_id=tenant_id,
        )

        result["policy_decision"] = policy.model_dump(mode="json")
        effective_requires_approval = policy.requires_approval or proposal_requires_approval

        # Persist policy decision on the proposal
        proposal_status = "blocked" if policy.denied else (
            "approval_required" if effective_requires_approval else "approved"
        )
        try:
            sb.table("action_proposals").update({
                "status": proposal_status,
                "policy_decision_json": to_jsonable(policy),
                "requires_approval": effective_requires_approval,
                "policy_decision_id": str(uuid4()),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(proposal_id)).execute()
        except Exception as exc:
            logger.warning("Failed to update proposal with policy decision: %s", exc)

        # Blocked
        if policy.denied:
            result["outcome"] = "blocked"
            _persist_execution(
                str(tenant_id), business_id, proposal_id, None, action_type, action_type,
                proposed_payload, "blocked", policy.decision_notes, "agent", None,
                trace_id=trace_id,
            )
            return result

        # Approval required -> create or reuse a REAL approval request
        if effective_requires_approval:
            approval_id = uuid4()
            approval_idempotency_key = f"approval.required:{proposal_id}"
            existing_approval = _find_existing_approval(sb, str(tenant_id), approval_idempotency_key)
            if existing_approval:
                result["outcome"] = "approval_required"
                result["approval_request_id"] = existing_approval.get("id")
                return result

            try:
                title = proposal.get("title", "Action requires approval")
                reason = proposal.get("reason", "")
                sb.table("approval_requests").insert({
                    "id": str(approval_id),
                    "tenant_id": str(tenant_id),
                    "business_id": str(business_id) if business_id else None,
                    "action_proposal_id": str(proposal_id),
                    "status": "pending",
                    "requested_by_type": "agent",
                    "requested_by_id": proposal.get("proposed_by_id"),
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                    "title": title,
                    "summary": reason,
                    "draft_payload": to_jsonable(proposed_payload),
                    "risk_level": proposal_risk,
                    "agent_run_id": proposal.get("agent_run_id"),
                    "idempotency_key": approval_idempotency_key,
                    "trace_id": trace_id,
                }).execute()
            except Exception as exc:
                existing_approval = _find_existing_approval(sb, str(tenant_id), approval_idempotency_key)
                if existing_approval:
                    result["outcome"] = "approval_required"
                    result["approval_request_id"] = existing_approval.get("id")
                    return result
                logger.error("Failed to create approval request: %s", exc)
                return {"outcome": "failed", "error": f"Approval request creation failed: {exc}"}

            result["outcome"] = "approval_required"
            result["approval_request_id"] = str(approval_id)

            # Emit approval.required event
            try:
                sb.table("events").insert({
                    "id": str(uuid4()),
                    "tenant_id": str(tenant_id),
                    "business_id": str(business_id) if business_id else None,
                    "event_type": "approval.required",
                    "source_type": "tool_broker",
                    "source_id": str(proposal_id),
                    "entity_type": "action_proposal",
                    "entity_id": str(proposal_id),
                    "payload_json": {
                        "proposal_id": str(proposal_id),
                        "approval_request_id": str(approval_id),
                        "action_type": action_type,
                    },
                    "idempotency_key": f"approval.required.event:{proposal_id}",
                    "trace_id": trace_id,
                }).execute()
            except Exception:
                pass

            _persist_execution(
                str(tenant_id), business_id, proposal_id, approval_id, action_type, action_type,
                proposed_payload, "approval_required", policy.decision_notes, "agent", None,
                trace_id=trace_id, idempotency_key=f"approval.required.ledger:{proposal_id}",
            )
            return result

        # Allowed -> execute immediately
        try:
            from chromagora_api.services.action_executor import execute_approved_action
            exec_result = execute_approved_action(
                action_proposal_id=proposal_id,
                trace_id=trace_id,
            )
            result["execution_result"] = exec_result
            if exec_result.get("status") == "success":
                result["outcome"] = "allowed_executed"
            else:
                result["outcome"] = "failed"
                result["error"] = exec_result.get("error", "Execution failed")
        except Exception as exc:
            logger.error("Execution failed: %s", exc)
            result["outcome"] = "failed"
            result["error"] = str(exc)

        return result

    # ── Mode 1: Legacy path (no existing proposal) ─────────────────────
    if not tool_args_json:
        tool_args_json = {}

    result["tool_name"] = tool_name
    result["tool_action"] = tool_action

    if not business_id:
        return {"outcome": "failed", "error": "business_id required"}

    # 1. Look up ToolDefinition
    tool_def = _lookup_tool(tool_name, tool_action)
    if not tool_def:
        result["outcome"] = "blocked"
        result["errors"] = [f"Tool not found: {tool_name}/{tool_action}"]
        return result

    tool_def_id = tool_def["id"]

    # 2. Check BusinessToolPermission
    permission = _check_tool_permission(business_id, tool_def_id)
    if not permission:
        if tool_def.get("is_external_action"):
            result["outcome"] = "blocked"
            result["errors"] = [f"No permission for external tool: {tool_name}"]
            return result

    # 3. Create ActionProposal
    proposal_id = uuid4()
    result["action_proposal_id"] = str(proposal_id)

    # 4. Evaluate policy
    tool_autonomy = tool_def.get("autonomy_level_required_default", 1)
    permission_max = permission.get("max_autonomy_level", tool_autonomy) if permission else tool_autonomy
    effective_autonomy = min(tool_autonomy, permission_max)

    approval_override = permission.get("requires_approval_override") if permission else None
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
        tenant_id=tenant_id,
    )

    result["policy_decision"] = policy.model_dump(mode="json")
    _persist_proposal(
        tenant_id=str(tenant_id),
        business_id=business_id,
        proposal_id=proposal_id,
        tool_name=tool_name,
        tool_action=tool_action,
        tool_args=tool_args_json,
        actor_type=actor_type,
        actor_id=actor_id,
        risk_level=risk_level,
        autonomy_level=effective_autonomy,
        status="blocked" if policy.denied else (
            "approval_required" if policy.requires_approval or requires_approval else "approved"
        ),
        policy=policy,
        trace_id=trace_id,
    )

    # 5. If denied -> blocked
    if policy.denied:
        result["outcome"] = "blocked"
        if sb:
            _persist_execution(
                str(tenant_id), business_id, proposal_id, None, tool_name, tool_action,
                tool_args_json, "blocked", policy.decision_notes, actor_type, actor_id,
                trace_id=trace_id,
            )
        return result

    # 6. If approval required -> create real ApprovalRequest
    if policy.requires_approval or requires_approval:
        approval_id = uuid4()
        try:
            sb.table("approval_requests").insert({
                "id": str(approval_id),
                "tenant_id": str(tenant_id),
                "business_id": str(business_id),
                "action_proposal_id": str(proposal_id),
                "status": "pending",
                "requested_by_type": actor_type,
                "requested_by_id": str(actor_id) if actor_id else None,
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "title": f"{tool_name}.{tool_action}",
                "risk_level": risk_level,
                "idempotency_key": f"approval.required:{proposal_id}",
                "trace_id": trace_id,
            }).execute()
            result["approval_request_id"] = str(approval_id)
        except Exception as exc:
            logger.warning("Failed to create approval request: %s", exc)

        result["outcome"] = "approval_required"
        if sb:
            _persist_execution(
                str(tenant_id), business_id, proposal_id, approval_id, tool_name, tool_action,
                tool_args_json, "approval_required", policy.decision_notes, actor_type, actor_id,
                trace_id=trace_id,
            )
        return result

    # 7. If allowed -> execute via action_executor
    if dry_run:
        result["outcome"] = "allowed_executed"
        result["execution_result"] = {
            "dry_run": True,
            "tool": tool_name,
            "action": tool_action,
            "args_preview": {k: str(v)[:100] for k, v in tool_args_json.items()},
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        if sb:
            _persist_execution(
                str(tenant_id), business_id, proposal_id, None, tool_name, tool_action,
                tool_args_json, "dry_run", "Dry run executed successfully",
                actor_type, actor_id, trace_id=trace_id,
            )
        return result

    # Real execution
    try:
        from chromagora_api.services.action_executor import execute_approved_action
        exec_result = execute_approved_action(
            action_proposal_id=proposal_id,
            trace_id=trace_id,
        )
        result["execution_result"] = exec_result
        if exec_result.get("status") == "success":
            result["outcome"] = "allowed_executed"
        else:
            result["outcome"] = "failed"
            result["error"] = exec_result.get("error", "Execution failed")
    except Exception as exc:
        result["outcome"] = "failed"
        result["error"] = str(exc)

    return result


def _persist_proposal(
    tenant_id: str,
    business_id: UUID,
    proposal_id: UUID,
    tool_name: str,
    tool_action: str,
    tool_args: dict,
    actor_type: str,
    actor_id: Optional[UUID],
    risk_level: str,
    autonomy_level: int,
    status: str,
    policy: PolicyDecision,
    trace_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> None:
    """Persist the action proposal that ledger entries reference."""
    try:
        _table_admin("action_proposals").insert({
            "id": str(proposal_id),
            "tenant_id": tenant_id,
            "business_id": str(business_id),
            "proposed_by_type": actor_type,
            "proposed_by_id": str(actor_id) if actor_id else None,
            "action_type": tool_action,
            "title": f"{tool_name}.{tool_action}",
            "description": f"Tool execution request for {tool_name}/{tool_action}",
            "target_system": tool_name,
            "proposed_payload": to_jsonable(_redact_args(tool_args)),
            "confidence": None,
            "risk_level": risk_level,
            "autonomy_level_required": autonomy_level,
            "status": status,
            "policy_decision_json": to_jsonable(policy),
            "trace_id": trace_id or str(proposal_id),
        }).execute()
    except Exception as exc:
        logger.warning("Failed to persist action proposal: %s", exc)


def _persist_execution(
    tenant_id: str,
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
    trace_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> None:
    """Persist action execution to the ledger."""
    try:
        _table_admin("action_executions").insert({
            "tenant_id": tenant_id,
            "business_id": str(business_id),
            "action_proposal_id": str(proposal_id),
            "approval_request_id": str(approval_id) if approval_id else None,
            "tool_name": tool_name,
            "tool_action": tool_action,
            "tool_args_hash": _hash_args(tool_args),
            "tool_args_redacted": to_jsonable(_redact_args(tool_args)),
            "idempotency_key": idempotency_key,
            "result_status": result_status,
            "error_message": notes if result_status == "blocked" else None,
            "executed_by_type": actor_type,
            "executed_by_id": str(actor_id) if actor_id else None,
            "reversibility": "reversible",
            "trace_id": trace_id or str(proposal_id),
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
            "output_schema": {"type": "object", "properties": {"success": {"type": "boolean"}}},
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
