from __future__ import annotations
from typing import Any, Dict

def normalize(state: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize structured state into deterministic signals used by rules.

    This is *not* NLU. It assumes state values are already normalized enums.
    """
    def missing(x):
        return x is None or (isinstance(x, str) and x.strip() == "")

    frequency = state.get("frequency")
    if missing(frequency):
        intermittent_pattern = None
    elif frequency == "sometimes":
        intermittent_pattern = True
    elif frequency == "always":
        intermittent_pattern = False
    else:
        intermittent_pattern = None

    desire = state.get("desire")
    if missing(desire):
        desire_preserved = None
    elif desire == "present":
        desire_preserved = True
    elif desire in ("low", "reduced"):
        desire_preserved = False
    else:
        desire_preserved = None

    stress = state.get("stress")
    if missing(stress):
        stress_high = None
    elif stress == "high":
        stress_high = True
    elif stress == "low":
        stress_high = False
    elif stress == "moderate":
        stress_high = None
    else:
        stress_high = None

    morning_erection = state.get("morning_erection")
    if missing(morning_erection):
        morning_erection_reduced = None
    elif morning_erection in ("reduced", "rare"):
        morning_erection_reduced = True
    elif morning_erection in ("normal", "often"):
        morning_erection_reduced = False
    else:
        morning_erection_reduced = None

    wants_meds = state.get("wants_meds")
    if missing(wants_meds):
        user_requests_meds = None
    else:
        if isinstance(wants_meds, str):
            v = wants_meds.strip().lower()
            if v in ("yes", "true", "1", "y"):
                user_requests_meds = True
            elif v in ("no", "false", "0", "n"):
                user_requests_meds = False
            else:
                user_requests_meds = None
        elif wants_meds is True:
            user_requests_meds = True
        elif wants_meds is False:
            user_requests_meds = False
        else:
            user_requests_meds = None

    return {
        "intermittent_pattern": intermittent_pattern,
        "desire_preserved": desire_preserved,
        "stress_high": stress_high,
        "morning_erection_reduced": morning_erection_reduced,
        "user_requests_meds": user_requests_meds,
    }
