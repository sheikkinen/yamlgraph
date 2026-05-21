---
type: fix
scope: hooks
---
- **FR-433 Post-edit apply_patch coverage + optional auto-ruff**: `post-edit-checks.sh` now inspects `apply_patch` payloads, aggregates per-file diagnostics across multi-file patches, and supports opt-in `POST_EDIT_AUTO_RUFF=1` to run `ruff check --fix` + `ruff format` with audit logging when edits are applied.
