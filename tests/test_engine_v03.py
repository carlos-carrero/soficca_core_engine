from __future__ import annotations
import json, hashlib
from soficca_core.engine import evaluate
from soficca_core.rules import ALL_RULE_IDS
from soficca_core.safety_policy import ALL_POLICY_RULE_IDS

def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def test_determinism_same_input_same_output():
    inp = {"state": {"frequency": "sometimes", "desire": "present", "stress": "high", "morning_erection": "normal", "wants_meds": True}, "context": {"source": "USER"}}
    out1 = evaluate(inp)
    out2 = evaluate(inp)
    assert _hash(out1) == _hash(out2)

def test_safety_overrides_everything():
    inp = {"state": {"frequency": "sometimes", "desire": "present", "stress": "high", "morning_erection": "normal", "wants_meds": True, "country": "Colombia", "safety_flags": ["RED_FLAG_SELF_HARM"]}, "context": {"source": "USER"}}
    out = evaluate(inp)
    assert out["safety"]["status"] == "TRIGGERED"
    assert out["decision"]["status"] == "ESCALATED"
    assert out["decision"]["path"] == "PATH_ESCALATE_HUMAN"

def test_needs_more_info_requires_fields():
    inp = {"state": {"frequency": None, "desire": "present", "stress": "high", "morning_erection": "normal", "wants_meds": True}, "context": {"source": "USER"}}
    out = evaluate(inp)
    assert out["decision"]["status"] == "NEEDS_MORE_INFO"
    assert "frequency" in out["decision"]["required_fields"]
    assert len(out["decision"]["required_fields"]) >= 1

def test_conflict_yields_conflict_status():
    inp = {"state": {"frequency": "always", "desire": "present", "stress": "moderate", "morning_erection": "normal", "wants_meds": True, "conflicts": [{"field": "frequency", "a": "always", "b": "sometimes"}]}, "context": {"source": "USER"}}
    out = evaluate(inp)
    assert out["decision"]["status"] == "CONFLICT"
    notes = " ".join(out["trace"]["uncertainty_notes"]).lower()
    assert "conflict" in notes

def test_trace_completeness_includes_all_ids():
    inp = {"state": {"frequency": "sometimes", "desire": "present", "stress": "low", "morning_erection": "normal", "wants_meds": False}, "context": {"source": "USER"}}
    out = evaluate(inp)
    assert out["versions"]["engine"]
    assert out["versions"]["ruleset"]
    assert out["versions"]["safety_policy"]
    assert set(out["trace"]["rules_evaluated"]) == set(ALL_RULE_IDS)
    assert set(out["trace"]["policy_trace"]["evaluated"]) == set(ALL_POLICY_RULE_IDS)
