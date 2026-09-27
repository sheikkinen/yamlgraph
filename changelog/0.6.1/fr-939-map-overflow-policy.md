---
type: feat
scope: map
req: REQ-YG-699
---
- **FR-939 Map overflow policy**: map nodes whose `over` list exceeds the cap now raise `ValueError` (node, count, cap) before any `Send` unless `on_overflow: truncate` is declared on the node or in `defaults`; truncation keeps the exact prefix and warns once. `config.max_map_items` now actually reaches map fan-out (it was parsed and dropped), and the undocumented `defaults.max_map_items` seam is gone. (REQ-YG-699)
