from __future__ import annotations

from typing import List

from pen_hair_v1.constants import RULE_DEFAULT_SAFEST_START, RULE_EXCLUDE_ORAL_FOR_HYPERTENSION
from pen_hair_v1.schema import PenNormalizedIntake, TraceEvidence


def build_trace_evidence(intake: PenNormalizedIntake) -> List[TraceEvidence]:
    evidence: List[TraceEvidence] = [
        TraceEvidence(
            field="high_blood_pressure",
            value="true" if intake.high_blood_pressure else "false",
            reason="Explicitly provided by intake payload.",
        )
    ]

    if intake.cardiovascular_conditions:
        evidence.append(
            TraceEvidence(
                field="cardiovascular_conditions",
                value=", ".join(intake.cardiovascular_conditions),
                reason="Explicit comorbidity list; no inferred additions.",
            )
        )

    return evidence


def rules_evaluated() -> List[str]:
    return [RULE_EXCLUDE_ORAL_FOR_HYPERTENSION, RULE_DEFAULT_SAFEST_START]
