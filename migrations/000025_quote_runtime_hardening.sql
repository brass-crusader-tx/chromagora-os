-- Migration: 000025_quote_runtime_hardening
-- Created: 2026-06-26
-- Description: Hardens the quote follow-up runtime with event claiming,
--              retries/dead-lettering, idempotent approvals/executions,
--              and worker heartbeat support.

-- =============================================================================
-- 1. EVENT CLAIMING / RETRIES / DEAD LETTERS
-- =============================================================================

ALTER TABLE events ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'pending';
ALTER TABLE events ADD COLUMN IF NOT EXISTS claimed_by text;
ALTER TABLE events ADD COLUMN IF NOT EXISTS claimed_at timestamptz;
ALTER TABLE events ADD COLUMN IF NOT EXISTS retry_count integer NOT NULL DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS max_retries integer NOT NULL DEFAULT 5;
ALTER TABLE events ADD COLUMN IF NOT EXISTS last_error text;
ALTER TABLE events ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz;
ALTER TABLE events ADD COLUMN IF NOT EXISTS dead_lettered_at timestamptz;

ALTER TABLE events DROP CONSTRAINT IF EXISTS events_status_check;
ALTER TABLE events ADD CONSTRAINT events_status_check
    CHECK (status IN ('pending', 'processing', 'processed', 'failed', 'dead_letter'));

UPDATE events
SET status = 'processed'
WHERE processed_at IS NOT NULL AND status <> 'processed';

CREATE INDEX IF NOT EXISTS idx_events_status_attempt
    ON events(status, next_attempt_at, occurred_at)
    WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_events_claimed_by ON events(claimed_by) WHERE claimed_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_dead_letter ON events(dead_lettered_at) WHERE status = 'dead_letter';

-- =============================================================================
-- 2. IDEMPOTENCY KEYS ON PROPOSALS / APPROVALS / EXECUTIONS / ARTIFACTS
-- =============================================================================

ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_action_proposals_idempotency
    ON action_proposals(tenant_id, business_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_approval_requests_idempotency
    ON approval_requests(tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- Existing status check did not include the transitional 'running' state that
-- action_executor inserts before completion.
ALTER TABLE action_executions DROP CONSTRAINT IF EXISTS action_executions_result_status_check;
ALTER TABLE action_executions ADD CONSTRAINT action_executions_result_status_check
    CHECK (result_status IN (
        'running', 'dry_run', 'success', 'failed', 'blocked',
        'approval_required', 'cancelled'
    ));

CREATE UNIQUE INDEX IF NOT EXISTS idx_action_executions_idempotency
    ON action_executions(tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_crm_tasks_idempotency
    ON crm_tasks(tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE message_drafts ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_message_drafts_idempotency
    ON message_drafts(business_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- Follow-up runtime settings are stored as one preference value per business
-- key. PostgREST upserts use ON CONFLICT (business_id, key), which requires
-- this uniqueness in both fresh and upgraded databases.
WITH ranked_preferences AS (
    SELECT
        id,
        row_number() OVER (
            PARTITION BY business_id, key
            ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
        ) AS preference_rank
    FROM business_preferences
)
DELETE FROM business_preferences
USING ranked_preferences
WHERE business_preferences.id = ranked_preferences.id
  AND ranked_preferences.preference_rank > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_business_preferences_business_key
    ON business_preferences(business_id, key);

-- =============================================================================
-- 3. WORKER HEARTBEATS
-- =============================================================================

CREATE TABLE IF NOT EXISTS worker_heartbeats (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id text NOT NULL UNIQUE,
    worker_type text NOT NULL,
    status text NOT NULL DEFAULT 'running' CHECK (status IN (
        'starting', 'running', 'idle', 'stopping', 'stopped', 'failed'
    )),
    last_started_at timestamptz NOT NULL DEFAULT now(),
    last_heartbeat_at timestamptz NOT NULL DEFAULT now(),
    last_cycle_json jsonb NOT NULL DEFAULT '{}',
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_worker_heartbeats_type ON worker_heartbeats(worker_type);
CREATE INDEX IF NOT EXISTS idx_worker_heartbeats_last_seen ON worker_heartbeats(last_heartbeat_at DESC);

CREATE TRIGGER update_worker_heartbeats_updated_at
    BEFORE UPDATE ON worker_heartbeats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
