# Soficca Cardio Pilot — Final Persisted Flow QA

## A. Purpose

Validate the full persisted Cardio Pilot workflow from session creation through
case persistence, reviewer feedback, and session summary — with verified Supabase
records and confirmed local fallback.

---

## B. Required Setup

| Component            | Requirement                                           |
|----------------------|-------------------------------------------------------|
| Backend              | Running on port 8000                                  |
| Frontend             | Running on port 3001 (or project default)             |
| DATABASE_URL         | Configured in `soficca_core_engine/.env`              |
| Migrations           | Applied via `python scripts/run_migrations.py`        |
| OPENAI_API_KEY       | Configured if testing real AI extraction               |
| PYTHONPATH           | `src` (backend)                                       |
| Supabase dashboard   | Open for table verification (optional but recommended)|

---

## C. Commands

### Backend

```powershell
cd soficca_core_engine
$env:PYTHONPATH = "src"
uvicorn api.main:app --reload --port 8000
```

### Frontend

```powershell
cd cardio_pilot
npm run dev
```

### Backend tests

```powershell
cd soficca_core_engine
$env:PYTHONPATH = "src"
python -m pytest tests/ -q --tb=short
```

### Backend endpoint roundtrip script

```powershell
cd soficca_core_engine
python scripts/test_persistence_endpoints.py
```

### Full persisted flow script (backend-only)

```powershell
cd soficca_core_engine
python scripts/test_full_persisted_flow.py
```

### Frontend type check

```powershell
cd cardio_pilot
npx tsc --noEmit
```

---

## D. Full Manual QA Flow

### Step 1 — Create persisted pilot session

1. Open **Metrics Dashboard**.
2. Click **Create Persisted Session**.
3. Confirm: badge shows "Active", session ID visible.
4. Verify in Supabase: `pilot_sessions` table has new row.

### Step 2 — Run case intake

1. Switch to Flow surface.
2. Enter or paste an emergency narrative.
3. Proceed through intake.

### Step 3 — AI extraction

1. Confirm extraction runs (real AI or mock fallback with notice).
2. Review extracted fields.

### Step 4 — Human confirmation / correction

1. On extraction preview, modify at least one field (e.g., change age).
2. Confirm extraction.
3. Verify human correction fields tracked.

### Step 5 — Deterministic routing

1. Confirm routing runs (real backend or mock fallback with notice).
2. Report screen displays route, safety, audit.

### Step 6 — Save case to database

1. In report screen export sidebar, click **Save Case to Database**.
2. Confirm UI: "Saved to database".
3. Confirm Pilot Mode badge says "Persisted" or "Saved".
4. Verify in Supabase:
   - `pilot_cases` — row exists, `session_id` matches active session.
   - `ai_extractions` — row exists linked to case.
   - `human_corrections` — row exists if human edits were made.
   - `engine_reports` — row exists linked to case.
   - `audit_records` — row exists linked to case.

### Step 7 — Send to reviewer

1. Click **Send to Reviewer** in report screen.
2. Switch to Reviewer surface.
3. Confirm queue item shows case, with `persisted` badge or indication.

### Step 8 — Submit reviewer feedback

1. Select case in reviewer queue.
2. Fill out feedback form.
3. Click **Submit feedback**.
4. Confirm UI: "Reviewer feedback saved to database" (green banner).
5. Verify in Supabase: `reviewer_feedback` table has row.
6. Verify `pilot_cases` status updated to "reviewed" if implemented.

### Step 9 — Load persisted cases

1. In reviewer workspace, click **Load Persisted Cases**.
2. Confirm saved case appears in persisted cases table (or is excluded if already local — deduplicated).
3. Click **Details** on a persisted case.
4. Confirm bundle detail loads (reviewer feedback count, audit record, engine report).

### Step 10 — Save session summary

1. Return to **Metrics Dashboard**.
2. Click **Save Session Summary**.
3. Confirm UI: "Summary saved".
4. Verify in Supabase: `session_summaries` table has row linked to session.

### Step 11 — Load persisted session summary

1. Click **Load Latest Persisted Summary**.
2. Confirm preview panel appears.
3. Verify fields: Summary ID, cases processed, cases reviewed, agreement rate, autonomous events = 0.

