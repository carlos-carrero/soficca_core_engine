from __future__ import annotations
from typing import Any, Dict, List, Tuple

PATH_MORE_QUESTIONS = "PATH_MORE_QUESTIONS"
PATH_EVAL_FIRST = "PATH_EVAL_FIRST"
PATH_MEDS_OK = "PATH_MEDS_OK"
PATH_ESCALATE_HUMAN = "PATH_ESCALATE_HUMAN"  # set by safety override

RULESET_VERSION = "0.3.0"

# Stable rule IDs (auditable)
RULE_INTERMITTENT_MEDS_OK = "RULE_INTERMITTENT_MEDS_OK_V1"
RULE_MORNING_REDUCED_EVAL_PARALLEL = "RULE_MORNING_REDUCED_EVAL_PARALLEL_V1"
RULE_PERSISTENT_EVAL_FIRST = "RULE_PERSISTENT_EVAL_FIRST_V1"
RULE_PERSISTENT_MEDS_REQUIRES_EVAL_PARALLEL = "RULE_PERSISTENT_MEDS_REQUIRES_EVAL_PARALLEL_V1"

ALL_RULE_IDS = [
    RULE_INTERMITTENT_MEDS_OK,
    RULE_MORNING_REDUCED_EVAL_PARALLEL,
    RULE_PERSISTENT_EVAL_FIRST,
    RULE_PERSISTENT_MEDS_REQUIRES_EVAL_PARALLEL,
]

def apply_rules(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic ruleset. Expects normalized signals."""
    decision = {
        "path": PATH_MORE_QUESTIONS,
        "flags": [],
        "reasons": [],
        "recommendations": [],
        "rules_evaluated": list(ALL_RULE_IDS),
        "rules_triggered": [],
    }

    intermittent = signals.get("intermittent_pattern")
    user_requests_meds = signals.get("user_requests_meds")
    morning_reduced = signals.get("morning_erection_reduced") is True

    # Evaluate intermittent branch
    if intermittent is True:
        decision["rules_triggered"].append(RULE_INTERMITTENT_MEDS_OK)
        decision["path"] = PATH_MEDS_OK
        decision["reasons"].append("Symptoms appear intermittent.")
        decision["recommendations"].append("Medication support can be considered (with appropriate authorization).")

        if user_requests_meds is True:
            decision["reasons"].append("User requested medication support.")
            decision["recommendations"].append("Provide medication pathway options and screening questions.")

        if morning_reduced:
            decision["rules_triggered"].append(RULE_MORNING_REDUCED_EVAL_PARALLEL)
            decision["flags"].extend(["physiology_signal", "needs_eval_parallel"])
            decision["reasons"].append("Reduced morning erections can be a physiological signal worth evaluating.")
            decision["recommendations"].append("Recommend clinician evaluation in parallel with any medication support.")

    # Evaluate persistent branch
    elif intermittent is False:
        if user_requests_meds is True:
            decision["rules_triggered"].append(RULE_PERSISTENT_MEDS_REQUIRES_EVAL_PARALLEL)
            decision["path"] = PATH_MEDS_OK
            decision["flags"].append("needs_eval_parallel")
            decision["reasons"].append("User requested medication support.")
            decision["reasons"].append("Persistent pattern suggests clinician review should occur in parallel.")
            decision["recommendations"].append("Provide medication pathway options and screening questions.")
            decision["recommendations"].append("Recommend clinician evaluation in parallel.")
        else:
            decision["rules_triggered"].append(RULE_PERSISTENT_EVAL_FIRST)
            decision["path"] = PATH_EVAL_FIRST
            decision["flags"].append("persistent_pattern")
            decision["reasons"].append("Symptoms seem consistent rather than intermittent.")
            decision["recommendations"].append("Recommend clinician evaluation before a medication-first approach.")

        if morning_reduced and "physiology_signal" not in decision["flags"]:
            decision["flags"].append("physiology_signal")
            decision["reasons"].append("Reduced morning erections can be a physiological signal worth evaluating.")

    return decision
