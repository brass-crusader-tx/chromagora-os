-- Migration: 000010_create_authority
-- Created: 2026-06-24
-- Description: Authority Envelopes — agent action boundaries

CREATE TABLE IF NOT EXISTS authority_envelopes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    name text NOT NULL,
    description text,
    agent_scope text,                  -- null = wildcard (any agent)
    tool_scope text,                   -- null = wildcard (any tool)
    action_type_scope text,            -- null = wildcard (any action type)
    autonomy_level int NOT NULL DEFAULT 0 CHECK (autonomy_level BETWEEN 0 AND 6),
    max_dollar_exposure numeric(12,2), -- null = no limit
    requires_approval bool NOT NULL DEFAULT true,
    conditions_json jsonb NOT NULL DEFAULT '{}',
    forbidden_conditions_json jsonb NOT NULL DEFAULT '{}',
    is_active bool NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_authority_business ON authority_envelopes(business_id);
CREATE INDEX IF NOT EXISTS idx_authority_business_active ON authority_envelopes(business_id, is_active);
CREATE INDEX IF NOT EXISTS idx_authority_autonomy ON authority_envelopes(autonomy_level);
ALTER TABLE authority_envelopes ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_authority ON authority_envelopes
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
