---
type: feat
scope: novel_fandom
req: REQ-YG-505
---
- **FR-655 Genesis Pipeline**: Two-phase premise-to-canon bootstrapping graph. Phase 1 generates prose (synopsis, roster, character cards) using prompts adapted from dungeon_master. Phase 2 structures prose into typed canon YAML via single `structure_world` LLM pass. Persists via existing `persist_pages`. (REQ-YG-505, REQ-YG-506, REQ-YG-507, REQ-YG-508)
