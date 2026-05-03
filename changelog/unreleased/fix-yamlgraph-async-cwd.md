---
type: fix
scope: chaplain
---
- **FR-314 yamlgraph_async cwd**: `YamlgraphAsyncAction` now sets `cwd` to the worktree directory so relative paths (e.g. `fr_path`) resolve against the feature branch, not main. Fixes judge rejecting valid FRs that only exist on the feature branch.
