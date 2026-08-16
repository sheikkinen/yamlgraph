---
type: feat
scope: examples
req: REQ-YG-590
---
- **FR-784 Playwright Network Sniff Utility**: `network-sniff.js` loads a URL in headless Chromium, captures XHR/fetch traffic, classifies data vs telemetry, flags auth/CAPTCHA walls, redacts token material, and emits one stable JSON object; exposed as FR-768 shell manifest `network_sniff.tool.yaml` with a pinned Playwright package boundary under `examples/api-discovery/tools/`. (REQ-YG-590)
