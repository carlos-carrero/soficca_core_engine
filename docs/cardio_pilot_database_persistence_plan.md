# Soficca Cardio Pilot — Database Persistence Plan

**Stage:** 3A — Architecture Planning  
**Status:** Complete  
**Created:** 2026-05-06  
**Updated:** 2026-05-06 (Stage 3D completed)  
**Scope:** Planning only. No database connections, migrations, or production logic changes.

> **Stage 3B status:** Database foundation implemented. See `docs/cardio_pilot_database_setup.md`.  
> **Stage 3C status:** Repository layer implemented. See `src/repositories/`.  
> **Stage 3D status:** Persistence endpoints implemented. See `api/routers/cardio_persistence_router.py`.

---

## 1. Current State

### Data Flow

```
Free-text intake (user types narrative)
  → AI extraction (backend /v1/cardio/pilot/extract)
  → Human confirmation/correction (frontend)
  → Deterministic routing (backend /v1/cardio/pilot/report)
  → Governed report (frontend state)
  → Audit export (browser file download)
  → Reviewer queue (frontend state)
  → Reviewer feedback (frontend state)
  → Local session metrics (computed from frontend state)
  → Session summary export (browser file download)
```

### Where Data Is Created

| Step | Created In | Current Storage |
|------|-----------|----------------|
| Narrative input | Frontend (IntakeScreen) | React state (`narrative`) |
| AI extraction | Backend endpoint → Frontend | React state (`extraction: CardioExtraction`) |
| Human correction | Frontend (ExtractionPreviewScreen) | React state (`humanCorrection: HumanCorrectionStatus`) |
| Engine input / routing | Backend endpoint → Frontend | React state (`pilotCase.engine_input`, `pilotCase.engine_report`) |
| Full PilotCase bundle | Frontend (page.tsx) | React state (`pilotCase`, `completedCases[]`) |
| Audit record | Frontend (export-helpers) | Browser file download only |
| Reviewer queue | Frontend (page.tsx) | React state (`reviewerQueue: ReviewerQueueItem[]`) |
| Reviewer feedback | Frontend (ReviewerWorkspace) | React state (inside ReviewerQueueItem) |
| Session metrics | Frontend (computed) | Derived from `completedCases` + `reviewerQueue` |
| Session summary | Frontend (session-export) | Browser file download only |

### Key Types (Frontend)

- `PilotCase` — top-level case with extraction, engine_input, engine_report, humanCorrection
- `CardioExtraction` — AI extraction output with fields, evidence, quality flags, PII warnings
- `HumanCorrectionStatus` — diffs between AI extraction and human-confirmed fields
- `CardioReport` — deterministic routing output (decision, safety, trace, versions)
- `CardioPayload` — engine input (state + context)
- `CardioPilotAuditRecord` — full auditable case record
- `ReviewerQueueItem` — case in reviewer queue with feedback
- `ReviewerFeedback` — structured physician feedback
- `SessionMetrics` — aggregated session metrics
- `CardioPilotSessionSummary` — exportable session summary

### What Data Is Included In Exports

**Case audit JSON/Markdown:**
- case_id, created_at, raw_narrative
- AI extraction record (model, fields, evidence, quality flags, PII warnings)
- Human correction (diffs, final structured input)
- Engine input and full engine report
- Signal chain, report integrity, safety assertions, pilot mode

**Session summary JSON/Markdown:**
- session_id, metrics, route distribution, AI intake metrics
- Governance metrics, workflow impact signals
- Reviewer metrics (agreement, usefulness, time saved)
- Per-case summaries (route, status, source, human edits, review status)
- Safety assertions, disclaimers

### What Should Become Persisted

| Data | Persist? | Reason |
|------|----------|--------|
| Raw narrative | Yes | Source signal for audit |
| AI extraction | Yes | Reproducibility, audit trail |
| Human correction | Yes | Human-in-the-loop evidence |
| Engine report | Yes | Deterministic output audit |
| Full audit record | Yes | Compliance, traceability |
| Reviewer feedback | Yes | Pilot outcome measurement |
| Session summary | Yes | Aggregated pilot evidence |
| Session metrics | Yes (computed or stored) | Cross-session analysis |

### What Should Remain Local/Transient

