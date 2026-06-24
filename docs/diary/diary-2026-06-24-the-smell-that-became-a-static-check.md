# The smell that became a static check

**Date:** 2026-06-24
**FR:** FR-586 (W026 prompt-monolith linter check)
**Predecessor reflections:** [the hard part buried in bookkeeping](diary-2026-06-24-the-hard-part-buried-in-bookkeeping.md), [the flood that only changed its name](diary-2026-06-24-the-flood-that-only-changed-its-name.md)

## What happened

FR-584 proved empirically that a prompt fusing ~12 cognitive jobs starves its one
load-bearing judgement, and FR-585 set out to decompose it. The lesson — *length
is not the signal, judgement count is* — lived only in two diaries and three FRs.
The Seed was: make the smell visible at authoring time, the way `radon` flags an
overloaded function before it ships. FR-586 graduates that Seed into W026: a
static, warning-level `graph lint` check with two detectors (inline-schema field
count, curated prose phrases), calibrated against the 7-prompt plot_modeller
audit.

Judge-then-enforce went clean. The judgement caught one real defect before any
code: the FR claimed the threshold was "configurable via lint config," but the
linter has *no config mechanism* — every check is a pure
`(graph_path, project_root)` function with hardcoded constants. That phrase would
have required inventing a config-file loader. Amendment A1 demoted it to a
`field_threshold` function parameter; the custom-threshold test calls the check
directly. The cheapest interface is the one never invented.

## The trap

The calibration is a knife-edge, and I nearly trusted the analogues over reality.
Two clean prompts that must stay *silent* both carry near-miss phrases:
`extract_glosses` says "Every major plot point **should** be its own beat" and
`classify_kinds` says "exactly **ONE** action type." The regexes stay silent only
because they demand a trailing `(later|close)` / `.* and one` the clean prompts
lack. Amendment A2 pinned those two exact phrases as required negative-fixture
members, so any future loosening is caught as a regression.

But the deeper near-miss was almost methodological: I wrote the test with *minimal
analogues* (faithful to the frozen calibration, immune to FR-585 decomposing the
real files) — and a minimal analogue can agree with itself while disagreeing with
the world. The cure was to run W026 against the **real** `plot_modeller/graphs/*`
after GREEN. It reproduced the frozen calibration exactly: fire on the four
monoliths, silent on the two clean prompts *and* on the boundary `extract_goals`.
The analogue is the unit test; the real corpus is the witness.

## The insight

A regex that uses `.*` across a multi-line document is a cross-sentence
false-positive waiting to happen — "every" in line 3 binding to "later" in line
40. The fix needed no windowing logic: Python's default `.` does not cross
newlines, so `.*` is *already* line-scoped. The boundary I worried about was
enforced by the regex engine's defaults, not by code I had to write. Knowing the
tool's defaults is cheaper than re-implementing them.

## Heuristic

When a detector is calibrated on synthetic fixtures, the fixtures prove the rule
is *self-consistent*; only running it against the real corpus proves it is
*true*. Name the synthetic test after the seam (`calibration_witness`), but gate
the claim on the production artifacts the rule was born from.

**Seed:** W026 detects; it cannot decompose. The remedy ("split discrimination
from bookkeeping") is still a human judgement. Could a `graph lint --fix`
companion *propose* a two-node split for a W026 prompt — emitting the decode-node
skeleton FR-585 wrote by hand — turning the warning into a one-keystroke
refactor, while keeping the actual semantic split under human review?
