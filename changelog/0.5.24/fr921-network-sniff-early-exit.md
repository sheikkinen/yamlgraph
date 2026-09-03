---
type: fix
scope: tools
req: REQ-YG-590
---
- **FR-921 Network-Sniff Early Exit**: `network-sniff.js` cleared the body-read race timer, so `--timeout` is a ceiling instead of a floor. An uncleared `setTimeout` kept Node's event loop alive to the full deadline, making every sniff cost the whole window regardless of when the page settled. The FR-784 test module drops from 82.2s to 13.3s and now passes under `pytest -n auto`. (REQ-YG-590)
