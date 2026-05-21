---
type: refactor
scope: hooks
---
- **FR-439 Tone down enforcement terminology**: Renamed three enforcement artifacts to neutral, descriptive names. `thoughtcrime-scan.sh` → `reasoning-pattern-check.sh`; `thoughtcrimes.json` → `reasoning-patterns.json`; `scripts/absolution.py` → `scripts/final_summary.py`. Sentinel filename `.thoughtcrime-<sid>` → `.reasoning-flag-<sid>`. Audit log `reason` values `thoughtcrime` → `reasoning-pattern` and `order66-*` → `lockdown-*`. Deny messages no longer reference *1984*, the Thought Police, or Order 66. Pre-commit hook id `absolution` → `final-summary` — existing checkouts must run `pre-commit clean && pre-commit install` after pulling. No behavioural change.
