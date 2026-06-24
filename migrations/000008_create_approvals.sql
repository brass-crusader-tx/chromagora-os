-- Migration: 000008_create_approvals
-- Created: 2026-06-24
-- Description: Action proposals and approval requests

CREATE TABLE IF NOT EXISTS action_proposals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    proposed_by_type text NOT NULL,
    proposed_by_id uuid,
    action_type text NOT NULL,
    title text NOT NULL,
    description text,
    target_system text,
    proposed_payload jsonb NOT NULL DEFAULT '{}',
    expected_value float,
    confidence float CHECK (confidence >= 0 AND confidence <= 1),
    risk_level text NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    autonomy_level_required int NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'proposed', 'approval_required', 'approved', 'rejected',
        'executed', 'failed', 'cancelled', 'blocked'
    )),
    evidence_json jsonb NOT NULL DEFAULT '{}',
    policy_decision_json jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_proposals_tenant ON action_proposals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_proposals_tenant_business ON action_proposals(tenant_id, business_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON action_proposals(status);
ALTER TABLE action_proposals ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_proposals ON action_proposals
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
CREATE TRIGGER update_proposals_updated_at
    BEFORE UPDATE ON action_proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS approval_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    action_proposal_id uuid NOT NULL REFERENCES action_proposals(id),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'rejected', 'cancelled', 'expired'
    )),
    requested_by_type text NOT NULL,
    requested_by_id uuid,
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_by text,
    decided_at timestamptz,
    decision_notes text,
    expires_at timestamptz,
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_approvals_tenant ON approval_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approvals_proposal ON approval_requests(action_proposal_id);
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_approvals ON approval_requests
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
CREATE TRIGGER update_approvals_updated_at
    BEFORE UPDATE ON approval_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
