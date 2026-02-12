from __future__ import annotations

from typing import Any, Dict

from soficca_core.engine import evaluate as evaluate_decision


def _eval(state: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return evaluate_decision({"state": state, "context": context or {}})


def test_invariant_decided_is_terminal_path() -> None:
    """
    Invariant (Option A):
    If decision.status == DECIDED, the engine must NOT ask for more questions.
    i.e. path != PATH_MORE_QUESTIONS and required_fields must be empty.
    """
    report = _eval(
        state={
            "frequency": "daily",
            "desire": "low",
            "stress": "high",
            "morning_erection": "sometimes",
            "wants_meds": True,
            "country": "CO",
            "safety_flags": [],
        },
        context={"source": "USER", "recency_days": 1},
    )

    decision = report["decision"]
    assert decision["status"] == "DECIDED"

    assert decision.get("path") != "PATH_MORE_QUESTIONS", (
        "DECIDED must not point to PATH_MORE_QUESTIONS. "
        "Use NEEDS_MORE_INFO for question-collection."
    )

    assert decision.get("required_fields") in ([], None), (
        "DECIDED must not require missing fields. "
        "required_fields must be empty when terminal."
    )


def test_invariant_needs_more_info_declares_required_fields() -> None:
    """
    Complementary invariant:
    If decision.status == NEEDS_MORE_INFO, it must declare required_fields (non-empty).
    """
    report = _eval(
        state={"desire": "low", "stress": "high"},
        context={"source": "USER"},
    )

    decision = report["decision"]
    assert decision["status"] == "NEEDS_MORE_INFO"
    required_fields = decision.get("required_fields") or []
    assert len(required_fields) > 0, "NEEDS_MORE_INFO must declare required_fields."
