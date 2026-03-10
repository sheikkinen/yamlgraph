---
type: fix
scope: lint
---
- **Lint Test Assertions**: Fix `severity.value` → `severity` in lint assertion tests (`test_enforce_yamlgraphication.py`, `test_bugfix_pipeline.py`). `LintIssue.severity` is a string, not an enum.
