---
type: feat
scope: examples
req: REQ-YG-579
---
- **FR-777 Shared Shell Toolbelt Manifests**: `examples/shared/toolbelt/` now holds four shell-runtime tool manifests (`read_file`, `search`, `list_dir`, `git_log`); the planner, enforcer, and judge demos consume them by manifest reference instead of byte-duplicated inline copies, with the `search` glob-example description unified as the canonical union. (REQ-YG-579)
