from cardio_triage_v1.validation import evaluate_readiness


def _base_complete_state() -> dict:
    return {
        "age": 60,
        "chest_pain_present": True,
        "pain_duration_minutes": 15,
        "pain_character": "pressure",
        "pain_severity": "low",
        "pain_radiation": "none",
        "dyspnea": False,
        "syncope": False,
        "systolic_bp": 122,
        "heart_rate": 78,
        "known_cad": False,
        "current_meds_none": True,
        "exertional_chest_pain": False,
        "diaphoresis": False,
        "cv_risk_factors_count": 1,
    }


def test_urgent_escalation_by_exertional_pain_plus_radiation() -> None:
    state = _base_complete_state()
    state["exertional_chest_pain"] = True
    state["pain_radiation"] = "jaw"

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["status"] == "DECIDED"
    assert report["decision"]["decision_id"] == "URGENT_ESCALATION"
    assert report["decision"]["path"] == "PATH_URGENT_SAME_DAY"


def test_urgent_escalation_by_symptom_risk_cluster() -> None:
    state = _base_complete_state()
    state["diaphoresis"] = True
    state["pain_severity"] = "high"
    state["cv_risk_factors_count"] = 3

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["decision_id"] == "URGENT_ESCALATION"
    assert report["decision"]["path"] == "PATH_URGENT_SAME_DAY"


def test_routine_review_for_stable_complete_case() -> None:
    state = _base_complete_state()

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["status"] == "DECIDED"
    assert report["decision"]["decision_id"] == "ROUTINE_REVIEW"
    assert report["decision"]["path"] == "PATH_ROUTINE"
    assert report["safety"]["override_applied"] is False


def test_emergency_override_still_wins_over_urgent_routine_logic() -> None:
    state = _base_complete_state()
    state["exertional_chest_pain"] = True
    state["pain_radiation"] = "jaw"
    state["syncope"] = True

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["trace"]["preliminary_route"] == "PATH_URGENT_SAME_DAY"
    assert report["decision"]["status"] == "ESCALATED"
    assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
    assert report["trace"]["final_route"] == "PATH_EMERGENCY_NOW"
    assert report["safety"]["override_applied"] is True
