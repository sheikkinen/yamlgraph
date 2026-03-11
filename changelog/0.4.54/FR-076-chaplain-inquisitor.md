---
type: feat
scope: chaplain
---
- **FR-076 Chaplain Inquisitor**: `.chaplain/inquisitor.sh` — one-shot audit script that checks recent commits against the Scripture (CLAUDE.md doctrine), classifies findings as ✓ COMPLIANT / ⚠ DRIFT / ✗ VIOLATION, and appends results to `docs/diary.md`
  - Post-commit hook: `inquisitor-background` spawns audit asynchronously after each commit
  - Output logged to `.chaplain/inquisitor.log` (gitignored)
