from cardio_triage_v1.validation import evaluate_readiness


def _base_complete_state() -> dict:
    return {
        "age": 55,
        "chest_pain_present": True,
        "pain_duration_minutes": 15,
        "pain_character": "pressure",
        "pain_severity": "low",
        "pain_radiation": "none",
        "dyspnea": False,
        "syncope": False,
        "systolic_bp": 124,
        "heart_rate": 78,
        "known_cad": False,
        "current_meds_none": True,
        "exertional_chest_pain": False,
    }


def test_conflicting_input_returns_deferred_pending_data() -> None:
    state = _base_complete_state()
    state["chest_pain_present"] = False
    state["pain_severity"] = "high"
    state["pain_duration_minutes"] = 20

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["status"] == "CONFLICT"
    assert report["decision"]["decision_type"] == "DEFERRED_PENDING_DATA"
    assert report["decision"]["decision_id"] == "DEFERRED_PENDING_DATA"


def test_conflicts_detected_is_populated_correctly() -> None:
    state = _base_complete_state()
    state["chest_pain_present"] = False
    state["pain_severity"] = "moderate"
    state["pain_radiation"] = "jaw"
    state["exertional_chest_pain"] = True

    report = evaluate_readiness({"state": state, "context": {}})

    conflicts = report["trace"]["conflicts_detected"]
    assert len(conflicts) >= 3
    assert "CONFLICT_PAIN_SEVERITY_WITHOUT_CHEST_PAIN" in conflicts
    assert "CONFLICT_RADIATION_WITHOUT_CHEST_PAIN" in conflicts
    assert "CONFLICT_EXERTIONAL_WITHOUT_CHEST_PAIN" in conflicts


def test_clinical_summary_and_required_actions_are_present() -> None:
    state = _base_complete_state()
    state["chest_pain_present"] = False
    state["pain_character"] = "crushing"

    report = evaluate_readiness({"state": state, "context": {}})

    assert isinstance(report["decision"]["clinical_summary"], str)
    assert len(report["decision"]["clinical_summary"]) > 0
    assert isinstance(report["decision"]["required_actions"], list)
    assert len(report["decision"]["required_actions"]) > 0


def test_emergency_override_still_wins_when_applicable() -> None:
    state = _base_complete_state()
    state["chest_pain_present"] = False
    state["pain_severity"] = "high"  # creates conflict
    state["systolic_bp"] = 80  # hard emergency red flag

    report = evaluate_readiness({"state": state, "context": {}})

    assert report["decision"]["status"] == "ESCALATED"
    assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
    assert report["decision"]["decision_type"] == "EMERGENCY_OVERRIDE"
    assert report["safety"]["override_applied"] is True
