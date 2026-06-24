-- Migration: 000020_trace_id_propagation
-- Created: 2026-06-24
-- Description: Add trace_id to all tables missing it + structured logging table
-- Chapter 18.1 — Observability and Evals

-- Tables missing trace_id: workflow_step_logs, spawn_contracts, leads, quotes, jobs, message_drafts

ALTER TABLE workflow_step_logs ADD COLUMN IF NOT EXISTS trace_id text;
ALTER TABLE spawn_contracts ADD COLUMN IF NOT EXISTS trace_id text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS trace_id text;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS trace_id text;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS trace_id text;
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS trace_id text;

-- Index for trace lookups
CREATE INDEX IF NOT EXISTS idx_wf_steps_trace ON workflow_step_logs(trace_id);
CREATE INDEX IF NOT EXISTS idx_spawn_trace ON spawn_contracts(trace_id);
CREATE INDEX IF NOT EXISTS idx_leads_trace ON leads(trace_id);
CREATE INDEX IF NOT EXISTS idx_quotes_trace ON quotes(trace_id);
CREATE INDEX IF NOT EXISTS idx_jobs_trace ON jobs(trace_id);
CREATE INDEX IF NOT EXISTS idx_drafts_trace ON message_drafts(trace_id);

-- Structured logging table for observability
CREATE TABLE IF NOT EXISTS structured_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    trace_id text NOT NULL,
    service_name text NOT NULL,
    log_level text NOT NULL DEFAULT 'info' CHECK (log_level IN ('debug', 'info', 'warning', 'error', 'critical')),
    event_type text NOT NULL,
    message text NOT NULL DEFAULT '',
    context_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_structured_logs_trace ON structured_logs(trace_id);
CREATE INDEX IF NOT EXISTS idx_structured_logs_tenant ON structured_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_structured_logs_service ON structured_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_structured_logs_event ON structured_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_structured_logs_created ON structured_logs(created_at DESC);
ALTER TABLE structured_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_structured_logs ON structured_logs
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
