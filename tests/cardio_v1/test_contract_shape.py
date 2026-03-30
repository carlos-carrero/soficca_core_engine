from cardio_triage_v1.constants import (
    ALL_PATH_IDS,
    CONTRACT_VERSION,
    ENGINE_VERSION,
    REPORT_TOP_LEVEL_KEYS,
    RULESET_VERSION,
    SAFETY_POLICY_VERSION,
    TRACE_SECTION_KEYS,
)
from cardio_triage_v1.decision_contract import build_base_report, validate_report


def test_stable_top_level_response_shape() -> None:
    report = build_base_report()
    assert list(report.keys()) == REPORT_TOP_LEVEL_KEYS


def test_stable_decision_safety_trace_sections() -> None:
    report = build_base_report()

    assert set(report["decision"].keys()) == {
        "status",
        "path",
        "flags",
        "reasons",
        "recommendations",
        "required_fields",
        "missing_fields",
        "decision_id",
    }
    assert set(report["safety"].keys()) == {
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
    assert set(report["trace"].keys()) == set(TRACE_SECTION_KEYS)


def test_fixed_version_identifiers_are_present() -> None:
    report = build_base_report()
    versions = report["versions"]

    assert versions["engine"] == ENGINE_VERSION
    assert versions["ruleset"] == RULESET_VERSION
    assert versions["safety_policy"] == SAFETY_POLICY_VERSION
    assert versions["contract"] == CONTRACT_VERSION


def test_fixed_route_constants_are_stable() -> None:
    assert ALL_PATH_IDS == [
        "PATH_MORE_QUESTIONS",
        "PATH_EMERGENCY_NOW",
        "PATH_URGENT_SAME_DAY",
        "PATH_ROUTINE",
        "PATH_SELF_CARE",
        "PATH_ESCALATE_HUMAN",
    ]


def test_contract_validator_accepts_stage1_scaffold_report() -> None:
    report = build_base_report()
    assert validate_report(report) == []
