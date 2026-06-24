-- Migration: 000011_create_compliance
-- Created: 2026-06-24
-- Description: Compliance rules — regulatory and policy constraints

CREATE TABLE IF NOT EXISTS compliance_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),  -- null = tenant-wide
    name text NOT NULL,
    jurisdiction text NOT NULL DEFAULT 'US',
    rule_type text NOT NULL CHECK (rule_type IN (
        'casl_commercial_message',
        'privacy_personal_data',
        'call_recording_notice',
        'public_claims',
        'review_request_policy',
        'procurement_submission',
        'supplier_credit_application'
    )),
    description text,
    applies_to_action_type text,       -- null = applies to all action types
    rule_config_json jsonb NOT NULL DEFAULT '{}',
    is_active bool NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_compliance_tenant ON compliance_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_compliance_tenant_business ON compliance_rules(tenant_id, business_id);
CREATE INDEX IF NOT EXISTS idx_compliance_type ON compliance_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_compliance_action_type ON compliance_rules(applies_to_action_type);
CREATE INDEX IF NOT EXISTS idx_compliance_active ON compliance_rules(is_active);
ALTER TABLE compliance_rules ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_compliance ON compliance_rules
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
