# Soficca Decision Report Contract v0.3

This repository demonstrates **Soficca Core Engine** as an **infrastructure-grade decision engine**.

The engine evaluates a **structured clinical state** and returns a **Decision Report** that is:
- deterministic
- auditable (formal trace)
- governed (versioned safety policy + ruleset)
- safe-by-design (safety overrides everything)

## Output schema
The canonical JSON Schema is:
- `contract/decision_report_v0_3.schema.json`

## Key invariants (must always hold)
1. If `safety.status == TRIGGERED` then:
   - `decision.status == ESCALATED`
   - `decision.path == PATH_ESCALATE_HUMAN`
   - clinical recommendations must not be emitted

2. If `decision.status == NEEDS_MORE_INFO` then:
   - `decision.required_fields` is a non-empty list

3. Trace completeness:
   - `trace.rules_evaluated` includes the full ruleset IDs
   - `trace.policy_trace.evaluated` includes the full safety policy IDs
   - `trace.evidence` includes at least core fields (even if value is null)

4. If `decision.status == CONFLICT` then:
   - `trace.uncertainty_notes` must explicitly mention conflict

## Input format (decision-first)
```
{
  "state": { ... },     // structured signals/slots (partial allowed)
  "context": { ... }    // optional metadata (source, recency_days, etc.)
}
```

The engine is designed so adapters (forms, EHR, chat, etc.) can produce `state` in a reproducible way.
