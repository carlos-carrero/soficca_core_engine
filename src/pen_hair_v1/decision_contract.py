from __future__ import annotations

from pen_hair_v1.constants import CONTRACT_VERSION, ENGINE_VERSION, RULESET_VERSION, SAFETY_POLICY_VERSION
from pen_hair_v1.schema import PenEvaluationResponse, PenVersions


def build_versions() -> PenVersions:
    return PenVersions(
        engine=ENGINE_VERSION,
        ruleset=RULESET_VERSION,
        safety_policy=SAFETY_POLICY_VERSION,
        contract=CONTRACT_VERSION,
    )


def assert_valid_response(response: PenEvaluationResponse) -> PenEvaluationResponse:
    return PenEvaluationResponse.model_validate(response.model_dump(mode="python"))
