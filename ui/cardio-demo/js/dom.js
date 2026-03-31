export const ui = {
  scenarioSelect: document.getElementById('scenario'),
  scenarioCards: document.getElementById('scenario-cards'),
  requestJson: document.getElementById('request-json'),
  runBtn: document.getElementById('run-btn'),
  resetBtn: document.getElementById('reset-btn'),
  statusNote: document.getElementById('status-note'),
  decisionSummary: document.getElementById('decision-summary'),
  preliminaryRoute: document.getElementById('preliminary-route'),
  recommendedRoute: document.getElementById('recommended-route'),
  urgencyLevel: document.getElementById('urgency-level'),
  safety: document.getElementById('safety'),
  safetyTriggers: document.getElementById('safety-triggers'),
  safetyBanner: document.getElementById('safety-banner'),
  clinicalSummary: document.getElementById('clinical-summary'),
  requiredFields: document.getElementById('required-fields'),
  requiredActions: document.getElementById('required-actions'),
  trace: document.getElementById('trace'),
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
