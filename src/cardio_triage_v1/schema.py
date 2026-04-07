from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from cardio_triage_v1.constants import (
    ALL_PATH_IDS,
    DECISION_CONFLICT,
    DECISION_DECIDED,
    DECISION_ESCALATED,
    DECISION_NEEDS_MORE_INFO,
    SAFETY_ACTION_NONE,
    SAFETY_ACTION_OVERRIDE_BLOCK_RECS,
    SAFETY_ACTION_OVERRIDE_ESCALATE,
    SAFETY_CLEAR,
    SAFETY_TRIGGERED,
)


class DecisionStatus(str, Enum):
    DECIDED = DECISION_DECIDED
    NEEDS_MORE_INFO = DECISION_NEEDS_MORE_INFO
    CONFLICT = DECISION_CONFLICT
    ESCALATED = DECISION_ESCALATED


class PathId(str, Enum):
    PATH_MORE_QUESTIONS = ALL_PATH_IDS[0]
    PATH_EMERGENCY_NOW = ALL_PATH_IDS[1]
    PATH_URGENT_SAME_DAY = ALL_PATH_IDS[2]
    PATH_ROUTINE = ALL_PATH_IDS[3]
    PATH_SELF_CARE = ALL_PATH_IDS[4]
    PATH_ESCALATE_HUMAN = ALL_PATH_IDS[5]


class SafetyStatus(str, Enum):
    CLEAR = SAFETY_CLEAR
    TRIGGERED = SAFETY_TRIGGERED


class SafetyAction(str, Enum):
    NONE = SAFETY_ACTION_NONE
    OVERRIDE_ESCALATE = SAFETY_ACTION_OVERRIDE_ESCALATE
    OVERRIDE_BLOCK_RECS = SAFETY_ACTION_OVERRIDE_BLOCK_RECS


class PolicyTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluated: List[str]
    triggered: List[str]


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: Any


class CardioVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: str
    ruleset: str
    safety_policy: str
    contract: str


class CardioDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DecisionStatus
    path: Optional[PathId]
    flags: List[str]
    reasons: List[str]
    recommendations: List[str]
    required_fields: List[str]
    missing_fields: List[str]
    decision_id: str
    case_status: str
    decision_type: str
    recommended_route: Optional[PathId]
    urgency_level: str
    clinical_summary: str
    required_actions: List[str]


class CardioSafety(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SafetyStatus
    action: SafetyAction
    triggers: List[str]
    policy_version: str
    safety_id: str
    has_red_flags: bool
    override_applied: bool
    severity: str
    flags: List[str]


class CardioTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_trace: PolicyTrace
    rules_evaluated: List[str]
    rules_triggered: List[str]
    evidence: Dict[str, EvidenceItem]
    uncertainty_notes: List[str]
    missing_fields: List[str]
    activated_rules: List[str]
    preliminary_route: Optional[PathId]
    final_route: Optional[PathId]
    override_reason: Optional[str]
    conflicts_detected: List[str]


class CardioReport(BaseModel):
    model_config = ConfigDict(extra="forbid", title="Soficca Cardio Triage Report v1")

    ok: bool
    errors: List[Dict[str, Any]]
    versions: CardioVersions
    decision: CardioDecision
    safety: CardioSafety
    trace: CardioTrace

    @model_validator(mode="after")
    def check_cross_field_invariants(self) -> "CardioReport":
        if self.decision.missing_fields != self.trace.missing_fields:
            raise ValueError("decision.missing_fields and trace.missing_fields must match")

        if self.safety.status == SafetyStatus.TRIGGERED:
            if self.decision.status != DecisionStatus.ESCALATED:
                raise ValueError("If safety.TRIGGERED, decision.status must be ESCALATED")
            if self.safety.action != SafetyAction.OVERRIDE_ESCALATE:
                raise ValueError("If safety.TRIGGERED, safety.action must be OVERRIDE_ESCALATE")

        return self
