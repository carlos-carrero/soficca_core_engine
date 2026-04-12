from __future__ import annotations

from fastapi import APIRouter

from pen_hair_v1.schema import PenEvaluationResponse, PenIntakeRequest
from pen_hair_v1.service import evaluate_pen_intake

router = APIRouter(prefix="/v1/pen", tags=["Pen Hair v1"])


@router.get("/contract")
def pen_contract() -> dict:
    return PenEvaluationResponse.model_json_schema()


@router.post("/evaluate", response_model=PenEvaluationResponse)
def evaluate_pen(payload: PenIntakeRequest) -> PenEvaluationResponse:
    return evaluate_pen_intake(payload)