| Data | Reason |
|------|--------|
| UI state (selected tab, form inputs before submit) | Ephemeral interaction state |
| In-progress extraction (before confirmation) | Not yet committed |
| Signal analysis guidance (sidebar) | Computed real-time |
| Example case selection | UI convenience only |
| Quick fields before submit | Ephemeral input helpers |

---

## 2. Persistence Goals

1. **Persist completed case bundles** after routing, so cases survive session reload.
2. **Persist reviewer feedback** so pilot outcome data accumulates across sessions.
3. **Persist session summaries** for longitudinal pilot analysis.
4. **Maintain full audit trail** — never overwrite clinical workflow data.
5. **Backend-first access** — frontend never connects directly to database.
6. **Simulated data only** in early pilot — no real PHI.
7. **No changes to routing logic, extraction behavior, or product boundaries.**

---

## 3. Recommended Database Provider

**Supabase (Postgres)**

Reasons:
- Managed Postgres with built-in Row Level Security (RLS) for future access control.
- REST and realtime APIs available (but we will use backend-mediated access only).
- Encryption at rest included.
- Easy migration path to self-hosted Postgres if needed.
- Compatible with FastAPI + asyncpg/psycopg for server-side access.

Alternative: Any managed Postgres (Railway, Neon, AWS RDS). The schema is standard SQL.

---

## 4. Schema Proposal

### 4.1 pilot_sessions

Groups a demo/pilot run.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK, default gen_random_uuid() |
| created_at | timestamptz | default now() |
| updated_at | timestamptz | default now() |
| label | text | Optional human label |
| mode | text | e.g. "local_browser_session", "controlled_pilot" |
| notes | text | Optional notes |
| environment | text | e.g. "development", "staging", "pilot" |
| created_by | text | Optional (future: user id) |

**Behavior:** One per pilot run. Append-only (never deleted in pilot).

### 4.2 pilot_cases

Top-level case record.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| session_id | uuid | FK → pilot_sessions |
| case_id | text | Application-level ID (e.g. "CP-20260506-abc123") |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| source | text | "example_case", "free_text", "golden_scenario" |
| raw_narrative | text | Original free-text input |
| chief_complaint_summary | text | Short summary (from extraction) |
| current_status | text | Maps to CaseStatus enum |
| final_route | text | PathId or null |
| decision_status | text | DecisionStatus or null |
| human_review_required | boolean | Always true in pilot |
| extraction_source | text | "ai" or "mock" |
| routing_source | text | "backend" or "mock_fallback" |
| is_simulated | boolean | true for demo/example data |
| contains_pii_warning | boolean | true if PII detected |
| metadata_json | jsonb | Flexible metadata |

**Behavior:** One per case. Updated as case progresses through stages.

### 4.3 ai_extractions

Store AI extraction results. Append-only for auditability.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| case_id | uuid | FK → pilot_cases |
| extraction_id | text | Application-level ID |
| model | text | e.g. "gpt-4o-mini" |
| extraction_source | text | "ai" or "mock" |
| confidence | float | 0.0–1.0 |
| structured_summary | text | AI-generated summary |
| fields_json | jsonb | CardioExtractionFields |
| field_evidence_json | jsonb | CardioFieldEvidence[] |
| missing_information_json | jsonb | CardioMissingInformation |
| completion_questions_json | jsonb | string[] |
| quality_flags_json | jsonb | ExtractionQualityFlag[] |
| pii_warnings_json | jsonb | PiiWarning[] |
| warnings_json | jsonb | string[] |
| unmapped_signals_json | jsonb | string[] |
| possible_conflicts_json | jsonb | string[] |
| raw_response_json | jsonb | Optional: full AI response for debugging |
| created_at | timestamptz | |

**Behavior:** Append-only. A case could have multiple extractions (re-runs), but typically one. Latest can be determined by created_at.

### 4.4 human_corrections

Store human confirmation/edits before routing.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| case_id | uuid | FK → pilot_cases |
| reviewed_at | timestamptz | When human confirmed |
| human_edits_applied | boolean | Whether any fields changed |
| fields_edited_count | integer | Number of fields changed |
| diffs_json | jsonb | EditedFieldDiff[] |
| final_structured_input_json | jsonb | Final CardioExtractionFields after edits |
| reviewer_label | text | Optional: who confirmed |

