from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PenIntakePayload(BaseModel):
    age: int = Field(..., description="Edad del paciente")
    norwood_stage: int = Field(..., description="Nivel en la escala Norwood (1-7)")
    comorbidities: List[str] = Field(default=[], description="Lista de comorbilidades")
    concurrent_symptoms: List[str] = Field(default=[], description="Síntomas concurrentes en el cuero cabelludo")

class SoficcaDecisionResponse(BaseModel):
    decision_path: str
    trace_evidence: Dict[str, Any]