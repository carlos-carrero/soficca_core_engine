export type DecisionStatus = 'DECIDED' | 'NEEDS_MORE_INFO' | 'CONFLICT' | 'ESCALATED';

export type CardioDecision = {
  status: DecisionStatus;
  decision_type: 'NEEDS_MORE_INFO' | 'ROUTINE_REVIEW' | 'URGENT_ESCALATION' | 'EMERGENCY_OVERRIDE' | 'DEFERRED_PENDING_DATA';
  decision_id: string;
  path: string | null;
  recommended_route: string | null;
  case_status: 'PENDING_DATA' | 'TRIAGED';
  urgency_level: 'UNKNOWN' | 'ROUTINE' | 'URGENT' | 'EMERGENCY';
  clinical_summary: string;
  required_fields: string[];
  missing_fields: string[];
  required_actions: string[];
  reasons: string[];
  flags: string[];
};

export type CardioSafety = {
  status: 'CLEAR' | 'TRIGGERED';
  action: 'NONE' | 'OVERRIDE_ESCALATE';
  triggers: string[];
  policy_version: string;
  safety_id: string;
  has_red_flags: boolean;
  override_applied: boolean;
  severity: 'NONE' | 'EMERGENCY';
  flags: string[];
};

export type CardioTrace = {
  policy_trace: { evaluated: string[]; triggered: string[] };
  rules_evaluated: string[];
  rules_triggered: string[];
  activated_rules: string[];
  evidence: Record<string, { value: unknown }>;
  uncertainty_notes: string[];
  missing_fields: string[];
  conflicts_detected: string[];
  preliminary_route: string | null;
  final_route: string | null;
  override_reason: string | null;
};

export type CardioReport = {
  ok: boolean;
  errors: Array<{ code?: string; message?: string }>;
  versions: {
    engine: string;
    ruleset: string;
    safety_policy: string;
    contract: string;
  };
  decision: CardioDecision;
  safety: CardioSafety;
  trace: CardioTrace;
};

export type CardioScenarioId =
  | 'NEEDS_MORE_INFO'
  | 'ROUTINE_REVIEW'
  | 'URGENT_ESCALATION'
  | 'EMERGENCY_ROUTE'
  | 'DEFERRED_PENDING_DATA';

export type CardioScenario = {
  id: CardioScenarioId;
  label: string;
  report: CardioReport;
};
