---
type: feat
scope: ci
---
- **FR-1104 Retire `core-test`, Python 3.14 ceiling**: every code PR now runs `tests/unit/` twice instead of three times. The separate `core-test` job (a `-m "not process"` rerun on 3.13, ~70% overlap with `test (3.13)`) is deleted. The `test` matrix is `3.11` + `3.14` with a per-leg `extras` key: 3.11 installs every extra; 3.14 omits `otel` and `vision` and carries FR-759's missing-extra proof. `requires-python` widens to `>=3.11,<3.15` with a 3.14 classifier. Required status checks become `commitlint`, `test (3.11)`, `test (3.14)`.
