"""
Cardio Pilot AI extraction endpoint.

This endpoint ONLY structures free-text clinical narratives into
deterministic engine-compatible extraction fields.

It does NOT:
- diagnose
- prescribe
- recommend treatment
- decide route or emergency status
- replace clinical judgment

The deterministic Soficca Cardio engine remains the only routing authority.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/v1/cardio/pilot", tags=["cardio-pilot-extract"])


# ── Disallowed fields that must be stripped from AI output ─────────

DISALLOWED_FIELDS = frozenset({
    "diagnosis",
    "treatment",
    "prescription",
    "route",
    "recommended_route",
    "emergency_decision",
    "clinical_advice",
    "patient_instruction",
})


# ── Pydantic models ──────────────────────────────────────────────


class CardioPilotExtractRequest(BaseModel):
    """Input for the AI extraction endpoint."""

    model_config = ConfigDict(extra="forbid")

    case_text: str = Field(..., min_length=1, description="Free-text clinical narrative")
    language: str = Field(default="auto", description="Language hint (auto, en, es)")
    source: str = Field(default="free_text", description="Source identifier")


class CardioPilotExtractionFields(BaseModel):
    """Structured extraction fields (AI output schema)."""

    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = None
    chest_pain_present: Optional[bool] = None
    pain_duration_minutes: Optional[int] = None
    pain_character: Optional[
        Literal["pressure", "sharp", "burning", "tightness", "heaviness", "other"]
    ] = None
    pain_severity: Optional[Literal["low", "moderate", "high"]] = None
    pain_radiation: Optional[
        Literal["none", "left_arm", "right_arm", "jaw", "back", "shoulder", "multiple", "other"]
    ] = None
    exertional_chest_pain: Optional[bool] = None
    diaphoresis: Optional[bool] = None
    dyspnea: Optional[bool] = None
    syncope: Optional[bool] = None
    systolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    prior_mi: Optional[bool] = None
    known_cad: Optional[bool] = None
    cv_risk_factors_count: Optional[int] = None
    current_meds_none: Optional[bool] = None
    current_meds_summary: Optional[str] = None


class CardioFieldEvidence(BaseModel):
    """Per-field evidence linking extraction to source text."""

    model_config = ConfigDict(extra="forbid")

    field: str
    value: str
    source_text: str
    confidence: float


ExtractionQualityFlag = Literal[
    "low_confidence_extraction",
    "critical_missing_fields",
    "contradictory_narrative",
    "limited_vitals",
    "medication_status_unclear",
    "cardiovascular_history_unclear",
    "requires_human_confirmation",
    "possible_identifier_detected",
]

PiiWarning = Literal[
    "possible_name_detected",
    "possible_phone_detected",
    "possible_email_detected",
    "possible_id_number_detected",
    "possible_address_detected",
]


class CardioMissingInformation(BaseModel):
    """Categorized missing information from the extraction."""

    model_config = ConfigDict(extra="forbid")

    required_for_routing: List[str]
    clinically_useful: List[str]
    unconfirmed: List[str]


class CardioAIRawOutput(BaseModel):
    """Schema sent to OpenAI for structured output parsing.

    NOTE: OpenAI structured output requires all fields to be explicitly typed
    with no defaults. Keep this model compatible with the Structured Outputs API.
    """

    model_config = ConfigDict(extra="forbid")

    fields: CardioPilotExtractionFields
    structured_clinical_summary: str
    missing_fields: List[str]
    missing_information: CardioMissingInformation
    completion_questions: List[str]
    possible_conflicts: List[str]
    field_evidence: List[CardioFieldEvidence]
    extraction_quality_flags: List[ExtractionQualityFlag]
    pii_warnings: List[PiiWarning]
    warnings: List[str]
    confidence: float
    language_detected: str


class CardioPilotExtractResponse(BaseModel):
    """Response from the extraction endpoint."""

    extraction_id: str
    model: str
    language_detected: str
    ai_role: str = "STRUCTURING_ONLY"
    confidence: float
    fields: CardioPilotExtractionFields
    structured_clinical_summary: str
    missing_fields: List[str]
    missing_information: CardioMissingInformation
    completion_questions: List[str]
    possible_conflicts: List[str]
    field_evidence: List[CardioFieldEvidence]
    extraction_quality_flags: List[ExtractionQualityFlag]
    pii_warnings: List[PiiWarning]
    warnings: List[str]


# ── System instruction ────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are a clinical signal extraction component for Soficca Cardio Pilot.
You only convert free-text cardiovascular symptom narratives into structured fields.
You do not diagnose.
You do not prescribe.
You do not recommend treatment.
You do not decide triage route.
You do not decide emergency status.
The deterministic Soficca engine will perform routing after validation.

CRITICAL — null vs false distinction:
- null means the field was NOT mentioned in the text or is uncertain.
- false means the text EXPLICITLY denies the condition.
- NEVER infer false from absence of mention. If a symptom is not mentioned, it is null.
- Examples:
  "No dyspnea" → dyspnea = false
  "Denies shortness of breath" → dyspnea = false
  Dyspnea not mentioned at all → dyspnea = null
- Apply this rule to ALL boolean fields: syncope, diaphoresis, dyspnea, exertional_chest_pain, known_cad, prior_mi, current_meds_none, chest_pain_present.

Medication logic:
- "No current medications", "not on cardiac meds", "not taking cardiac medications" → current_meds_none = true, current_meds_summary = null
- Medications not mentioned at all → current_meds_none = null, current_meds_summary = null
- Medications are mentioned (e.g. "taking aspirin and metoprolol") → current_meds_none = false, current_meds_summary = "aspirin, metoprolol"

Pain severity rules:
- Only set when explicitly stated or strongly supported by specific words.
- "severe", "intense", "excruciating" → high
- "moderate" → moderate
- "mild", "low-grade", "slight" → low
- If severity is not stated or unclear → null

Field types and allowed values:
- pain_character: pressure, sharp, burning, tightness, heaviness, other, or null.
- pain_severity: low, moderate, high, or null.
- pain_radiation: none, left_arm, right_arm, jaw, back, shoulder, multiple, other, or null.
  "No radiation" → pain_radiation = "none". Radiation not mentioned → pain_radiation = null.

Conflict detection:
- If the patient denies chest pain but describes chest-pain-like symptoms (pressure, radiation, duration), add to possible_conflicts: describe the contradiction.
- If vital signs seem contradictory or age seems inconsistent with the narrative, note it.

Field evidence:
- For each extracted non-null field, include the exact snippet from the text that supports it in field_evidence.
- The value field in evidence must be a string representation (e.g. "true", "false", "64", "pressure").
- Do not fabricate evidence. If no text supports a field, do not include evidence for it.

structured_clinical_summary:
- Write a short physician-review summary of the extracted signals.
- Use phrases like "The narrative reports..." or "The case text describes..."
- NEVER include diagnosis, treatment recommendation, triage route, or emergency recommendation.
- Mention confirmed findings, vitals, and which fields are missing or unconfirmed.

missing_information:
- Categorize missing/unconfirmed fields into three buckets:
  required_for_routing: fields the deterministic engine likely needs for safe routing (e.g. age, chest_pain_present, pain_severity, syncope, systolic_bp, heart_rate).
  clinically_useful: useful clinical context not strictly required by the engine (e.g. cv_risk_factors_count, current_meds_summary).
  unconfirmed: fields not mentioned or uncertain that could not be categorized above.
- Do not invent missing items. Only include fields that are genuinely absent or uncertain.

completion_questions:
- Generate concise questions to complete the intake.
- Questions only. No advice. No diagnosis. No treatment. No route recommendation.
- Examples: "How long has the chest discomfort been present?", "Does the discomfort radiate to the arm, jaw, back, or shoulder?"

extraction_quality_flags:
- Use only these controlled values:
  low_confidence_extraction, critical_missing_fields, contradictory_narrative, limited_vitals,
  medication_status_unclear, cardiovascular_history_unclear, requires_human_confirmation, possible_identifier_detected.
- Flag contradictions, critical missing fields, limited vitals, unclear medication or cardiovascular history, and possible identifiers.
- If overall confidence is below 0.70, include low_confidence_extraction.
- If the narrative appears to contain contradictions, include contradictory_narrative.
- If systolic_bp or heart_rate is missing, include limited_vitals.
- If current_meds_none is null, include medication_status_unclear.
- If prior_mi and known_cad are both null, include cardiovascular_history_unclear.
- Always include requires_human_confirmation (all AI extractions require physician review).

pii_warnings:
- Detect likely personal identifiers in the narrative: names, phone numbers, emails, ID numbers, addresses.
- Use only these controlled values: possible_name_detected, possible_phone_detected, possible_email_detected, possible_id_number_detected, possible_address_detected.
- Only warn. Do not transform or redact identifiers.
- If no identifiers detected, return empty list.

Other rules:
- For missing_fields, list field names that were not mentioned or could not be determined.
- For warnings, note any important extraction caveats.
- Set confidence as a float 0.0-1.0 reflecting overall extraction quality. Never set confidence to exactly 1.0.
- Detect the language of the input and set language_detected (e.g. "en", "es").
"""

