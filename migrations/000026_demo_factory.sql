-- Migration: 000026_demo_factory
-- Created: 2026-07-01
-- Description: Durable substrate for the Demo Factory vertical:
--              CSV batches, ordered rows, projects, evidence artifacts,
--              framework retrievals, SiteSpecs, QA, deployments, model calls,
--              and supervisor events.

-- =============================================================================
-- 1. BATCHES, ROWS, PROJECTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_site_batches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    source_filename text NOT NULL,
    total_rows integer NOT NULL DEFAULT 0,
    queued_count integer NOT NULL DEFAULT 0,
    running_count integer NOT NULL DEFAULT 0,
    published_count integer NOT NULL DEFAULT 0,
    failed_count integer NOT NULL DEFAULT 0,
    current_row_number integer,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN (
        'queued', 'running', 'paused', 'completed', 'failed', 'cancelled'
    )),
    started_at timestamptz,
    completed_at timestamptz,
    metadata_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_batch_rows (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    batch_id uuid NOT NULL REFERENCES demo_site_batches(id) ON DELETE CASCADE,
    project_id uuid,
    row_number integer NOT NULL,
    rank numeric,
    business_name text NOT NULL,
    website_url text,
    website_domain text,
    demo_slug text NOT NULL,
    raw_row_json jsonb NOT NULL DEFAULT '{}',
    status text NOT NULL DEFAULT 'queued' CHECK (status IN (
        'queued', 'running', 'published', 'failed_retryable',
        'failed_terminal', 'skipped', 'paused'
    )),
    attempt_count integer NOT NULL DEFAULT 0,
    last_error text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid REFERENCES businesses(id),
    batch_id uuid REFERENCES demo_site_batches(id) ON DELETE SET NULL,
    batch_row_id uuid REFERENCES demo_site_batch_rows(id) ON DELETE SET NULL,
    source_domain text,
    normalized_domain text,
    source_url text,
    business_name text NOT NULL,
    demo_slug text NOT NULL,
    demo_host text,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN (
        'queued', 'crawling', 'brand_synthesis', 'copy_strategy',
        'site_architecture', 'asset_curation', 'review_evidence',
        'site_spec', 'rendering', 'qa', 'publishing', 'published',
        'failed_retryable', 'failed_terminal', 'archived',
        'waiting_rate_limit'
    )),
    current_stage text,
    verify_before_build boolean NOT NULL DEFAULT true,
    priority_score numeric,
    input_row_json jsonb NOT NULL DEFAULT '{}',
    trace_id text,
    error_message text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'demo_site_batch_rows_project_id_fkey'
    ) THEN
        ALTER TABLE demo_site_batch_rows
            ADD CONSTRAINT demo_site_batch_rows_project_id_fkey
            FOREIGN KEY (project_id) REFERENCES demo_site_projects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- =============================================================================
