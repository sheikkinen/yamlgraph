---
type: feat
scope: audit
---
- **FR-245 Dependency Rationale Deep Audit**: Add orphan detection and stale module-path validation to `scripts/dependency_rationale.py`. Fixes stale `projects/outcaller/` references and tolerates symlinks (even broken) as intentional module references.
