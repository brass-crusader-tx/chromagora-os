-- Migration: 000018_create_crm
-- Created: 2026-06-24
-- Description: CRM-lite models (leads, quotes, jobs)

CREATE TABLE IF NOT EXISTS leads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    customer_name text NOT NULL,
    customer_contact text NOT NULL,
    source text,
    service_type text,
    status text NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'contacted', 'qualified', 'converted', 'lost'
    )),
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quotes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    lead_id uuid REFERENCES leads(id),
    quote_amount numeric(12,2),
    service_type text NOT NULL,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'sent', 'accepted', 'rejected', 'stale'
    )),
    sent_at timestamptz,
    last_followup_at timestamptz,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    lead_id uuid REFERENCES leads(id),
    quote_id uuid REFERENCES quotes(id),
    customer_name text NOT NULL,
    service_type text NOT NULL,
    status text NOT NULL DEFAULT 'scheduled' CHECK (status IN (
        'scheduled', 'in_progress', 'completed', 'cancelled'
    )),
    scheduled_at timestamptz,
    completed_at timestamptz,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_leads_business ON leads(business_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_quotes_business ON quotes(business_id);
CREATE INDEX IF NOT EXISTS idx_quotes_lead ON quotes(lead_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_jobs_business ON jobs(business_id);
CREATE INDEX IF NOT EXISTS idx_jobs_lead ON jobs(lead_id);
CREATE INDEX IF NOT EXISTS idx_jobs_quote ON jobs(quote_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_leads ON leads
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_quotes ON quotes
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_jobs ON jobs
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
