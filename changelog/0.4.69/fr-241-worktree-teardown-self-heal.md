---
type: fix
scope: worktree
req: REQ-YG-244
---
- **FR-241 Complete Worktree Teardown Self-Heal**: Added `validate_editable_install()` to `worktree_helpers.py` for import health probing via `sys.executable`. `enforce_worktree.sh` cleanup now validates `import yamlgraph` after `.pth` cleaning and self-heals with `pip install -e`. `bugfix_worktree.sh` reaches FR-174 parity: `validate_venv_health` before symlink, `validate_venv_symlink` after symlink, `clean_stale_pth_entries` in cleanup, import validation, and `pip install -e` self-heal. (REQ-YG-242)
