import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location("api_main", Path("api/main.py"))
assert spec and spec.loader
api_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_main)


CardioReportRequest = api_main.CardioReportRequest
cardio_contract = api_main.cardio_contract
v1_cardio_report = api_main.v1_cardio_report

CardioReportRequest.model_rebuild(_types_namespace={"Dict": dict, "Any": object})

def test_cardio_endpoint_response_shape_and_path_verification() -> None:
    payload = CardioReportRequest(
        state={
            "age": 63,
            "chest_pain_present": True,
            "pain_duration_minutes": 20,
            "pain_character": "pressure",
            "pain_severity": "moderate",
            "pain_radiation": "jaw",
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 126,
            "heart_rate": 88,
            "known_cad": False,
            "current_meds_none": True,
            "exertional_chest_pain": True,
            "diaphoresis": False,
            "cv_risk_factors_count": 1,
        },
        context={"source": "USER"},
    )

    report = v1_cardio_report(payload)
    assert set(report.keys()) == {"ok", "errors", "versions", "decision", "safety", "trace"}
    assert report["decision"]["decision_type"] == "URGENT_ESCALATION"
    assert report["decision"]["path"] == "PATH_URGENT_SAME_DAY"


def test_cardio_contract_endpoint_available() -> None:
    schema = cardio_contract()
    assert schema.get("title") == "Soficca Cardio Triage Report v1"
    assert schema.get("type") == "object"
