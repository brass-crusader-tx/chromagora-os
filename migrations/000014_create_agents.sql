-- Migration: 000014_create_agents
-- Created: 2026-06-24
-- Description: Agent definitions and business agent instances

CREATE TABLE IF NOT EXISTS agent_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    agent_type text NOT NULL,
    description text,
    standing_mission text,
    default_subscribed_events jsonb NOT NULL DEFAULT '[]',
    default_allowed_tools jsonb NOT NULL DEFAULT '[]',
    default_authority_level int NOT NULL DEFAULT 1,
    default_model_tier int NOT NULL DEFAULT 1,
    is_active bool NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS business_agent_instances (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    agent_definition_id uuid NOT NULL REFERENCES agent_definitions(id),
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'disabled')),
    config_json jsonb NOT NULL DEFAULT '{}',
    authority_envelope_id uuid REFERENCES authority_envelopes(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_defs_type ON agent_definitions(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_defs_active ON agent_definitions(is_active);
CREATE INDEX IF NOT EXISTS idx_agent_inst_business ON business_agent_instances(business_id);
CREATE INDEX IF NOT EXISTS idx_agent_inst_definition ON business_agent_instances(agent_definition_id);
CREATE INDEX IF NOT EXISTS idx_agent_inst_status ON business_agent_instances(status);
ALTER TABLE agent_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_defs ON agent_definitions
    USING (true);  -- definitions are global
ALTER TABLE business_agent_instances ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_inst ON business_agent_instances
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
