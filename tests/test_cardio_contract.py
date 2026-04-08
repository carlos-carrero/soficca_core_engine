import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cardio_triage_v1.constants import ALL_PATH_IDS, DECISION_STATUSES, SAFETY_ACTIONS, SAFETY_STATUSES
from cardio_triage_v1.decision_contract import assert_valid_report, build_base_report
from cardio_triage_v1.schema import CardioReport
from cardio_triage_v1.validation import evaluate_readiness


SCENARIOS_PATH = Path("examples/cardio_v1_scenarios.json")
MANUAL_REQUESTS_PATH = Path("examples/cardio_v1_manual_requests.json")


def _load_scenarios() -> list[dict]:
    payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    return payload["scenarios"]


def _load_manual_requests() -> list[dict]:
    payload = json.loads(MANUAL_REQUESTS_PATH.read_text(encoding="utf-8"))
    return payload["manual_requests"]


def test_base_report_is_valid_against_frozen_contract() -> None:
    report = build_base_report()
    assert_valid_report(report)


def test_model_json_schema_freezes_required_nested_structure_and_ids() -> None:
    schema = CardioReport.model_json_schema()
    assert schema["type"] == "object"
    assert set(schema["required"]) == {"ok", "errors", "versions", "decision", "safety", "trace"}

    defs = schema["$defs"]
    decision_props = defs["CardioDecision"]["properties"]
    safety_props = defs["CardioSafety"]["properties"]
    trace_props = defs["CardioTrace"]["properties"]

    assert set(defs["CardioDecision"]["required"]) >= {
        "status",
        "path",
        "flags",
        "reasons",
        "recommendations",
        "required_fields",
        "missing_fields",
        "decision_id",
        "case_status",
        "decision_type",
        "recommended_route",
        "urgency_level",
        "clinical_summary",
        "required_actions",
    }
    assert set(defs["CardioSafety"]["required"]) >= {
        "status",
        "action",
        "triggers",
        "policy_version",
        "safety_id",
        "has_red_flags",
        "override_applied",
        "severity",
        "flags",
    }
    assert set(defs["CardioTrace"]["required"]) >= {
        "policy_trace",
        "rules_evaluated",
        "rules_triggered",
        "evidence",
        "uncertainty_notes",
        "missing_fields",
        "activated_rules",
        "preliminary_route",
        "final_route",
        "override_reason",
        "conflicts_detected",
    }

    decision_status_ref = decision_props["status"]["$ref"].split("/")[-1]
    safety_status_ref = safety_props["status"]["$ref"].split("/")[-1]
    safety_action_ref = safety_props["action"]["$ref"].split("/")[-1]
    path_ref = defs["PathId"]["enum"]

    assert set(defs[decision_status_ref]["enum"]) == set(DECISION_STATUSES)
    assert set(defs[safety_status_ref]["enum"]) == set(SAFETY_STATUSES)
    assert set(defs[safety_action_ref]["enum"]) == set(SAFETY_ACTIONS)
    assert set(path_ref) == set(ALL_PATH_IDS)
    assert trace_props["policy_trace"]["$ref"].endswith("/PolicyTrace")


def test_canonical_scenarios_validate_against_frozen_contract() -> None:
    for scenario in _load_scenarios():
        report = evaluate_readiness(scenario["input"])
        assert_valid_report(report)


def test_manual_requests_validate_against_frozen_contract() -> None:
    for item in _load_manual_requests():
        report = evaluate_readiness(item["request"])
        assert_valid_report(report)


def test_validator_rejects_triggered_safety_without_escalated_decision() -> None:
    scenario = next(s for s in _load_scenarios() if s["id"] == "CARDIO_URGENT_ESCALATION")
    report = evaluate_readiness(scenario["input"])

    report["safety"]["status"] = "TRIGGERED"
    report["safety"]["action"] = "OVERRIDE_ESCALATE"
    report["decision"]["status"] = "DECIDED"

    with pytest.raises(ValidationError) as exc_info:
        assert_valid_report(report)
    assert "ESCALATED" in str(exc_info.value)
