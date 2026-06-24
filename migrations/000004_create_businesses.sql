-- Migration: 000004_create_businesses
-- Created: 2026-06-24
-- Description: Client businesses

CREATE TABLE IF NOT EXISTS businesses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    legal_name text NOT NULL,
    public_name text,
    slug text NOT NULL,
    business_type text,
    primary_vertical text,
    country text,
    province_state text,
    city text,
    service_area_description text,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_businesses_tenant ON businesses(tenant_id);
CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status);

ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_businesses ON businesses
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE TRIGGER update_businesses_updated_at
    BEFORE UPDATE ON businesses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
