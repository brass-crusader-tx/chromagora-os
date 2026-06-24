-- Migration: 000017_create_spawn_contracts
-- Created: 2026-06-24
-- Description: Spawn contracts for tactical subagents

CREATE TABLE IF NOT EXISTS spawn_contracts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_agent_run_id uuid NOT NULL REFERENCES agent_runs(id),
    business_id uuid NOT NULL REFERENCES businesses(id),
    subagent_type text NOT NULL,
    objective text NOT NULL,
    scope text,
    input_refs jsonb NOT NULL DEFAULT '[]',
    allowed_tools jsonb NOT NULL DEFAULT '[]',
    forbidden_tools jsonb NOT NULL DEFAULT '[]',
    source_boundaries jsonb NOT NULL DEFAULT '{}',
    max_side_effects text NOT NULL DEFAULT 'none' CHECK (max_side_effects IN ('none', 'internal_only', 'low_risk_external')),
    ttl_seconds int NOT NULL DEFAULT 300,
    token_budget jsonb NOT NULL DEFAULT '{}',
    output_schema_name text,
    evidence_requirements jsonb NOT NULL DEFAULT '[]',
    success_condition text,
    kill_condition text,
    authority_level int NOT NULL DEFAULT 1,
    memory_write_policy text NOT NULL DEFAULT 'no_durable_write' CHECK (memory_write_policy IN ('no_durable_write', 'write_to_business_twin', 'write_to_memory')),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'killed', 'expired')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_spawn_parent ON spawn_contracts(parent_agent_run_id);
CREATE INDEX IF NOT EXISTS idx_spawn_business ON spawn_contracts(business_id);
CREATE INDEX IF NOT EXISTS idx_spawn_status ON spawn_contracts(status);
ALTER TABLE spawn_contracts ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_spawn ON spawn_contracts
    USING (parent_agent_run_id IN (
        SELECT id FROM agent_runs
        WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
    ));
