# Feature Request: Consolidate Chatterbox Demos and Add CLI Speak Tool

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Merge `examples/demos/chatterbox/` (FR-233, multilingual TTS) and
`examples/demos/chatterbox_clone/` (FR-236, voice cloning) into a single
`examples/demos/chatterbox/` folder. Migrate the clone graph as
`chatterbox/clone.yaml`. Add a standalone `speak.py` CLI tool that takes a
reference WAV and a text string as arguments and produces `outputs/chatterbox/speak.wav`.

## Value Statement

Demo users get a unified, immediately runnable Chatterbox entry point — one
folder, one CLI command — instead of navigating two separate demos with
overlapping structure and a missing quick-start path.

## Problem

FR-233 and FR-236 were designed as separate demos to isolate two concepts:
multilingual fan-out (map node) and voice cloning (reference audio). Both are
now implemented and proven. Keeping them in parallel sibling folders creates
friction:

1. **Duplication** — both `tools.py` files share device-detection logic and
   output-directory setup; neither references the other.
2. **Discoverability** — a user who finds one demo may not discover the other.
3. **Missing CLI entry point** — both demos require `yamlgraph graph run ...`
   invocations with multiple `--var` flags. There is no single command a user
   can run to synthesise text with a personal reference voice clip.

## Proposed Solution

### 1. Consolidate into `examples/demos/chatterbox/`

Keep the existing multilingual graph (`graph.yaml`) and prompt
(`prompts/translate.yaml`) unchanged. Move `chatterbox_clone/tools.py`'s
`synthesize_cloned_audio` function into the shared `tools.py` alongside the
existing `synthesize_audio`. Update its default `output_dir` from
`outputs/chatterbox-clone` to `outputs/chatterbox` for consistency.

### 2. Migrate `chatterbox_clone/graph.yaml` as `chatterbox/clone.yaml`

Copy `chatterbox_clone/graph.yaml` to `chatterbox/clone.yaml`, updating the
`module` path from `examples.demos.chatterbox_clone.tools` to
`examples.demos.chatterbox.tools`. Document in README.md.

```yaml
# examples/demos/chatterbox/clone.yaml
version: "1.0"
name: chatterbox-voice-clone
description: Voice cloning demo using Chatterbox reference audio (FR-236, consolidated FR-237)

tools:
  synthesize_cloned_audio:
    type: python
    module: examples.demos.chatterbox.tools
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

### 3. Add `speak.py` CLI tool

A standalone Python script accepting two parameters — reference WAV and text
string. `--lang` is **not included** (Judge Issue 2 resolution, option b): the
tool uses `ChatterboxTTS`, which is English-focused and does not accept a
`language_id` kwarg. A `--lang` argument that controls only the output filename
would mislead users who expect it to change pronunciation. Users needing true
multilingual synthesis should use `graph.yaml` with `ChatterboxMultilingualTTS`.

```
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav \
    "Hello from YAMLGraph"
```

| Argument   | Short | Type | Required | Description                             |
|------------|-------|------|----------|-----------------------------------------|
| `--ref`    | `-r`  | path | Yes      | Path to reference WAV for voice cloning |
| positional | —     | str  | Yes      | Text string to synthesise               |

Behaviour:
- Uses `ChatterboxTTS` (from `chatterbox.tts`) — not `ChatterboxMultilingualTTS`.
- Device priority: `cuda > mps > cpu`.
- Validates `--ref` path exists; exits with code 1 and a message to stderr if not.
- Writes output to `outputs/chatterbox/speak.wav`.
- Prints the output path to stdout on success.

```python
# examples/demos/chatterbox/speak.py
"""CLI tool: synthesise text with a reference voice clone.

Usage:
    python examples/demos/chatterbox/speak.py \
        --ref examples/demos/chatterbox/source.wav "Hello world"

Note: Uses ChatterboxTTS (English-focused). Voice timbre transfers from the
reference clip, but pronunciation quality for non-English text may vary.
For true multilingual synthesis use graph.yaml with ChatterboxMultilingualTTS.
"""
import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chatterbox voice-clone TTS CLI (FR-237)"
    )
    parser.add_argument("text", help="Text to synthesise")
    parser.add_argument(
        "--ref", "-r", required=True, type=Path,
        help="Path to reference WAV for voice cloning",
    )
    args = parser.parse_args()

    if not args.ref.exists():
        print(f"Error: reference file not found: {args.ref}", file=sys.stderr)
        sys.exit(1)

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    device = (
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    model = ChatterboxTTS.from_pretrained(device=device)

    output_dir = Path("outputs/chatterbox")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "speak.wav"

    wav = model.generate(args.text, audio_prompt_path=str(args.ref))
    ta.save(str(output_path), wav, model.sr)
    print(output_path)


if __name__ == "__main__":
    main()
```

### 4. Update `demo.sh`

Remove the `demo_chatterbox_clone()` function and its `chatterbox_clone)` case.
Keep the `chatterbox` entry (multilingual graph). Add a `chatterbox_speak` entry
demonstrating the CLI tool using `source.wav` as reference (excluded from `all`,
since it requires GPU and a real audio file):

```bash
# chatterbox_speak entry in demo.sh — no stdout redirect (Judge Issue 1 fix)
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav \
    "Hello from YAMLGraph speak CLI"
