---
type: feat
scope: examples
req: REQ-YG-593
---
- **FR-789 API Discovery Browser-Sniff Step**: single-agent graph under `examples/api-discovery/steps/browser-sniff/` loads a SPA URL in headless Chromium via the FR-784 `network_sniff` manifest, retains only data-classified XHR/fetch requests as `CapturedRequest` entries, excludes telemetry noise, and maps auth/CAPTCHA evidence to a typed `needs_manual` verdict (`verdict_hint`/`manual_reason`) instead of an error. Deterministic fixture smokes proved retained `/api/*` data, excluded `/analytics/collect`, and the CAPTCHA `needs_manual` path. Exposed to the orchestrator as `browser_sniff.tool.yaml`. (REQ-YG-593)
