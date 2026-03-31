# Cardio Demo UI (Integration-Ready Notes)

This folder contains a modular browser demo for the cardio endpoint.

## Component / file structure

- `index.html`
  - Static shell and layout containers.
  - Loads `js/main.js` as an ES module.
- `styles.css`
  - Shared visual tokens and serious clinical presentation styles.
- `js/config.js`
  - API base URL configuration for local and embedded environments.
- `js/api.js`
  - HTTP client functions (`fetchManualRequests`, `postCardioReport`).
- `js/dom.js`
  - DOM references + shared UI utilities (loading/status/list rendering).
- `js/scenarios.js`
  - Scenario state and selector/card rendering.
- `js/render.js`
  - Report rendering for decision/safety/route/trace.
- `js/main.js`
  - Orchestration and event wiring.

## API base URL configuration

Default mode uses same-origin API paths (`/v1/cardio/...`).

To run this UI against another API host (future Soficca website embedding), set:

```html
<script>
  window.__SOFICCA_DEMO_CONFIG__ = {
    apiBaseUrl: "https://api.soficca.example"
  };
</script>
```

This is read in `js/config.js`.

## Embedding / production adaptation strategy

For Soficca website integration with minimal rework:

1. Keep `js/` modules and move them into the site frontend bundler unchanged.
2. Replace static `index.html` shell with a site page/component while reusing:
   - `api.js`
   - `render.js`
   - `scenarios.js`
3. Keep API environment config from `window.__SOFICCA_DEMO_CONFIG__` or map to site env vars.
4. If needed, wrap `main.js` logic in a mount function (e.g., `mountCardioDemo(rootElement, config)`).
5. Continue using endpoint contracts as-is (`POST /v1/cardio/report`, `GET /v1/cardio/manual-requests`).

No engine logic is required for frontend adaptation.
