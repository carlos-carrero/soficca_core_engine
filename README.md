# Soficca Core Engine (v0.3)

Decision-first, deterministic clinical decision engine with **explicit safety gates** and a **versioned, auditable output contract**.

> **Status:** v0.3 (decision-first, no chat)  
> **API stability:** Stable contract (v0.3 output schema)  
> **License:** Proprietary (subject to change)

---

## What this is

**Soficca Core Engine** evaluates a **structured clinical state** and returns a **Decision Report** that is:

- **Deterministic** (rule-based decision logic)
- **Safety-first** (policy gates can override decisions)
- **Auditable** (explicit rule/policy trace + evidence normalization)
- **Versioned** (engine / ruleset / safety policy versions are returned)

This repository also includes a **thin FastAPI adapter** (“Core API”) that exposes the engine via HTTP.

---

## What this is NOT

- Not a chat UI
- Not a session system (no DB, no accounts, no logging by default)
- Not an LLM-driven decision maker
- Not a diagnosis or prescription system
- Not a replacement for clinical judgment

---

## Core invariants (guarantees)

These invariants are enforced in the **core engine** and covered by tests:

- The engine **never guesses** missing clinical fields.
- If `decision.status == NEEDS_MORE_INFO`, the engine **declares** `decision.required_fields` (non-empty).
- If `decision.status == DECIDED`, the decision is **terminal**:
  - `decision.path != PATH_MORE_QUESTIONS`
  - `decision.required_fields` is empty
- When safety is triggered, the system can **override** decision behavior via:
  - `safety.status = TRIGGERED`
  - `safety.action = OVERRIDE_*`

---

## Decision Report contract (v0.3)

Every evaluation returns the **Decision Report v0.3** contract with:

- `ok`, `errors`
- `versions` (`engine`, `ruleset`, `safety_policy`)
- `decision` (`status`, `path`, `flags`, `reasons`, `recommendations`, `required_fields`)
- `safety` (`status`, `action`, `triggers`, `policy_version`)
- `trace` (`policy_trace`, `rules_evaluated`, `rules_triggered`, `evidence`, `uncertainty_notes`)

The canonical JSON Schema is exposed at:

- `GET /contract`

---

## Run the API demo (FastAPI)

### Install

```bash
pip install -r requirements.txt
```

### Run (dev)

```bash
uvicorn api.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/healthz`
- Contract: `http://127.0.0.1:8000/contract`

---

## Demo scenarios (canonical)

The `examples/` folder contains canonical inputs/outputs used to communicate system behavior in seconds:

1. **Missing information** → engine refuses to decide (`NEEDS_MORE_INFO`)
2. **Complete safe input** → terminal decision (`DECIDED`)
3. **Safety trigger** → escalation / blocking (`safety.status = TRIGGERED`)

Recommended workflow:
- Open `/docs`
- Run the three payloads from `examples/`
- Inspect the resulting `trace` and `versions`

### Example: terminal decision output

See: `examples/02_decided_safe_output.json`

---

## Testing

### Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

### Run tests

```bash
pytest -q
```

Tests include contract invariants such as:
- `DECIDED` is terminal (never `PATH_MORE_QUESTIONS`)
- `NEEDS_MORE_INFO` declares `required_fields`

---

## Project structure (high level)

```
api/
  main.py            # Thin FastAPI adapter (decision-first)
examples/
  02_decided_safe_output.json
tests/
  test_invariants.py
src/soficca_core/
  engine.py          # Deterministic evaluation + invariants enforcement
  ...                # ruleset, safety policies, normalization, etc.
```

---

## Disclaimer

Soficca Core Engine is a **clinical decision-support system** prototype.  
It is intended to support — not replace — professional clinical judgment.
