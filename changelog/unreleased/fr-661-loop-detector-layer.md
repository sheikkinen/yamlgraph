---
type: feat
scope: import
req: REQ-YG-218
---
- **FR-661 Register loop_detector in import-linter Layer 3**: `loop_detector.py` (extracted in FR-658) was not listed in any `.importlinter` layer — violations would be silently ignored. Now explicitly registered in Layer 3. (REQ-YG-218)
