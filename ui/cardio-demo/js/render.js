import { renderList, ui } from './dom.js';

function buildDecisionHeadline(decision) {
  const type = decision.decision_type || decision.decision_id;
  switch (type) {
    case 'EMERGENCY_OVERRIDE':
      return 'Immediate emergency escalation required';
    case 'URGENT_ESCALATION':
      return 'Urgent same-day clinical escalation recommended';
    case 'ROUTINE_REVIEW':
      return 'Routine cardiology review is appropriate';
    case 'DEFERRED_PENDING_DATA':
      return 'Routing deferred pending data reconciliation';
    case 'NEEDS_MORE_INFO':
      return 'Additional clinical information is required';
    default:
      if (decision.status === 'NEEDS_MORE_INFO') return 'Additional clinical information is required';
      if (decision.status === 'CONFLICT') return 'Routing deferred pending data reconciliation';
      return 'Clinical routing decision available';
  }
}

function buildSafetyMessage(safety) {
  if (safety.status === 'TRIGGERED') {
    return 'Safety override triggered — emergency red flags detected';
  }
  return 'No active safety override';
}

export function renderReport(report) {
  const decision = report.decision || {};
  const safety = report.safety || {};
  const trace = report.trace || {};
  const versions = report.versions || {};
  const headline = buildDecisionHeadline(decision);

  ui.metaEngine.textContent = versions.engine || '—';
  ui.metaRuleset.textContent = versions.ruleset || '—';
  ui.metaSafetyPolicy.textContent = versions.safety_policy || '—';
  ui.metaContract.textContent = versions.contract || 'n/a';

  ui.decisionHeadline.textContent = headline;
  ui.decisionSupporting.textContent = decision.clinical_summary || 'No clinical summary available.';
  ui.decisionTech.textContent = [
    'Technical status:',
    decision.decision_type || decision.decision_id || 'UNKNOWN',
    decision.status || 'UNKNOWN',
    decision.case_status || 'UNKNOWN',
  ].join(' ');
  ui.preliminaryRoute.textContent = trace.preliminary_route || '—';
  ui.recommendedRoute.textContent = trace.final_route || decision.recommended_route || decision.path || '—';
  ui.urgencyLevel.textContent = decision.urgency_level || '—';
  ui.safetyMessage.textContent = buildSafetyMessage(safety);
  ui.safetyTech.textContent = [
    'Technical safety:',
    safety.status || 'UNKNOWN',
    safety.action || 'UNKNOWN_ACTION',
    safety.severity || 'UNKNOWN',
  ].join(' ');

  renderList(ui.requiredFields, decision.required_fields || decision.missing_fields || []);
  renderList(ui.requiredActions, decision.required_actions || []);
  const safetyTriggers = safety.triggers || [];
  renderList(
    ui.safetyTriggers,
    safetyTriggers.length ? safetyTriggers : ['No emergency red flags detected'],
    'No emergency red flags detected',
  );

  ui.safetyBanner.classList.remove('safety-clear', 'safety-triggered');
  ui.safetyBanner.classList.add(safety.status === 'TRIGGERED' ? 'safety-triggered' : 'safety-clear');

  const activatedRules = trace.activated_rules || trace.rules_triggered || [];
  ui.traceActivatedRules.textContent = activatedRules.length ? activatedRules.join(', ') : 'None';
  ui.tracePreliminaryRoute.textContent = trace.preliminary_route || '—';
  ui.traceFinalRoute.textContent = trace.final_route || '—';
  ui.traceOverrideReason.textContent = trace.override_reason || 'None';
  const conflicts = trace.conflicts_detected || [];
  ui.traceConflicts.textContent = conflicts.length ? conflicts.join(', ') : 'None';

  ui.trace.textContent = JSON.stringify(trace, null, 2);
}

export function resetReportView() {
  ui.metaEngine.textContent = '—';
  ui.metaRuleset.textContent = '—';
  ui.metaSafetyPolicy.textContent = '—';
  ui.metaContract.textContent = '—';

  ui.decisionHeadline.textContent = 'Awaiting evaluation';
  ui.decisionSupporting.textContent = 'Run a case to view the clinical routing recommendation.';
  ui.decisionTech.textContent = 'Technical status: —';
  ui.preliminaryRoute.textContent = '—';
  ui.recommendedRoute.textContent = '—';
  ui.urgencyLevel.textContent = '—';
  ui.safetyMessage.textContent = 'No active safety override';
  ui.safetyTech.textContent = 'Technical safety: —';

  renderList(ui.requiredFields, []);
  renderList(ui.requiredActions, []);
  renderList(ui.safetyTriggers, ['No emergency red flags detected'], 'No emergency red flags detected');

  ui.safetyBanner.classList.remove('safety-triggered');
  ui.safetyBanner.classList.add('safety-clear');
  ui.traceActivatedRules.textContent = '—';
  ui.tracePreliminaryRoute.textContent = '—';
  ui.traceFinalRoute.textContent = '—';
  ui.traceOverrideReason.textContent = '—';
  ui.traceConflicts.textContent = 'None';
  ui.trace.textContent = '{}';
}
