from __future__ import annotations
from typing import Any, Dict, List, Tuple
from soficca_core.errors import make_error

def validate_input(input_data: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Validate input structure for decision-first engine.

    Supported input shapes:
    A) {"state": {...}, "context": {...}}
    B) Legacy-ish: {"context": {"chat_state": {...}}} etc. (best-effort mapping)
    """
    errors: List[Dict[str, Any]] = []
    cleaned: Dict[str, Any] = {}

    if not isinstance(input_data, dict):
        errors.append(make_error("INVALID_TYPE", "Input data must be a dict", path="$"))
        return errors, cleaned

    # Preferred
    state = input_data.get("state")
    context = input_data.get("context")

    if state is None and "context" in input_data and isinstance(input_data.get("context"), dict):
        # Best-effort: accept old format by mapping slots->state if present.
        ctx = input_data.get("context") or {}
        chat_state = ctx.get("chat_state")
        if isinstance(chat_state, dict):
            slots = (chat_state.get("slots") or {})
            state = dict(slots)
            # pull safety flags if present
            if chat_state.get("safety_flags"):
                state["safety_flags"] = chat_state.get("safety_flags")
            # pull conflicts if present
            if chat_state.get("conflicts"):
                state["conflicts"] = chat_state.get("conflicts")
        context = ctx

    if not isinstance(state, dict):
        errors.append(make_error("INVALID_STATE", "Input must include a 'state' object", path="$.state"))
        return errors, cleaned

    if context is None:
        context = {}
    if not isinstance(context, dict):
        errors.append(make_error("INVALID_CONTEXT", "If provided, context must be an object", path="$.context"))
        return errors, cleaned

    cleaned["state"] = state
    cleaned["context"] = context
    return errors, cleaned
