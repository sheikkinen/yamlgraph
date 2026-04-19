# Chatterbox TTS Demo

Unified Chatterbox demo: multilingual TTS and voice cloning (FR-233, FR-236, consolidated FR-237).

## What It Does

### Multilingual TTS (`graph.yaml`)

1. **Generate** — fans out over 5 languages (en, es, fi, sv, de) via `type: map`
2. **Synthesize** — converts each translation to speech using Chatterbox Multilingual TTS
3. **Output** — saves `.wav` files to `outputs/chatterbox/`

### Voice Cloning (`clone.yaml`)

1. **Synthesize** — converts text to speech using `ChatterboxTTS` with a reference voice clip
2. **Output** — saves `outputs/chatterbox/output.wav`

### CLI Tool (`speak.py`)

Standalone one-command voice cloning without the graph runner:

```bash
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav "Hello from YAMLGraph"
```

Output saved to: `outputs/chatterbox/speak.wav`

> **Language note:** `speak.py` uses `ChatterboxTTS` which is English-focused. Voice timbre
> transfers from the reference clip but pronunciation quality for non-English text may vary.
> `--lang` is intentionally absent — an argument that only changes the filename without
> influencing synthesis would mislead users. For true multilingual synthesis use `graph.yaml`
> with `ChatterboxMultilingualTTS`.

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

### Multilingual TTS

```bash
yamlgraph graph run examples/demos/chatterbox/graph.yaml \
  --var topic="the beauty of nature" --full
```

Output saved to: `outputs/chatterbox/{en,es,fi,sv,de}.wav`

### Voice Cloning (graph)

```bash
yamlgraph graph run examples/demos/chatterbox/clone.yaml \
  --var text="Hello from YAMLGraph" \
  --var voice_prompt_path="examples/demos/chatterbox/source.wav"
```

Output saved to: `outputs/chatterbox/output.wav`

### Voice Cloning (CLI)

```bash
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav "Hello"
```

Output saved to: `outputs/chatterbox/speak.wav`

## Key Concepts

- **Structured `over:` list** — map node iterates over dicts with `lang` and `lang_name`
- **`collect:`** — aggregates parallel LLM results into `state.translations`
- **Python tool for TTS** — `synthesize_audio` loads Chatterbox and generates WAV files
- **Hardware detection** — automatically uses CUDA > MPS > CPU

## Pipeline

### Multilingual (`graph.yaml`)

```
START → generate (map: 5 languages) → synthesize → END
              ↓                            ↓
        translations[]              outputs/chatterbox/*.wav
```

### Voice Clone (`clone.yaml` / `speak.py`)

```
START → synthesize → END
              ↓
    outputs/chatterbox/output.wav (graph)
    outputs/chatterbox/speak.wav  (CLI)
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Multilingual TTS graph (map fan-out over 5 languages) |
| `clone.yaml` | Voice cloning graph (text + reference audio → WAV) |
| `speak.py` | Standalone CLI: one command voice cloning |
| `prompts/translate.yaml` | Per-language translation prompt with schema |
| `tools.py` | `synthesize_audio` (multilingual) + `synthesize_cloned_audio` (cloning) |
