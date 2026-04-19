---
type: feat
scope: a2a
req: REQ-YG-245
---
- **FR-244 A2A SDK v1.0 Compatibility**: Upgraded `a2a-sdk` from v0.3 to v1.0 (protobuf-based). Removed `kind` discriminator from Part construction/extraction, updated all enum values to `TASK_STATE_*`/`ROLE_*` format, replaced `A2AStarletteApplication` with route factories, adapted to protobuf `MessageToDict` serialization. All 96 A2A tests updated and passing. (REQ-YG-245)
