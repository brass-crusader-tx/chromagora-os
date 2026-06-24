-- Migration: 000015_create_agent_runs
-- Created: 2026-06-24
-- Description: Agent execution runs

CREATE TABLE IF NOT EXISTS agent_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    agent_instance_id uuid REFERENCES business_agent_instances(id),
    agent_type text NOT NULL,
    trigger_type text NOT NULL,
    trigger_event_id uuid REFERENCES events(id),
    workflow_run_id uuid REFERENCES workflow_runs(id),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),
    input_json jsonb NOT NULL DEFAULT '{}',
    context_packet_json jsonb,
    output_json jsonb,
    error_message text,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    cost_estimate numeric(10,4),
    model_name text,
    model_tier int,
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant ON agent_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_business ON agent_runs(business_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_instance ON agent_runs(agent_instance_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_type ON agent_runs(agent_type);
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_runs ON agent_runs
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
