-- =============================================================================
-- Migration 001: Cardio Pilot Initial Schema
-- =============================================================================
-- Stage: 3B
-- Created: 2026-05-06
-- Provider: Postgres / Supabase compatible
--
-- Product boundary:
--   AI structures the signal.
--   Human confirms or corrects.
--   Soficca governs the route.
--   Physicians make the final decision.
-- =============================================================================

-- Enable UUID generation (Supabase has this by default)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Schema migrations tracking table
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     text        PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 1. pilot_sessions
-- =============================================================================

CREATE TABLE pilot_sessions (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    label           text,
    mode            text        NOT NULL DEFAULT 'local_browser_session',
    notes           text,
    environment     text        NOT NULL DEFAULT 'development',
    created_by      text
);

CREATE INDEX idx_pilot_sessions_created_at ON pilot_sessions (created_at DESC);

-- =============================================================================
-- 2. pilot_cases
-- =============================================================================

CREATE TABLE pilot_cases (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              uuid        REFERENCES pilot_sessions(id) ON DELETE CASCADE,
    case_id                 text        NOT NULL UNIQUE,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    source                  text        NOT NULL DEFAULT 'free_text',
    raw_narrative           text        NOT NULL,
    chief_complaint_summary text,
    current_status          text        NOT NULL DEFAULT 'pending_intake',
    final_route             text,
    decision_status         text,
    human_review_required   boolean     NOT NULL DEFAULT true,
    extraction_source       text,
    routing_source          text,
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

CREATE TABLE ai_extractions (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    extraction_id               text        NOT NULL,
    model                       text        NOT NULL,
    extraction_source           text        NOT NULL,
    confidence                  float       NOT NULL,
    structured_summary          text,
    fields_json                 jsonb       NOT NULL,
    field_evidence_json         jsonb       DEFAULT '[]'::jsonb,
    missing_information_json    jsonb       DEFAULT '{}'::jsonb,
    completion_questions_json   jsonb       DEFAULT '[]'::jsonb,
    quality_flags_json          jsonb       DEFAULT '[]'::jsonb,
    pii_warnings_json           jsonb       DEFAULT '[]'::jsonb,
    warnings_json               jsonb       DEFAULT '[]'::jsonb,
    unmapped_signals_json       jsonb       DEFAULT '[]'::jsonb,
    possible_conflicts_json     jsonb       DEFAULT '[]'::jsonb,
    raw_response_json           jsonb,
    created_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_extractions_case_id ON ai_extractions (case_id);
CREATE INDEX idx_ai_extractions_created_at ON ai_extractions (created_at DESC);

-- =============================================================================
-- 4. human_corrections
-- =============================================================================

CREATE TABLE human_corrections (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    reviewed_at                 timestamptz NOT NULL DEFAULT now(),
    human_edits_applied         boolean     NOT NULL DEFAULT false,
    fields_edited_count         integer     NOT NULL DEFAULT 0,
    diffs_json                  jsonb       NOT NULL DEFAULT '[]'::jsonb,
    final_structured_input_json jsonb       NOT NULL,
    reviewer_label              text
);

CREATE INDEX idx_human_corrections_case_id ON human_corrections (case_id);

-- =============================================================================
-- 5. engine_reports
-- =============================================================================

CREATE TABLE engine_reports (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                 uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    route                   text,
    decision_status         text,
    report_json             jsonb       NOT NULL,
    engine_input_json       jsonb       NOT NULL,
    safety_json             jsonb,
    trace_json              jsonb,
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

CREATE TABLE audit_records (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    audit_id            text        NOT NULL,
    audit_json          jsonb       NOT NULL,
    markdown_snapshot   text,
    generated_at        timestamptz NOT NULL DEFAULT now(),
    exported_count      integer     NOT NULL DEFAULT 0
);

CREATE INDEX idx_audit_records_case_id ON audit_records (case_id);
CREATE INDEX idx_audit_records_audit_id ON audit_records (audit_id);

-- =============================================================================
-- 7. reviewer_feedback
-- =============================================================================

CREATE TABLE reviewer_feedback (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                     uuid        NOT NULL REFERENCES pilot_cases(id) ON DELETE CASCADE,
    reviewer_name               text,
    reviewer_role               text,
    route_appropriate           text        NOT NULL,
    usefulness_score            integer     NOT NULL,
    missing_info_surfaced       text,
    safety_flags_assessment     text,
    estimated_review_time_saved text,
    useful_before_consultation  text,
    comments                    text,
    reviewed_at                 timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_reviewer_feedback_case_id ON reviewer_feedback (case_id);

-- =============================================================================
-- 8. session_summaries
-- =============================================================================

CREATE TABLE session_summaries (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id                  uuid        NOT NULL REFERENCES pilot_sessions(id) ON DELETE CASCADE,
    summary_id                  text        NOT NULL,
    metrics_json                jsonb       NOT NULL,
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
-- Updated_at trigger
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
-- Record this migration
-- =============================================================================

INSERT INTO schema_migrations (version) VALUES ('001_cardio_pilot_initial_schema');
