# Book Reviewer Example

Critique a book-shaped Markdown manuscript with YAMLGraph using a **decomposed
map → reduce** pipeline — the deliberate opposite of a single "almighty prompt"
that judges a whole book at once.

- **No single LLM call ever sees the whole book.** Each chapter is judged alone,
  each adjacent seam is checked for continuity alone, and the synopsis is judged
  against compact chapter *summaries* — never the prose.
- **No LLM ever emits a number.** Every score in the final review is **computed**
  by a deterministic Python reduce. The only generative book-level task is a
  one-line prose verdict over the already-computed findings.
- **Parallel fan-out** via `map` nodes: chapters and seams are reviewed
  concurrently, then re-sorted into reading order (map collection order is
  completion order, not input order).

This is a stand-alone example: it imports only YAMLGraph framework code and reads
a Markdown manuscript. It has no dependency on any other example.

## Why decompose? (the research)

Long-context LLM judges degrade in well-documented ways, which the architecture
is built to avoid:

- **Lost in the Middle** (arXiv:2307.03172) — accuracy sags for evidence in the
  middle of a long context. *Cure: each chapter prompt holds one chapter.*
- **BooookScore** (arXiv:2310.00785) — book-length summarization is best done
  incrementally/hierarchically, not in one shot. *Cure: map per chapter, reduce.*
- **FActScore** (arXiv:2305.14251) — reliable factuality comes from decomposing
  into atomic, independently-checkable claims. *Cure: pairwise continuity and
  per-beat synopsis delivery.*
- **HANNA / Of Human Criteria** (arXiv:2208.11646) — human story evaluation uses
  distinct axes. *We score a manuscript-judgeable subset: Coherence, Engagement,
  Prose, Character (per chapter); Continuity and Relevance/synopsis-delivery
  (book-level).*

## Quick Start

```bash
# Review the bundled sample manuscript
cp examples/book_reviewer/sample_book.md /tmp/story.md
yamlgraph graph run examples/book_reviewer/graph.yaml \
  --var manuscript_path=/tmp/story.md \
  --full

# The human-readable review is written next to the manuscript:
cat /tmp/review.md
```

`manuscript_path` may be a file, or a directory containing `story.md`.

## Pipeline Flow

```
START
  │
  ▼
load (py)  ──▶  parse (py)  ──▶  lint (py)
                                   │
                                   ▼
                        chapter_review  (map: 1 body / prompt)
                                   │
                                   ▼
                          make_pairs (py)
                                   │
                                   ▼
                          continuity  (map: 2 bodies / prompt)
                                   │
                                   ▼
                       synopsis_beats (llm: summaries only)
                                   │
                                   ▼
                          compute (py: COMPUTE every score)
                                   │
                                   ▼
                          verdict (llm: prose only, no numbers)
                                   │
                                   ▼
                          finalize (py: write review.md)
                                   │
                                   ▼
                                  END
```

## File Structure

```
examples/book_reviewer/
├── graph.yaml                 # The map → reduce pipeline
├── prompts/
│   ├── chapter_review.yaml    # Per-chapter craft scoring (one body)
│   ├── continuity.yaml        # Pairwise seam check (two bodies)
│   ├── synopsis_beats.yaml    # Synopsis delivery (summaries only)
│   └── verdict.yaml           # One-line prose verdict (findings only)
├── models.py                  # Pydantic models (parsed book, reviews, report)
├── nodes/
│   └── tools.py               # Pure functions + python-node wrappers
├── sample_book.md             # Bundled sample manuscript
├── tests/                     # Pure unit tests + mocked graph + K4 gate
└── README.md                  # This file
```

## Key Design Decisions

### Anti-"almighty-prompt" (a tested invariant)

The temptation is to paste the whole book into one prompt and ask "rate this 1–5".
That prompt is unauditable, hits long-context failure modes, and hides its
reasoning behind a single number. Instead, each stage sees only what it needs,
and this scope is enforced by tests in [`tests/test_review.py`](tests/test_review.py):

| Stage             | Sees                              | Must NOT see        |
|-------------------|-----------------------------------|---------------------|
| `chapter_review`  | exactly **one** chapter body      | other chapter bodies |
| `continuity`      | exactly **two** adjacent bodies   | the whole book      |
| `synopsis_beats`  | synopsis + chapter **summaries**  | any chapter body    |
| `verdict`         | computed **findings** digest      | the manuscript      |

### Scores are computed, not asked

The LLM scores each *chapter* on four criteria, but the **book-level** numbers —
overall, per-criterion means, continuity, synopsis delivery — are all arithmetic
in [`nodes/tools.py`](nodes/tools.py) (`compute_review`). The LLM's only book-level
output is the prose verdict. This keeps the aggregate defensible and reproducible.

### Self-contained map items

Map sub-nodes see only their injected item plus parent state. The continuity map
therefore carries **both** chapter bodies inside each seam item, and each item
echoes its identity (`number`, `between`) so the reduce can re-sort the
completion-ordered results back into reading order.

### Normalize at the boundary

An `llm` node stores the executor's *dynamically built* schema instance — a class
distinct from this example's own models despite a shared name. `compute_node`
coerces model-or-dict inputs to a dict before validating (see `_as_dict`), and the
continuity `breaks` are plain strings so no provider key-naming quirk can break the
run. (Trust no provider's type.)

## Documented Extensions

Deliberately out of scope for this example, but natural next steps:

- **More HANNA axes** — Empathy, Surprise, Complexity require reader-modelling
  beyond what a single manuscript pass supports cheaply.
- **Running-state ledger** — continuity here is adjacent-pair only; a book-wide
  state ledger (who holds what, where, when) would catch non-adjacent
  contradictions at the cost of a stateful reduce.

## Tests

```bash
python -m pytest examples/book_reviewer/tests/ -q --no-cov
```

The suite covers the pure parse/lint/reduce functions, a fully mocked map → reduce
graph run, the K4 prompt-scope gate, the boundary-normalization regression, and an
import-purity check (no foreign example, no DM JSON).
