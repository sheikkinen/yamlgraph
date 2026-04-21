# Feature Request: Chatterbox speak.py — Batch TTS from Text File (FR-243)

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Add `--file` / `-f` option to `examples/demos/chatterbox/speak.py` that reads a plain-text file, splits it into paragraphs, synthesises each paragraph independently, and writes numbered WAV files (`00001.wav`, `00002.wav`, …) to the output directory.

## Value Statement

Authors and content creators can convert long-form written content (articles, scripts, book chapters) to audio in one command without manually splitting the text, with each paragraph as a ready-to-use audio segment.

## Problem

`speak.py` currently accepts a single text string on the command line. Multi-paragraph content must be split and looped manually by the caller, producing ad-hoc scripts and inconsistent output naming. There is no first-class workflow for converting a structured document to a set of audio files.

## Proposed Solution

Extend `speak.py` to accept an optional `--file PATH` argument. When provided:

1. Read the file as UTF-8 text.
2. Split on one or more blank lines (`\n\n+`) to obtain paragraphs; strip leading/trailing whitespace; discard empty paragraphs.
3. Synthesise each paragraph using the existing synthesis path (English via `ChatterboxTTS` + `--ref`, or multilingual via `ChatterboxMultilingualTTS` + optional `--ref`).
4. Write each result to `outputs/chatterbox/<NNNNN>.wav` with a zero-padded 5-digit index starting at `00001`.
5. Print each output path to stdout as it is written (one path per line), matching the existing single-file behaviour.

`--file` and positional `text` are mutually exclusive. If both are supplied, argparse exits with an error at parse time.

### Example CLI usage

```bash
# English batch (voice cloning required)
python examples/demos/chatterbox/speak.py \
    --file chapter1.txt \
    --ref examples/demos/chatterbox/source.wav

# Finnish batch, default voice
python examples/demos/chatterbox/speak.py \
    --lang fi \
    --file chapter1.txt

# Finnish batch with voice cloning
python examples/demos/chatterbox/speak.py \
    --lang fi \
    --ref source.wav \
    --file chapter1.txt
```

### Expected output structure

```
outputs/chatterbox/
  00001.wav   ← paragraph 1
  00002.wav   ← paragraph 2
  00003.wav   ← paragraph 3
  …
```

### Implementation sketch (speak.py)

Replace the positional `text` argument with a mutually exclusive group:

```python
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("text", nargs="?", help="Text to synthesise")
group.add_argument("--file", "-f", type=Path, help="Plain-text file; each paragraph becomes one WAV")
```

Extract synthesis into a `_synthesise(args, text, model)` helper, then drive the batch loop:

```python
if args.file:
    raw = args.file.read_text(encoding="utf-8")
    import re
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", raw) if p.strip()]
    for idx, para in enumerate(paragraphs, start=1):
        output_path = output_dir / f"{idx:05d}.wav"
        wav = _synthesise(args, para, model)
        ta.save(str(output_path), wav, model.sr)
        print(output_path)
```

No new dependencies; no changes to `tools.py`, `graph.yaml`, or any other module.

### Requirement

| ID | Description | Location |
|----|-------------|----------|
| REQ-YG-245 | `speak.py --file PATH` reads UTF-8 text, splits on blank lines, discards empty paragraphs, synthesises each via the engine selected by `--lang`, writes `outputs/chatterbox/NNNNN.wav` (5-digit 1-based index), prints each path to stdout; `--file` and positional `text` are mutually exclusive (argparse enforced); missing file exits non-zero (FR-243) | `examples/demos/chatterbox/speak.py` |

## Acceptance Criteria

- [ ] `--file PATH` is accepted by `speak.py`; positional `text` and `--file` are mutually exclusive (argparse enforces at parse time, exits non-zero)
- [ ] File is read as UTF-8; split on `\n\n+`; empty paragraphs discarded
- [ ] Each paragraph is synthesised via the engine selected by `--lang` (English `ChatterboxTTS` or multilingual `ChatterboxMultilingualTTS`)
- [ ] Output files are named `00001.wav`, `00002.wav`, … (5-digit zero-padded, 1-based) in `outputs/chatterbox/`
- [ ] Each output path is printed to stdout as it is written
- [ ] A 3-paragraph test fixture exercises the split + naming logic; asserted without model load (mock `_synthesise` helper)
- [ ] Existing single-text invocation (`speak.py "hello" --ref …`) is unaffected
- [ ] `speak.py --file missing.txt` exits non-zero with a clear error message
- [ ] `demo-output.log` updated to include a `--file` invocation example
- [ ] New tests marked `@pytest.mark.req("REQ-YG-245")`; REQ-YG-245 registered in `.chaplain/id-registry.yaml` and added to `ARCHITECTURE.md` requirements table

## Alternatives Considered

- **Shell loop over paragraphs**: Works but forces callers to implement splitting; no standard naming convention.
- **New graph node / YAML graph**: Over-engineered for a pure I/O transformation with no LLM routing; the synthesis tool already lives in `speak.py`.
- **tools.py batch function**: Would split graph concerns from CLI; the CLI is the right boundary for file I/O.

## Related

- `examples/demos/chatterbox/speak.py` — file to extend
- `examples/demos/chatterbox/tools.py` — synthesis helpers (unchanged)
- FR-239 — `speak.py` multilingual CLI (parent feature, REQ-YG-242)
- FR-237 — Chatterbox consolidation (REQ-YG-238)
