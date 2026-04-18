# Diary: FR-236 Chatterbox Voice Cloning Demo

**Date:** 2026-04-18
**FR:** FR-236
**Requirement:** REQ-YG-235

## Cognitive Process

The task was a clean, well-specified feature request. The prior art (FR-233 / CAP-92) was
directly navigable and the implementation was a straightforward delta: swap
`ChatterboxMultilingualTTS` for `ChatterboxTTS`, swap the map fan-out for a single synthesis
path, add `voice_prompt_path` → `audio_prompt_path` threading, and extend the device chain
from `cuda > cpu` to `cuda > mps > cpu`.

## Traps Encountered

### trap: `working_system_inertia`
The FR-233 tool is a good template, but I had to resist copying its structure uncritically.
The multilingual variant iterates over a translations list; the cloning variant is a simple
single call. Reusing the iteration structure would have introduced unnecessary complexity.

### trap: `partial_remediation` (README audit gate)
The unit tests passed immediately (15/15 GREEN on first run), but the full suite caught one
additional failure: the examples README audit test (`REQ-YG-147`) required `chatterbox_clone`
to appear in `examples/README.md`. This is the audit-gate pattern from the knowledge graph —
detection without enforcement at the task boundary is insufficient. The cure was immediate:
add the table row to `examples/README.md`.

## Insights

- The `examples/README.md` audit gate (`test_all_demos_listed_in_readme`) is a reliable
  catch for demos that would otherwise be invisible to users. Running the full unit suite
  rather than only the targeted test file surfaced this cleanly.
- Device chain extension (`cuda > mps > cpu`) is a two-line change once the pattern is
  identified from the FR. The MPS check (`torch.backends.mps.is_available()`) sits between
  the CUDA check and the CPU fallback.
- The FR explicitly notes that `audio_prompt_path` belongs to `ChatterboxTTS`, not
  `ChatterboxMultilingualTTS`. Writing a dedicated test
  (`test_uses_chatterbox_tts_not_multilingual`) makes this constraint machine-checkable
  and guards against future drift.

## Heuristic

> When cloning a demo from a sibling, list every structural difference in the FR before
> touching code. "Simpler" usually means fewer loops, fewer state keys, fewer edges — check
> all three.

## Seed

Could YAMLGraph support an `audio_prompt_path` as a first-class graph input type — with
automatic validation (file exists, duration check, format check) in the linter — to make
reference-conditioned synthesis a declared, auditable capability rather than an opaque
string variable?
