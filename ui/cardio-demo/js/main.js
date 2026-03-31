import { fetchManualRequests, postCardioReport } from './api.js';
import { setLoadingState, setStatus, ui } from './dom.js';
import { renderReport, resetReportView } from './render.js';
import { getScenarios, renderScenarioControls, selectScenario, setScenarios } from './scenarios.js';

async function loadScenarios() {
  setStatus('Loading scenarios from /v1/cardio/manual-requests ...');
  try {
    const payload = await fetchManualRequests();
    const manualRequests = payload.manual_requests || [];
    if (!Array.isArray(manualRequests) || !manualRequests.length) {
      throw new Error('manual_requests missing or empty.');
    }

    setScenarios(manualRequests);
    renderScenarioControls();
    selectScenario(manualRequests[0].id);
    setStatus(`Loaded ${manualRequests.length} manual scenarios.`);
  } catch (err) {
    setStatus(`Failed to load scenarios: ${err.message}`, true);
  }
}

async function runEvaluation() {
  let requestPayload;
  try {
    requestPayload = JSON.parse(ui.requestJson.value);
  } catch (err) {
    setStatus(`Invalid JSON payload: ${err.message}`, true);
    return;
  }

  setLoadingState(true);
  setStatus('Submitting request to /v1/cardio/report ...');
  try {
    const report = await postCardioReport(requestPayload);
    renderReport(report);
    setStatus(`Completed · ok=${String(report.ok)}`);
  } catch (err) {
    setStatus(`Request failed: ${err.message}`, true);
  } finally {
    setLoadingState(false);
  }
}

ui.scenarioSelect.addEventListener('change', () => {
  selectScenario(ui.scenarioSelect.value);
});

ui.runBtn.addEventListener('click', runEvaluation);

ui.resetBtn.addEventListener('click', () => {
  const first = getScenarios()[0];
  if (first) {
    selectScenario(first.id);
  } else {
    ui.requestJson.value = '{}';
  }
  resetReportView();
});

loadScenarios();
