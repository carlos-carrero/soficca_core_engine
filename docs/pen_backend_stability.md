# Pen backend demo stability note

## Stable endpoints
- `POST /v1/pen/evaluate`
- `GET /v1/pen/contract`

## Frozen demo contract surface
Treat these top-level response sections as stable for the current demo:
- `versions`
- `decision`
- `decision_rationale`
- `trace`
- `journey_views`
- `frontend_adapter`

## Canonical demo case (must not regress)
- Input includes `high_blood_pressure=true` (with no conflicting manual-review trigger conditions).
- Expected output keeps:
  - `decision.decision_path = topical_treatment`
  - `decision.excluded_options` includes `oral_treatment`

## Golden-case gate
Curated deterministic cases live in:
- `tests/pen_hair_v1/golden_cases.py`

Contract freeze and golden-case tests:
- `tests/pen_hair_v1/test_contract_freeze.py`
- `tests/pen_hair_v1/test_pen_hair_v1.py`

Run gate locally/CI:
```bash
scripts/test_pen_contract_gate.sh
```

## What should not be changed casually
- Remove/rename frozen top-level response sections.
- Change current decision outcome IDs.
- Alter canonical hypertension behavior.
- Break `frontend_adapter.evaluation` or `frontend_adapter.journey` shape.

## Later-stage work (not this pass)
- New clinical branches beyond current deterministic demo scope.
- Frontend rendering redesigns.
- Larger contract versioning framework changes.
