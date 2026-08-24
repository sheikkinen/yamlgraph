# The Scorer That Could Not Write

**Date:** 2026-08-24
**Arc:** small-model voicebot eval → char-GPT scenarios → recraft-v4 roster addition

## What happened

One session, three descending model scales, one capability cliff mapped.
Replayed csap's frozen promptfoo suite against Qwen2.5-1.5B on CPU:
closed-label classification held (2.4s warm, correct); extraction parroted
field *descriptions* as field *values*; generation copied in-prompt examples
into output — telling a caller they wanted to move an appointment that was
never mentioned. Then FR-876's 5M char-GPT at the bottom: register without
semantics.

Ended concrete: recraft-ai/recraft-v4 added to deviant-daily's roster,
webp→png normalized at the download boundary, RED/GREEN witnessed on a live
artifact, CI green.

## The trap

**Task-size intuition.** I initially framed suitability as "how big is the
task" — classification small, extraction medium, generation large. Wrong
axis. The 1.5B model failed *extraction* (medium) in the same mode it failed
generation: by producing plausible text from the prompt's own scaffolding
instead of the transcript. The suite's shape checks passed; the semantics
were fabricated — `plausible_wrong_answer` in its purest form, at three
scales.

## The insight

The suitability boundary is **copy-vs-generate discrimination**, not task
size. A model is safe below the cliff exactly when the task is *selection
from a closed set* (labels, enum members) and unsafe the moment the output
space includes free text — because a small model fills free text from the
nearest available source, which is the prompt itself. Corollary: the 5M
char-GPT is not a broken generator but a working **measuring instrument** —
perplexity against a learned register is a scorer, and scorers don't need
semantics. The same inversion cured extraction on paper: a
transcript-containment guard (mirror of FR-876's novelty gate, sign
flipped) rejects extraction output that does NOT copy the transcript.

Second, smaller insight: the recraft docstring I first wrote claimed PNG
output because the filename said `.png`. The RIFF magic bytes said webp.
`what_does_the_raw_record_say` fired one `xxd` before the false claim
shipped — verification caught documentation, not code.

## Seed

**Seed:** If closed-set selection is the safe zone for tiny models, can a
graph *compiler* pass mechanically classify each prompt node as
selection-vs-freetext (schema is enum-only vs contains str fields) and emit
a per-node minimum-model floor — making the copy-vs-generate cliff a
lintable property of the YAML instead of a discovered production failure?
