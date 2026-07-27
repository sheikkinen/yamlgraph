---
type: feat
scope: governance
req: REQ-YG-569
---
- **FR-758 Sole-Route Judge/Review Traceability**: The csap-ported
  judge/review wrappers (`scripts/judge.sh`, `scripts/review.sh`) gain
  a local traceability spine: CAP-211 registry entry, REQ-YG-569, and
  18 stubbed contract tests witnessing the exit-code taxonomy
  (usage 64, missing FR 66, artifact contract 65, re-entry sentinel 70,
  lock held 73 / stale 75, executor resolution 69, success 0), lock
  cleanup, and `YAMLGRAPH_BIN` precedence. Real smoke of both wrappers
  recorded in the FR. (REQ-YG-569)