USER_PROMPT_TEMPLATE = """\
Extract structured cardiovascular fields from the following clinical narrative.
Return ONLY the structured extraction. Do not diagnose, prescribe, or decide any route.

---
{case_text}
---
"""


# ── Safety filter ─────────────────────────────────────────────────


DISALLOWED_PHRASES = [
    "recommend",
    "should be treated",
    "prescribe",
    "administer",
    "route to",
    "send to emergency",
    "triage to",
    "classified as emergency",
    "classified as urgent",
    "diagnosis is",
    "diagnosed with",
    "patient should",
    "advise the patient",
    "take the patient to",
]


def strip_disallowed_fields(raw: Dict[str, Any]) -> List[str]:
    """Remove any disallowed clinical-decision fields from raw AI output.
    Returns list of warning messages for each stripped field."""
    warnings: List[str] = []
    fields_data = raw.get("fields", {})
    if isinstance(fields_data, dict):
        for key in list(fields_data.keys()):
            if key in DISALLOWED_FIELDS:
                del fields_data[key]
                warnings.append(
                    f"Disallowed clinical-decision field removed from extraction output: {key}"
                )
    # Also check top-level keys
    for key in list(raw.keys()):
        if key in DISALLOWED_FIELDS:
            del raw[key]
            warnings.append(
                f"Disallowed clinical-decision field removed from extraction output: {key}"
            )
    return warnings


