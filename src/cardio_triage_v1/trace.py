from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TraceBuilder:
    """Deterministic audit-trace accumulator for cardio_triage_v1 scaffold."""

    rules_evaluated: List[str] = field(default_factory=list)
    rules_triggered: List[str] = field(default_factory=list)
    policy_evaluated: List[str] = field(default_factory=list)
    policy_triggered: List[str] = field(default_factory=list)
    evidence: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    uncertainty_notes: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    activated_rules: List[str] = field(default_factory=list)
    preliminary_route: Optional[str] = None
    final_route: Optional[str] = None
    override_reason: Optional[str] = None

    def add_rule_evaluated(self, rule_id: str) -> None:
        if rule_id not in self.rules_evaluated:
            self.rules_evaluated.append(rule_id)

    def add_rule_triggered(self, rule_id: str) -> None:
        if rule_id not in self.rules_triggered:
            self.rules_triggered.append(rule_id)

    def add_policy_evaluated(self, policy_id: str) -> None:
        if policy_id not in self.policy_evaluated:
            self.policy_evaluated.append(policy_id)

    def add_policy_triggered(self, policy_id: str) -> None:
        if policy_id not in self.policy_triggered:
            self.policy_triggered.append(policy_id)

    def add_evidence(
        self,
        field_name: str,
        *,
        value: Any,
        source: str = "UNKNOWN",
        recency_days: Optional[float] = None,
        confidence: Optional[float] = None,
        contradiction: bool = False,
    ) -> None:
        self.evidence[field_name] = {
            "value": value,
            "source": source,
            "recency_days": recency_days,
            "confidence": confidence,
            "contradiction": bool(contradiction),
        }

    def note_uncertainty(self, msg: str) -> None:
        self.uncertainty_notes.append(msg)

    def set_missing_fields(self, fields: List[str]) -> None:
        self.missing_fields = list(fields)

    def set_routes(self, preliminary_route: Optional[str], final_route: Optional[str]) -> None:
        self.preliminary_route = preliminary_route
        self.final_route = final_route

    def set_override_reason(self, reason: Optional[str]) -> None:
        self.override_reason = reason

    def set_activated_rules(self, activated_rules: List[str]) -> None:
        self.activated_rules = list(activated_rules)

    def build(self) -> Dict[str, Any]:
        return {
            "policy_trace": {
                "evaluated": self.policy_evaluated,
                "triggered": self.policy_triggered,
            },
            "rules_evaluated": self.rules_evaluated,
            "rules_triggered": self.rules_triggered,
            "evidence": self.evidence,
            "uncertainty_notes": self.uncertainty_notes,
            "missing_fields": self.missing_fields,
            "activated_rules": self.activated_rules,
            "preliminary_route": self.preliminary_route,
            "final_route": self.final_route,
            "override_reason": self.override_reason,
        }
