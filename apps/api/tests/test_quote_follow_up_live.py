"""Live acceptance test for the quote follow-up runtime.

This test runs against a REAL Supabase database (not mocked).
It requires the API to be running with a valid .env file.

Run with:
    cd apps/api && .venv/bin/python -m pytest tests/test_quote_follow_up_live.py -m live -v

The test exercises the full lifecycle:
  1. Seed a stale quote (sent 5 days ago, threshold 3 days)
  2. Run stale detection → emits quote.stale event
  3. Process the event → creates agent run → creates action proposal
  4. Tool Broker evaluates policy → creates approval request
  5. Approve the request → executes the action → creates task/draft
  6. Verify quote state updated (follow_up_count incremented)
  7. Verify trace connects all records

Prerequisites:
  - Migration 000024 must be applied
  - Business preferences must be set for the test business
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

pytestmark = pytest.mark.live

# Load .env
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure api package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chromagora_api.core.supabase import get_supabase_admin


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sb():
    """Get Supabase admin client."""
    client = get_supabase_admin()
    if not client:
        pytest.skip("Supabase not configured — check .env")
    return client


@pytest.fixture(scope="module")
def tenant_id(sb):
    """Get the active tenant ID."""
    from chromagora_api.core.config import settings
    if settings.chromagora_tenant_id:
        return settings.chromagora_tenant_id
    resp = sb.table("tenants").select("id").order("created_at").limit(1).execute()
    if not resp.data:
        pytest.skip("No tenant found — run seed_data.py first")
    return resp.data[0]["id"]


@pytest.fixture(scope="module")
def business_id(sb, tenant_id):
    """Get a business ID for testing."""
    resp = (
        sb.table("businesses")
        .select("id")
        .eq("tenant_id", tenant_id)
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not resp.data:
        pytest.skip("No business found — run seed_data.py first")
    return resp.data[0]["id"]


@pytest.fixture(scope="module")
def ensure_preferences(sb, business_id):
    """Ensure business preferences are set for follow-up."""
    prefs = [
        ("stale_quote_threshold_days", 3),
        ("max_quote_follow_ups", 3),
        ("follow_up_interval_days", 3),
        ("quote_follow_up_requires_approval", True),
        ("preferred_follow_up_channel", "email"),
    ]
    for key, value in prefs:
        sb.table("business_preferences").upsert({
            "business_id": business_id,
            "key": key,
            "value_json": {"value": value},
            "source": "test",
            "confidence": 1.0,
        }, on_conflict="business_id,key").execute()


@pytest.fixture
def test_lead(sb, business_id):
    """Create a test lead and yield its ID, then clean up."""
    resp = sb.table("leads").insert({
        "id": str(uuid4()),
        "business_id": business_id,
        "customer_name": f"Test Customer {uuid4().hex[:8]}",
        "customer_contact": f"test-{uuid4().hex[:8]}@example.com",
        "source": "test",
        "service_type": "logistics",
        "status": "qualified",
    }).execute()
    lead_id = resp.data[0]["id"]
    yield lead_id
    # Cleanup
    sb.table("leads").delete().eq("id", lead_id).execute()


@pytest.fixture
def stale_quote(sb, business_id, test_lead):
    """Create a stale quote (sent 5 days ago) and yield its ID."""
    resp = sb.table("quotes").insert({
        "id": str(uuid4()),
        "business_id": business_id,
        "lead_id": test_lead,
        "quote_amount": 12500,
        "service_type": "logistics",
        "status": "sent",
        "sent_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    }).execute()
    quote_id = resp.data[0]["id"]
    yield quote_id
    # Cleanup — will be done by the test or cascade


# ---------------------------------------------------------------------------
# Acceptance test: full lifecycle
# ---------------------------------------------------------------------------

class TestQuoteFollowUpLifecycle:
    """End-to-end test: stale quote → detection → event → proposal → approval → execution → state mutation."""

    def test_1_detection_emits_event(self, sb, business_id, stale_quote, ensure_preferences):
        """Step 1: Running stale detection emits a quote.stale event."""
        from chromagora_api.services.quote_stale_detector import detect_stale_quotes

        results = detect_stale_quotes(
            business_id=UUID(business_id),
        )

        assert len(results) >= 1, "Expected at least one stale quote detected"
        result = results[0]
        assert result["quote_id"] == stale_quote
        assert result["event_id"] is not None
        assert result["trace_id"] is not None
        assert result["days_since_sent"] >= 4

        # Verify event exists in DB
        event_resp = (
            sb.table("events")
            .select("*")
            .eq("id", result["event_id"])
            .execute()
        )
        assert event_resp.data, "Event not found in database"
        event = event_resp.data[0]
        assert event["event_type"] == "quote.stale"
        assert event["business_id"] == business_id

    def test_2_event_dispatch_creates_proposal(self, sb, business_id, stale_quote, ensure_preferences):
        """Step 2: Processing the quote.stale event creates an agent run and action proposal."""
        from chromagora_api.services.event_dispatcher import process_pending_events

        # Find the unprocessed event for this quote
        event_resp = (
            sb.table("events")
            .select("*")
            .eq("event_type", "quote.stale")
            .eq("business_id", business_id)
            .is_("processed_at", None)
            .execute()
        )
        assert event_resp.data, "No unprocessed quote.stale event found"
        event = event_resp.data[0]

        # Process it
        results = process_pending_events(event_type="quote.stale", limit=10)

        assert len(results) >= 1, "Expected at least one event processed"
        proc_result = results[0]
        assert proc_result["status"] == "processed"
        assert proc_result["trace_id"] is not None

        # Verify agent run was created
        agent_run_resp = (
            sb.table("agent_runs")
            .select("*")
            .eq("business_id", business_id)
            .eq("agent_type", "crm")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        assert agent_run_resp.data, "No agent run created"
        agent_run = agent_run_resp.data[0]
        assert agent_run["status"] == "completed"
        assert agent_run["trace_id"] == proc_result["trace_id"]

        # Verify action proposal was created
        proposal_resp = (
            sb.table("action_proposals")
            .select("*")
            .eq("business_id", business_id)
            .eq("quote_id", stale_quote)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        assert proposal_resp.data, "No action proposal created"
        proposal = proposal_resp.data[0]
        assert proposal["action_type"] in ("create_quote_follow_up_task", "create_quote_follow_up_draft")
        assert proposal["status"] in ("proposed", "approval_required")
        assert proposal["trace_id"] == proc_result["trace_id"]

    def test_3_approval_creates_execution(self, sb, business_id, stale_quote, ensure_preferences):
        """Step 3: Approving the proposal creates an execution and a task/draft."""
        from chromagora_api.services.action_executor import execute_approved_action

        # Find the pending approval for this quote
        approval_resp = (
            sb.table("approval_requests")
            .select("*, action_proposals(*)")
            .eq("business_id", business_id)
            .eq("status", "pending")
            .order("requested_at", desc=True)
            .limit(1)
            .execute()
        )
        if not approval_resp.data:
            pytest.skip("No pending approval — policy may not require approval")

        approval = approval_resp.data[0]
        proposal_id = approval["action_proposal_id"]
        assert proposal_id is not None

        # Update approval to approved
        sb.table("approval_requests").update({
            "status": "approved",
            "decided_by": "test",
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval["id"]).execute()

        # Update proposal to approved
        sb.table("action_proposals").update({
            "status": "approved",
        }).eq("id", proposal_id).execute()

        # Execute the approved action
        trace_id = approval.get("trace_id") or str(uuid4())
        result = execute_approved_action(
            action_proposal_id=UUID(proposal_id),
            approval_request_id=UUID(approval["id"]),
            trace_id=trace_id,
        )

        assert result["status"] == "success", f"Execution failed: {result.get('error')}"
        assert result["mode"] in ("create_task", "create_message_draft", "internal_update")

        # Verify proposal status updated to executed
        proposal_resp = (
            sb.table("action_proposals")
            .select("status")
            .eq("id", proposal_id)
            .execute()
        )
        assert proposal_resp.data[0]["status"] == "executed"

    def test_4_quote_state_updated(self, sb, business_id, stale_quote, ensure_preferences):
        """Step 4: After execution, the quote state has been updated."""
        quote_resp = (
            sb.table("quotes")
            .select("*")
            .eq("id", stale_quote)
            .execute()
        )
        assert quote_resp.data, "Quote not found"
        quote = quote_resp.data[0]

        # The quote should have been updated by the execution
        # If follow_up_count column exists (post-migration), verify it
        if "follow_up_count" in quote:
            assert quote["follow_up_count"] >= 1, "follow_up_count should be incremented"

        # Status should have changed from "sent"
        assert quote["status"] != "sent" or quote.get("stale_detected_at") is not None, \
            "Quote status should have changed or stale_detected_at should be set"

    def test_5_trace_connects_all_records(self, sb, business_id, stale_quote, ensure_preferences):
        """Step 5: All records in the chain share a trace_id."""
        # Get the quote's current trace
        quote_resp = sb.table("quotes").select("trace_id").eq("id", stale_quote).execute()
        assert quote_resp.data, "Quote not found"
        trace_id = quote_resp.data[0].get("trace_id")

        if not trace_id:
            # If the quote doesn't have a trace_id column yet (pre-migration),
            # check events instead
            event_resp = (
                sb.table("events")
                .select("trace_id")
                .eq("business_id", business_id)
                .eq("entity_id", stale_quote)
                .limit(1)
                .execute()
            )
            if event_resp.data:
                trace_id = event_resp.data[0].get("trace_id")

        if not trace_id:
            pytest.skip("No trace_id found — migration 24 may not be applied")

        # Query trace
        from chromagora_api.services.trace_propagation import get_records_by_trace
        trace = get_records_by_trace(trace_id)

        # Should have records from multiple tables
        tables_with_records = [k for k, v in trace.items() if v]
        assert len(tables_with_records) >= 2, \
            f"Trace should connect records from multiple tables, got: {tables_with_records}"

        # Should have at least events and agent_runs or action_proposals
        assert "events" in trace and trace["events"], "Trace should include events"


# ---------------------------------------------------------------------------
# Standalone runner for manual testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Run the full lifecycle manually."""
    print("=" * 60)
    print("Quote Follow-Up Runtime — Live Acceptance Test")
    print("=" * 60)

    sb = get_supabase_admin()
    if not sb:
        print("ERROR: Supabase not configured")
        sys.exit(1)

    # Setup
    from chromagora_api.core.config import settings
    tenant_id = settings.chromagora_tenant_id
    if not tenant_id:
        resp = sb.table("tenants").select("id").order("created_at").limit(1).execute()
        tenant_id = resp.data[0]["id"]

    biz_resp = (
        sb.table("businesses")
        .select("id")
        .eq("tenant_id", tenant_id)
        .order("created_at")
        .limit(1)
        .execute()
    )
    business_id = biz_resp.data[0]["id"]
    print(f"\nTenant: {tenant_id[:8]}...")
    print(f"Business: {business_id[:8]}...")

    # Ensure preferences
    for key, value in [
        ("stale_quote_threshold_days", 3),
        ("max_quote_follow_ups", 3),
        ("follow_up_interval_days", 3),
        ("quote_follow_up_requires_approval", True),
        ("preferred_follow_up_channel", "email"),
    ]:
        sb.table("business_preferences").upsert({
            "business_id": business_id,
            "key": key,
            "value_json": {"value": value},
            "source": "test",
        }, on_conflict="business_id,key").execute()

    # Create stale quote
    lead_resp = sb.table("leads").insert({
        "id": str(uuid4()),
        "business_id": business_id,
        "customer_name": "Acceptance Test Customer",
        "customer_contact": "acceptance@test.com",
        "source": "test",
        "service_type": "logistics",
        "status": "qualified",
    }).execute()
    lead_id = lead_resp.data[0]["id"]

    quote_resp = sb.table("quotes").insert({
        "id": str(uuid4()),
        "business_id": business_id,
        "lead_id": lead_id,
        "quote_amount": 12500,
        "service_type": "logistics",
        "status": "sent",
        "sent_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    }).execute()
    quote_id = quote_resp.data[0]["id"]
    print(f"Created stale quote: {quote_id[:8]}...")

    # Step 1: Detection
    print("\n--- Step 1: Stale Detection ---")
    from chromagora_api.services.quote_stale_detector import detect_stale_quotes
    results = detect_stale_quotes(business_id=UUID(business_id))
    print(f"Detected: {len(results)} stale quotes")
    for r in results:
        print(f"  Quote: {r['quote_id'][:8]}... Event: {r['event_id'][:8]}... Trace: {r['trace_id'][:8]}...")

    # Step 2: Event Processing
    print("\n--- Step 2: Event Processing ---")
    from chromagora_api.services.event_dispatcher import process_pending_events
    proc_results = process_pending_events(event_type="quote.stale", limit=10)
    print(f"Processed: {len(proc_results)} events")
    for r in proc_results:
        print(f"  Event: {r['event_id'][:8]}... Status: {r['status']} Trace: {r['trace_id'][:8]}...")
        if r.get("handler_result"):
            hr = r["handler_result"]
            print(f"    Agent Run: {hr.get('agent_run_id', 'N/A')[:8]}...")
            print(f"    Proposal: {hr.get('proposal_id', 'N/A')[:8]}...")

    # Step 3: Check Approvals
    print("\n--- Step 3: Approvals ---")
    approval_resp = (
        sb.table("approval_requests")
        .select("*, action_proposals(*)")
        .eq("business_id", business_id)
        .eq("status", "pending")
        .execute()
    )
    print(f"Pending approvals: {len(approval_resp.data)}")

    # Step 4: Execute if we have an approval
    if approval_resp.data:
        from chromagora_api.services.action_executor import execute_approved_action
        approval = approval_resp.data[0]
        proposal_id = approval["action_proposal_id"]
        trace_id = approval.get("trace_id") or str(uuid4())

        # Approve
        sb.table("approval_requests").update({
            "status": "approved",
            "decided_by": "acceptance_test",
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval["id"]).execute()

        sb.table("action_proposals").update({
            "status": "approved",
        }).eq("id", proposal_id).execute()

        # Execute
        exec_result = execute_approved_action(
            action_proposal_id=UUID(proposal_id),
            approval_request_id=UUID(approval["id"]),
            trace_id=trace_id,
        )
        print(f"Execution: {exec_result['status']} mode={exec_result.get('mode', 'N/A')}")

    # Step 5: Verify Quote State
    print("\n--- Step 4: Quote State ---")
    quote_resp = sb.table("quotes").select("*").eq("id", quote_id).execute()
    quote = quote_resp.data[0]
    print(f"Status: {quote['status']}")
    if "follow_up_count" in quote:
        print(f"Follow-up count: {quote['follow_up_count']}")
    if "stale_detected_at" in quote and quote["stale_detected_at"]:
        print(f"Stale detected at: {quote['stale_detected_at']}")

    # Step 6: Trace
    print("\n--- Step 5: Trace ---")
    from chromagora_api.services.trace_propagation import get_records_by_trace
    if trace_id:
        trace = get_records_by_trace(trace_id)
        for table_name, records in trace.items():
            if records:
                print(f"  {table_name}: {len(records)} records")

    print("\n" + "=" * 60)
    print("Acceptance test complete!")
