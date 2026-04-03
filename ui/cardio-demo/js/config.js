export const DEMO_CONFIG = {
  apiBaseUrl: (window.__SOFICCA_DEMO_CONFIG__ && window.__SOFICCA_DEMO_CONFIG__.apiBaseUrl) || '',
};

export function buildApiUrl(path) {
  const base = DEMO_CONFIG.apiBaseUrl || '';
  if (!base) {
    return path;
  }
  return `${base.replace(/\/$/, '')}${path}`;
}
