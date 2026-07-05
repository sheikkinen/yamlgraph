---
type: feat
scope: novel_fandom
req: REQ-YG-515
---
- **FR-683 Ref Integrity Graph-Tool**: Extracted `validate_referential_integrity` from `persist_genesis.py` into standalone `ref_integrity.py`. Created `ref_check.yaml` graph-tool. Wired as tool for `deepen_events` agent in worldgen. Deleted `validate_genesis.py` (importlib hack). (REQ-YG-515)
