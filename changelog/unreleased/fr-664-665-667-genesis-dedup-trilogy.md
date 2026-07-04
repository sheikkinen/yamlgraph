---
type: feat
scope: novel_fandom
req: REQ-YG-512
---
- **FR-664 FR-665 FR-667 Genesis Stub Pipeline and Worldgen Dedup**: Streamlined genesis from 8-9 LLM calls to 2 (synopsis + stubs). Added referential integrity validation gate to persist_genesis (warn-only). Added semantic entity deduplication node to worldgen between collect and create_skeletons. Deleted genesis_roster, genesis_character, structure_world prompts and parse_roster function. (REQ-YG-512, REQ-YG-513, REQ-YG-514)