### Step 12 — Duplicate case behavior

1. Go back to report for the same case (if possible).
2. Click **Save Case to Database** again.
3. Confirm UI: "Already exists" or graceful error — no crash.

### Step 13 — Local fallback

1. Stop the backend (`Ctrl+C`).
2. Attempt to save a new case → confirm controlled error message.
3. Attempt to create session → confirm controlled error.
4. Confirm local metrics, audit export, session summary export still work.
5. Confirm local reviewer queue and feedback still work.

---

## E. Expected Supabase Tables Updated

| Table                | Expected After QA                                   |
|----------------------|-----------------------------------------------------|
| `pilot_sessions`     | ≥ 1 row with label "Cardio Pilot Demo Session"     |
| `pilot_cases`        | ≥ 1 row with matching `session_id`                 |
| `ai_extractions`     | ≥ 1 row linked to case                             |
| `human_corrections`  | ≥ 1 row linked to case (if edits were made)        |
| `engine_reports`     | ≥ 1 row linked to case                             |
| `audit_records`      | ≥ 1 row linked to case                             |
| `reviewer_feedback`  | ≥ 1 row linked to case                             |
| `session_summaries`  | ≥ 1 row linked to session                          |

---

## F. Expected UI Confirmations

| Action                     | Expected UI Message                               |
|----------------------------|---------------------------------------------------|
| Create session             | Badge: "Active", Session ID visible               |
| Save case                  | "Saved to database"                               |
| Duplicate save             | "Already exists" or graceful error                |
| Reviewer feedback          | "Reviewer feedback saved to database"             |
| Load persisted cases       | Table shows persisted cases or "no additional"    |
| Save session summary       | "Summary saved"                                   |
| Load persisted summary     | Preview panel with metrics                        |
| Backend unavailable        | "Backend unavailable" or controlled error message |

---

## G. Fallback Checks

| Scenario                | Expected Behavior                                    |
|-------------------------|------------------------------------------------------|
| Backend stopped          | Local flow works, save shows controlled error        |
| DB unavailable           | Backend returns 503, frontend shows safe message     |
| Duplicate case_id        | 409 → "Already exists" in UI                         |
| No persisted session     | Cases save with `session_id = null`, all else works  |
| Local-only case review   | Feedback saved locally, no backend call attempted    |
| Network error            | "Network error" or "Backend unavailable" message     |

---

## H. Pass / Fail Checklist

| #  | Check                                    | Pass | Fail | Notes |
|----|------------------------------------------|------|------|-------|
| 1  | Create persisted session                 | [ ]  | [ ]  |       |
| 2  | Session ID in Supabase                   | [ ]  | [ ]  |       |
| 3  | AI extraction (real or fallback)         | [ ]  | [ ]  |       |
| 4  | Human correction tracked                 | [ ]  | [ ]  |       |
| 5  | Deterministic routing (real or fallback) | [ ]  | [ ]  |       |
| 6  | Save case to database                    | [ ]  | [ ]  |       |
| 7  | Case has session_id in Supabase          | [ ]  | [ ]  |       |
| 8  | Nested resources in Supabase             | [ ]  | [ ]  |       |
| 9  | Send to reviewer (persistence-backed)    | [ ]  | [ ]  |       |
| 10 | Reviewer feedback saved to database      | [ ]  | [ ]  |       |
| 11 | Load persisted cases                     | [ ]  | [ ]  |       |
| 12 | Save session summary                     | [ ]  | [ ]  |       |
| 13 | Load persisted session summary           | [ ]  | [ ]  |       |
| 14 | Duplicate case_id handled                | [ ]  | [ ]  |       |
| 15 | Backend unavailable — local fallback     | [ ]  | [ ]  |       |
| 16 | Local audit/session export works         | [ ]  | [ ]  |       |
| 17 | Frontend TS build passes                 | [ ]  | [ ]  |       |
| 18 | Backend tests pass                       | [ ]  | [ ]  |       |

---

## I. Safety Reminders

- All data is simulated / anonymized.
- Soficca does not diagnose, prescribe, or replace clinical judgment.
- No database secrets are stored in the frontend.
- No direct Supabase access from the browser.
- Autonomous diagnosis events: 0. Autonomous prescription events: 0.
