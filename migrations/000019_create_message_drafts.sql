-- Migration: 000019_create_message_drafts
-- Created: 2026-06-24
-- Description: Email/SMS draft artifacts (no sending)

CREATE TABLE IF NOT EXISTS message_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    channel text NOT NULL CHECK (channel IN ('email', 'sms')),
    recipient text NOT NULL,
    subject text,
    body text NOT NULL,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'approval_required', 'approved', 'sent', 'cancelled'
    )),
    related_action_proposal_id uuid REFERENCES action_proposals(id),
    related_workflow_run_id uuid REFERENCES workflow_runs(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_drafts_business ON message_drafts(business_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON message_drafts(status);
ALTER TABLE message_drafts ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_drafts ON message_drafts
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
