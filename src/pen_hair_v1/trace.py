from __future__ import annotations

from typing import List

from pen_hair_v1.constants import (
    RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
    RULE_DEFAULT_SAFEST_START,
    RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
    RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
    RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
    RULE_SUPPORT_PATH_COMFORT_PRIORITY,
    RULE_SUPPORT_PATH_LOW_CONSISTENCY,
    RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
)
from pen_hair_v1.schema import PenNormalizedIntake, TraceEvidence


def build_trace_evidence(intake: PenNormalizedIntake) -> List[TraceEvidence]:
    evidence: List[TraceEvidence] = [
        TraceEvidence(
            field="high_blood_pressure",
            value="true" if intake.high_blood_pressure else "false",
            reason="Explicitly provided by intake payload.",
        )
    ]

    evidence.append(
        TraceEvidence(
            field="cardiovascular_conditions",
            value="true" if intake.cardiovascular_conditions else "false",
            reason="Explicit yes/no cardiovascular risk signal from intake payload.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="prior_treatment_use",
            value="true" if intake.prior_treatment_use else "false",
            reason="Used for deterministic side-effect safety branching.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="had_side_effects",
            value="true" if intake.had_side_effects else "false",
            reason="Used for deterministic side-effect safety branching.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="scalp_sensitivities",
            value="true" if intake.scalp_sensitivities else "false",
            reason="Used for support-path selection.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="routine_consistency",
            value=intake.routine_consistency,
            reason="Used for support-path or missing-info branching.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="priority_factor",
            value=intake.priority_factor,
            reason="Used for comfort-priority support branching.",
        )
    )
    evidence.append(
        TraceEvidence(
            field="treatment_preference",
            value=intake.treatment_preference,
            reason="Used for missing-info guardrail branching.",
        )
    )

    return evidence


def rules_evaluated() -> List[str]:
    return [
        RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
        RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
        RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
        RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
        RULE_SUPPORT_PATH_LOW_CONSISTENCY,
        RULE_SUPPORT_PATH_COMFORT_PRIORITY,
        RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
        RULE_DEFAULT_SAFEST_START,
    ]
