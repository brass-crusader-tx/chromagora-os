-- Migration: 000005_create_business_twin
-- Created: 2026-06-24
-- Description: Business Twin — services, areas, capacity, preferences

-- Business Twin base
CREATE TABLE IF NOT EXISTS business_twins (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    version int NOT NULL DEFAULT 1,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    summary text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_business_twins_business ON business_twins(business_id);
ALTER TABLE business_twins ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_business_twins ON business_twins
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_business_twins_updated_at
    BEFORE UPDATE ON business_twins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Business Services
CREATE TABLE IF NOT EXISTS business_services (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    name text NOT NULL,
    description text,
    category text,
    is_active boolean NOT NULL DEFAULT true,
    base_price_notes text,
    margin_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_business_services_business ON business_services(business_id);
ALTER TABLE business_services ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_business_services ON business_services
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_business_services_updated_at
    BEFORE UPDATE ON business_services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Service Areas
CREATE TABLE IF NOT EXISTS service_areas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    name text NOT NULL,
    area_type text,
    description text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_service_areas_business ON service_areas(business_id);
ALTER TABLE service_areas ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_service_areas ON service_areas
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_service_areas_updated_at
    BEFORE UPDATE ON service_areas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Business Capacity Profile
CREATE TABLE IF NOT EXISTS business_capacity_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    crew_notes text,
    equipment_notes text,
    scheduling_notes text,
    max_daily_estimates int,
    max_weekly_jobs int,
    seasonal_constraints text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(business_id)
);

CREATE INDEX IF NOT EXISTS idx_capacity_business ON business_capacity_profiles(business_id);
ALTER TABLE business_capacity_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_capacity ON business_capacity_profiles
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_capacity_updated_at
    BEFORE UPDATE ON business_capacity_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Business Preferences
CREATE TABLE IF NOT EXISTS business_preferences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    key text NOT NULL,
    value_json jsonb NOT NULL DEFAULT '{}',
    source text,
    confidence float CHECK (confidence >= 0 AND confidence <= 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_preferences_business ON business_preferences(business_id);
ALTER TABLE business_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_preferences ON business_preferences
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON business_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
