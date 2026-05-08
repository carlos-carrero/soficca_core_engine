-- =============================================================================
-- Soficca Cardio Pilot — Database Schema (DRAFT)
-- =============================================================================
--
-- Status: DRAFT — Do not apply to production.
-- Created: 2026-05-06
-- Stage: 3A Planning
-- Provider: Postgres / Supabase compatible
--
-- This schema is for planning review only.
-- It will be finalized and applied in Stage 3B.
--
-- Product boundary:
--   AI structures the signal.
--   Human confirms or corrects.
--   Soficca governs the route.
--   Physicians make the final decision.
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. pilot_sessions
-- =============================================================================
-- Groups a demo/pilot run. One per session. Append-only.

CREATE TABLE pilot_sessions (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    label           text,                                   -- optional human label
    mode            text        NOT NULL DEFAULT 'local_browser_session',
    notes           text,
    environment     text        NOT NULL DEFAULT 'development',
    created_by      text                                    -- optional, future: user id
);

CREATE INDEX idx_pilot_sessions_created_at ON pilot_sessions (created_at DESC);

-- =============================================================================
-- 2. pilot_cases
-- =============================================================================
-- Top-level case record. One per case. Status is updatable.

CREATE TABLE pilot_cases (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              uuid        REFERENCES pilot_sessions(id) ON DELETE CASCADE,
    case_id                 text        NOT NULL UNIQUE,     -- application-level ID
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    source                  text        NOT NULL DEFAULT 'free_text',
    raw_narrative           text        NOT NULL,
    chief_complaint_summary text,
    current_status          text        NOT NULL DEFAULT 'pending_intake',
    final_route             text,                            -- PathId or null
    decision_status         text,                            -- DecisionStatus or null
    human_review_required   boolean     NOT NULL DEFAULT true,
    extraction_source       text,                            -- 'ai' or 'mock'
    routing_source          text,                            -- 'backend' or 'mock_fallback'
    is_simulated            boolean     NOT NULL DEFAULT true,
    contains_pii_warning    boolean     NOT NULL DEFAULT false,
    metadata_json           jsonb       DEFAULT '{}'::jsonb
);

CREATE INDEX idx_pilot_cases_session_id ON pilot_cases (session_id);
CREATE INDEX idx_pilot_cases_case_id ON pilot_cases (case_id);
CREATE INDEX idx_pilot_cases_created_at ON pilot_cases (created_at DESC);
CREATE INDEX idx_pilot_cases_final_route ON pilot_cases (final_route);
CREATE INDEX idx_pilot_cases_current_status ON pilot_cases (current_status);

-- =============================================================================
-- 3. ai_extractions
-- =============================================================================
-- Store AI extraction results. Append-only for auditability.

