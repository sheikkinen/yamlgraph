---
type: fix
scope: linter
req: REQ-YG-069
---
- **FR-1119 Lint knows map-owned state fields**: E007 no longer flags reads of the fields a map node creates — its failures key (`failures:` or `<collect>_failures`), `_map_accounting`, `_map_open` and `_map_verdict`. The three shared channels stay unknown in graphs without a map node. A parity test pins the linter's list to `extract_node_fields`. (REQ-YG-069)
