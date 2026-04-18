# Chatterbox TTS Demo

Multilingual text-to-speech demo using Chatterbox (FR-233).

## What It Does

1. **Generate** — fans out over 5 languages (en, es, fi, sv, de) via `type: map`
2. **Synthesize** — converts each translation to speech using Chatterbox Multilingual TTS
3. **Output** — saves `.wav` files to `outputs/chatterbox/`

## Requirements

- **Chatterbox TTS**: `pip install chatterbox-tts`
- **PyTorch**: Required by Chatterbox (CPU or CUDA)
- **~2GB disk**: Model downloaded on first run
- **GPU recommended**: CPU inference is slow (~30s per utterance)

Install:
```bash
pip install -e ".[chatterbox]"
```

## Usage

```bash
yamlgraph graph run examples/demos/chatterbox/graph.yaml \
  --var topic="the beauty of nature" --full
```

Output saved to: `outputs/chatterbox/{en,es,fi,sv,de}.wav`

## Key Concepts

- **Structured `over:` list** — map node iterates over dicts with `lang` and `lang_name`
- **`collect:`** — aggregates parallel LLM results into `state.translations`
- **Python tool for TTS** — `synthesize_audio` loads Chatterbox and generates WAV files
- **Hardware detection** — automatically uses CUDA if available, falls back to CPU

## Pipeline

```
START → generate (map: 5 languages) → synthesize → END
              ↓                            ↓
        translations[]              outputs/chatterbox/*.wav
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with map node and TTS tool |
| `prompts/translate.yaml` | Per-language translation prompt with schema |
| `tools.py` | `synthesize_audio` function using Chatterbox Multilingual |
