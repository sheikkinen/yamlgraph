---
type: feat
scope: hooks
---
- **FR-888 Main-Write Guard**: enforcement-class writes on the main checkout are denied with an executable worktree cure; git-plumbing worktree detection; audited `FR888_ALLOW_MAIN=1` escape; `worktree.sh` gains `.env` symlink, final `cd` line, and `rm-safe` (untracked files never auto-removed).
- Orphan-worktree flags on the `now.py` board (no open PR → age + untracked count; never auto-deleted).
- Review fixes: rm-safe merge-state check; directory-copy materialization denied; executable placeholder-free denial cure.
- Round-2 review fixes: time/nohup/nice wrappers classified; rm-safe --merged-confirmed for squash merges.
- Round-3 review fixes: guard-root scoping (foreign repos never policed), apply_patch Delete hunks denied, hooks-README runbook.
- Round-4 review fixes: apply_patch Move-to header denied; whitespace-variant inline writers classified.
- Round-4 followup: Move-to findall verified landed by probe.
- Round-5 review fixes: rm-safe .gitignore edit safety; normalized escape-audit targets.
- Round-6: diary renamed to gate pattern; quoted-redirect/mv/env-prefixed witnesses added.
- Round-7: $PWD-expanded targets denied; quoted cd cure; AC-10 live-pipeline suppression input.
