---
type: feat
scope: observability
---
- **FR-752/FR-753 Route Overlay Workflow**: extended `YAMLGRAPH_ROUTE_LOG` path handling (directory targets, trailing-separator intent, parent auto-create, CWD-relative resolution, warn-once invalid target fallback) and added a standalone `examples/route_overlay_cli/` app that validates route input, renders authored+overlay Mermaid files, and invokes `mmdc` to produce image artifacts with deterministic names. (REQ-YG-552)
