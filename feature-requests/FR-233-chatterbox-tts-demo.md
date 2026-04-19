# Feature Request: Chatterbox TTS Demo

**Priority:** LOW
**Type:** Feature
**Status:** Implemented (Superseded by FR-237 — tools merged into `chatterbox/tools.py`)
**Effort:** 2 days
**Requested:** 2026-04-18

## Summary

Build a demo that generates multilingual text via an LLM graph, then synthesizes it to audio using Chatterbox TTS (resemble-ai/chatterbox). Test English, Spanish, Finnish, Swedish, and German. Store results as `.wav` files in `outputs/`.

## Value Statement

Demo authors see that YAMLGraph pipelines can produce audio artifacts — not just text — expanding the framework's showcase to multimedia outputs.

## Problem

All existing demos produce text or markdown output. There is no demonstration of generating binary artifacts (audio files) from a YAMLGraph pipeline. A TTS demo would showcase:

1. Map-node fan-out across multiple languages (like the horoscope demo fans out across zodiac signs)
2. Python tool nodes performing heavyweight side-effect work (model loading, inference, file I/O)
3. Integration with a state-of-the-art open-source TTS model

## Proposed Solution

Create `examples/demos/chatterbox/` following the established demo structure (hello, horoscope patterns).

### Pipeline

```
START → generate (map: 5 languages) → save_audio (python tool) → END
                ↓                            ↓
          translations[]              outputs/chatterbox-*.wav
```

### Graph definition

```yaml
# examples/demos/chatterbox/graph.yaml
version: "1.0"
name: chatterbox-tts
description: Multilingual TTS demo using Chatterbox

prompts_relative: true
prompts_dir: prompts

tools:
  synthesize_audio:
    type: python
    module: examples.demos.chatterbox.tools
    function: synthesize_audio

state:
  topic: str

nodes:
  generate:
    type: map
    over:
      - {lang: en, lang_name: English}
      - {lang: es, lang_name: Spanish}
      - {lang: fi, lang_name: Finnish}
      - {lang: sv, lang_name: Swedish}
      - {lang: de, lang_name: German}
    as: target
    node:
      prompt: translate
      state_key: translation
      variables:
        lang: "{state.target.lang}"
        lang_name: "{state.target.lang_name}"
        topic: "{state.topic}"
    collect: translations

  synthesize:
    type: python
    tool: synthesize_audio
    state_key: audio_paths

edges:
  - from: START
    to: generate
  - from: generate
    to: synthesize
  - from: synthesize
    to: END
```

### Python tool

```python
# examples/demos/chatterbox/tools.py
def synthesize_audio(state: dict) -> dict:
    """Synthesize translations to WAV files using Chatterbox Multilingual."""
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    import torchaudio as ta
    from pathlib import Path

    translations = state.get("translations", [])
    output_dir = Path("outputs/chatterbox")
    output_dir.mkdir(parents=True, exist_ok=True)

    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")

    audio_paths = []
    for item in translations:
        lang = item["lang"]
        text = item["translation"]
        wav = model.generate(text, language_id=lang)
        path = output_dir / f"{lang}.wav"
        ta.save(str(path), wav, model.sr)
        audio_paths.append(str(path))

    return {"audio_paths": audio_paths}
```

### Prompt

```yaml
# examples/demos/chatterbox/prompts/translate.yaml
system: |
  You are a professional translator and creative writer.

user: |
  Write a short paragraph (2-3 sentences) about "{topic}" in {lang_name}.
  The text should sound natural for a native {lang_name} speaker.
  Write ONLY the {lang_name} text, no translations or explanations.

schema:
  name: Translation
  fields:
    lang: {type: str, description: "ISO 639-1 language code"}
    translation: {type: str, description: "The text in the target language"}
```

### Demo entry

Add `demo_chatterbox` to `examples/demos/demo.sh` (not in `all` — requires GPU/large model).

## Acceptance Criteria

- [x] `examples/demos/chatterbox/graph.yaml` passes `yamlgraph graph lint`
- [x] `examples/demos/chatterbox/tools.py` contains `synthesize_audio` function
- [x] `examples/demos/chatterbox/prompts/translate.yaml` exists with schema
- [x] `examples/demos/chatterbox/README.md` documents usage and requirements
- [ ] Running the demo produces `.wav` files for all 5 languages (en, es, fi, sv, de)
- [ ] Audio files are playable and contain speech in the correct language
- [x] `demo.sh` includes `chatterbox` entry (excluded from `all` — heavy dependency)
- [ ] `demo-output.log` included proving the demo was executed (FR-206 gate)
- [x] `chatterbox-tts` added as optional dependency in `pyproject.toml`
- [x] Tests added (unit test with mocked TTS model for `tools.py`)
- [ ] Diary reflection written

## Alternatives Considered

1. **ElevenLabs API** — already used in `scripts/generate_tts_fixtures.py` for test fixtures; requires API key and is a paid service. Chatterbox is open-source and runs locally.
2. **Coqui TTS** — another open-source option but less actively maintained. Chatterbox has better multilingual support (23 languages) and higher quality.
3. **Single-language demo** — simpler but misses the opportunity to showcase map-node fan-out and the multilingual model's capabilities.

## Implementation Notes

- Chatterbox Multilingual (500M params) supports all requested languages: English (en), Spanish (es), Finnish (fi), Swedish (sv), German (de).
- The model runs on CPU (slower) or CUDA GPU (fast). The demo should detect and use available hardware.
- Model download is ~2GB on first run — document this in README.
- The demo is heavyweight (large model, GPU preferred) so it should be excluded from the default `all` target in `demo.sh`, similar to how `interview` and `codegen` are skipped.

## Related

- `examples/demos/horoscope/` — closest pattern (map fan-out + python tool save)
- `scripts/generate_tts_fixtures.py` — existing TTS usage (ElevenLabs)
- `feature-requests/FR-179-asterisk-ari-audiosocket-provider.md` — voice/audio domain
- https://github.com/resemble-ai/chatterbox — Chatterbox TTS repository
