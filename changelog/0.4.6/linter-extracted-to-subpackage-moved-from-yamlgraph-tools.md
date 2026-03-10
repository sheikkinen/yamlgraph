---
type: feat
scope: linter
---
- **Linter extracted to subpackage** - Moved from `yamlgraph/tools/` to `yamlgraph/linter/`
  - Public API: `from yamlgraph.linter import lint_graph, LintIssue`
  - Internal structure: `linter/checks.py`, `linter/patterns/*.py`
  - CLI `yamlgraph graph lint` unchanged
  - 1,232 LOC now isolated in dedicated subpackage
