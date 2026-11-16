---
type: removal
scope: contrib
req: REQ-YG-727
---
- **FR-1160 Map memo contrib retired**: the unreleased `yamlgraph.contrib.map_memo` module and the `examples/demos/map_memo` demo are removed. The map memo stays in `examples/shared/map_memo.py`, loaded by the shared tool manifests through `path:` as before. (REQ-YG-727)
