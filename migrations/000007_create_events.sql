-- Migration: 000007_create_events
-- Created: 2026-06-24
-- Description: Event log — all important state changes become events

CREATE TABLE IF NOT EXISTS events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    event_type text NOT NULL,
    source_type text,
    source_id uuid,
    payload_json jsonb NOT NULL DEFAULT '{}',
    occurred_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    correlation_id uuid,
    causation_id uuid,
    workflow_run_id uuid,
    trace_id text
);

CREATE INDEX IF NOT EXISTS idx_events_tenant ON events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_events_tenant_business ON events(tenant_id, business_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events(occurred_at DESC);

ALTER TABLE events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_events ON events
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
