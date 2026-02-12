# Evaluation Harness

The demo for incubators is **behavioral evaluation**, not UX.

## What this proves
- Determinism (same input => same output)
- Safety overrides (policy > clinical rules)
- Explicit uncertainty & conflict handling
- Auditability (formal trace with evaluated/triggered rule IDs)
- Governability (versioned ruleset + safety policy)

## Run
1) Install deps (pytest only required for tests):
- `pip install -e .` (optional if packaging)
- `pip install pytest`

2) Run tests:
- `pytest -q`

3) Run golden-case evaluation:
- `python run_evaluation.py`

This prints PASS/FAIL and writes `evaluation_report.json`.
