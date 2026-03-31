import { ui } from './dom.js';

let scenarios = [];
let selectionHandler = null;

export function getScenarios() {
  return scenarios;
}

export function setScenarios(items) {
  scenarios = Array.isArray(items) ? items : [];
}

export function getScenarioById(id) {
  return scenarios.find((item) => item.id === id) || scenarios[0];
}

export function writeScenarioPayload(scenario) {
  ui.requestJson.value = JSON.stringify(scenario.request, null, 2);
}

export function highlightScenarioCard(selectedId) {
  ui.scenarioCards.querySelectorAll('.scenario-card').forEach((card) => {
    card.classList.toggle('active', card.dataset.scenarioId === selectedId);
  });
}

export function selectScenario(scenarioId) {
  const scenario = getScenarioById(scenarioId);
  if (!scenario) {
    return null;
  }
  ui.scenarioSelect.value = scenario.id;
  writeScenarioPayload(scenario);
  highlightScenarioCard(scenario.id);
  if (selectionHandler) {
    selectionHandler(scenario);
  }
  return scenario;
}

export function setScenarioSelectionHandler(handler) {
  selectionHandler = handler;
}

export function renderScenarioControls() {
  ui.scenarioSelect.innerHTML = '';
  ui.scenarioCards.innerHTML = '';

  scenarios.forEach((scenario, index) => {
    const option = document.createElement('option');
    option.value = scenario.id;
    option.textContent = `${index + 1}. ${scenario.id}`;
    ui.scenarioSelect.appendChild(option);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'scenario-card';
    button.dataset.scenarioId = scenario.id;
    button.textContent = scenario.id;
    button.addEventListener('click', () => selectScenario(scenario.id));
    ui.scenarioCards.appendChild(button);
  });
}
