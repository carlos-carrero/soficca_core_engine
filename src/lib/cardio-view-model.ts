import type { CardioReport } from '@/lib/cardio-types';

export function decisionHeadline(report: CardioReport): string {
  switch (report.decision.decision_type) {
    case 'EMERGENCY_OVERRIDE':
      return 'Immediate Emergency Escalation Required';
    case 'URGENT_ESCALATION':
      return 'Urgent Same-Day Clinical Escalation';
    case 'ROUTINE_REVIEW':
      return 'Routine Cardiology Review Recommended';
    case 'DEFERRED_PENDING_DATA':
      return 'Routing Deferred Pending Data Reconciliation';
    case 'NEEDS_MORE_INFO':
    default:
      return 'Additional Clinical Information Required';
  }
}

export function decisionTone(status: CardioReport['decision']['status']): string {
  if (status === 'ESCALATED') return 'text-danger';
  if (status === 'CONFLICT') return 'text-warning';
  if (status === 'NEEDS_MORE_INFO') return 'text-warning';
  return 'text-success';
}

export function safetyLabel(report: CardioReport): string {
  if (report.safety.status === 'TRIGGERED') {
    return 'Safety override triggered — emergency red flags detected';
  }
  return 'Safety clear — no active emergency override';
}
