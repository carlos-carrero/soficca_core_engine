# Safety Policy Changelog

This file is the governance log for safety policy changes.

## 0.3.0
- Introduced versioned policy rule IDs:
  - POLICY_SELF_HARM_V1
  - POLICY_ACUTE_CARDIORESP_V1
  - POLICY_NEURO_V1
  - POLICY_PRIAPISM_V1
  - POLICY_SEVERE_PAIN_BLEEDING_V1
- Policy action: safety triggers force `decision.status=ESCALATED` and `PATH_ESCALATE_HUMAN`
- Added requirement for `country` when escalation localization is needed.
