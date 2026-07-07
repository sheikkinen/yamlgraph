---
type: feat
scope: novel-fandom
req: REQ-YG-523
---
- **FR-690 Event Sequence Field**: `Event` schema gains an optional integer `sequence` giving a global total order across all events. Optional at the Pydantic layer so genesis/create_event keep validating; mandatory for the Floodmark canon via `check_event_sequence`, which enforces completeness, uniqueness, and year/sequence consistency (arithmetic, not an LLM task). All 22 Floodmark events backfilled with gapped values (10, 20, 30 …). (REQ-YG-523)
