---
type: feat
scope: map
req: REQ-YG-728
---
- **FR-1161 `type: cached_map` runs item 0 before the rest**: a new node type with the same keys and result contract as `type: map`. Item 0 runs alone, then items 1..N-1 fan out together, so a long shared prompt prefix is written to the Anthropic prompt cache once instead of by every concurrent call. Both waves are built from a snapshot of the items and state taken at dispatch, so item 0's writes cannot change the rest. Items 1..N-1 start whatever item 0's outcome; `min_success`, accounting, failures and the verdict follow the FR-1073 map contract. (REQ-YG-728)
