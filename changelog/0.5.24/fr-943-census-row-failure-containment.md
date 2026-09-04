---
type: fix
scope: demos
req: REQ-YG-634
---
- **FR-943 Census Row-Level Failure Containment**: one malformed model
  output no longer forfeits a census batch. Attributable model-owned
  failures (map-error findings, error-string judgements, model-owned
  envelope validation errors) become fail-closed abstained rows with a
  bounded `row failed:` reason and full causal evidence preserved in
  `raw_judgement`; structural impossibilities remain batch-fatal
  (FR-892). Summary line gains a `row-failed` count. (REQ-YG-634)
