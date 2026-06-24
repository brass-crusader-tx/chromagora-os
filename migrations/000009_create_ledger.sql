-- Migration: 000009_create_ledger
-- Created: 2026-06-24
-- Description: Action execution ledger — immutable record of every execution

CREATE TABLE IF NOT EXISTS action_executions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    action_proposal_id uuid REFERENCES action_proposals(id),
    approval_request_id uuid REFERENCES approval_requests(id),
    tool_name text NOT NULL,
    tool_action text NOT NULL,
    tool_args_hash text,
    tool_args_redacted jsonb NOT NULL DEFAULT '{}',
    result_status text NOT NULL CHECK (result_status IN (
        'dry_run', 'success', 'failed', 'blocked', 'approval_required', 'cancelled'
    )),
    result_json jsonb,
    error_message text,
    executed_by_type text NOT NULL,
    executed_by_id uuid,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    idempotency_key text,
    reversibility text NOT NULL DEFAULT 'reversible' CHECK (reversibility IN ('reversible', 'irreversible')),
    rollback_status text CHECK (rollback_status IN ('not_applicable', 'rolled_back', 'failed')),
    evidence_json jsonb NOT NULL DEFAULT '{}',
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_ledger_tenant ON action_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ledger_tenant_business ON action_executions(tenant_id, business_id);
CREATE INDEX IF NOT EXISTS idx_ledger_status ON action_executions(result_status);
CREATE INDEX IF NOT EXISTS idx_ledger_tool ON action_executions(tool_name, tool_action);
CREATE INDEX IF NOT EXISTS idx_ledger_started ON action_executions(started_at DESC);
ALTER TABLE action_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_ledger ON action_executions
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
