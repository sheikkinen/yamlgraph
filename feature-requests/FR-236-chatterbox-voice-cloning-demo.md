# Feature Request: Chatterbox Voice Cloning Demo

**Priority:** LOW
**Type:** Feature
**Status:** Implemented (Superseded by FR-237 — consolidated into `examples/demos/chatterbox/`)
**Effort:** 1 day
**Requested:** 2026-04-18

## Summary

Add `examples/demos/chatterbox_clone/` — a minimal single-path demo that synthesises
text to audio using `ChatterboxTTS` with a caller-supplied reference audio clip
(`audio_prompt_path`), strictly separate from the multilingual TTS demo in FR-233.

## Value Statement

Demo authors see how YAMLGraph handles reference-audio-conditioned speech synthesis —
a distinct capability from the default-voice multilingual TTS path already demonstrated
in `examples/demos/chatterbox/`.

## Problem

The existing Chatterbox demo (FR-233) proves that YAMLGraph can generate multilingual
audio artifacts through a map fan-out using `ChatterboxMultilingualTTS`, but it does not
demonstrate the voice cloning path (`audio_prompt_path`). Extending the current demo
would mix two concerns — multilingual fan-out and reference-conditioned synthesis —
into a single example, reducing clarity. A separate, minimal demo isolates the
voice-cloning workflow.

**API clarification (from upstream README):**
`audio_prompt_path` is a parameter of the **standard** `ChatterboxTTS` class
(`chatterbox.tts`), not `ChatterboxMultilingualTTS`. The standard model is
English-focused; `language_id` is not used. The multilingual variant handles
language-switched synthesis without reference-conditioned cloning.

Evidence from upstream [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox):

```python
# Standard TTS with voice cloning (audio_prompt_path)
from chatterbox.tts import ChatterboxTTS
model = ChatterboxTTS.from_pretrained(device="cuda")
wav = model.generate(text, audio_prompt_path="reference.wav")
```

## Proposed Solution

Create `examples/demos/chatterbox_clone/` with a single-path graph: accept `text` and
`voice_prompt_path` as runtime variables, synthesise using `ChatterboxTTS`, and write
output to `outputs/chatterbox-clone/output.wav`.

### Pipeline

```
START → synthesize → END
           ↓
   outputs/chatterbox-clone/output.wav
```

### Graph definition

```yaml
# examples/demos/chatterbox_clone/graph.yaml
version: "1.0"
name: chatterbox-voice-clone
description: Voice cloning demo using Chatterbox reference audio (FR-236)

tools:
  synthesize_cloned_audio:
    type: python
    module: examples.demos.chatterbox_clone.tools
    function: synthesize_cloned_audio

state:
  text: str
  voice_prompt_path: str

nodes:
  synthesize:
    type: python
    tool: synthesize_cloned_audio
    state_key: audio_path

edges:
  - from: START
    to: synthesize
  - from: synthesize
    to: END
```

### Python tool

```python
# examples/demos/chatterbox_clone/tools.py
"""FR-236 Chatterbox voice cloning demo tools."""

from pathlib import Path


def synthesize_cloned_audio(
    state: dict,
    *,
    output_dir: Path | str = Path("outputs/chatterbox-clone"),
) -> dict:
    """Synthesize text to WAV using ChatterboxTTS with a reference voice clip.

    Uses ChatterboxTTS (chatterbox.tts) — not ChatterboxMultilingualTTS.
    The standard model supports audio_prompt_path for voice cloning;
    see upstream README: https://github.com/resemble-ai/chatterbox

    Args:
        state: Graph state containing 'text' and 'voice_prompt_path'.
        output_dir: Directory for WAV output files.

    Returns:
        Dict with 'audio_path' string.
    """
    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    model = ChatterboxTTS.from_pretrained(device=device)

    text = state["text"]
    voice_prompt_path = state["voice_prompt_path"]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.wav"

    wav = model.generate(text, audio_prompt_path=voice_prompt_path)
    ta.save(str(output_path), wav, model.sr)
    return {"audio_path": str(output_path)}
```

### Usage

```bash
yamlgraph graph run examples/demos/chatterbox_clone/graph.yaml \
  --var text="Hello from YAMLGraph voice cloning" \
  --var voice_prompt_path="/absolute/path/to/reference.wav" \
  --full
```

### Scope Rules

