---
type: fix
scope: examples
req: REQ-YG-590
---
- **FR-784 network-sniff live-found hardening**: redact vendor-prefixed key params (segment-based name matching) and token-shaped query values under any name; classify telemetry hostname labels (e.g. `telemetry.<vendor>`) as telemetry. Found by live validation against hn.algolia.com. (REQ-YG-590)