**Behavior:** Append-only. Typically one per case. Multiple if re-reviewed.

### 4.5 engine_reports

Store deterministic Soficca routing output.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| case_id | uuid | FK → pilot_cases |
| route | text | PathId |
| decision_status | text | DecisionStatus |
| report_json | jsonb | Full CardioReport |
| engine_input_json | jsonb | CardioPayload sent to engine |
| decisive_inputs_json | jsonb | Key inputs that determined route |
| safety_json | jsonb | CardioSafety |
| trace_json | jsonb | CardioTrace |
| activated_rules_json | jsonb | string[] |
| engine_version | text | |
| ruleset_version | text | |
| safety_policy_version | text | |
| contract_version | text | |
| created_at | timestamptz | |

**Behavior:** Append-only. Typically one per case. If re-routed, new row is appended.

### 4.6 audit_records

Store full auditable case records (what gets exported).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| case_id | uuid | FK → pilot_cases |
| audit_id | text | Application-level ID |
| audit_json | jsonb | Full CardioPilotAuditRecord |
| markdown_snapshot | text | Optional: rendered markdown |
| generated_at | timestamptz | |
| exported_count | integer | How many times downloaded |

**Behavior:** Append-only. Multiple records possible if regenerated. Event-like.

### 4.7 reviewer_feedback

Store physician/reviewer feedback.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| case_id | uuid | FK → pilot_cases |
| reviewer_name | text | Optional |
| reviewer_role | text | Optional |
| route_appropriate | text | "agree", "partially_agree", "disagree" |
| usefulness_score | integer | 1–5 |
| missing_info_surfaced | text | "yes", "partially", "no", "not_applicable" |
| safety_flags_assessment | text | "no", "missing_flag", "incorrect_flag", "unsure" |
| estimated_review_time_saved | text | "0_minutes", "1_2_minutes", "3_5_minutes", "5_plus_minutes" |
| useful_before_consultation | text | "yes", "maybe", "no" |
| comments | text | |
| reviewed_at | timestamptz | |

**Behavior:** Append-only. A case could receive multiple reviews (different reviewers).

### 4.8 session_summaries

Store aggregate session summaries.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| session_id | uuid | FK → pilot_sessions |
| summary_id | text | Application-level ID |
| metrics_json | jsonb | SessionMetrics |
| route_distribution_json | jsonb | RouteDistribution |
| reviewer_metrics_json | jsonb | Reviewer aggregate metrics |
| workflow_impact_json | jsonb | WorkflowImpactSignals |
| governance_metrics_json | jsonb | GovernanceMetrics |
| safety_assertions_json | jsonb | SafetyAssertions |
| case_summaries_json | jsonb | CardioPilotSessionCaseSummary[] |
| generated_at | timestamptz | |

**Behavior:** Append-only. New summary generated each time session is exported.

---

## 5. Relationships

```
pilot_sessions (1) ──→ (many) pilot_cases
pilot_cases    (1) ──→ (many) ai_extractions        [append-only, latest wins for display]
pilot_cases    (1) ──→ (many) human_corrections     [append-only, latest wins for display]
pilot_cases    (1) ──→ (many) engine_reports         [append-only, latest wins for display]
pilot_cases    (1) ──→ (many) audit_records          [append-only, event-like]
pilot_cases    (1) ──→ (many) reviewer_feedback      [append-only, multiple reviewers possible]
pilot_sessions (1) ──→ (many) session_summaries      [append-only, event-like]
```

### Table Behavior Classification

| Table | Pattern | Rationale |
|-------|---------|-----------|
| pilot_sessions | One per pilot run | Grouping container |
| pilot_cases | One per case, updatable status | Central record, status updates allowed |
| ai_extractions | Append-only | Audit: never overwrite AI output |
| human_corrections | Append-only | Audit: preserve correction history |
| engine_reports | Append-only | Audit: never overwrite deterministic routing |
| audit_records | Append-only, event-like | Generated artifacts |
| reviewer_feedback | Append-only | Multiple reviews possible, never overwrite |
| session_summaries | Append-only, event-like | Snapshots at point in time |

**Design principle:** Prefer auditability over overwriting. Only `pilot_cases.current_status` is updatable. All clinical workflow records are append-only.

