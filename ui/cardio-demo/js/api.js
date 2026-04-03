import { buildApiUrl } from './config.js';

async function requestJson(path, init = {}) {
  const response = await fetch(buildApiUrl(path), init);
  const rawText = await response.text();

  let payload = {};
  if (rawText) {
    try {
      payload = JSON.parse(rawText);
    } catch (err) {
      throw new Error(`Non-JSON response from ${path} (HTTP ${response.status}).`);
    }
  }

  if (!response.ok) {
    const detail = (payload.errors && JSON.stringify(payload.errors)) || rawText || 'request failed';
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }

  return payload;
}

export async function fetchManualRequests() {
  return requestJson('/v1/cardio/manual-requests');
}

export async function postCardioReport(payload) {
  return requestJson('/v1/cardio/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
