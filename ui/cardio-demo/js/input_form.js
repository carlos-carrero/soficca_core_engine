import { ui } from './dom.js';

const NUMBER_FIELDS = new Set(['age', 'pain_duration_minutes', 'systolic_bp', 'heart_rate', 'cv_risk_factors_count']);
const BOOLEAN_FIELDS = new Set([
  'chest_pain_present',
  'dyspnea',
  'syncope',
  'known_cad',
  'current_meds_none',
  'exertional_chest_pain',
  'diaphoresis',
]);

function parseBoolean(value) {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return undefined;
}

function normalizeStateValue(field, raw) {
  if (raw === '' || raw === null || raw === undefined) {
    return undefined;
  }
  if (NUMBER_FIELDS.has(field)) {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  if (BOOLEAN_FIELDS.has(field)) {
    return parseBoolean(raw);
  }
  return String(raw);
}

function normalizeFormValue(field, value) {
  if (value === null || value === undefined) {
    return '';
  }
  if (BOOLEAN_FIELDS.has(field)) {
    if (typeof value === 'boolean') {
      return String(value);
    }
    if (typeof value === 'string') {
      const parsed = parseBoolean(value.toLowerCase());
      return parsed === undefined ? '' : String(parsed);
    }
    if (typeof value === 'number') {
      if (value === 1) return 'true';
      if (value === 0) return 'false';
      return '';
    }
    return '';
  }
  return String(value);
}

export function buildPayloadFromForm() {
  const state = {};
  Object.entries(ui.form).forEach(([field, element]) => {
    if (field === 'context_source') {
      return;
    }
    const normalized = normalizeStateValue(field, element.value);
    if (normalized !== undefined) {
      state[field] = normalized;
    }
  });

  const contextSource = (ui.form.context_source.value || '').trim() || 'USER';
  return {
    state,
    context: {
      source: contextSource,
    },
  };
}

export function writePayloadPreviewFromForm() {
  ui.requestJson.value = JSON.stringify(buildPayloadFromForm(), null, 2);
}

export function applyPayloadToForm(payload) {
  const state = (payload && payload.state) || {};
  Object.entries(ui.form).forEach(([field, element]) => {
    if (field === 'context_source') {
      return;
    }
    element.value = normalizeFormValue(field, state[field]);
  });

  const source = (payload && payload.context && payload.context.source) || 'USER';
  ui.form.context_source.value = source;
}

export function bindFormSync() {
  Object.values(ui.form).forEach((element) => {
    element.addEventListener('input', writePayloadPreviewFromForm);
    element.addEventListener('change', writePayloadPreviewFromForm);
  });
}

export function tryApplyPreviewJsonToForm() {
  const raw = ui.requestJson.value;
  const payload = JSON.parse(raw);
  if (!payload || typeof payload !== 'object' || typeof payload.state !== 'object') {
    throw new Error('Payload must include an object "state".');
  }
  applyPayloadToForm(payload);
  writePayloadPreviewFromForm();
}
