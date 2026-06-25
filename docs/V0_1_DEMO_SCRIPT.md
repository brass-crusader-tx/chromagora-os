# Chromagora OS v0.1 Demo Script

Scenario: Brass Landscaping & Snow Removal — a real SMB going live with Chromagora.

## Prerequisites

1. API running at `http://localhost:8000`
2. Supabase project configured in `.env`
3. Frontend running at `http://localhost:3010`

## Step 1 — Business Setup

```
POST /tenants
{"name": "Brass Landscaping", "slug": "brass-landscaping", "status": "active"}

POST /businesses
{"tenant_id": "<tenant-id>", "legal_name": "Brass Landscaping LLC", "public_name": "Brass Landscaping", "slug": "brass", "business_type": "llc", "primary_vertical": "landscaping", "country": "CA", "province_state": "ON", "city": "Kitchener", "service_area_description": "Kitchener-Waterloo-Cambridge tri-city", "status": "active"}
```

Note the `business_id` — everything below uses it.

## Step 2 — Business Twin

```
POST /businesses/{id}/twin
{
  "summary": "Family-operated landscaping and snow removal. 3 crews. 15+ years.",
  "services": [
    {"name": "Lawn Care", "description": "Weekly mowing, edging, fertilizing", "category": "maintenance", "is_active": true},
    {"name": "Snow Removal", "description": "Seasonal contract and per-push", "category": "seasonal", "is_active": true},
    {"name": "Softscaping", "description": "Garden beds, planting, mulch", "category": "installation", "is_active": true}
  ],
  "areas": [
    {"name": "Primary Kitchener", "description": "South of Victoria St", "is_active": true},
    {"name": "Primary Waterloo", "description": "University corridor", "is_active": true}
  ],
  "capacity": {
    "crew_notes": "3 full-time crews, seasonal hires Nov-Mar",
    "max_daily_estimates": 8,
    "max_weekly_jobs": 40
  },
  "approved_claims": [
    {"claim_type": "licensed", "claim_text": "Fully licensed and insured", "is_active": true},
    {"claim_type": "warranty", "claim_text": "30-day satisfaction guarantee on all softscaping", "is_active": true}
  ],
  "forbidden_claims": [
    {"claim_type": "emergency", "claim_text": "Do not claim 24/7 emergency service", "reason": "Snow removal is scheduled, not emergency"},
  ]
}
```

## Step 3 — Authority Envelope

```
POST /businesses/{id}/authority
{
  "name": "Default Agent Authority",
  "agent_scope": ["sales", "reputation", "procurement"],
  "tool_scope": ["crm.create_lead", "crm.update_lead_status", "reputation.queue_review_request"],
  "autonomy_level": 3,
  "max_dollar_exposure": 5000,
  "requires_approval": true,
  "conditions": {},
  "forbidden_conditions": {"compliance_sensitive": true}
}
```

## Step 4 — Enable Mock Tools

```
GET /businesses/{id}/tools
# Verify tools are listed

PATCH /businesses/{id}/tools/crm.create_lead
{"is_enabled": true}
```

## Step 5 — Completed Job → Review Request Simulation

```
POST /demo/review-request-simulation
{
  "business_id": "<id>",
  "customer_name": "Sarah Johnson",
  "customer_contact": "sarah@example.com",
  "job_summary": "Front garden bed cleanup and mulch refresh",
  "completed_at": "2026-06-24T14:00:00Z"
}
```

Expected result:
- `event_id` with event_type = "job.completed"
- `agent_run_id` with agent_type = "reputation"
- `action_proposal_id` with action_type = "reputation.queue_review_request"
- If approval needed: `approval_request_id` (status = "pending")
- If allowed: `action_execution_id` with result_status = "dry_run"
- `trace_id` present on all records

## Step 6 — Stale Quote → Follow-up Simulation

```
POST /demo/stale-quote-simulation
{
  "business_id": "<id>",
  "customer_name": "Mike Chen",
  "customer_contact": "mike@example.com",
  "quote_amount": 2500.00,
  "service_type": "lawn_care",
  "quote_sent_at": "2026-06-15T10:00:00Z"
}
```

Expected: Agent detects quote is stale (9+ days old), creates follow-up task.

## Step 7 — Commercial Snow Opportunity

```
POST /demo/opportunity-simulation
{
  "business_id": "<id>",
  "opportunity_type": "commercial_snow",
  "source_name": "Region of Waterloo Tender Portal",
  "title": "Snow Removal Contract — 3 Commercial Properties",
  "description": "Seasonal snow removal for 3 office park properties in Kitchener",
  "location": "Kitchener, ON",
  "deadline_at": "2026-09-01T00:00:00Z",
  "estimated_value_min": 15000,
  "estimated_value_max": 25000
}
```

Expected: Opportunity created, fit score calculated, ActionProposal generated.

## Step 8 — Approval Inbox

Navigate to `/approvals` in the frontend, or:

```
GET /mobile/approvals?business_id=<id>
```

Each pending approval shows:
- Action proposal title and description
- Risk level
- Confidence
- Approve/Reject buttons

## Step 9 — Approve/Reject

```
POST /mobile/approvals/{id}/approve
# or
POST /mobile/approvals/{id}/reject?notes=Lower price first
```

Watch:
- Approval status updates
- Event emitted
- If approved, tool execution recorded in Action Ledger

## Step 10 — Action Ledger

Navigate to `/ledger`, or:

GET /businesses/{id}/autonomy/scorecard

Shows: total proposals, approvals, executions, violations, recommended autonomy level.

## Step 11 — Trace Links

Every record from steps 5-9 shares a `trace_id`. Click any trace_id to see the full chain of events, proposals, approvals, and executions.

## Demo Script Notes

- This demo uses dry-run mode for all external actions
- All data persists in Supabase
- The same trace_id links every record generated during the demo
- Run time: ~5 minutes to walk through all steps
