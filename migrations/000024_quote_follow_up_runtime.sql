-- Migration: 000024_quote_follow_up_runtime
-- Created: 2026-06-26
-- Description: Extend tables for the quote follow-up runtime loop.
--              Adds follow-up tracking columns to quotes, idempotency to events,
--              CRM task linkage to proposals/approvals/executions/drafts,
--              and introduces the crm_tasks table.

-- =============================================================================
-- 1. EXTEND quotes TABLE
-- =============================================================================

-- Add tenant-scoped and follow-up tracking columns
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id);
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS customer_id uuid;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS currency text NOT NULL DEFAULT 'CAD';
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS description text;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS accepted_at timestamptz;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS declined_at timestamptz;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS follow_up_count integer NOT NULL DEFAULT 0;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS next_follow_up_at timestamptz;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS stale_detected_at timestamptz;

-- Update the status CHECK constraint to support follow-up lifecycle states
ALTER TABLE quotes DROP CONSTRAINT IF EXISTS quotes_status_check;
ALTER TABLE quotes ADD CONSTRAINT quotes_status_check
    CHECK (status IN (
        'draft', 'sent', 'stale', 'follow_up_pending', 'followed_up',
        'accepted', 'declined', 'expired', 'cancelled'
    ));

-- Indexes for detector queries (business + status) and staleness queries (sent_at)
CREATE INDEX IF NOT EXISTS idx_quotes_business_status ON quotes(business_id, status);
CREATE INDEX IF NOT EXISTS idx_quotes_sent_at ON quotes(sent_at);

-- =============================================================================
-- 2. EXTEND events TABLE
-- =============================================================================

-- Add idempotency and entity-scoped columns for reliable event emission
ALTER TABLE events ADD COLUMN IF NOT EXISTS idempotency_key text;
ALTER TABLE events ADD COLUMN IF NOT EXISTS processed_at timestamptz;
ALTER TABLE events ADD COLUMN IF NOT EXISTS entity_type text;
ALTER TABLE events ADD COLUMN IF NOT EXISTS entity_id uuid;

-- Unique partial index for idempotent event emission
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_idempotency_key
    ON events(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Index for entity-scoped event lookups
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_type, entity_id);

-- =============================================================================
-- 3. EXTEND action_proposals TABLE
-- =============================================================================

-- Link proposals to quotes, customers, agent runs, and policy decisions
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS quote_id uuid REFERENCES quotes(id);
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS customer_id uuid;
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS agent_run_id uuid REFERENCES agent_runs(id);
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS reason text;
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS requires_approval boolean NOT NULL DEFAULT true;
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS policy_decision_id uuid;

-- =============================================================================
-- 4. EXTEND approval_requests TABLE
-- =============================================================================

-- Add human-readable fields and risk classification for approval UX
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS title text;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS summary text;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS draft_payload jsonb;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS risk_level text
    CHECK (risk_level IN ('low', 'medium', 'high', 'critical'));
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS agent_run_id uuid REFERENCES agent_runs(id);

-- =============================================================================
-- 5. EXTEND action_executions TABLE
-- =============================================================================

-- Add execution_mode to classify the type of action performed
ALTER TABLE action_executions ADD COLUMN IF NOT EXISTS execution_mode text
    CHECK (execution_mode IN (
        'create_task', 'create_message_draft', 'send_message', 'internal_update'
    ));

-- =============================================================================
-- 6. EXTEND message_drafts TABLE
-- =============================================================================

-- Link drafts to tenants, quotes, customers, agent runs, and approval requests
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id);
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS quote_id uuid REFERENCES quotes(id);
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS customer_id uuid;
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS agent_run_id uuid REFERENCES agent_runs(id);
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS approval_request_id uuid REFERENCES approval_requests(id);
ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT 'manual';

-- =============================================================================
-- 7. CREATE crm_tasks TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS crm_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    business_id uuid NOT NULL REFERENCES businesses(id),
    quote_id uuid REFERENCES quotes(id),
    customer_id uuid,
    lead_id uuid REFERENCES leads(id),
    agent_run_id uuid REFERENCES agent_runs(id),
    action_proposal_id uuid REFERENCES action_proposals(id),
    approval_request_id uuid REFERENCES approval_requests(id),
    title text NOT NULL,
    description text,
    due_at timestamptz,
    status text NOT NULL DEFAULT 'open' CHECK (status IN (
        'open', 'in_progress', 'completed', 'cancelled'
    )),
    source text NOT NULL DEFAULT 'agent',
    trace_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_crm_tasks_business ON crm_tasks(business_id);
CREATE INDEX IF NOT EXISTS idx_crm_tasks_quote ON crm_tasks(quote_id);
CREATE INDEX IF NOT EXISTS idx_crm_tasks_status ON crm_tasks(status);
CREATE INDEX IF NOT EXISTS idx_crm_tasks_trace ON crm_tasks(trace_id);

-- Row-level security: tenant isolation via business_id
ALTER TABLE crm_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_crm_tasks ON crm_tasks
    USING (business_id IN (
        SELECT id FROM businesses WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));

-- Auto-update updated_at timestamp
CREATE TRIGGER update_crm_tasks_updated_at
    BEFORE UPDATE ON crm_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 8. BUSINESS PREFERENCES — follow-up settings (documented usage)
-- =============================================================================
-- The following keys are expected in the business_preferences table:
--
--   stale_quote_threshold_days        (int, default 3)
--       Number of days after sent_at before a quote is considered stale.
--
--   max_quote_follow_ups              (int, default 3)
--       Maximum number of follow-up attempts before stopping.
--
--   follow_up_interval_days           (int, default 3)
--       Number of days to wait between repeat follow-up attempts.
--
--   quote_follow_up_requires_approval (boolean, default true)
--       Whether follow-up message drafts require human approval.
--
--   preferred_follow_up_channel      (text, default "email")
--       Channel preference: "email" or "sms".
--
--   follow_up_tone                   (text, nullable)
--       Optional tone hint for follow-up message generation
--       (e.g. "friendly", "urgent", "value-focused").
--
-- No DDL needed — callers upsert these keys at runtime.
