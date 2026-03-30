from cardio_triage_v1.validation import evaluate_readiness


def _base_state() -> dict:
    return {
        "age": 58,
        "chest_pain_present": True,
        "pain_duration_minutes": 10,
        "pain_character": "pressure",
        "pain_radiation": "left_arm",
        "dyspnea": False,
        "syncope": False,
        "systolic_bp": 128,
        "heart_rate": 82,
        "known_cad": False,
        "current_meds_none": True,
    }


def test_emergency_route_triggered_by_syncope_plus_chest_pain() -> None:
    state = _base_state()
    state["syncope"] = True
    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
    assert report["safety"]["has_red_flags"] is True
    assert "FLAG_SYNCOPAL_CHEST_PAIN" in report["safety"]["flags"]


def test_emergency_route_triggered_by_severe_ongoing_chest_pain() -> None:
    state = _base_state()
    state["pain_character"] = "severe"
    state["pain_duration_minutes"] = 30
    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
    assert "FLAG_SEVERE_ONGOING_CHEST_PAIN" in report["safety"]["flags"]


def test_emergency_route_triggered_by_very_low_bp() -> None:
    state = _base_state()
    state["systolic_bp"] = 82
    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
    assert "FLAG_VERY_LOW_SBP" in report["safety"]["flags"]


def test_no_emergency_override_when_conditions_absent() -> None:
    state = _base_state()
    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["status"] == "DECIDED"
    assert report["decision"]["path"] in {"PATH_ROUTINE", "PATH_URGENT_SAME_DAY"}
    assert report["safety"]["override_applied"] is False
    assert report["safety"]["has_red_flags"] is False
    assert report["trace"]["final_route"] == report["decision"]["path"]
