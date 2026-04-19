---
type: fix
scope: worktree
req: REQ-YG-156
---
- **FR-236 Worktree Teardown Editable Install Guard**: `clean_stale_pth_entries()` now also removes stale `direct_url.json` inside `*.dist-info/` directories that reference a deleted worktree, preventing pip from reporting phantom editable installs. (REQ-YG-156)
