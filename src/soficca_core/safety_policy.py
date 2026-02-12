from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

SAFETY_POLICY_VERSION = "0.3.0"

# Stable policy rule IDs (governable)
POLICY_SELF_HARM = "POLICY_SELF_HARM_V1"
POLICY_ACUTE_CARDIORESP = "POLICY_ACUTE_CARDIORESP_V1"
POLICY_NEURO = "POLICY_NEURO_V1"
POLICY_PRIAPISM = "POLICY_PRIAPISM_V1"
POLICY_SEVERE_PAIN_BLEEDING = "POLICY_SEVERE_PAIN_BLEEDING_V1"

ALL_POLICY_RULE_IDS = [
    POLICY_SELF_HARM,
    POLICY_ACUTE_CARDIORESP,
    POLICY_NEURO,
    POLICY_PRIAPISM,
    POLICY_SEVERE_PAIN_BLEEDING,
]

# Mapping from detected flags -> policy rule IDs
FLAG_TO_POLICY = {
    "RED_FLAG_SELF_HARM": POLICY_SELF_HARM,
    "RED_FLAG_ACUTE_CARDIORESP": POLICY_ACUTE_CARDIORESP,
    "RED_FLAG_NEURO": POLICY_NEURO,
    "RED_FLAG_PRIAPISM": POLICY_PRIAPISM,
    "RED_FLAG_SEVERE_PAIN_BLEEDING": POLICY_SEVERE_PAIN_BLEEDING,
}

def evaluate_safety(state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Evaluate safety policy against structured state.

    Returns (safety_object, policy_trace_object).
    """
    safety_flags: List[str] = list(state.get("safety_flags") or [])
    evaluated = list(ALL_POLICY_RULE_IDS)
    triggered: List[str] = []

    for f in safety_flags:
        pid = FLAG_TO_POLICY.get(f)
        if pid and pid not in triggered:
            triggered.append(pid)

    triggered_flags = [f for f in safety_flags if f in FLAG_TO_POLICY]

    if triggered:
        safety = {
            "status": "TRIGGERED",
            "action": "OVERRIDE_ESCALATE",
            "triggers": triggered_flags,
            "user_guidance_required_fields": ["country"] if not state.get("country") else [],
            "policy_version": SAFETY_POLICY_VERSION,
        }
    else:
        safety = {
            "status": "CLEAR",
            "action": "NONE",
            "triggers": [],
            "user_guidance_required_fields": [],
            "policy_version": SAFETY_POLICY_VERSION,
        }

    policy_trace = {"evaluated": evaluated, "triggered": triggered}
    return safety, policy_trace
