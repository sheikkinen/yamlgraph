---
type: fix
scope: tests
---
- **Fix module-map regeneration side effect during pytest**: Tests that validate the module-map generator now write to temp files instead of overwriting `reference/module-map.md`, eliminating the pre-commit commit loop.
