---
type: feat
scope: demos
req: REQ-YG-235
---
- **FR-237 Chatterbox Consolidation**: Merged `chatterbox_clone/` into `chatterbox/`. `tools.py` now contains both `synthesize_audio` (multilingual) and `synthesize_cloned_audio` (voice cloning). Added `clone.yaml` graph and `speak.py` standalone CLI (`--ref <wav> <text>` → `outputs/chatterbox/speak.wav`). Removed `chatterbox_clone/` demo folder. (REQ-YG-235, REQ-YG-238)
