# Feature Request: Multilingual Support in `speak.py` CLI

**FR:** FR-239
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Extend `examples/demos/chatterbox/speak.py` with a `--lang` flag that routes to
`ChatterboxMultilingualTTS` when a non-English language is requested, while
preserving the existing voice-cloning path for English. Finnish is the
proof-of-concept language.

## Value Statement

Demo authors and end-users can synthesise Finnish (and other supported) speech
from the same CLI entry-point without manually wiring `graph.yaml`, removing the
friction of discovering a hidden multilingual path.

## Problem

`speak.py` is the entry-point users reach first. It currently invokes only
`ChatterboxTTS` (English-focused voice cloning). Attempting Finnish through it
produces degraded pronunciation. The multilingual capability already exists in
`tools.synthesize_audio` and `graph.yaml`, but is unreachable from the CLI.
Nothing in the CLI surface tells users a better path exists.

The gap is also architectural: the CLI implies a single synthesis model when the
codebase already has two — one for voice cloning, one for multilingual synthesis.
A flag-only change on top of a single-model CLI would be dishonest. The CLI
needs an explicit mode split that mirrors the split that already exists in the
graph layer.

## Proposed Solution

Add `--lang` (default `en`) to `speak.py`. When `--lang en` (or omitted), the
behaviour is identical to today: `ChatterboxTTS` with `audio_prompt_path` for
voice cloning. When any other language code is provided, the CLI routes to
`ChatterboxMultilingualTTS`.

Key design decisions to make explicit in the CLI help text and docstring:

- **Voice cloning is English-only.** `ChatterboxMultilingualTTS` does not accept
  `audio_prompt_path`; the `--ref` flag is incompatible with `--lang <non-en>`
  and must raise a clear error.
- **Language codes** are passed as `language_id` to `ChatterboxMultilingualTTS`;
  the CLI should state which codes are known-good (at minimum `fi`, `sv`, `de`,
  `es` — the set already exercised in `graph.yaml`).
- **Output file** stays `outputs/chatterbox/speak.wav` regardless of path, so
  shell pipelines are unaffected.

```bash
# Existing behaviour (unchanged)
python examples/demos/chatterbox/speak.py \
    --ref examples/demos/chatterbox/source.wav "Hello world"

# New: Finnish via multilingual model (no ref audio)
python examples/demos/chatterbox/speak.py \
    --lang fi "Hei maailma"

# Error: ref + non-English lang is unsupported
python examples/demos/chatterbox/speak.py \
    --ref source.wav --lang fi "Hei"
# → Error: --ref is only supported with --lang en (voice-cloning path)
```

### Implementation sketch

```python
# speak.py (simplified)
if args.lang == "en":
    # existing ChatterboxTTS + audio_prompt_path path (unchanged)
    ...
else:
    if args.ref:
        parser.error("--ref is only supported with --lang en")
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    wav = model.generate(args.text, language_id=args.lang)
    ta.save(str(output_path), wav, model.sr)
```

No new module or tool function is needed; the logic lives in `speak.py` directly
(it is a thin CLI script, not a library). `tools.synthesize_audio` is unchanged.

## Acceptance Criteria

- [ ] `speak.py --lang fi "Hei maailma"` produces `outputs/chatterbox/speak.wav`
      without error on a machine with `chatterbox` installed.
- [ ] `speak.py "Hello world" --ref source.wav` (no `--lang`) continues to work
      identically to the current behaviour.
- [ ] `speak.py --lang fi --ref source.wav "..."` exits with a clear error
      message referencing the incompatibility, not a Python traceback.
- [ ] `speak.py --help` lists `--lang`, its default (`en`), and documents which
      model each path uses.
- [ ] Docstring at top of `speak.py` updated to describe both synthesis paths.
- [ ] A unit test in `tests/unit/` (mock `ChatterboxMultilingualTTS`) verifies
      that `--lang fi` invokes the multilingual model and that `--lang fi --ref`
      raises `SystemExit` with a non-zero code.
- [ ] `demo-output.log` updated with a Finnish synthesis run.
- [ ] README in `examples/demos/chatterbox/` updated with the `--lang` flag and
      a note that voice cloning requires `--lang en` (or omission).
- [ ] Changelog fragment created in `changelog/unreleased/`.

## Alternatives Considered

### Separate `speak-multilingual.py` command
Keeps the two models completely separate, avoids the incompatible-flag problem.
Rejected: adds a second entry-point that users must discover; `speak.py` is the
natural home for all synthesis CLI.

### Expose `ChatterboxMultilingualTTS` via `clone.yaml` / `graph.yaml` run
The graph path already works. Rejected as scope for this FR: the gap is the CLI
entry-point, not the graph layer.

### Allow `--ref` with multilingual model (voice-cloned multilingual)
Would require verifying that `ChatterboxMultilingualTTS.generate()` accepts
`audio_prompt_path`. If the upstream API supports it in a future release this can
be a follow-on FR. For now, raise a clear error and document the limitation.

## Related

- FR-233: Chatterbox multilingual TTS demo (`graph.yaml`, `tools.synthesize_audio`)
- FR-236: Chatterbox voice cloning demo (`clone.yaml`, `synthesize_cloned_audio`)
- FR-237: Chatterbox CLI consolidation (`speak.py` first introduced)
- `examples/demos/chatterbox/tools.py` — `synthesize_audio` is the reference
  implementation of the multilingual path this FR exposes at the CLI level.
