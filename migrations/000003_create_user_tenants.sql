-- Migration: 000003_create_user_tenants
-- Created: 2026-06-24
-- Description: User-tenant junction table (auth via Supabase Auth)

CREATE TABLE IF NOT EXISTS user_tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    role text NOT NULL DEFAULT 'operator' CHECK (role IN ('owner', 'admin', 'operator', 'viewer')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_user_tenants_user ON user_tenants(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tenants_tenant ON user_tenants(tenant_id);

ALTER TABLE user_tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_user_tenants ON user_tenants
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE TRIGGER update_user_tenants_updated_at
    BEFORE UPDATE ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