---

## 6. Data Privacy / Safety Model

### Early Pilot Constraints

- **Simulated data only.** All early pilot cases use anonymized/fictional narratives.
- **`is_simulated = true`** for all demo and pilot cases.
- **`contains_pii_warning`** flag stored per case (from AI extraction PII detection).
- **No real identifiable patient data** stored in early pilot.
- **No PHI claims.** This system does not claim HIPAA compliance at this stage.
- **No clinical validation claims.** Pilot measures operational signals only.

### Fields Requiring Sensitivity Awareness

| Field | Risk | Mitigation |
|-------|------|------------|
| raw_narrative | May contain names, IDs, addresses | PII detection flag, simulated-only policy |
| structured_summary | May reflect sensitive details | Same as narrative |
| audit_json | Contains full case data | Access control in future stages |
| comments (reviewer) | Free text | Simulated-only policy |

### Recommended Future Protections (Not Implemented Yet)

1. **Database-level RLS** — Row Level Security via Supabase policies.
2. **Encryption at rest** — Provided by Supabase/managed Postgres.
3. **Access logging** — Track who accessed what case data.
4. **Reviewer roles** — Role-based access (admin, reviewer, observer).
5. **Organization isolation** — Multi-tenant data separation.
6. **Retention policy** — Auto-archive or delete after N days in pilot.
7. **Audit event log** — Separate table tracking all read/write events.
8. **PII redaction service** — Strip detected PII before persisting (future).

---

## 7. Backend-First Access Model

### Architecture

```
Frontend (Next.js)
    ↓ HTTP API calls only
FastAPI Backend (soficca_core_engine)
    ↓ Server-side DB credentials
Postgres/Supabase Database
```

### Rules

- **Frontend NEVER connects directly to Supabase/Postgres.**
- **Frontend calls FastAPI backend endpoints for all persistence.**
- **Backend holds all database credentials.**
- **Backend handles validation, authorization, and data integrity.**
- **No `NEXT_PUBLIC_` database keys ever.**

### Expected Future Environment Variables (Backend Only)

```env
# Database connection
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Optional Supabase-specific (server-side only)
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # NEVER in frontend

# Existing
OPENAI_API_KEY=sk-...
CARDIO_EXTRACTION_MODEL=gpt-4o-mini
```

### Backend Responsibilities

- Insert/read/update pilot data
- Validate payloads before persistence
- Compute aggregated metrics from persisted data
- Enforce future auth/roles
- Never expose raw DB errors to frontend

---

## 8. Future Backend Endpoint Plan

All endpoints under existing prefix: `/v1/cardio/pilot/`

### Session Management

| Method | Path | Purpose |
|--------|------|---------|
| POST | /sessions | Create a new pilot session |
| GET | /sessions | List sessions |
| GET | /sessions/{session_id} | Get session details |

### Case Lifecycle

| Method | Path | Purpose |
|--------|------|---------|
| POST | /cases | Create persisted case (after intake) |
| GET | /cases | List cases (with filters) |
| GET | /cases/{case_id} | Read full case bundle |
| PATCH | /cases/{case_id}/status | Update case status |

### Case Sub-Resources (Append-Only)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /cases/{case_id}/extraction | Save AI extraction |
| POST | /cases/{case_id}/correction | Save human correction |
| POST | /cases/{case_id}/report | Save engine report |
| POST | /cases/{case_id}/audit | Save/generate audit record |
| POST | /cases/{case_id}/review | Save reviewer feedback |

### Aggregation

| Method | Path | Purpose |
|--------|------|---------|
| GET | /sessions/{session_id}/metrics | Compute persisted session metrics |
| POST | /sessions/{session_id}/summary | Generate and save session summary |
| GET | /sessions/{session_id}/summary | Get latest session summary |

### Export (Future)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /cases/{case_id}/audit/json | Download audit JSON |
| GET | /cases/{case_id}/audit/markdown | Download audit Markdown |
| GET | /sessions/{session_id}/summary/json | Download session summary JSON |
| GET | /sessions/{session_id}/summary/markdown | Download session summary Markdown |

---

## 9. Migration Strategy — Local State → Persisted

### Guiding Principles

