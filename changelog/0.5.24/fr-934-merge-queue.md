---
type: feat
scope: ci
---
- **FR-934 Merge Queue on main**: Both required-context workflows (`workflow.yml`, `commitlint.yml`) now trigger on `merge_group` so queue candidates reach conclusions on `commitlint`, `test (3.11)` and `test (3.13)`. The commitlint job validates titles at PR time and reports a no-op conclusion on merge groups; merge groups run the full test matrix (R-2 option 1). Replaces the strict up-to-date rebase toll with a required merge queue (SQUASH, min 1 / max 5, 1 min wait, 30 min check timeout).