CREATE TABLE ai_extractions (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    extraction_id               text        NOT NULL,        -- application-level ID
    model                       text        NOT NULL,
    extraction_source           text        NOT NULL,        -- 'ai' or 'mock'
    confidence                  float       NOT NULL,
    structured_summary          text,
    fields_json                 jsonb       NOT NULL,        -- CardioExtractionFields
    field_evidence_json         jsonb       DEFAULT '[]'::jsonb,
    missing_information_json    jsonb       DEFAULT '{}'::jsonb,
    completion_questions_json   jsonb       DEFAULT '[]'::jsonb,
    quality_flags_json          jsonb       DEFAULT '[]'::jsonb,
    pii_warnings_json           jsonb       DEFAULT '[]'::jsonb,
    warnings_json               jsonb       DEFAULT '[]'::jsonb,
    unmapped_signals_json       jsonb       DEFAULT '[]'::jsonb,
    possible_conflicts_json     jsonb       DEFAULT '[]'::jsonb,
    raw_response_json           jsonb,                       -- optional: full AI response
    created_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_extractions_case_id ON ai_extractions (case_id);
CREATE INDEX idx_ai_extractions_created_at ON ai_extractions (created_at DESC);

-- =============================================================================
-- 4. human_corrections
-- =============================================================================
-- Store human confirmation/edits. Append-only.

CREATE TABLE human_corrections (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    reviewed_at                 timestamptz NOT NULL DEFAULT now(),
    human_edits_applied         boolean     NOT NULL DEFAULT false,
    fields_edited_count         integer     NOT NULL DEFAULT 0,
    diffs_json                  jsonb       NOT NULL DEFAULT '[]'::jsonb,
    final_structured_input_json jsonb       NOT NULL,        -- final CardioExtractionFields
    reviewer_label              text                         -- optional: who confirmed
);

CREATE INDEX idx_human_corrections_case_id ON human_corrections (case_id);

-- =============================================================================
-- 5. engine_reports
-- =============================================================================
-- Store deterministic Soficca routing output. Append-only.

CREATE TABLE engine_reports (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                 uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    route                   text,                            -- PathId
    decision_status         text,                            -- DecisionStatus
    report_json             jsonb       NOT NULL,            -- Full CardioReport
    engine_input_json       jsonb       NOT NULL,            -- CardioPayload
    safety_json             jsonb,                           -- CardioSafety
    trace_json              jsonb,                           -- CardioTrace
    activated_rules_json    jsonb       DEFAULT '[]'::jsonb,
    engine_version          text,
    ruleset_version         text,
    safety_policy_version   text,
    contract_version        text,
    created_at              timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_engine_reports_case_id ON engine_reports (case_id);
CREATE INDEX idx_engine_reports_route ON engine_reports (route);

-- =============================================================================
-- 6. audit_records
-- =============================================================================
-- Store full auditable case records. Append-only, event-like.

CREATE TABLE audit_records (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    audit_id            text        NOT NULL,                -- application-level ID
    audit_json          jsonb       NOT NULL,                -- Full CardioPilotAuditRecord
    markdown_snapshot   text,                                -- optional rendered markdown
    generated_at        timestamptz NOT NULL DEFAULT now(),
    exported_count      integer     NOT NULL DEFAULT 0
);

CREATE INDEX idx_audit_records_case_id ON audit_records (case_id);
CREATE INDEX idx_audit_records_audit_id ON audit_records (audit_id);

-- =============================================================================
-- 7. reviewer_feedback
-- =============================================================================
-- Store physician/reviewer feedback. Append-only (multiple reviewers possible).

CREATE TABLE reviewer_feedback (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    reviewer_name               text,
    reviewer_role               text,
    route_appropriate           text        NOT NULL,        -- agree, partially_agree, disagree
    usefulness_score            integer     NOT NULL,        -- 1-5
    missing_info_surfaced       text,                        -- yes, partially, no, not_applicable
    safety_flags_assessment     text,                        -- no, missing_flag, incorrect_flag, unsure
    estimated_review_time_saved text,                        -- 0_minutes, 1_2_minutes, etc.
    useful_before_consultation  text,                        -- yes, maybe, no
    comments                    text,
    reviewed_at                 timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_reviewer_feedback_case_id ON reviewer_feedback (case_id);

-- =============================================================================
-- 8. session_summaries
-- =============================================================================
-- Store aggregate session summaries. Append-only, event-like.

CREATE TABLE session_summaries (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id                  uuid        NOT NULL REFERENCES pilot_sessions(id) ON DELETE CASCADE,
    summary_id                  text        NOT NULL,        -- application-level ID
    metrics_json                jsonb       NOT NULL,        -- SessionMetrics
    route_distribution_json     jsonb,
    reviewer_metrics_json       jsonb,
    workflow_impact_json        jsonb,
    governance_metrics_json     jsonb,
    safety_assertions_json      jsonb,
    case_summaries_json         jsonb,
    generated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_session_summaries_session_id ON session_summaries (session_id);

-- =============================================================================
-- Updated_at trigger (reusable)
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_pilot_sessions
    BEFORE UPDATE ON pilot_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_pilot_cases
    BEFORE UPDATE ON pilot_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- End of draft schema
-- =============================================================================
--
-- DRAFT ONLY. Do not apply to production.
-- Finalize in Stage 3B after planning review.
--
-- Future tables (not included yet):
--   - organizations
--   - users / reviewers
--   - access_tokens
--   - case_events (event sourcing)
--   - export_events
-- =============================================================================
