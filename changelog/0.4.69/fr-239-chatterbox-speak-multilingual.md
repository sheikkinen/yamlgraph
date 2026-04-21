---
type: feat
scope: chatterbox
req: REQ-YG-242
---
- **FR-239 Chatterbox Multilingual CLI**: `speak.py` gains `--lang` flag routing to `ChatterboxMultilingualTTS` for non-English codes (`fi`, `sv`, `de`, `es`, …); `--ref` is incompatible with non-English lang (raises clear error); `--lang en` (default) preserves existing voice-cloning path. (REQ-YG-239)
