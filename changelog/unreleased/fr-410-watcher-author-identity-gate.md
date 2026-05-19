---
type: fix
scope: watcher
---
- **FR-410 Watcher Author Identity Gate**: Enforced runtime git author identity in watcher commits and added CI `author-identity-gate` to block placeholder commit authors (`Test <test@test.com>`) in PR commit ranges.
