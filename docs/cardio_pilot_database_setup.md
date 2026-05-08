# Soficca Cardio Pilot — Database Setup (Stage 3B)

## Overview

This document describes how to configure and verify the Postgres database foundation for Cardio Pilot persistence.

**Important:**
- Database access is backend-only. The frontend never connects to the database directly.
- All early pilot data uses simulated/anonymized cases. No real PHI.
- Existing AI extraction and routing endpoints continue working without DATABASE_URL.

---

## 1. Prerequisites

- Python 3.10+
- A Postgres database (Supabase recommended, or any managed Postgres)
- `asyncpg` installed (see below)

---

## 2. Install Dependencies

```bash
cd soficca_core_engine
pip install -r requirements.txt
```

This installs `asyncpg` alongside existing dependencies.

---

## 3. Configure DATABASE_URL

1. Copy `.env.example` to `.env` (if not already done):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your real `DATABASE_URL`:
   ```
   DATABASE_URL="postgresql://user:password@host:port/database"
   ```

   For Supabase, find this in: Project Settings → Database → Connection String → URI.

3. **Never commit `.env`** — it is gitignored.

4. **Never use `NEXT_PUBLIC_` database variables.** Database access is backend-only.

---

## 4. Test Database Connection

```bash
cd soficca_core_engine
set PYTHONPATH=src
python scripts/test_db_connection.py
```

Expected output:
```
Soficca Cardio Pilot — Database Connection Test
==================================================

DATABASE_URL is configured (value not printed).
Testing connection...

✓ Database connection OK.
  Database: your_db_name
  Provider: PostgreSQL 15.x
  SELECT 1: 1

No secrets printed.
```

If `DATABASE_URL` is not set, the script will print a clear error and exit.

---

## 5. Run Migrations

```bash
cd soficca_core_engine
set PYTHONPATH=src
python scripts/run_migrations.py
```

This will:
- Connect to the database
- Create `schema_migrations` table if not present
- Apply any pending `.sql` files from `migrations/` in order
- Skip already-applied migrations
- Print progress (no secrets)

Expected output on first run:
```
Soficca Cardio Pilot — Migration Runner
==================================================
Connecting to database...

Found 1 pending migration(s):
  • 001_cardio_pilot_initial_schema

Applying: 001_cardio_pilot_initial_schema ...
  ✓ Applied: 001_cardio_pilot_initial_schema

Done. 1 migration(s) applied successfully.
No secrets printed.
```

---

## 6. Verify Tables in Supabase

After running migrations, verify in Supabase Table Editor or SQL Editor:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected tables:
- `ai_extractions`
- `audit_records`
- `engine_reports`
- `human_corrections`
- `pilot_cases`
- `pilot_sessions`
- `reviewer_feedback`
- `schema_migrations`
- `session_summaries`

---

## 7. Backend Startup (Unaffected)

Existing backend starts normally without DATABASE_URL:

```bash
cd soficca_core_engine
set PYTHONPATH=src
uvicorn api.main:app --reload --port 8000
```

AI extraction (`/v1/cardio/pilot/extract`) and routing (`/v1/cardio/pilot/report`) endpoints work as before. Database is only used when persistence endpoints are added in Stage 3D.

---

## 8. File Structure

```
soficca_core_engine/
├── .env.example              # Template (no secrets)
├── .env                      # Your secrets (gitignored)
├── requirements.txt          # asyncpg, pytest-asyncio added
├── api/
│   ├── main.py               # App entrypoint (includes persistence router)
│   └── routers/
│       ├── cardio_persistence_router.py  # Stage 3D endpoints
│       ├── cardio_pilot_router.py        # Existing pilot report
│       └── cardio_extract_router.py      # Existing AI extraction
├── src/
│   ├── db/
│   │   ├── __init__.py       # Public API
│   │   ├── config.py         # DATABASE_URL loading
│   │   └── pool.py           # asyncpg pool management
│   └── repositories/
│       ├── __init__.py       # Public API
│       ├── cardio_models.py  # Pydantic create/row models
│       ├── cardio_pilot_repository.py  # Write/read functions
│       └── errors.py         # Repository error types
├── migrations/
│   └── 001_cardio_pilot_initial_schema.sql
├── scripts/
│   ├── test_db_connection.py
│   ├── run_migrations.py
│   ├── test_repository_roundtrip.py
│   └── test_persistence_endpoints.py
├── tests/
│   ├── test_cardio_pilot_repository.py
│   └── test_cardio_persistence_endpoints.py
└── docs/
    ├── cardio_pilot_database_persistence_plan.md
    ├── cardio_pilot_database_schema.sql (draft reference)
    └── cardio_pilot_database_setup.md (this file)
```

---

## 9. Reminders

- **Backend-only database access.** No frontend direct DB queries.
- **No real PHI.** Early pilot uses simulated cases only.
- **`is_simulated = true`** for all cases in this stage.
- **No auth yet.** Authentication is a future stage.
- **Append-only clinical tables.** Never overwrite extraction, correction, or routing data.

---

## 10. Repository Layer (Stage 3C — Complete)

The repository layer provides async database access for all Cardio Pilot tables.

### Run repository tests

```bash
cd soficca_core_engine
set PYTHONPATH=src
python -m pytest tests/test_cardio_pilot_repository.py -v
```

### Run optional roundtrip test (requires DATABASE_URL)

```bash
cd soficca_core_engine
set PYTHONPATH=src
python scripts/test_repository_roundtrip.py
```

This creates a test session, case, extraction, correction, engine report, audit record, reviewer feedback, and session summary — then reads the case bundle back. All records are marked `is_simulated=true`.

---

## 11. Persistence Endpoints (Stage 3D — Complete)

FastAPI persistence endpoints under `/v1/cardio/pilot/`:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/sessions` | Create pilot session |
| GET | `/sessions` | List sessions |
| POST | `/cases` | Persist case bundle (case + nested sub-resources) |
| GET | `/cases` | List cases |
| GET | `/cases/{case_id}` | Read full case bundle |
| POST | `/cases/{case_id}/review` | Save reviewer feedback |
| POST | `/sessions/{session_id}/summary` | Save session summary |
| GET | `/sessions/{session_id}/summary` | Read latest session summary |

### Run endpoint tests

```bash
cd soficca_core_engine
set PYTHONPATH=src
python -m pytest tests/test_cardio_persistence_endpoints.py -v
```

### Run manual endpoint test (requires running backend + DATABASE_URL)

```bash
# Terminal 1:
cd soficca_core_engine
set PYTHONPATH=src
uvicorn api.main:app --reload --port 8000

# Terminal 2:
cd soficca_core_engine
python scripts/test_persistence_endpoints.py
```

### Error behavior
- **503** — DATABASE_URL not configured
- **404** — Case or summary not found
- **409** — Duplicate case_id
- **422** — Invalid payload
- **500** — Database write failure

### Reminders
- Frontend is still local-only until Stage 3E
- Simulated/anonymized cases only
- Existing `/extract` and `/report` endpoints are unaffected

---

## 12. Next Steps (Stage 3E)

- Connect frontend to persistence endpoints
- Wire case submission flow through backend persistence
- Add session management to frontend
- Integration testing frontend ↔ backend ↔ database
