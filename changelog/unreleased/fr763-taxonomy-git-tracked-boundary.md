---
type: fix
scope: governance
req: REQ-YG-571
---
- **FR-763 Taxonomy Git-Tracked Boundary**: `scripts/example_taxonomy_scan.py`
  now scopes example-root discovery and marker evaluation to the git-tracked
  tree. Gitignored generator outputs (e.g. `examples/yamlgraph_gen/outputs/*`)
  and untracked half-added examples no longer become phantom taxonomy rows, so
  `--check` stops failing falsely on developer machines with local artifacts.
  Git is the sole source of truth for tracked paths (no `.gitignore`
  reimplementation); outside a git work tree the scanner warns and falls back
  to the raw filesystem walk. Local-module directory names are likewise
  derived only from directories with a tracked descendant, so an untracked
  directory named like a third-party package cannot change a root's
  classification. (REQ-YG-571)
