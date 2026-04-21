---
type: fix
scope: chatterbox
---
- **fix(chatterbox): enable multilingual voice cloning via --ref**: `speak.py` CLI now accepts `--ref` for non-English languages, passing `audio_prompt_path` to `ChatterboxMultilingualTTS.generate()` for zero-shot voice cloning in all 23 supported languages.
