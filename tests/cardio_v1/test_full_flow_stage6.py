import hashlib
import json
from pathlib import Path

from cardio_triage_v1.decision_contract import validate_report
from cardio_triage_v1.validation import evaluate_readiness


SCENARIOS_PATH = Path("examples/cardio_v1_scenarios.json")


def _hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _load_scenarios() -> list[dict]:
    payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    return payload["scenarios"]


def test_cardio_contract_stability_on_all_canonical_scenarios() -> None:
    for scenario in _load_scenarios():
        report = evaluate_readiness(scenario["input"])
        assert validate_report(report) == []


def test_canonical_scenario_outcomes_cover_core_paths() -> None:
    scenarios = {s["id"]: s for s in _load_scenarios()}

    needs_more_info = evaluate_readiness(scenarios["CARDIO_NEEDS_MORE_INFO"]["input"])
    assert needs_more_info["decision"]["status"] == "NEEDS_MORE_INFO"

    routine = evaluate_readiness(scenarios["CARDIO_ROUTINE_REVIEW"]["input"])
    assert routine["decision"]["decision_type"] == "ROUTINE_REVIEW"
    assert routine["decision"]["path"] == "PATH_ROUTINE"

    urgent = evaluate_readiness(scenarios["CARDIO_URGENT_ESCALATION"]["input"])
    assert urgent["decision"]["decision_type"] == "URGENT_ESCALATION"
    assert urgent["decision"]["path"] == "PATH_URGENT_SAME_DAY"

    emergency = evaluate_readiness(scenarios["CARDIO_EMERGENCY_ROUTE"]["input"])
    assert emergency["decision"]["decision_type"] == "EMERGENCY_OVERRIDE"
    assert emergency["decision"]["path"] == "PATH_EMERGENCY_NOW"

    deferred = evaluate_readiness(scenarios["CARDIO_DEFERRED_PENDING_DATA"]["input"])
    assert deferred["decision"]["decision_type"] == "DEFERRED_PENDING_DATA"
    assert deferred["decision"]["status"] == "CONFLICT"


def test_deterministic_replay_same_input_same_output() -> None:
    scenario = next(s for s in _load_scenarios() if s["id"] == "CARDIO_URGENT_ESCALATION")
    out1 = evaluate_readiness(scenario["input"])
    out2 = evaluate_readiness(scenario["input"])
    assert _hash(out1) == _hash(out2)
