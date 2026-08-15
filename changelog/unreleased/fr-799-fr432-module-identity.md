---
type: fix
scope: tests
req: REQ-YG-043
---
- **FR-799 fr432 Fixture Module-Identity Restore**: the fr432 autouse teardown re-imports `yamlgraph.config` after popping it, healing the orphaned package attribute that made a later `importlib.reload(config)` raise ImportError under xdist scheduling (~5%/run); permanent identity witness added. (REQ-YG-043)
