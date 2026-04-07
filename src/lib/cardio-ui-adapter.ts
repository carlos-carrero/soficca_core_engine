import type { CardioPayload, CardioReport, CardioScenario } from '@/lib/cardio-types';

export type UiUrgency = 'critical' | 'high' | 'moderate' | 'low' | 'pending';

export type EngineViewModel = {
  caseSummary: string;
  decisionSummary: {
    title: string;
    urgency: UiUrgency;
    finalRoute: string;
    recommendedRoute: string | null;
    status: CardioReport['decision']['status'];
    decisionType: CardioReport['decision']['decision_type'];
    rationale: string;
    preliminaryRoute: string | null;
  };
  safetyStatus: {
    overrideTriggered: boolean;
    action: CardioReport['safety']['action'];
    redFlagsDetected: string[];
    overrideReason: string | null;
    flags: string[];
  };
  operationalNextSteps: {
    recommendedActions: string[];
    missingCriticalInfo: string[];
    conflictsDetected: string[];
  };
  technicalTrace: {
    activatedRules: string[];
    triggeredPolicies: string[];
    rulesTriggered: string[];
    preliminaryRoute: string | null;
    finalRoute: string | null;
    overrideReason: string | null;
    timestamp: string;
    rawPayload: CardioPayload;
    evaluationDurationMs: number;
  };
};

function toUiUrgency(level: CardioReport['decision']['urgency_level']): UiUrgency {
  if (level === 'EMERGENCY') return 'critical';
  if (level === 'URGENT') return 'high';
  if (level === 'ROUTINE') return 'low';
  if (level === 'UNKNOWN') return 'pending';
  return 'moderate';
}

function normalizeRoute(route: string | null): string {
  return route ?? 'NOT_AVAILABLE';
}

export function mapReportToEngineViewModel(
  report: CardioReport,
  payload: CardioPayload,
  evaluatedAt: string,
  evaluationDurationMs: number
): EngineViewModel {
  return {
    caseSummary: report.decision.clinical_summary,
    decisionSummary: {
      title: report.decision.decision_type.replace(/_/g, ' '),
      urgency: toUiUrgency(report.decision.urgency_level),
      finalRoute: normalizeRoute(report.trace.final_route ?? report.decision.recommended_route),
      recommendedRoute: report.decision.recommended_route,
      status: report.decision.status,
      decisionType: report.decision.decision_type,
      rationale: report.decision.clinical_summary,
      preliminaryRoute: report.trace.preliminary_route,
    },
    safetyStatus: {
      overrideTriggered: report.safety.override_applied,
      action: report.safety.action,
      redFlagsDetected: report.safety.triggers,
      overrideReason: report.trace.override_reason,
      flags: report.safety.flags,
    },
    operationalNextSteps: {
      recommendedActions: report.decision.required_actions,
      missingCriticalInfo: report.decision.missing_fields,
      conflictsDetected: report.trace.conflicts_detected,
    },
    technicalTrace: {
      activatedRules: report.trace.activated_rules,
      triggeredPolicies: report.trace.policy_trace.triggered,
      rulesTriggered: report.trace.rules_triggered,
      preliminaryRoute: report.trace.preliminary_route,
      finalRoute: report.trace.final_route,
      overrideReason: report.trace.override_reason,
      timestamp: evaluatedAt,
      rawPayload: payload,
      evaluationDurationMs,
    },
  };
}

export const VERSION_METADATA = {
  engineVersion: 'cardio bridge',
  rulesetVersion: 'cardio v1',
  safetyPolicyVersion: 'cardio v1',
  contractVersion: 'cardio report v1',
};

export function getDefaultScenario(scenarios: CardioScenario[]): CardioScenario {
  return scenarios.find((s) => s.id === 'EMERGENCY_ROUTE') ?? scenarios[0];
}