```

**Judge Issue 1 resolution:** The original proposal redirected stdout to a `.wav`
file, which would overwrite the audio with the path string. The fix is to omit
the redirect entirely — `speak.py` writes the WAV internally via `torchaudio.save`
and only prints the path string to stdout.

### 5. Remove `chatterbox_clone/`

After migrating `synthesize_cloned_audio` into the shared `tools.py`, migrating
`graph.yaml` to `clone.yaml`, and verifying all unit tests pass, delete
`examples/demos/chatterbox_clone/`. Update `demo.sh` and `ARCHITECTURE.md`
(retain the CAP-93 capability entry, updating the path reference to
`chatterbox/` and extending the description to cover FR-237).

## Acceptance Criteria

### Consolidation
- [x] `examples/demos/chatterbox_clone/` is deleted
- [x] `examples/demos/chatterbox/tools.py` contains both `synthesize_audio`
      (FR-233) and `synthesize_cloned_audio` (FR-236) functions
- [x] `synthesize_cloned_audio` default `output_dir` is `outputs/chatterbox`
- [x] `examples/demos/chatterbox/clone.yaml` exists with `module` pointing to
      `examples.demos.chatterbox.tools`
- [x] `yamlgraph graph run examples/demos/chatterbox/clone.yaml` resolves
      without import errors (smoke test, mocked)

### CLI tool
- [x] `examples/demos/chatterbox/speak.py` exists and is executable
- [x] `speak.py` has no `--lang` argument; output filename is fixed to `speak.wav`
- [x] `speak.py --ref examples/demos/chatterbox/source.wav "text"` produces
      `outputs/chatterbox/speak.wav` (integration test skipped without
      GPU/chatterbox installed)
- [x] `speak.py` exits with code 1 and a stderr message when `--ref` path does
      not exist
- [x] `model.generate()` is called **without** any `language_id` kwarg

### Tests
- [x] `TestChatterboxCloneDemoStructure` in `test_chatterbox_clone_demo.py` is
      deleted (folder no longer exists)
- [x] All behavioural tests from `TestSynthesizeClonedAudio` are migrated to
      `test_chatterbox_demo.py`, importing from `examples.demos.chatterbox.tools`
- [x] A new `TestSpeakCLI` class is added in `test_chatterbox_demo.py` covering:
      - `generate()` called with correct `audio_prompt_path` and no `language_id`
      - Output written to `outputs/chatterbox/speak.wav`
      - Exit code 1 when `--ref` path does not exist
- [x] All existing `TestSynthesizeAudio` tests in `test_chatterbox_demo.py`
      continue to pass unchanged

### Documentation
- [x] `examples/demos/chatterbox/README.md` documents both the graph workflow
      (`graph.yaml`, `clone.yaml`) and the `speak.py` CLI tool
- [x] README includes a ready-to-run example using `source.wav` as reference:
      ```
      python examples/demos/chatterbox/speak.py \
          --ref examples/demos/chatterbox/source.wav "Hello"
      ```
- [x] README documents the language trade-off: `ChatterboxTTS` is
      English-focused; `--lang` intentionally absent; use `graph.yaml` for
      multilingual synthesis

### Demo infrastructure
- [x] `demo.sh` has no `chatterbox_clone` entry or `demo_chatterbox_clone()`
      function
- [x] `demo.sh` has a `chatterbox_speak` entry that calls `speak.py` without
      stdout redirect
- [x] `demo-output.log` in `examples/demos/chatterbox/` is updated to reflect
      consolidated demo execution (FR-206 gate)

### Traceability
- [x] `ARCHITECTURE.md` CAP-93 path updated from `chatterbox_clone` to
      `chatterbox/`; description extended to include FR-237 consolidation
- [x] FR-233 and FR-236 updated with "Superseded by FR-237 (consolidated)"
- [x] Diary reflection written in `docs/diary/`
- [x] Changelog fragment added in `changelog/unreleased/`

## Alternatives Considered

1. **Keep both folders, add `speak.py` only to `chatterbox_clone/`** — rejected;
   the two demos remain siloed and the duplication problem persists.
2. **Merge into a new `chatterbox_unified/` folder** — rejected; renaming the
   already-landed `chatterbox/` would break existing references without benefit.
3. **Use `ChatterboxMultilingualTTS` for `speak.py`** — rejected; the multilingual
   model does not expose `audio_prompt_path` (voice cloning). For a CLI tool
   centred on the reference-voice workflow, `ChatterboxTTS` is the correct class.
4. **Expose `speak.py` as a YAMLGraph tool** — out of scope; the FR explicitly
   requests a standalone Python CLI. The graph-based demos already cover the
   tool-node use case.
5. **Drop `chatterbox_clone/graph.yaml` instead of migrating** — rejected; the
   graph-based voice-cloning invocation via `yamlgraph graph run` has independent
   value and is preserved as `clone.yaml`.
6. **Include `--lang` for filename tagging** (option a/c) — rejected; a required
   argument that does not influence synthesis behaviour misleads users. Dropping
   `--lang` entirely (option b) gives a simpler, honest interface. Multilingual
   output naming is a concern for the graph-based workflow, not the CLI tool.

## Related

- [FR-233-chatterbox-tts-demo.md](../feature-requests/FR-233-chatterbox-tts-demo.md)
- [FR-236-chatterbox-voice-cloning-demo.md](../feature-requests/FR-236-chatterbox-voice-cloning-demo.md)
- `examples/demos/chatterbox/tools.py` — existing synthesis tool
- `examples/demos/chatterbox_clone/tools.py` — tool to merge
- `examples/demos/chatterbox/source.wav` — ready-made reference clip
- https://github.com/resemble-ai/chatterbox — upstream Chatterbox repository
