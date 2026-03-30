from cardio_triage_v1.constants import ENGINE_VERSION, RULESET_VERSION, SAFETY_POLICY_VERSION
from cardio_triage_v1.normalization import normalize_for_readiness
from cardio_triage_v1.validation import evaluate_readiness


def _base_complete_state() -> dict:
    return {
        "age": 60,
        "chest_pain_present": True,
        "pain_duration_minutes": 15,
        "pain_character": "pressure",
        "pain_severity": "moderate",
        "pain_radiation": "jaw",
        "dyspnea": False,
        "syncope": False,
        "systolic_bp": 122,
        "heart_rate": 82,
        "known_cad": False,
        "current_meds_none": True,
        "exertional_chest_pain": True,
        "diaphoresis": False,
        "cv_risk_factors_count": 1,
    }


def test_composite_cad_history_logic_is_true_only_when_true_flag_exists() -> None:
    base = _base_complete_state()

    n1 = normalize_for_readiness({**base, "prior_mi": None, "known_cad": None})
    assert n1["prior_mi_or_known_cad"] is False

    n2 = normalize_for_readiness({**base, "prior_mi": False, "known_cad": False})
    assert n2["prior_mi_or_known_cad"] is False

    n3 = normalize_for_readiness({**base, "prior_mi": True, "known_cad": False})
    assert n3["prior_mi_or_known_cad"] is True

    n4 = normalize_for_readiness({**base, "prior_mi": False, "known_cad": True})
    assert n4["prior_mi_or_known_cad"] is True


def test_activated_rules_consistent_with_routing_and_safety_logic() -> None:
    # non-emergency urgent: activated_rules should include rules_triggered
    urgent = evaluate_readiness({"state": _base_complete_state(), "context": {}})
    assert set(urgent["trace"]["rules_triggered"]).issubset(set(urgent["trace"]["activated_rules"]))

    # emergency override: activated_rules should include both routing + safety triggered
    emergency_state = _base_complete_state()
    emergency_state["syncope"] = True
    emergency = evaluate_readiness({"state": emergency_state, "context": {}})
    assert set(emergency["trace"]["rules_triggered"]).issubset(set(emergency["trace"]["activated_rules"]))
    assert set(emergency["trace"]["policy_trace"]["triggered"]).issubset(set(emergency["trace"]["activated_rules"]))


def test_version_labels_are_demo_ready_not_scaffold_placeholders() -> None:
    assert "scaffold" not in ENGINE_VERSION
    assert "scaffold" not in RULESET_VERSION
    assert "scaffold" not in SAFETY_POLICY_VERSION
