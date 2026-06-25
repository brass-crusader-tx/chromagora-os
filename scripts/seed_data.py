#!/usr/bin/env python3
"""Seed the Supabase database with realistic demo data.

Uses the service-role (admin) Supabase client to bypass RLS.
Run with:
    .venv/bin/python scripts/seed_data.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

# Load env BEFORE importing settings
load_dotenv(str(Path(__file__).parent.parent / "apps" / "api" / ".env"))

# Ensure we can import from the api package
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from chromagora_api.core.supabase import get_supabase_admin
from chromagora_api.core.config import settings


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def seed():
    sb = get_supabase_admin()
    if not sb:
        print("ERROR: Supabase admin client not configured.")
        sys.exit(1)

    print(f"Connected to: {settings.supabase_url[:40]}...")
    print(f"Admin client type: {type(sb)}")

    # Clean existing data (FK-safe order)
    print("\nCleaning existing data...")
    child_tables = [
        "action_executions", "workflow_step_logs", "workflow_runs",
        "call_summaries", "call_records", "memory_artifacts",
        "quotes", "jobs", "message_drafts", "leads",
        "opportunities", "agent_runs", "business_agent_instances",
        "approval_requests", "action_proposals",
        "authority_envelopes", "business_tool_permissions",
        "compliance_rules",
    ]
    for table in child_tables:
        try:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception:
            pass
    for table in ["workflow_definitions", "tool_definitions", "agent_definitions"]:
        try:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception:
            pass
    for table in ["business_twins", "claims", "businesses"]:
        try:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception:
            pass
    for table in ["user_tenants", "tenants"]:
        try:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception:
            pass
    print("  Done.")

    # 1. Tenant
    print("\n[1] Creating tenant...")
    tenant_id = str(uuid4())
    sb.table("tenants").insert({
        "id": tenant_id,
        "name": "Acme Holdings LLC",
        "slug": "acme-holdings",
        "created_at": now_iso(),
    }).execute()
    print(f"  Tenant: {tenant_id[:8]}...")

    # 2. Businesses
    print("\n[2] Creating businesses...")
    businesses_data = [
        {"legal_name": "Acme Logistics", "slug": "acme-logistics", "primary_vertical": "logistics", "status": "active"},
        {"legal_name": "Acme Labs", "slug": "acme-labs", "primary_vertical": "biotech", "status": "active"},
        {"legal_name": "Acme Properties", "slug": "acme-properties", "primary_vertical": "real_estate", "status": "active"},
        {"legal_name": "Acme Robotics", "slug": "acme-robotics", "primary_vertical": "manufacturing", "status": "inactive"},
    ]
    biz_ids = []
    for b in businesses_data:
        resp = sb.table("businesses").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            **b,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }).execute()
        biz_ids.append(resp.data[0]["id"])
    print(f"  {len(biz_ids)} businesses created")

    # 3. Agent Definitions
    print("\n[3] Creating agent definitions...")
    agent_defs_data = [
        {"name": "Atlas Dispatcher", "agent_type": "dispatching", "description": "Routes and dispatches tasks across the business", "default_authority_level": 3, "default_model_tier": 2},
        {"name": "Orion Scout", "agent_type": "scouting", "description": "Scans for opportunities and market intelligence", "default_authority_level": 2, "default_model_tier": 1},
        {"name": "Nova Analyst", "agent_type": "analysis", "description": "Analyzes data and produces reports", "default_authority_level": 2, "default_model_tier": 1},
        {"name": "Vega Guardian", "agent_type": "compliance", "description": "Monitors compliance and risk", "default_authority_level": 4, "default_model_tier": 1},
        {"name": "Helios Crafter", "agent_type": "crafting", "description": "Generates documents, messages, and content", "default_authority_level": 1, "default_model_tier": 1},
        {"name": "Cassiopeia Liaison", "agent_type": "crm", "description": "Manages customer relationships", "default_authority_level": 2, "default_model_tier": 1},
    ]
    def_ids = []
    for a in agent_defs_data:
        resp = sb.table("agent_definitions").insert({
            "id": str(uuid4()),
            **a,
            "is_active": True,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }).execute()
        def_ids.append(resp.data[0]["id"])
    print(f"  {len(def_ids)} agent definitions created")

    # 4. Business Agent Instances
    print("\n[4] Creating agent instances...")
    inst_pairs = [(0, 0), (1, 0), (2, 1), (3, 2), (0, 3), (1, 4), (2, 5), (3, 0)]
    inst_ids = []
    for biz_idx, def_idx in inst_pairs:
        resp = sb.table("business_agent_instances").insert({
            "id": str(uuid4()),
            "business_id": biz_ids[biz_idx],
            "agent_definition_id": def_ids[def_idx],
            "display_name": f"{agent_defs_data[def_idx]['name']} @ {businesses_data[biz_idx]['legal_name']}",
            "status": "active",
            "config_json": {},
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }).execute()
        inst_ids.append(resp.data[0]["id"])
    print(f"  {len(inst_ids)} agent instances created")

    # 5. Authority Envelopes
    print("\n[5] Creating authority envelopes...")
    envelope_ids = []
    amounts = [5000, 10000, 25000, 15000]
    for biz_idx, biz_id in enumerate(biz_ids):
        resp = sb.table("authority_envelopes").insert({
            "id": str(uuid4()),
            "business_id": biz_id,
            "name": f"Authority - {businesses_data[biz_idx]['legal_name']}",
            "description": f"Spending authority for {businesses_data[biz_idx]['legal_name']}",
            "max_dollar_exposure": amounts[biz_idx],
            "requires_approval": True,
            "conditions_json": json.dumps({"max_single_tx": amounts[biz_idx]}),
            "is_active": True,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }).execute()
        envelope_ids.append(resp.data[0]["id"])
    print(f"  {len(envelope_ids)} envelopes created")

    # 6. Action Proposals
    print("\n[6] Creating action proposals...")
    action_types = ["memo", "route", "approve", "file", "payment", "contact", "memo", "route"]
    proposal_titles = [
        "Review Q2 pipeline report",
        "Route task to logistics agent",
        "Approve vendor invoice #4421",
        "File compliance documentation",
        "Process vendor payment",
        "Contact churned customer",
        "Approve expansion budget",
        "Route urgent dispatch",
    ]
    proposal_ids = []
    for i in range(8):
        biz_idx = i % len(biz_ids)
        resp = sb.table("action_proposals").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": biz_ids[biz_idx],
            "proposed_by_type": "agent",
            "proposed_by_id": inst_ids[i % len(def_ids)],
            "action_type": action_types[i],
            "title": proposal_titles[i],
            "description": f"Automated proposal for {businesses_data[biz_idx]['legal_name']}",
            "proposed_payload": json.dumps({"action": action_types[i]}),
            "risk_level": ["low", "medium", "low", "high", "critical", "low", "medium", "low"][i],
            "autonomy_level_required": 1,
            "evidence_json": json.dumps({"agent": "system"}),
            "created_at": days_ago(i),
        }).execute()
        proposal_ids.append(resp.data[0]["id"])
    print(f"  {len(proposal_ids)} proposals created")

    # 7. Approval Requests
    print("\n[7] Creating approval requests...")
    approval_ids = []
    for i in range(8):
        biz_idx = i % len(biz_ids)
        status = "pending" if i < 5 else ["approved", "rejected", "cancelled"][i % 3]
        resp = sb.table("approval_requests").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": biz_ids[biz_idx],
            "action_proposal_id": proposal_ids[i],
            "status": status,
            "requested_by_type": "agent",
            "requested_by_id": inst_ids[i % len(inst_ids)],
            "requested_at": days_ago(i),
            "trace_id": f"trace-{i + 1:06d}",
        }).execute()
        approval_ids.append(resp.data[0]["id"])
    print(f"  {len(approval_ids)} approval requests created")

    # 8. Ledger / Action Executions
    print("\n[8] Creating ledger entries...")
    tool_names = ["mail", "crm", "router", "filesystem", "calendar"]
    tool_actions = ["send_message", "create_lead", "route_task", "write_file", "schedule_meeting"]
    statuses = ["success", "success", "dry_run", "success", "blocked", "approval_required"]
    for i in range(20):
        biz_idx = i % len(biz_ids)
        approval_id = approval_ids[i % len(approval_ids)] if approval_ids else None
        sb.table("action_executions").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": biz_ids[biz_idx],
            "approval_request_id": approval_id,
            "tool_name": tool_names[i % 5],
            "tool_action": tool_actions[i % 5],
            "tool_args_hash": f"hash-{i:04d}",
            "tool_args_redacted": json.dumps({"to": f"user{i}@acme.com"}),
            "result_status": statuses[i % 6],
            "result_json": json.dumps({"duration_ms": 120 + i * 10, "tokens": 50 + i * 5}),
            "executed_by_type": "agent",
            "executed_by_id": inst_ids[i % len(inst_ids)],
            "started_at": days_ago(i % 10),
            "completed_at": days_ago(i % 10),
            "reversibility": "reversible" if i % 3 == 0 else "irreversible",
            "evidence_json": json.dumps({"agent_display": "Atlas Dispatcher"}),
        }).execute()
    print("  20 ledger entries created")

    # 9. Opportunities
    print("\n[9] Creating opportunities...")
    opp_data = [
        {"title": "Western Regional Expansion", "opportunity_type": "expansion", "source_name": "LinkedIn", "location": "Denver, CO", "min": 15000, "max": 75000, "status": "detected"},
        {"title": "Fleet Maintenance Contract", "opportunity_type": "contract", "source_name": "Website", "location": "Remote", "min": 20000, "max": 100000, "status": "qualifying"},
        {"title": "Lab Equipment Lease", "opportunity_type": "lease", "source_name": "Referral", "location": "San Francisco, CA", "min": 10000, "max": 50000, "status": "qualified"},
        {"title": "Property Acquisition - Denver", "opportunity_type": "acquisition", "source_name": "Cold Outreach", "location": "Denver, CO", "min": 50000, "max": 250000, "status": "detected"},
        {"title": "Robotics Partnership", "opportunity_type": "partnership", "source_name": "Partner", "location": "Austin, TX", "min": 25000, "max": 150000, "status": "rejected"},
        {"title": "Supply Chain Optimization", "opportunity_type": "optimization", "source_name": "Marketplace", "location": "Remote", "min": 30000, "max": 120000, "status": "detected"},
        {"title": "Biotech Research Grant", "opportunity_type": "grant", "source_name": "LinkedIn", "location": "Remote", "min": 40000, "max": 200000, "status": "qualifying"},
        {"title": "Smart Building Retrofit", "opportunity_type": "retrofit", "source_name": "Website", "location": "New York, NY", "min": 18000, "max": 90000, "status": "detected"},
    ]
    for i, o in enumerate(opp_data):
        biz_idx = i % len(biz_ids)
        sb.table("opportunities").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": biz_ids[biz_idx],
            "opportunity_type": o["opportunity_type"],
            "source_name": o["source_name"],
            "title": o["title"],
            "description": f"Identified opportunity for {businesses_data[biz_idx]['legal_name']}",
            "location": o["location"],
            "estimated_value_min": o["min"],
            "estimated_value_max": o["max"],
            "fit_score": 0.6 + (i % 4) * 0.1,
            "urgency_score": 0.5 + (i % 3) * 0.15,
            "status": o["status"],
            "required_documents": json.dumps([]),
            "missing_documents": json.dumps([]),
            "evidence_json": json.dumps({"source": o["source_name"]}),
            "created_at": days_ago(i * 2),
            "updated_at": days_ago(i),
        }).execute()
    print(f"  {len(opp_data)} opportunities created")

    # 10. Leads / CRM
    print("\n[10] Creating CRM leads...")
    leads_data = [
        ("Jordan Mitchell", "jordan@westlogistics.com", "(555) 234-5678", "website", "consulting"),
        ("Casey Rivera", "casey@labtech.io", "(555) 345-6789", "referral", "analysis"),
        ("Morgan Chen", "morgan@props.com", "(555) 456-7890", "linkedin", "support"),
        ("Riley Thompson", "riley@botics.co", "(555) 567-8901", "cold_call", "development"),
        ("Avery Patel", "avery@ventures.io", "(555) 678-9012", "event", "consulting"),
        ("Taylor Brooks", "taylor@buildco.com", "(555) 789-0123", "website", "support"),
        ("Jamie Nguyen", "jamie@freight.com", "(555) 890-1234", "referral", "analysis"),
    ]
    statuses_lead = ["new", "contacted", "qualified", "new", "contacted", "qualified", "lost"]
    for i, (name, email, phone, source, svc) in enumerate(leads_data):
        biz_idx = i % len(biz_ids)
        sb.table("leads").insert({
            "id": str(uuid4()),
            "business_id": biz_ids[biz_idx],
            "customer_name": name,
            "customer_contact": email,
            "source": source,
            "service_type": svc,
            "status": statuses_lead[i],
            "notes": f"Lead #{i + 1} - interested in automation services.",
            "created_at": days_ago(i * 2 + 1),
            "updated_at": days_ago(i),
        }).execute()
    print(f"  {len(leads_data)} leads created")

    # 11. Memory Artifacts
    print("\n[11] Creating memory artifacts...")
    mem_data = [
        ("document", "Q2 Operations Report", "Summary of operational metrics and KPIs for Q2 2026."),
        ("insight", "Customer Churn Pattern", "Analysis: 3 customers churned after 90 days."),
        ("decision", "Approved Tool Access", "Nova Analyst granted access to forecasting tools."),
        ("event", "System Maintenance Window", "Scheduled: June 30 02:00-04:00 UTC."),
        ("insight", "Efficiency Gain: Routing", "Atlas reduced routing time by 23%."),
        ("document", "Acme Logistics SLA", "SLA: 99.9% uptime, 2hr response time."),
        ("decision", "New Agent Deployed", "Cassiopeia Liaison activated for Acme Logistics."),
    ]
    for i, (atype, title, content) in enumerate(mem_data):
        sb.table("memory_artifacts").insert({
            "id": str(uuid4()),
            "business_id": biz_ids[i % len(biz_ids)],
            "artifact_type": atype,
            "title": title,
            "text_content": content,
            "source_ref": f"seed-{i:04d}",
            "created_at": days_ago(i * 3),
            "updated_at": days_ago(i),
        }).execute()
    print(f"  {len(mem_data)} memory artifacts created")

    # 12. Call Records
    print("\n[12] Creating call records...")
    callers = ["+15551234567", "+15559876543", "+15555551234", "+15554443333", "+15552221111"]
    statuses_call = ["inbound", "outbound", "missed", "inbound", "voicemail", "inbound", "outbound", "missed", "inbound", "voicemail"]
    for i in range(10):
        sb.table("call_records").insert({
            "id": str(uuid4()),
            "business_id": biz_ids[i % len(biz_ids)],
            "caller_phone": callers[i % 5],
            "caller_name": f"Caller {i + 1}",
            "call_status": statuses_call[i],
            "started_at": days_ago(i),
            "ended_at": days_ago(i),
            "transcript_text": f"Call #{i + 1}: Customer inquired about pricing and availability.",
            "consent_recorded": True,
            "created_at": days_ago(i),
            "updated_at": now_iso(),
        }).execute()
    print("  10 call records created")

    # 13. Workflow Definitions
    print("\n[13] Creating workflow definitions...")
    wf_data = [
        ("Client Onboarding", "Standard new client onboarding", "onboarding"),
        ("Invoice Approval", "Multi-step invoice approval", "approval"),
        ("Incident Response", "Automated incident detection", "incident"),
        ("Vendor Evaluation", "Periodic vendor review", "evaluation"),
    ]
    # Insert one at a time due to RLS policy on table
    wf_ids = []
    for i, (name, desc, wtype) in enumerate(wf_data):
        resp = sb.table("workflow_definitions").insert({
            "id": str(uuid4()),
            "name": name,
            "description": desc,
            "workflow_type": wtype,
            "version": 1,
            "config_json": json.dumps({"steps": ["init", "review", "approve", "complete"]}),
            "is_active": True,
            "created_at": days_ago(i * 5),
            "updated_at": now_iso(),
        }).execute()
        wf_ids.append(resp.data[0]["id"])
    print(f"  {len(wf_ids)} workflow definitions created")

    # 14. Workflow Runs
    print("\n[14] Creating workflow runs...")
    wf_statuses = ["running", "completed", "completed", "failed", "running", "pending"]
    for i in range(6):
        sb.table("workflow_runs").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": biz_ids[i % len(biz_ids)],
            "workflow_definition_id": wf_ids[0] if wf_ids else None,
            "workflow_type": "onboarding",
            "status": wf_statuses[i],
            "current_step": "review",
            "input_json": json.dumps({"trigger": "manual"}),
            "state_json": json.dumps({"step": 1}),
            "started_at": days_ago(i + 1),
            "updated_at": days_ago(i),
        }).execute()
    print("  6 workflow runs created")

    # 15. Quotes (bonus CRM data)
    print("\n[15] Creating quotes...")
    for i in range(4):
        biz_idx = i % len(biz_ids)
        sb.table("quotes").insert({
            "id": str(uuid4()),
            "business_id": biz_ids[biz_idx],
            "quote_amount": 5000 + i * 2500,
            "service_type": ["consulting", "logistics", "analysis", "support"][i],
            "status": ["draft", "sent", "accepted", "rejected"][i],
            "created_at": days_ago(i * 2),
            "updated_at": days_ago(i),
        }).execute()
    print("  4 quotes created")

    # Summary
    print("\n" + "=" * 50)
    print("Seed complete!")
    print(f"  Businesses:     {len(biz_ids)}")
    print(f"  Agent defs:     {len(def_ids)}")
    print(f"  Agent instances:{len(inst_ids)}")
    print(f"  Proposals:      {len(proposal_ids)}")
    print(f"  Approvals:      {len(approval_ids)}")
    print(f"  Ledger entries: 20")
    print(f"  Opportunities:  {len(opp_data)}")
    print(f"  Leads:          {len(leads_data)}")
    print(f"  Memory:         {len(mem_data)}")
    print(f"  Calls:          10")
    print(f"  Workflows:      {len(wf_data)}")
    print(f"  Quotes:         4")


if __name__ == "__main__":
    seed()
