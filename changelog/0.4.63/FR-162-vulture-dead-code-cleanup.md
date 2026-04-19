---
type: removal
scope: vulture
---
- **FR-162 Vulture Dead Code Cleanup**: Delete dead `yamlgraph/utils/sanitize.py` module and orphaned `tests/unit/test_sanitize.py` (zero production callers). Add `vulture_whitelist.py` for `worktree_helpers` false positives (shell-invoked via `python3 -c`). Lower Vulture confidence threshold from 80→60. (REQ-YG-046)
