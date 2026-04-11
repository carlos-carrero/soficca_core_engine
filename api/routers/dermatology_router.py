from fastapi import APIRouter
from schemas.dermatology_schemas import PenIntakePayload, SoficcaDecisionResponse
from rules.dermatology_rules import evaluate_hairloss_case

router = APIRouter(
    prefix="/api/v1/dermatology",
    tags=["Dermatology / Pen"]
)

@router.post("/hairloss/evaluate", response_model=SoficcaDecisionResponse)
async def evaluate_hairloss_endpoint(payload: PenIntakePayload):
    # Pasamos el JSON al evaluador de reglas y devolvemos la respuesta
    result = evaluate_hairloss_case(payload)
    return result