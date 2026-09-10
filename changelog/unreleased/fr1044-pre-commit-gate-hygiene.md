---
type: fix
scope: hooks
req: REQ-YG-676
---
- **FR-1044 Pre-commit gate hygiene**: The `ruff-pre-commit` rev is pinned to `v0.16.0`, matching the `ruff==0.16.0` pin in `constraints/dev-py312.txt`; the hook and the developer environment previously formatted at `v0.8.6` and `0.16.0` respectively, so each reverted the other's output on every commit and a test now blocks the two pins from diverging again. `scripts/noqa_coverage.py --fix` realigns the `#L<n>` references in `docs/confessions.md` when a file's suppressions map one-to-one and in order onto its ledger entries by rule code, and refuses to touch anything otherwise, leaving added or code-changed suppressions for `--strict` to report; the fix hook runs before the strict hook and stages nothing. Six stale entries (`CONF-127`..`CONF-132`) that duplicated `CONF-133`..`CONF-138` at pre-drift line numbers are removed — a duplicated series is exactly what the ledger accumulates when re-confessing is easier than realigning, and it also defeats the one-to-one match `--fix` requires. The FR-460 unit test no longer rewrites `ARCHITECTURE.md` as a side effect of asserting the generator's exit code. (REQ-YG-676, REQ-YG-677, REQ-YG-425)
