---
type: feat
scope: hooks
req: REQ-YG-631
---
- **FR-889 OS-Enforced Main-Write Lock**: governed roots on the main checkout are now `chmod -R u-w` locked via `scripts/worktree.sh lock-main|unlock-main|sync`; the FR-888 shell-command grammar in Check 7 is deleted, replaced by a lintable module (`checks/main_write.py`) doing edit-tool classification and a lock-mutator fence (git never fenced, sudo passes). FR-902 cwd-proxy heuristics retired (`checks/lane_guard.py`); `now.py` board warns on unlocked main; widened file-size gate (`scripts/size_gate.py`, py+sh, shrink-only baseline); docs-only PR required-check deadlock cured with always-reporting no-op steps. (REQ-YG-631)
