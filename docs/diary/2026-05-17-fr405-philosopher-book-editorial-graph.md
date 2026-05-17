# 2026-05-17 — FR-405 Philosopher Book Editorial Graph

The editorial graph surfaced the same boundary lesson as the chapters it edits:
editing a manuscript while generation is still active is not safe unless the
input boundary is made stable. The tempting implementation was to read directly
from `outputs/philosopher-book/chapters` and fan out over whatever files were
there. That would have made the editorial pass vulnerable to half-written,
missing, or later-regenerated chapters.

The fix was to normalize at the editorial boundary. `load_chapters` snapshots
repo-contained inputs into the output directory before any LLM work begins.
The LLM receives prose and editorial context; Python owns filesystem effects.
That separation keeps the editorial graph useful while preserving the original
drafts for comparison.

Trap: `downstream_fix` would have edited live files and hoped generation did
not move underneath it.

Heuristic: When a batch workflow reads artifacts produced by another active
workflow, snapshot the input set before fan-out.

Seed: Should YAMLGraph grow a first-class snapshot/input-freeze helper for
batch examples that consume generated files?
