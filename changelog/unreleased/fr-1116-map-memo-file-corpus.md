---
type: feat
scope: examples
req: REQ-YG-706
---
- **FR-1116 Map memo for file corpora**: `examples/shared/map_memo.py` with `map_memo_split` / `map_memo_merge` manifests. Split drops file items whose bytes and computation signature match a stored SQLite outcome; the map runs only `todo`; merge stores executed outcomes in one transaction and returns records, failures and an FR-1073 verdict over the whole current population, raising `MapCompletenessError` only after commit. `meta_map` is the first consumer. Supersedes FR-1076. (REQ-YG-706)
