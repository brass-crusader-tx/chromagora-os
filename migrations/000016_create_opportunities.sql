-- Migration: 000016_create_opportunities
-- Created: 2026-06-24
-- Description: Procurement opportunities

CREATE TABLE IF NOT EXISTS opportunities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid NOT NULL REFERENCES businesses(id),
    opportunity_type text NOT NULL,
    source_name text NOT NULL,
    source_url text,
    title text NOT NULL,
    description text,
    location text,
    published_at timestamptz,
    deadline_at timestamptz,
    estimated_value_min numeric(12,2),
    estimated_value_max numeric(12,2),
    fit_score numeric(3,2),
    urgency_score numeric(3,2),
    capacity_fit numeric(3,2),
    margin_confidence numeric(3,2),
    strategic_value numeric(3,2),
    status text NOT NULL DEFAULT 'detected' CHECK (status IN (
        'detected', 'qualifying', 'qualified', 'rejected',
        'approval_required', 'pursuing', 'submitted', 'won', 'lost', 'archived'
    )),
    required_documents jsonb NOT NULL DEFAULT '[]',
    missing_documents jsonb NOT NULL DEFAULT '[]',
    evidence_json jsonb NOT NULL DEFAULT '{}',
    recommended_next_action text,
    agent_owner uuid REFERENCES business_agent_instances(id),
    workflow_run_id uuid REFERENCES workflow_runs(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_opp_tenant ON opportunities(tenant_id);
CREATE INDEX IF NOT EXISTS idx_opp_business ON opportunities(business_id);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opp_type ON opportunities(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_opp_created ON opportunities(created_at DESC);
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_opp ON opportunities
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
