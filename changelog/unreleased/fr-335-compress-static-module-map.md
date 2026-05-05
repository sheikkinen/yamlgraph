---
type: feat
scope: module-map
---
- **FR-335 Compress Module Map**: Compress static module-map output by keeping only internal `yamlgraph.*` dependencies, collapsing trivial `__init__.py` modules, and rendering compact one-line module metadata. Brings `reference/module-map.md` from 1511 lines to <=250 lines.
