export const ui = {
  scenarioSelect: document.getElementById('scenario'),
  scenarioCards: document.getElementById('scenario-cards'),
  requestJson: document.getElementById('request-json'),
  applyJsonBtn: document.getElementById('apply-json-btn'),
  runBtn: document.getElementById('run-btn'),
  resetBtn: document.getElementById('reset-btn'),
  statusNote: document.getElementById('status-note'),
  metaEngine: document.getElementById('meta-engine'),
  metaRuleset: document.getElementById('meta-ruleset'),
  metaSafetyPolicy: document.getElementById('meta-safety-policy'),
  metaContract: document.getElementById('meta-contract'),
  decisionHeadline: document.getElementById('decision-headline'),
  decisionSupporting: document.getElementById('decision-supporting'),
  decisionTech: document.getElementById('decision-tech'),
  preliminaryRoute: document.getElementById('preliminary-route'),
  recommendedRoute: document.getElementById('recommended-route'),
  urgencyLevel: document.getElementById('urgency-level'),
  safetyMessage: document.getElementById('safety-message'),
  safetyTech: document.getElementById('safety-tech'),
  safetyTriggers: document.getElementById('safety-triggers'),
  safetyBanner: document.getElementById('safety-banner'),
  requiredFields: document.getElementById('required-fields'),
  requiredActions: document.getElementById('required-actions'),
  trace: document.getElementById('trace'),
  traceActivatedRules: document.getElementById('trace-activated-rules'),
  tracePreliminaryRoute: document.getElementById('trace-preliminary-route'),
  traceFinalRoute: document.getElementById('trace-final-route'),
  traceOverrideReason: document.getElementById('trace-override-reason'),
  traceConflicts: document.getElementById('trace-conflicts'),
  copyTraceBtn: document.getElementById('copy-trace-btn'),
  form: {
    age: document.getElementById('f-age'),
    chest_pain_present: document.getElementById('f-chest-pain-present'),
    pain_duration_minutes: document.getElementById('f-pain-duration-minutes'),
    pain_character: document.getElementById('f-pain-character'),
    pain_severity: document.getElementById('f-pain-severity'),
    pain_radiation: document.getElementById('f-pain-radiation'),
    dyspnea: document.getElementById('f-dyspnea'),
    syncope: document.getElementById('f-syncope'),
    systolic_bp: document.getElementById('f-systolic-bp'),
    heart_rate: document.getElementById('f-heart-rate'),
    prior_mi: document.getElementById('f-prior-mi'),
    known_cad: document.getElementById('f-known-cad'),
    current_meds_none: document.getElementById('f-current-meds-none'),
    exertional_chest_pain: document.getElementById('f-exertional-chest-pain'),
    diaphoresis: document.getElementById('f-diaphoresis'),
    cv_risk_factors_count: document.getElementById('f-cv-risk-factors-count'),
    context_source: document.getElementById('f-context-source'),
  },
};

export function renderList(element, values, emptyValue = 'None') {
  element.innerHTML = '';
  const normalized = Array.isArray(values) ? values : [];
  if (!normalized.length) {
    const li = document.createElement('li');
    li.textContent = emptyValue;
    element.appendChild(li);
    return;
  }

  normalized.forEach((value) => {
    const li = document.createElement('li');
    li.textContent = String(value);
    element.appendChild(li);
  });
}

export function setStatus(message, isError = false) {
  ui.statusNote.textContent = message;
  ui.statusNote.style.color = isError ? '#a22a2a' : '';
}

export function setLoadingState(isLoading) {
  ui.runBtn.disabled = isLoading;
  ui.resetBtn.disabled = isLoading;
  ui.scenarioSelect.disabled = isLoading;
  ui.scenarioCards.querySelectorAll('.scenario-card').forEach((card) => {
    card.disabled = isLoading;
  });
  ui.runBtn.textContent = isLoading ? 'Running...' : 'Run Engine Evaluation';
}
