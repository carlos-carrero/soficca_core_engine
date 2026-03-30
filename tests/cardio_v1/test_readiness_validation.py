from cardio_triage_v1.validation import CORE_REQUIRED_FIELDS, evaluate_readiness


def test_complete_minimal_input_passes_readiness_checks() -> None:
    payload = {
        "state": {
            "age": 58,
            "chest_pain_present": True,
            "pain_duration_minutes": 30,
            "pain_character": "pressure",
            "pain_radiation": "left_arm",
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 128,
            "heart_rate": 82,
            "known_cad": False,
            "current_meds_none": True,
        },
        "context": {"source": "USER"},
    }

    report = evaluate_readiness(payload)

    assert report["ok"] is True
    assert report["decision"]["status"] == "DECIDED"
    assert report["decision"]["required_fields"] == []
    assert report["decision"]["missing_fields"] == []
    assert report["trace"]["missing_fields"] == []


def test_incomplete_critical_input_returns_needs_more_info() -> None:
    payload = {
        "state": {
            "age": 58,
            "chest_pain_present": True,
            "pain_duration_minutes": 30,
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 128,
            "heart_rate": 82,
            "current_meds_none": True,
        },
        "context": {"source": "USER"},
    }

    report = evaluate_readiness(payload)

    assert report["decision"]["status"] == "NEEDS_MORE_INFO"
    assert "pain_character" in report["decision"]["required_fields"]
    assert "pain_radiation" in report["decision"]["required_fields"]
    assert "prior_mi_or_known_cad" in report["decision"]["required_fields"]


def test_required_fields_and_missing_fields_are_populated_consistently() -> None:
    payload = {
        "state": {
            "age": 58,
            "chest_pain_present": True,
            "pain_duration_minutes": 30,
            "pain_character": "pressure",
            "pain_radiation": "left_arm",
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 128,
            "heart_rate": 82,
        },
        "context": {},
    }

    report = evaluate_readiness(payload)

    expected_missing = ["prior_mi_or_known_cad", "current_meds_summary_or_none"]
    assert report["decision"]["status"] == "NEEDS_MORE_INFO"
    assert report["decision"]["required_fields"] == expected_missing
    assert report["decision"]["missing_fields"] == expected_missing
    assert report["trace"]["missing_fields"] == expected_missing

    for f in report["decision"]["required_fields"]:
        assert f in CORE_REQUIRED_FIELDS
