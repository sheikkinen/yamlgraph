---
type: feat
scope: routing
req: REQ-YG-552
---
- **FR-723 Execution Path Visualization**: opt-in route decision hook emitting one JSON line per routing decision (simple router, expression match, loop-limit exit, map fan-out with name+count, no state content) on the public `yamlgraph.route` logger, with thread_id carried by contextvar from run entrypoints; `yamlgraph graph export --mermaid` renders the authored graph including explicit loop-exit edges; `--overlay route.jsonl` highlights taken edges with decision ordinals so the ordered route is reconstructible from the render; `--diff` compares two routes occurrence-aligned per (node, Nth firing). (REQ-YG-552, REQ-YG-553)
