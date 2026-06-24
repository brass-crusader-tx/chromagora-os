-- Migration: 000013_create_workflows
-- Created: 2026-06-24
-- Description: Workflow-lite engine — database-backed workflows

CREATE TABLE IF NOT EXISTS workflow_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    workflow_type text NOT NULL,
    version int NOT NULL DEFAULT 1,
    config_json jsonb NOT NULL DEFAULT '{}',
    is_active bool NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    workflow_definition_id uuid REFERENCES workflow_definitions(id),
    workflow_type text NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'waiting_for_approval',
        'waiting_for_external_event', 'completed', 'failed', 'cancelled'
    )),
    current_step text,
    input_json jsonb NOT NULL DEFAULT '{}',
    state_json jsonb NOT NULL DEFAULT '{}',
    result_json jsonb,
    started_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    correlation_id uuid,
    trace_id text
);

CREATE TABLE IF NOT EXISTS workflow_step_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id uuid NOT NULL REFERENCES workflow_runs(id),
    step_name text NOT NULL,
    status text NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    input_json jsonb NOT NULL DEFAULT '{}',
    output_json jsonb,
    error_message text,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_wf_def_type ON workflow_definitions(workflow_type);
CREATE INDEX IF NOT EXISTS idx_wf_def_active ON workflow_definitions(is_active);
CREATE INDEX IF NOT EXISTS idx_wf_runs_tenant ON workflow_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wf_runs_business ON workflow_runs(business_id);
CREATE INDEX IF NOT EXISTS idx_wf_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_wf_runs_type ON workflow_runs(workflow_type);
CREATE INDEX IF NOT EXISTS idx_wf_steps_run ON workflow_step_logs(workflow_run_id);
ALTER TABLE workflow_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_wf_def ON workflow_definitions
    USING (true);  -- definitions are global
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_wf_runs ON workflow_runs
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
ALTER TABLE workflow_step_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_wf_steps ON workflow_step_logs
    USING (workflow_run_id IN (
        SELECT id FROM workflow_runs
        WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
