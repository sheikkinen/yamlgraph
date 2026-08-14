---
type: fix
scope: hooks
---
- **FR-793 Hook ruff venv fallback + error surfacing**: `post-edit-python-checks` now resolves ruff via `HOOK_RUFF_BIN` → PATH → hook-repo `.venv/bin/ruff`, ending 3 months of silently skipped edit-time lint feedback (1,818 `ruff-missing` errors); `.github/hooks/cmd status` now reports last-7-days hook error counts grouped by hook/reason with an explicit `none` line, so a silently failing hook can no longer accrue errors invisibly.
