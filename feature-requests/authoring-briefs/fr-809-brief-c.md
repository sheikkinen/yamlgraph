# Task: FR-809 resumed validation — FR-784 fixture smokes (SPA + CAPTCHA)

Validation-only continuation of the FR-809 authoring run. The v2
orchestrator is authored in the working tree; do not modify it unless a
smoke exposes a defect — repair honestly and record the repair.

The committed FR-784 SPA fixture server (an existing fixture at
tests/fixtures/fr784_spa/spa_server.py) is ALREADY RUNNING at
http://127.0.0.1:8799/ — do not start or stop it. It serves the SPA index
at `/` (client-rendered, fetches /api/data, /api/item, /api/search, and
telemetry /analytics/collect) and a CAPTCHA page at `/captcha.html`.

## Validation

```bash
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="A local test portal exposes a JSON data API used by its single-page frontend" --var purpose="capture the SPA's backing data API" --var country="FI" --var domain_hint="http://127.0.0.1:8799/" --var use_recon=false --full
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="A local test portal exposes a JSON data API behind its page" --var purpose="capture the portal's backing data API" --var country="FI" --var domain_hint="http://127.0.0.1:8799/captcha.html" --var use_recon=false --full
```

Assertions (read the raw terminal `result` for each run):

1. SPA smoke: the run routes through browser-sniff — `steps_tried`
   contains `browser-sniff`; terminal API evidence/profile carries
   `/api/data`, `/api/item`, and `/api/search` endpoints; the telemetry
   URL `/analytics/collect` is EXCLUDED from API evidence.
2. CAPTCHA smoke: `verdict == "needs_manual"` and
   `manual_reason == "captcha"`.

Record both commands, quoted raw evidence (actual endpoints and
manual_reason values from the output), outcomes, and any repairs in
tmp/draft-authoring-report.md.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
