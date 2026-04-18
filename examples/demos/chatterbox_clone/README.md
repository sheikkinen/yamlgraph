# Chatterbox Voice Cloning Demo

Voice cloning demo using `ChatterboxTTS` with a reference audio clip (FR-236).

Strictly separate from the multilingual TTS demo in `examples/demos/chatterbox/` (FR-233).

## What It Does

1. **Synthesize** — generates speech from `text` conditioned on a `voice_prompt_path` reference clip
2. **Output** — saves the result to `outputs/chatterbox-clone/output.wav`

The synthesised voice will **inherit characteristics from the reference clip** — timbre,
accent, and speaking style. Provide a clean, quiet recording for best results.

## Class Used

`ChatterboxTTS` from `chatterbox.tts` — **not** `ChatterboxMultilingualTTS`.
The standard model supports the `audio_prompt_path` parameter for voice cloning.
See the upstream README for details: <https://github.com/resemble-ai/chatterbox>

## Reference Clip Requirements

- Format: WAV (16-bit PCM recommended)
- Duration: **5–10 seconds** of clean speech
- Content: Single speaker, minimal background noise
- Language: English (the standard `ChatterboxTTS` model is English-focused)

## Requirements

- **Chatterbox TTS**: `pip install chatterbox-tts`
- **PyTorch**: Required by Chatterbox (CPU, CUDA, or MPS)
- **~2 GB disk**: Model downloaded on first run
- **GPU recommended**: CPU inference is slow

Install:
```bash
pip install -e ".[chatterbox]"
```

## Usage

```bash
yamlgraph graph run examples/demos/chatterbox_clone/graph.yaml \
  --var text="Hello from YAMLGraph voice cloning" \
  --var voice_prompt_path="/absolute/path/to/reference.wav" \
  --full
```

Output saved to: `outputs/chatterbox-clone/output.wav`

## Key Concepts

- **`audio_prompt_path`** — passed to `ChatterboxTTS.generate()` to condition the voice
- **Hardware detection** — automatically selects `cuda > mps > cpu`
- **Single-path graph** — no map fan-out; one text → one audio file

## Pipeline

```
START → synthesize → END
           ↓
   outputs/chatterbox-clone/output.wav
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with single `python` node |
| `tools.py` | `synthesize_cloned_audio` using `ChatterboxTTS` |
