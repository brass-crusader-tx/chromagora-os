-- Demo Engine finish-buildout support.

-- Separate technical publish state from operator sendability review.
ALTER TABLE demo_site_projects
    ADD COLUMN IF NOT EXISTS sendability_status text NOT NULL DEFAULT 'unreviewed'
        CHECK (sendability_status IN ('unreviewed', 'needs_edits', 'sendable', 'sent', 'archived'));

ALTER TABLE demo_site_projects
    ADD COLUMN IF NOT EXISTS sendability_score integer
        CHECK (sendability_score IS NULL OR (sendability_score >= 0 AND sendability_score <= 100));

ALTER TABLE demo_site_projects
    ADD COLUMN IF NOT EXISTS operator_review_json jsonb NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_demo_site_projects_sendability
    ON demo_site_projects(tenant_id, sendability_status, created_at DESC);
