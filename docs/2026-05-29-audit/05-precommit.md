# Audit Report — Pre-commit Hook Compliance

**Date**: 2026-05-29 | **Version**: 0.5.4

## Full Hook Run Results

```
Command: pre-commit run --all-files
Result:  34/34 PASSED (after auto-fix)
```

### Initial Run Findings

One hook auto-fixed trailing whitespace in 5 diary files:
- `docs/diary/2026-05-26-world-digest.md`
- `docs/diary/2026-05-22-git-report.md`
- `docs/diary/2026-05-23-git-report.md`
- `docs/diary/2026-05-24-git-report.md`
- `docs/diary/2026-05-22-credit-attribution-forensics.md`

These were auto-generated files that had trailing whitespace. The hook auto-corrected them. This is normal operation — the hook is working as designed.

## Hook-by-Hook Results (Second Run — Clean)

| Hook | Result | Duration |
|------|--------|----------|
| ruff | Passed | — |
| ruff-format | Passed | — |
| trim trailing whitespace | Passed | — |
| fix end of files | Passed | — |
| check yaml | Passed | — |
| check for added large files | Passed | — |
| check for merge conflicts | Passed | — |
| check python ast | Passed | — |
| check toml | Passed | — |
| debug statements (python) | Passed | — |
| detect private key | Passed | — |
| diary import (scheduled entries) | Passed | — |
| diary-reflection-check | Passed | — |
| req_coverage --strict | Passed | — |
| Capability registry schema validation | Passed | — |
| ID registry validation | Passed | — |
| capability architecture sync | Passed | — |
| noqa_coverage --strict | Passed | — |
| dependency-rationale --strict | Passed | — |
| inline LLM orchestration check | Passed | — |
| radon CC gate (block grade D) | Passed | — |
| file size gate (>450 error, >400 warn) | Passed | — |
| forbid TODOs and compatibility drift | Passed | — |
| jscpd duplicate check (local) | Passed | — |
| import-linter architectural boundaries | Passed | — |
| vulture (dead code) | Passed | — |
| hedging check (silent fallbacks) | Passed | — |
| gitignore-boundary-guard | Passed | — |
| demo-proof-check | Passed | — |
| changelog req cross-check | Passed | — |
| changelog release sync | Passed | — |
| diary filename pattern validation | Passed | — |
| pytest (unit only, ~20s) | Passed | — |
| Final summary | Passed | — |

## Verdict

**PASS** — All 34 pre-commit hooks pass. The only auto-fix was trailing whitespace in auto-generated diary files.
