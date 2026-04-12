from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DecisionStatus(str, Enum):
    DECIDED = "DECIDED"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"


class DecisionPath(str, Enum):
    TOPICAL_TREATMENT = "topical_treatment"
    ORAL_TREATMENT = "oral_treatment"


class TraceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    value: str
    reason: str


class PenIntakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=18, le=100)
    norwood_stage: int = Field(ge=1, le=7)
    loss_noticed: str = Field(min_length=1)
    loss_areas: List[str] = Field(default_factory=list)
    main_goal: str = Field(min_length=1)
    high_blood_pressure: bool
    cardiovascular_conditions: List[str] = Field(default_factory=list)
    current_medication: bool
    medication_detail: Optional[str] = None
    prior_treatment_use: bool
    which_treatment: List[str] = Field(default_factory=list)
    had_side_effects: bool
    side_effect_detail: Optional[str] = None
    scalp_sensitivities: bool
    scalp_detail: Optional[str] = None
    treatment_preference: str = Field(min_length=1)
    routine_consistency: str = Field(min_length=1)
    priority_factor: str = Field(min_length=1)
    baseline_photos_uploaded: bool


class PenNormalizedIntake(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int
    norwood_stage: int
    loss_noticed: str
    loss_areas: List[str]
    main_goal: str
    high_blood_pressure: bool
    cardiovascular_conditions: List[str]
    current_medication: bool
    medication_detail: Optional[str]
    prior_treatment_use: bool
    which_treatment: List[str]
    had_side_effects: bool
    side_effect_detail: Optional[str]
    scalp_sensitivities: bool
    scalp_detail: Optional[str]
    treatment_preference: str
    routine_consistency: str
    priority_factor: str
    baseline_photos_uploaded: bool


class PenVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: str
    ruleset: str
    safety_policy: str
    contract: str


class PenDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DecisionStatus
    decision_path: DecisionPath
    title: str
    explanation: str
    flags: List[str]
    excluded_options: List[DecisionPath]


class PenTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules_evaluated: List[str]
    rules_triggered: List[str]
    trace_evidence: List[TraceEvidence]


class JourneySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    body: str


class JourneyView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hero: JourneySection
    progress_strip: List[str]
    progress_photos: Dict[str, str]
    narrative: JourneySection
    recommendation: JourneySection
    decision_trace_badge: str


class PenJourneyViews(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month_0: JourneyView
    week_6: JourneyView
    month_3: JourneyView
    month_6: JourneyView


class FrontendEvaluationAdapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_path: DecisionPath
    decision_title: str
    decision_explanation: str
    trace_evidence: List[TraceEvidence]


class FrontendJourneyAdapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month_0: JourneyView
    week_6: JourneyView
    month_3: JourneyView
    month_6: JourneyView


class FrontendAdapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation: FrontendEvaluationAdapter
    journey: FrontendJourneyAdapter


class PenEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    versions: PenVersions
    decision: PenDecision
    trace: PenTrace
    journey_views: PenJourneyViews
    frontend_adapter: FrontendAdapter
