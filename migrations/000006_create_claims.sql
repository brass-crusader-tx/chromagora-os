-- Migration: 000006_create_claims
-- Created: 2026-06-24
-- Description: Approved and forbidden business claims

CREATE TABLE IF NOT EXISTS approved_business_claims (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    claim_type text NOT NULL,
    claim_text text NOT NULL,
    evidence_json jsonb NOT NULL DEFAULT '{}',
    approved_by text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_approved_claims_business ON approved_business_claims(business_id);
ALTER TABLE approved_business_claims ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_approved_claims ON approved_business_claims
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_approved_claims_updated_at
    BEFORE UPDATE ON approved_business_claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS forbidden_business_claims (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    claim_type text NOT NULL,
    claim_text text NOT NULL,
    reason text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_forbidden_claims_business ON forbidden_business_claims(business_id);
ALTER TABLE forbidden_business_claims ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_forbidden_claims ON forbidden_business_claims
    USING (business_id IN (SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid));
CREATE TRIGGER update_forbidden_claims_updated_at
    BEFORE UPDATE ON forbidden_business_claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
