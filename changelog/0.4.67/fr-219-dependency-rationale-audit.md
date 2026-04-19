---
type: feat
scope: audit
req: REQ-YG-219
---
- **FR-219 Dependency Rationale Audit**: Pre-commit hook that enforces every PyPI dependency has a documented rationale in `docs/dependency-rationale.yaml`. Strict mode blocks commits with undocumented packages. (REQ-YG-180, REQ-YG-181)