def sanitize_summary_and_questions(raw: Dict[str, Any]) -> List[str]:
    """Check structured_clinical_summary and completion_questions for
    disallowed clinical-decision language. Returns warning messages."""
    warnings: List[str] = []

    summary = raw.get("structured_clinical_summary", "")
    if isinstance(summary, str):
        lower = summary.lower()
        for phrase in DISALLOWED_PHRASES:
            if phrase in lower:
                raw["structured_clinical_summary"] = (
                    "[Summary contained clinical decision language and was redacted for safety. "
                    "See extracted fields for structured data.]"
                )
                warnings.append(
                    f"structured_clinical_summary contained disallowed phrase '{phrase}' and was redacted."
                )
                break

    questions = raw.get("completion_questions", [])
    if isinstance(questions, list):
        cleaned: List[str] = []
        for q in questions:
            if not isinstance(q, str):
                continue
            lower_q = q.lower()
            blocked = False
            for phrase in DISALLOWED_PHRASES:
                if phrase in lower_q:
                    warnings.append(
                        f"completion_question removed (contained '{phrase}'): {q[:80]}"
                    )
                    blocked = True
                    break
            if not blocked:
                cleaned.append(q)
        raw["completion_questions"] = cleaned

    return warnings


# ── OpenAI call ───────────────────────────────────────────────────


def _call_openai(case_text: str, model: str) -> CardioAIRawOutput:
    """Call OpenAI with structured output parsing.

    Error handling:
    - Missing key → 503
    - Auth / invalid key → 503 with safe message
    - Bad request / schema error → 502
    - Other provider error → 502
    - Never exposes API key or sensitive data in error messages.
    """
    from openai import OpenAI, AuthenticationError, BadRequestError, APIError

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. AI extraction is unavailable.",
        )

    client = OpenAI(api_key=api_key)

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(case_text=case_text)},
            ],
            response_format=CardioAIRawOutput,
            temperature=0.1,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=503,
            detail="OpenAI authentication failed. Check OPENAI_API_KEY configuration.",
        )
    except BadRequestError as e:
        safe_msg = str(e)
        # Strip anything that might contain the key
        if "api_key" in safe_msg.lower() or "sk-" in safe_msg:
            safe_msg = "Invalid request to OpenAI. Check model and schema configuration."
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI bad request: {safe_msg}",
        )
    except APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {e.message if hasattr(e, 'message') else 'Provider error'}",
        )
    except Exception as e:
        # Catch-all: never expose raw exception details
        raise HTTPException(
            status_code=502,
            detail="Unexpected error calling OpenAI. AI extraction is temporarily unavailable.",
        )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise HTTPException(
            status_code=502,
            detail="OpenAI returned an unparseable response.",
        )

    return parsed


# ── Endpoint ──────────────────────────────────────────────────────


@router.post("/extract", response_model=CardioPilotExtractResponse)
def pilot_extract(payload: CardioPilotExtractRequest) -> CardioPilotExtractResponse:
    """
    Extract structured clinical fields from a free-text narrative.

    This endpoint ONLY structures the signal. It does not route, diagnose, or prescribe.
    """
    model = os.environ.get("CARDIO_EXTRACTION_MODEL", "gpt-4o-mini")

    raw_output = _call_openai(payload.case_text, model)

    # Safety: strip any disallowed fields from raw dict, then re-validate
    raw_dict = raw_output.model_dump()
    safety_warnings = strip_disallowed_fields(raw_dict)
    content_warnings = sanitize_summary_and_questions(raw_dict)

    # Re-validate after stripping
    cleaned = CardioAIRawOutput.model_validate(raw_dict)

    all_warnings = list(cleaned.warnings) + safety_warnings + content_warnings

    extraction_id = f"EXT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    return CardioPilotExtractResponse(
        extraction_id=extraction_id,
        model=model,
        language_detected=cleaned.language_detected,
        ai_role="STRUCTURING_ONLY",
        confidence=cleaned.confidence,
        fields=cleaned.fields,
        structured_clinical_summary=cleaned.structured_clinical_summary,
        missing_fields=cleaned.missing_fields,
        missing_information=cleaned.missing_information,
        completion_questions=cleaned.completion_questions,
        possible_conflicts=cleaned.possible_conflicts,
        field_evidence=cleaned.field_evidence,
        extraction_quality_flags=cleaned.extraction_quality_flags,
        pii_warnings=cleaned.pii_warnings,
        warnings=all_warnings,
    )