- **No big bang.** Migrate incrementally.
- **Local fallback.** Frontend continues working without DB during transition.
- **Backend-first.** Add persistence to backend before wiring frontend.
- **Feature flag.** Optional `PERSISTENCE_ENABLED=true` env var to gate DB writes.

### Staged Migration Plan

#### Stage 3B — Database Configuration & Migrations

- Add `DATABASE_URL` to backend `.env.example`
- Add database dependency (asyncpg or psycopg2)
- Create SQL migration files (from draft schema)
- Create `db/` module in backend with connection pool
- Run migrations against dev database
- **No frontend changes. No endpoint changes.**

#### Stage 3C — Backend Persistence Layer

- Create repository modules: `repositories/pilot_cases.py`, `repositories/extractions.py`, etc.
- Implement insert/read functions for each table
- Add Pydantic models for DB records
- Unit test repositories against test database
- **No endpoint changes yet. No frontend changes.**

#### Stage 3D — Backend Endpoints

- Add new endpoints (from Section 8)
- Wire endpoints to repositories
- Add validation, error handling
- Integration test endpoints
- **Existing extraction/routing endpoints unchanged.**
- **No frontend changes yet.**

#### Stage 3E — Frontend Saves Case Bundle

- After routing completes, frontend calls `POST /cases` to persist full bundle
- Frontend sends extraction, correction, and report in one payload
- Backend splits and stores in correct tables
- Frontend falls back gracefully if backend persistence fails
- **Reviewer still local for now.**

#### Stage 3F — Reviewer Reads/Writes Persisted Data

- Reviewer workspace calls `GET /cases` to load queue
- Feedback calls `POST /cases/{id}/review` to persist
- Frontend maintains local state for responsiveness
- Syncs to backend on submit

#### Stage 3G — Metrics From Persisted Data

- Metrics dashboard calls `GET /sessions/{id}/metrics`
- Backend computes aggregates from persisted data
- Session summary calls `POST /sessions/{id}/summary`
- Local metrics remain available as fallback

---

## 10. Out of Scope (Stage 3A)

- ❌ Database connection or credentials
- ❌ SQL migrations applied
- ❌ Authentication / access control
- ❌ Real patient data
- ❌ Multi-site deployment
- ❌ Frontend direct DB access
- ❌ Changes to extraction behavior
- ❌ Changes to routing logic
- ❌ Changes to safety policy
- ❌ Changes to cardio_triage_v1 engine
- ❌ Modifications to Pen or Soficca Page projects
- ❌ Production deployment

---

## 11. Implementation Checklist

### Stage 3B (Next)

- [ ] Add `DATABASE_URL` to `.env.example` (not `.env`)
- [ ] Add database dependency to `requirements.txt` (asyncpg or psycopg2-binary)
- [ ] Create `db/` module with connection pool setup
- [ ] Create `migrations/` directory
- [ ] Write `001_initial_schema.sql` migration
- [ ] Add migration runner script
- [ ] Test migration against local/dev Supabase
- [ ] Document setup in README

### Stage 3C

- [ ] Create `repositories/` module
- [ ] Implement `pilot_sessions` repository
- [ ] Implement `pilot_cases` repository
- [ ] Implement `ai_extractions` repository
- [ ] Implement `human_corrections` repository
- [ ] Implement `engine_reports` repository
- [ ] Implement `audit_records` repository
- [ ] Implement `reviewer_feedback` repository
- [ ] Implement `session_summaries` repository
- [ ] Unit tests for all repositories

### Stage 3D

- [ ] Add session endpoints
- [ ] Add case CRUD endpoints
- [ ] Add sub-resource POST endpoints
- [ ] Add metrics/summary endpoints
- [ ] Integration tests
- [ ] Update API documentation

### Stage 3E–3G

- [ ] Frontend calls POST /cases after routing
- [ ] Reviewer workspace reads from backend
- [ ] Feedback persists to backend
- [ ] Metrics reads from backend
- [ ] Graceful fallback when persistence unavailable

---

## 12. Product Boundary (Unchanged)

> AI structures the signal.  
> Human confirms or corrects.  
> Soficca governs the route.  
> Physicians make the final decision.

This persistence layer stores the evidence of that chain. It does not change who decides, how routing works, or what AI does.

---

*End of Stage 3A planning document.*
