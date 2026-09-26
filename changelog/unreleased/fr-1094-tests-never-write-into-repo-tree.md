---
type: fix
scope: tests
req: REQ-YG-631
---
- **FR-1094 Tests never write into FR-889 governed roots**: the untracked-file witness in `test_fr_numbering.py` now builds a temporary git repo instead of writing a probe into the real `feature-requests/`, so the unit suite passes on a locked main checkout. The CI test job runs `scripts/worktree.sh lock-main` before pytest, so any test that writes into a governed root fails in CI. (REQ-YG-631)
