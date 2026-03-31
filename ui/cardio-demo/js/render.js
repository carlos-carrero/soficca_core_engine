import { renderList, ui } from './dom.js';

export function renderReport(report) {
  const decision = report.decision || {};
  const safety = report.safety || {};
  const trace = report.trace || {};

  const decisionSummary = [
    decision.decision_type || decision.decision_id || 'UNSPECIFIED_DECISION',
    decision.status || null,
    decision.case_status || null,
  ]
    .filter(Boolean)
    .join(' · ');

  ui.decisionSummary.textContent = decisionSummary || '—';
  ui.preliminaryRoute.textContent = trace.preliminary_route || '—';
  ui.recommendedRoute.textContent = trace.final_route || decision.recommended_route || decision.path || '—';
  ui.urgencyLevel.textContent = decision.urgency_level || '—';
  ui.safety.textContent = [safety.status || 'UNKNOWN', safety.action || 'UNKNOWN_ACTION', safety.severity || null]
    .filter(Boolean)
    .join(' · ');
  ui.clinicalSummary.textContent = decision.clinical_summary || '—';

  renderList(ui.requiredFields, decision.required_fields || decision.missing_fields || []);
  renderList(ui.requiredActions, decision.required_actions || []);
  renderList(ui.safetyTriggers, safety.triggers || []);

  ui.safetyBanner.classList.remove('safety-clear', 'safety-triggered');
  ui.safetyBanner.classList.add(safety.status === 'TRIGGERED' ? 'safety-triggered' : 'safety-clear');

  ui.trace.textContent = JSON.stringify(trace, null, 2);
}

export function resetReportView() {
  ui.decisionSummary.textContent = 'Awaiting run…';
  ui.preliminaryRoute.textContent = '—';
  ui.recommendedRoute.textContent = '—';
  ui.urgencyLevel.textContent = '—';
  ui.safety.textContent = '—';
  ui.clinicalSummary.textContent = '—';

  renderList(ui.requiredFields, []);
  renderList(ui.requiredActions, []);
  renderList(ui.safetyTriggers, [], 'No triggers');

  ui.safetyBanner.classList.remove('safety-triggered');
  ui.safetyBanner.classList.add('safety-clear');
  ui.trace.textContent = '{}';
}
