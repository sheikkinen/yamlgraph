---
type: feat
scope: diary
req: REQ-YG-122
---
- **FR-124 Diary Import CLI**: `yamlgraph diary import` CLI command imports pending scheduled diary entries and git reports into `docs/diary/` with `--dry-run` and `--source` flags. Extracted shared import logic from `scripts/diary_rotate.py` into `yamlgraph/diary/importer.py`. (REQ-YG-122)
