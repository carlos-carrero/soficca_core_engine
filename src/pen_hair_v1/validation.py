from __future__ import annotations

from pen_hair_v1.schema import PenIntakeRequest


def validate_intake(payload: PenIntakeRequest) -> PenIntakeRequest:
    """Stage-1 explicit validation hook for Pen intake payload."""
    return payload
