-- Migration: 000012_create_tools
-- Created: 2026-06-24
-- Description: Tool registry and business tool permissions

CREATE TABLE IF NOT EXISTS tool_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    target_system text NOT NULL,
    tool_action text NOT NULL,
    input_schema_json jsonb NOT NULL DEFAULT '{}',
    output_schema_json jsonb NOT NULL DEFAULT '{}',
    risk_level_default text NOT NULL DEFAULT 'low' CHECK (risk_level_default IN ('low', 'medium', 'high')),
    autonomy_level_required_default int NOT NULL DEFAULT 1,
    is_external_action bool NOT NULL DEFAULT false,
    is_active bool NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS business_tool_permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    tool_definition_id uuid NOT NULL REFERENCES tool_definitions(id),
    is_enabled bool NOT NULL DEFAULT true,
    max_autonomy_level int NOT NULL DEFAULT 1,
    requires_approval_override bool,       -- null = use default from envelope
    config_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(business_id, tool_definition_id)
);

CREATE INDEX IF NOT EXISTS idx_tools_target ON tool_definitions(target_system);
CREATE INDEX IF NOT EXISTS idx_tools_active ON tool_definitions(is_active);
CREATE INDEX IF NOT EXISTS idx_tool_perms_business ON business_tool_permissions(business_id);
CREATE INDEX IF NOT EXISTS idx_tool_perms_business_active ON business_tool_permissions(business_id, is_enabled);
CREATE INDEX IF NOT EXISTS idx_tool_perms_definition ON business_tool_permissions(tool_definition_id);
ALTER TABLE tool_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tools ON tool_definitions
    USING (true);  -- tool definitions are global, not tenant-scoped
ALTER TABLE business_tool_permissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tool_perms ON business_tool_permissions
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
