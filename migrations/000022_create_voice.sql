-- Migration: 000022_create_voice
-- Created: 2026-06-24
-- Description: Call records and call summaries for voice agent prep
-- Chapter 23 — Voice Agent Preparation

-- Call records: inbound/outbound call tracking
CREATE TABLE IF NOT EXISTS call_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES businesses(id),
    caller_phone text NOT NULL,
    caller_name text,
    call_status text NOT NULL DEFAULT 'inbound' CHECK (call_status IN ('inbound', 'outbound', 'missed', 'voicemail')),
    started_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz,
    recording_url text,
    transcript_text text,
    consent_recorded boolean NOT NULL DEFAULT false,
    trace_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_call_records_business ON call_records(business_id);
CREATE INDEX IF NOT EXISTS idx_call_records_status ON call_records(call_status);
CREATE INDEX IF NOT EXISTS idx_call_records_started ON call_records(started_at DESC);
ALTER TABLE call_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_call_records ON call_records
    USING (
        business_id IN (
            SELECT id FROM businesses
            WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
        )
    );

-- Call summaries: structured extraction from call transcripts
CREATE TABLE IF NOT EXISTS call_summaries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_record_id uuid NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    intent text NOT NULL DEFAULT 'unknown',
    service_type text,
    address_or_area text,
    urgency text NOT NULL DEFAULT 'normal' CHECK (urgency IN ('low', 'normal', 'high', 'emergency')),
    lead_quality text NOT NULL DEFAULT 'unknown' CHECK (lead_quality IN ('hot', 'warm', 'cold', 'unknown')),
    escalation_required boolean NOT NULL DEFAULT false,
    escalation_reason text,
    structured_notes jsonb NOT NULL DEFAULT '{}',
    confidence float NOT NULL DEFAULT 0.0,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_call_summaries_call ON call_summaries(call_record_id);
CREATE INDEX IF NOT EXISTS idx_call_summaries_intent ON call_summaries(intent);
CREATE INDEX IF NOT EXISTS idx_call_summaries_urgency ON call_summaries(urgency);
ALTER TABLE call_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_call_summaries ON call_summaries
    USING (
        call_record_id IN (
            SELECT id FROM call_records
            WHERE business_id IN (
                SELECT id FROM businesses
                WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
            )
        )
    );