-- 2. SOURCE SNAPSHOTS, ASSETS, BRAND DOCUMENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_site_source_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    source_url text NOT NULL,
    final_url text,
    page_type text,
    http_status integer,
    title text,
    meta_description text,
    visible_text text,
    text_summary text,
    screenshot_bucket text,
    screenshot_path text,
    metadata_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    snapshot_id uuid REFERENCES demo_site_source_snapshots(id) ON DELETE SET NULL,
    asset_type text NOT NULL,
    source_url text,
    storage_bucket text,
    storage_path text,
    public_url text,
    alt_text text,
    width integer,
    height integer,
    status text NOT NULL DEFAULT 'candidate' CHECK (status IN (
        'candidate', 'selected', 'rejected', 'published'
    )),
    metadata_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_brand_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'current', 'archived', 'failed'
    )),
    summary text,
    document_json jsonb NOT NULL DEFAULT '{}',
    evidence_refs_json jsonb NOT NULL DEFAULT '[]',
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 3. FRAMEWORK RETRIEVAL
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_site_framework_sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    source_key text NOT NULL,
    title text NOT NULL,
    source_type text NOT NULL DEFAULT 'private_corpus',
    license_scope text,
    metadata_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_framework_patterns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    source_id uuid REFERENCES demo_site_framework_sources(id) ON DELETE SET NULL,
    pattern_key text NOT NULL,
    title text NOT NULL,
    tags text[] NOT NULL DEFAULT '{}',
    pattern_json jsonb NOT NULL DEFAULT '{}',
    embedding_json jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_framework_retrievals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    stage text NOT NULL DEFAULT 'conversion_strategy',
    query_json jsonb NOT NULL DEFAULT '{}',
    selected_pattern_ids uuid[] NOT NULL DEFAULT '{}',
    result_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 4. REVIEWS, SITE SPECS, QA, DEPLOYMENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_site_reviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    source_name text,
    source_url text,
    reviewer_name text,
    rating numeric,
    review_text text,
    review_date date,
    identity_match_json jsonb NOT NULL DEFAULT '{}',
    confidence_score numeric,
    status text NOT NULL DEFAULT 'candidate' CHECK (status IN (
        'candidate', 'selected', 'rejected', 'omitted'
    )),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_specs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'qa_passed', 'published', 'archived', 'failed'
    )),
    spec_json jsonb NOT NULL DEFAULT '{}',
    version integer NOT NULL DEFAULT 1,
    is_current boolean NOT NULL DEFAULT false,
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_qa_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    spec_id uuid REFERENCES demo_site_specs(id) ON DELETE SET NULL,
    report_type text NOT NULL DEFAULT 'visual' CHECK (report_type IN (
        'visual', 'adversarial', 'combined'
    )),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'passed', 'failed', 'warning'
    )),
    blocking_issues_json jsonb NOT NULL DEFAULT '[]',
    warnings_json jsonb NOT NULL DEFAULT '[]',
    screenshots_json jsonb NOT NULL DEFAULT '[]',
    report_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS demo_site_deployments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    spec_id uuid REFERENCES demo_site_specs(id) ON DELETE SET NULL,
    demo_slug text NOT NULL,
    demo_host text NOT NULL,
    demo_url text NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'published', 'failed', 'archived'
    )),
    published_at timestamptz,
    verified_at timestamptz,
    error_message text,
    metadata_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 5. MODEL CALLS AND SUPERVISION
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_model_calls (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid NOT NULL REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    batch_id uuid REFERENCES demo_site_batches(id) ON DELETE SET NULL,
    agent_run_id uuid REFERENCES agent_runs(id) ON DELETE SET NULL,
    agent_name text NOT NULL,
    stage text NOT NULL,
    model text NOT NULL,
    request_hash text NOT NULL,
    input_token_estimate integer,
    output_token_estimate integer,
    status text NOT NULL DEFAULT 'running' CHECK (status IN (
        'running', 'succeeded', 'failed', 'rate_limited'
    )),
    http_status integer,
    error_code text,
    latency_ms integer,
    attempt_number integer NOT NULL DEFAULT 1,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS demo_factory_supervisor_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    project_id uuid REFERENCES demo_site_projects(id) ON DELETE CASCADE,
    batch_id uuid REFERENCES demo_site_batches(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    severity text NOT NULL DEFAULT 'info' CHECK (severity IN (
        'info', 'warning', 'error'
    )),
    stage text,
    message text,
    payload_json jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 6. INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_demo_site_batches_tenant_status ON demo_site_batches(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_demo_site_batches_created ON demo_site_batches(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_demo_site_batch_rows_tenant_batch ON demo_site_batch_rows(tenant_id, batch_id);
CREATE INDEX IF NOT EXISTS idx_demo_site_batch_rows_batch_order ON demo_site_batch_rows(batch_id, row_number, rank);
CREATE INDEX IF NOT EXISTS idx_demo_site_batch_rows_status ON demo_site_batch_rows(batch_id, status, row_number);
CREATE INDEX IF NOT EXISTS idx_demo_site_batch_rows_project ON demo_site_batch_rows(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_site_batch_rows_batch_row
    ON demo_site_batch_rows(batch_id, row_number);

CREATE INDEX IF NOT EXISTS idx_demo_site_projects_tenant_status ON demo_site_projects(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_demo_site_projects_batch ON demo_site_projects(batch_id);
CREATE INDEX IF NOT EXISTS idx_demo_site_projects_batch_row ON demo_site_projects(batch_row_id);
CREATE INDEX IF NOT EXISTS idx_demo_site_projects_created ON demo_site_projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_demo_site_projects_trace ON demo_site_projects(trace_id) WHERE trace_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_site_projects_tenant_slug
    ON demo_site_projects(tenant_id, demo_slug);

CREATE INDEX IF NOT EXISTS idx_demo_site_source_snapshots_project ON demo_site_source_snapshots(project_id);
CREATE INDEX IF NOT EXISTS idx_demo_site_assets_project ON demo_site_assets(project_id);
CREATE INDEX IF NOT EXISTS idx_demo_site_assets_status ON demo_site_assets(project_id, status);
CREATE INDEX IF NOT EXISTS idx_demo_site_brand_documents_project ON demo_site_brand_documents(project_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_site_framework_sources_key
    ON demo_site_framework_sources(tenant_id, source_key);
CREATE INDEX IF NOT EXISTS idx_demo_site_framework_patterns_tags
    ON demo_site_framework_patterns USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_demo_site_framework_retrievals_project
    ON demo_site_framework_retrievals(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_demo_site_reviews_project_status ON demo_site_reviews(project_id, status);
CREATE INDEX IF NOT EXISTS idx_demo_site_specs_project_status ON demo_site_specs(project_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_site_specs_one_current
    ON demo_site_specs(project_id) WHERE is_current;
CREATE INDEX IF NOT EXISTS idx_demo_site_qa_reports_project ON demo_site_qa_reports(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_demo_site_deployments_project ON demo_site_deployments(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_site_deployments_slug_current
    ON demo_site_deployments(tenant_id, demo_slug) WHERE status = 'published';

CREATE INDEX IF NOT EXISTS idx_demo_model_calls_project ON demo_model_calls(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_demo_model_calls_stage_status ON demo_model_calls(stage, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_demo_model_calls_batch ON demo_model_calls(batch_id);
CREATE INDEX IF NOT EXISTS idx_demo_factory_supervisor_events_project
    ON demo_factory_supervisor_events(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_demo_factory_supervisor_events_batch
    ON demo_factory_supervisor_events(batch_id, created_at DESC);

-- =============================================================================
-- 7. RLS AND UPDATED_AT TRIGGERS
-- =============================================================================

ALTER TABLE demo_site_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_batch_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_source_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_brand_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_framework_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_framework_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_framework_retrievals ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_specs ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_qa_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_site_deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_model_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_factory_supervisor_events ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'demo_site_batches',
        'demo_site_batch_rows',
        'demo_site_projects',
        'demo_site_source_snapshots',
        'demo_site_assets',
        'demo_site_brand_documents',
        'demo_site_framework_sources',
        'demo_site_framework_patterns',
        'demo_site_framework_retrievals',
        'demo_site_reviews',
        'demo_site_specs',
        'demo_site_qa_reports',
        'demo_site_deployments',
        'demo_model_calls',
        'demo_factory_supervisor_events'
    ]
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_%I ON %I', table_name, table_name);
        EXECUTE format(
            'CREATE POLICY tenant_isolation_%I ON %I USING (tenant_id = nullif(current_setting(''app.current_tenant'', true), '''')::uuid)',
            table_name,
            table_name
        );
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', table_name, table_name);
        EXECUTE format(
            'CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            table_name,
            table_name
        );
    END LOOP;
END $$;
