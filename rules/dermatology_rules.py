from schemas.dermatology_schemas import PenIntakePayload, SoficcaDecisionResponse

def evaluate_hairloss_case(payload: PenIntakePayload) -> SoficcaDecisionResponse:
    # Variables iniciales
    decision = "PATH_MEDS_OK"
    safety_flag = None

    # Regla 1: Menores de edad
    if payload.age < 18:
        decision = "PATH_INELIGIBLE"
        safety_flag = "Paciente menor de edad. Tratamiento no recomendado."
    
    # Regla 2: Chequeo de Seguridad (Hipertensión -> Bloqueo Oral)
    elif "hypertension" in [c.lower() for c in payload.comorbidities]:
        decision = "PATH_TOPICAL_ONLY"
        safety_flag = "Minoxidil oral bloqueado por historial de hipertensión."

    # Regla 3: Construcción del "Trace Evidence" (Zero-Noise)
    # Solo agregamos los campos que tienen datos reales
    raw_trace = {
        "patient_age": payload.age,
        "norwood_scale": payload.norwood_stage,
        "comorbidities": payload.comorbidities if payload.comorbidities else None,
        "concurrent_symptoms": payload.concurrent_symptoms if payload.concurrent_symptoms else None,
        "safety_flag": safety_flag
    }

    # Filtrar valores nulos o listas vacías para no ensuciar el frontend
    clean_trace = {k: v for k, v in raw_trace.items() if v is not None and v != []}

    return SoficcaDecisionResponse(
        decision_path=decision,
        trace_evidence=clean_trace
    )