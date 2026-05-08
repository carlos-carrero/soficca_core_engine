"""
Cardio Pilot adapter endpoint.

The pilot adapter maps structured extraction into deterministic engine input.
It does not decide route. It does not diagnose. It does not prescribe.

Flow:
  Pilot extraction payload
    -> map extraction fields to engine state
    -> call existing deterministic cardio_triage_v1 engine
    -> return real CardioReport + metadata
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from cardio_triage_v1.decision_contract import assert_valid_report
from cardio_triage_v1.validation import evaluate_readiness as evaluate_cardio_report

router = APIRouter(prefix="/v1/cardio/pilot", tags=["cardio-pilot"])


# ── Pydantic models ──────────────────────────────────────────────


class CardioPilotExtraction(BaseModel):
    """Structured extraction fields from the pilot frontend (mock or real LLM)."""

    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = None
    chest_pain_present: Optional[bool] = None
    pain_duration_minutes: Optional[int] = None
    pain_character: Optional[str] = None
    pain_severity: Optional[str] = None
    pain_radiation: Optional[str] = None
    exertional_chest_pain: Optional[bool] = None
    diaphoresis: Optional[bool] = None
    dyspnea: Optional[bool] = None
    syncope: Optional[bool] = None
    systolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    prior_mi: Optional[bool] = None
    known_cad: Optional[bool] = None
    cv_risk_factors_count: Optional[int] = None
    current_meds_summary: Optional[str] = None
    current_meds_none: Optional[bool] = None


class CardioPilotReportRequest(BaseModel):
    """Input accepted by the pilot report endpoint."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "case_id": "CP-EXAMPLE-001",
                    "raw_text": "64-year-old with severe chest pain and syncope.",
                    "source": "mock_extraction",
                    "extraction": {
                        "age": 64,
                        "chest_pain_present": True,
                        "pain_duration_minutes": 10,
                        "pain_character": "pressure",
                        "pain_severity": "high",
                        "pain_radiation": "left_arm",
                        "syncope": True,
                        "systolic_bp": 120,
                        "heart_rate": 96,
                        "known_cad": False,
                        "current_meds_none": True,
                    },
                }
            ]
        },
    )

    case_id: str = Field(..., min_length=1, description="Pilot case identifier")
    raw_text: str = Field(default="", description="Original narrative text (metadata only)")
    source: str = Field(default="mock_extraction", description="Extraction source identifier")
    extraction: CardioPilotExtraction


class CardioPilotReportResponse(BaseModel):
    """Output returned by the pilot report endpoint."""

    case_id: str
    source: str
    raw_text: str
    engine_input: Dict[str, Any]
    engine_report: Dict[str, Any]
    human_review_required: bool = True
    pilot_mode: str = "deterministic_routing_v1"


# ── Mapper ────────────────────────────────────────────────────────


def map_extraction_to_engine_input(
    extraction: CardioPilotExtraction,
    source: str,
) -> Dict[str, Any]:
    """
    Map pilot extraction fields to the engine state/context shape.

    Rules:
    - Preserve None for missing fields (engine handles NEEDS_MORE_INFO).
    - Do not infer extra clinical facts.
    - Field names map 1:1 to what normalization.normalize_for_readiness expects.
    """
    state: Dict[str, Any] = {}

    # Only include fields that have values — let engine normalization handle None
    field_map = extraction.model_dump()
    for key, value in field_map.items():
        if value is not None:
            state[key] = value

    context = {"source": source}

    return {"state": state, "context": context}


# ── Endpoint ──────────────────────────────────────────────────────


@router.post("/report", response_model=CardioPilotReportResponse)
def pilot_report(payload: CardioPilotReportRequest) -> CardioPilotReportResponse:
    """
    Accept a pilot extraction payload, map to engine input,
    run the existing deterministic cardio_triage_v1 engine,
    and return the real CardioReport.
    """
    engine_input = map_extraction_to_engine_input(payload.extraction, payload.source)

    raw_report = evaluate_cardio_report(engine_input)
    validated_report = assert_valid_report(raw_report)

    return CardioPilotReportResponse(
        case_id=payload.case_id,
        source=payload.source,
        raw_text=payload.raw_text,
        engine_input=engine_input,
        engine_report=validated_report.model_dump(mode="json"),
        human_review_required=True,
        pilot_mode="deterministic_routing_v1",
    )
