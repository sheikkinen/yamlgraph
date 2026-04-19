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

Standalone synthesis CLI supporting both voice cloning and multilingual TTS:

```bash
# English voice cloning (requires --ref)
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav "Hello from YAMLGraph"

# Finnish via multilingual model (no --ref)
python examples/demos/chatterbox/speak.py \
    --lang fi "Hei maailmasta YAMLGraphista"
```

Output saved to: `outputs/chatterbox/speak.wav`

Two synthesis paths:

| Path | Flag | Model | `--ref` |
|------|------|-------|---------|
| English / Voice Cloning | `--lang en` (default) | `ChatterboxTTS` | **Required** |
| Multilingual | `--lang fi/sv/de/es/…` | `ChatterboxMultilingualTTS` | **Incompatible** |

> **Voice cloning is English-only.** `--ref` is incompatible with `--lang <non-en>` and
> raises a clear error. For multilingual synthesis, omit `--ref` and supply a language code.

## Platform Requirements

> ⚠️ **Apple Silicon (arm64) or Linux/Windows only.**
>
> `chatterbox-tts` requires `torch==2.6.0`, which has **no macOS Intel (x86_64) wheel**.
> PyTorch dropped Intel Mac support after 2.2.x. Running on an Intel Mac will fail at install time.

| Platform | Status |
|----------|--------|
| Apple Silicon Mac (M1/M2/M3/M4) | ✅ Supported |
| Linux x86_64 / aarch64 | ✅ Supported |
| Windows x86_64 | ✅ Supported |
| Intel Mac (x86_64) | ❌ Not supported — `torch==2.6.0` unavailable |

## Requirements

- **Chatterbox TTS**: `pip install chatterbox-tts`
- **PyTorch 2.6.0**: Required by Chatterbox (CPU or CUDA)
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

### Multilingual TTS (CLI)

```bash
python examples/demos/chatterbox/speak.py \
    --lang fi "Hei maailmasta YAMLGraphista"

# Other supported language codes: sv, de, es
python examples/demos/chatterbox/speak.py --lang sv "Hej världen"
python examples/demos/chatterbox/speak.py --lang de "Hallo Welt"
python examples/demos/chatterbox/speak.py --lang es "Hola mundo"
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