1. Do not bundle a third-party speaker reference clip in the repository.
2. Require the operator to supply a local reference audio path at runtime via
   `voice_prompt_path`.
3. Keep this demo strictly separate from `examples/demos/chatterbox/`.
4. Document in `README.md` that the reference clip should be clean speech, ideally
   5–10 seconds.
5. Document in `README.md` that the synthesised voice will inherit characteristics
   from the reference clip.
6. No map fan-out; a single synthesis path is sufficient for this demo.
7. Use the device priority chain `cuda > mps > cpu`, extending FR-233's `cuda > cpu`
   with MPS support for Apple Silicon.
8. Use `ChatterboxTTS` from `chatterbox.tts` — not `ChatterboxMultilingualTTS`.
   Add a code comment citing the upstream README to document this choice.

**Status:** Implemented

## Acceptance Criteria

- [x] `examples/demos/chatterbox_clone/graph.yaml` exists and passes `yamlgraph graph lint`
- [x] `examples/demos/chatterbox_clone/tools.py` exposes `synthesize_cloned_audio(state: dict) -> dict`
- [x] The tool imports `ChatterboxTTS` from `chatterbox.tts` (not `ChatterboxMultilingualTTS`)
- [x] Device selection follows the `cuda > mps > cpu` priority chain (extends FR-233's `cuda > cpu` by adding MPS support for Apple Silicon)
- [x] The demo accepts `voice_prompt_path` as a runtime variable and passes it to `audio_prompt_path`
- [ ] Running the demo with a valid local reference clip produces a playable `.wav` at `outputs/chatterbox-clone/output.wav`
- [x] `examples/demos/chatterbox_clone/README.md` documents: correct class used, reference clip requirements, and example invocation
- [x] `examples/demos/demo.sh` includes a dedicated `chatterbox_clone` entry and excludes it from the `all` target (requires real audio file)
- [x] `demo-output.log` is committed alongside the demo files proving execution (FR-206 gate)
- [x] Unit tests mock `ChatterboxTTS` and assert:
  - The mock was instantiated as `ChatterboxTTS` (not `ChatterboxMultilingualTTS`)
  - `generate()` was called with the correct `audio_prompt_path` value
- [x] REQ-YG-235 reserved in `.chaplain/id-registry.yaml` and capability row added to ARCHITECTURE.md requirements table
- [x] `capabilities/CAP-93-chatterbox-voice-clone-demo.yaml` created (pattern: CAP-92)
- [x] Unit tests carry `@pytest.mark.req("REQ-YG-235")`
- [x] Diary reflection written in `docs/diary/`

## Alternatives Considered

1. **Extend the existing Chatterbox demo** — rejected; multilingual fan-out and voice
   cloning are distinct concepts that should be demonstrated independently.
2. **Use `ChatterboxMultilingualTTS` with `audio_prompt_path`** — rejected; the upstream
   README shows `audio_prompt_path` as a feature of the standard `ChatterboxTTS` class,
   not the multilingual variant. Mixing APIs would produce a misleading demo.
3. **Use `ChatterboxTurboTTS`** — possible (Turbo also supports `audio_prompt_path`),
   but the standard `ChatterboxTTS` is better for demonstrating the foundational
   voice-cloning capability. Turbo is optimised for low-latency agents.
4. **Use `ChatterboxVC` for voice conversion** — off-topic; `ChatterboxVC` converts
   source audio to a target voice rather than synthesising text from a reference speaker.
5. **Bundle a sample reference clip** — rejected; voice-asset provenance and consent
   issues are out of scope for a framework demo.

## Related

- [FR-233-chatterbox-tts-demo.md](../../feature-requests/FR-233-chatterbox-tts-demo.md) — existing multilingual TTS artifact demo
- [examples/demos/chatterbox/tools.py](../../examples/demos/chatterbox/tools.py) — current Chatterbox synthesis tool (device detection pattern to follow)
- https://github.com/resemble-ai/chatterbox — upstream Chatterbox repository

## Implementation Status

- Reserved IDs: **REQ-YG-235**, **CAP-93**
- Scope Rule 7: Device chain `cuda > mps > cpu` extends FR-233 (`cuda > cpu`) by adding MPS — the claim of "consistency" from the inbox draft is corrected to "extends".
- Unit test AC explicitly references `@pytest.mark.req("REQ-YG-235")` and the REQ-YG/CAP-XX infra steps required by ADR-001.
