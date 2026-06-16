# Feature Request: FR-497 — `book-reviewer` stand-alone example

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed — **replanned** (decomposed map/reduce review); supersedes the 2026-06-16 freeze, needs re-judge
**Effort:** 1–2 days
**Requested:** 2026-06-16
**Replanned:** 2026-06-16 (1) a new stand-alone **example** (`examples/book_reviewer/`), not a pipeline step; (2) **decomposed** evaluation — map per-chapter + pairwise continuity + reduce — *not* one almighty prompt over the whole book

## Summary

The DM v2 prototype can now generate a complete story end to end
([scripts/generate.py](examples/dungeon_master/scripts/generate.py)) and serialize
it to a reader `story.md` ([api/render.py](examples/dungeon_master/api/render.py)).
What nothing can do is say whether the story is any **good** — the only quality
signals today are the per-turn director's `scene_complete` and `reviewed` flags,
gates on *whether a stage finished*, not on *whether the finished book is coherent,
faithful, or well-told*.

This FR adds a new **stand-alone YAMLGraph example** — `examples/book_reviewer/`,
a sibling of [examples/book_translator](examples/book_translator) — that takes a
**book-shaped Markdown manuscript as its sole input** and produces a structured
review. It is its **own** example: it does **not** live under `dungeon_master`, does
**not** import the DM `api`/`session`/`render`/`story_doc` code, and never reads
`story.json`. The DM's `story.md` is merely one **sample input**; the reviewer works
on any manuscript that follows the book shape (tagline lead, `# Synopsis`, `# Cast`,
`# Chapter N: …`), DM-made or hand-written.

The example dogfoods the framework: a `graph.yaml` orchestrates a deterministic
Markdown **parse** + **lint** (Python tools) followed by an LLM **review** node
with a typed Pydantic output. It scores the book against dimensions grounded in the
craft contracts the DM generation prompts promised — coherence, character
consistency, cross-chapter continuity, pacing/climax, prose craft, ending — but
phrased generically so the example reviews *any* book, not only DM output.

## Value Statement

A finished book can be **scored and inspected on demand**, decoupled from how it was
made: run the `book-reviewer` example against any `story.md` (DM-rendered or
hand-written) and get a per-dimension score with **specific, quotable issues** so a
weak book is diagnosable, not just "felt off". As a stand-alone example it also
serves as a reusable YAMLGraph reference for the **parse → deterministic lint →
LLM-judge** pattern (text in, typed evaluation out) — the mirror of
`book_translator`'s text-in/text-out pipeline. Evaluation is the missing,
*separable* half of "generate a book": FR-494 proved we can *produce* one; this
example proves we can *judge* one, from the artifact alone.

## Problem

The generation pipeline makes explicit quality promises in its prompts, but
nothing checks the finished story against them:

- [final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml) contracts
  **"COMPOSE, do not invent"**, **"preserve every canonical BEAT"**, **"state each
  standing fact once"**, and **"give each beat weight proportionate to its
  importance"** (climax gets the most space). Nothing verifies the final text kept
  these promises.
- [synopsis.yaml](examples/dungeon_master/prompts/synopsis.yaml) commits the story
  to an outline; nothing checks the **played** story matches the synopsis it
  committed to.
- [character.yaml](examples/dungeon_master/prompts/character.yaml) gives each
  character a `DRIVE` / `FLAW` / `ROLE`; nothing checks the characters **act**
  consistently with their own sheet.
- The forward-carry `world_state` ledger (FR-491 J7) is meant to keep chapter
  *N+1* consistent with chapter *N*'s end-state; nothing checks for **continuity
  breaks** (a fact contradicted across chapters).

And on the structural side, the FR-495 (doubled heading) and FR-496 (leaked
`SUMMARY:`/`ROLE:`/… scaffolding) defects were both **invisible to the unit
suite** and only caught by a human reading one live sample. There is no harness
that re-asserts those invariants on real rendered output, so the next prompt
mannerism that reintroduces a leak would ship unnoticed.

This is a **boundary** problem (the `evaluation` boundary): to the reviewer the
manuscript is *external text*, and the method of evaluation determines the
conclusion. A pure shape check ("is it valid Markdown?") passes a book that is
structurally clean but narratively incoherent; only a rubric that reads the
*substance* can tell whether the book is good. Shipping the reviewer as its **own
example** that consumes only the Markdown is what keeps the book external: a step
inside `dungeon_master` — or one that reads `story.json` — would have privileged,
structured access to the author's intermediate state and judge its own work from
the inside. A separate example that parses the *rendered manuscript* reads exactly
what a reader reads, recovering the structure from the prose.

## Research — how a book is actually evaluated

The first plan smuggled in a hidden assumption: that one LLM call, handed the whole
book, can reliably score it on eight dimensions. The literature condemns that
"almighty prompt" and points uniformly to **decomposition + aggregation**:

1. **Lost in the Middle** (Liu et al., TACL 2023, arXiv:2307.03172). LLMs do **not**
   robustly use information in the *middle* of a long context; accuracy is highest
   when the relevant material is at the very start or end and degrades sharply in
   the middle — *even for models advertised as long-context*. A reviewer that pastes
   the entire book into one prompt therefore **systematically under-weights the
   middle chapters** — exactly where continuity breaks hide. The almighty prompt is
   not just costly, it is positionally biased.
2. **BooookScore** (Chang et al., ICLR 2024, arXiv:2310.00785). The first systematic
   study of book-length (>100K-token) processing. Because the book exceeds the
   window you must **chunk**, then either (a) hierarchically merge chunk-level
   results or (b) incrementally update a running summary/state. They catalogue
   **eight recurring coherence-error types** and define the metric as the
   *proportion of sentences free of any error* — a decomposed, countable score, not a
   holistic 1–5 guess.
3. **FActScore** (Min et al., EMNLP 2023, arXiv:2305.14251). Binary/holistic
   judgments of long text are inadequate because a passage mixes supported and
   unsupported claims. Their fix: break the text into **atomic facts** and score the
   fraction verified against a source. *Decompose-then-verify* beats "is this
   consistent? (y/n)".
4. **HANNA / Of Human Criteria** (Chhun et al., COLING 2022, arXiv:2208.11646).
   Proposes **six orthogonal human criteria** for story evaluation — *Relevance,
   Coherence, Empathy, Surprise, Engagement, Complexity* — grounded in social-science
   theory, and shows automatic metrics **correlate poorly** with human judgment.
   Lesson: use an established orthogonal criteria set, and distrust any single
   automatic number.

**Design implication.** Evaluation must be **decomposed and aggregated (map →
reduce), never one prompt over the whole book.** Each LLM call sees a *small,
focused* slice — one chapter, one chapter-pair, or the synopsis alone — so the
relevant text lands in the high-attention head/tail region; the book-level verdict
is **computed** from those slices, not hallucinated over thousands of chars of
middle-of-context prose. This is also a strictly better YAMLGraph example: it
dogfoods the **`map` node** (per-chapter fan-out) and a reduce node, mirroring
BooookScore's chunk-then-merge.

## Proposed Solution

A new example directory `examples/book_reviewer/`, structured like
[examples/book_translator](examples/book_translator):

```
examples/book_reviewer/
  README.md            # what it does, how to run
  graph.yaml           # parse → lint → map(chapter) → map(pair) → synopsis → reduce
  models.py            # ParsedBook, ChapterSection, LintReport,
                       #   ChapterReview, ContinuityReport, SynopsisDelivery, BookReview
  nodes/
    tools.py           # parse_manuscript, lint_manuscript, chapter_pairs (pure, no LLM)
  prompts/
    chapter_review.yaml  # per-chapter LLM review (inline ChapterReview schema)
    continuity.yaml      # per-pair continuity check (inline ContinuityReport schema)
    synopsis_beats.yaml  # synopsis → beats + coverage (inline SynopsisDelivery schema)
    verdict.yaml         # reduce: overall/verdict over aggregated findings
  tests/
    test_parse.py      # parse recovers structure from Markdown
    test_lint.py       # lint flags leaks / numbering gaps / empty chapters
    test_review.py     # mock-LLM: map+reduce graph returns typed BookReview
  sample_book.md       # a captured story.md, the worked example input
```

The graph takes the manuscript path as input and runs a **decomposed map → reduce**
evaluation, cheapest stages first; nothing mutates the input. Every LLM call sees a
*single chapter, a single chapter-pair, or the synopsis alone* — never the whole
book. The example imports **only** YAMLGraph framework code — no `dungeon_master`
import, no `story.json`.

### Stage 0 — Parse the manuscript into structure (Python tool, no LLM)

The entry reads a **path to a `.md` file** (or a directory containing `story.md`).
The `parse_manuscript` tool parses the Markdown — by the book shape FR-494 emits —
to flesh out a typed structure the rest of the graph reasons over:

```python
class ChapterSection(BaseModel):
    number: int          # the heading ordinal ("# Chapter 3: …" → 3)
    title: str           # the cleaned heading title (may be "")
    body: str            # the chapter's prose, to the next H1

class ParsedBook(BaseModel):
    tagline: str                       # the leading blockquote ("> …")
    synopsis: str                      # the "# Synopsis" section body
    cast: list[str]                    # the "# Cast" bullet lines (name — gloss)
    chapters: list[ChapterSection]     # in document order
```

The parse is the structure-recovery this revision is built on: it walks the H1
sections (`# Synopsis`, `# Cast`, `# Chapter N: …`), reads the tagline blockquote
lead, and splits each chapter's prose to the next heading. It is the **single**
place that knows the book's Markdown shape, and it is pure text — no DM import, no
JSON. Everything the review needs (synopsis intent, cast, chapter prose) comes
**from this parse**.

### Stage 1 — Manuscript lint (Python tool, no LLM)

A pure pre-pass over the **parsed** structure, returning a typed report. Cheap,
always run, catches mechanical defects an LLM might gloss over — and (when the input
is a DM `story.md`) re-asserts the FR-494/495/496 render invariants from the
manuscript side (the **golden-sample** check seeded by the FR-495/FR-496 diary
reflection, "the demo is a test boundary"):

```python
class LintIssue(BaseModel):
    code: str           # "leaked-label" | "doubled-heading" | …
    detail: str         # the offending line

class LintReport(BaseModel):
    ok: bool
    issues: list[LintIssue]
```

Checks (each operates on the parsed structure — pure text, no DM import, no JSON):

- **`leaked-label`** — no scaffolding label from a configurable set
  (default the DM sheet labels `SUMMARY:`/`ROLE:`/`ORIGIN:`/`APPEARANCE:`/
  `PERSONALITY:`/`DRIVE:`/`BOND:`/`FLAW:`) survives into the cast or prose
  (FR-496). The label set is a tool parameter so the check generalises beyond DM.
- **`doubled-heading`** — no chapter whose `title` still begins `Chapter N …`
  (FR-495).
- **`heading-numbering`** — the parsed chapter `number`s are `1..k`, monotonic
  (FR-494).
- **`missing-frontmatter`** — the parse recovered a non-empty `tagline`,
  `synopsis`, and (when a `# Cast` section exists) a non-empty `cast` (FR-494
  J1/J2).
- **`empty-chapter-body`** — every parsed chapter has non-empty `body` prose.

### Stage 2 — Per-chapter review (LLM **map** over chapters)

A `map` node fans out over `parsed.chapters`. **Each chapter gets its own LLM
call** with a *small* context — that chapter's body plus the cast glosses and the
synopsis for reference — and scores the *local* craft criteria that are judgeable
within a chapter: **Coherence**, **Engagement**, **Prose craft**, and **Character
consistency** (do the cast act as introduced). It returns a typed `ChapterReview`.
Because every call sees exactly one chapter, no chapter is ever buried "in the
middle" of a long context (Lost-in-the-Middle), and the per-chapter scores are the
countable, decomposed signal BooookScore argues for.

```python
class CriterionScore(BaseModel):
    name: str              # "coherence" | "engagement" | "prose" | "character"
    score: int             # 1–5
    justification: str

class ChapterReview(BaseModel):
    number: int
    criteria: list[CriterionScore]
    issues: list[str]      # specific, quotable problems in this chapter
```

### Stage 3 — Pairwise continuity (LLM over adjacent chapter **pairs**)

A windowed pass: a `chapter_pairs` tool builds the list of adjacent windows
`(N, N+1)`, and a `map` node runs one LLM call per pair asking a single question —
does chapter *N+1* contradict a fact, location, or character state established at
the **end of chapter N**? This is FActScore's *decompose-then-verify* applied to
continuity: instead of "is the whole book continuous?", verify **each seam** in
isolation. Adjacent-pair scope keeps every call small.

```python
class ContinuityBreak(BaseModel):
    between: tuple[int, int]   # (N, N+1)
    detail: str                # the contradicted fact, quoted from both sides

class ContinuityReport(BaseModel):
    score: int                 # 1–5, derived from break count/severity
    breaks: list[ContinuityBreak]
```

(A running-state ledger — BooookScore's *incremental-update* workflow, carrying
standing facts forward chapter by chapter — is the richer variant; adjacent-pair is
the minimal version and the example notes the ledger as a documented extension.)

### Stage 4 — Synopsis delivery (LLM, decomposed into **beats**)

The synopsis is the book's own declared destination, so it is the natural
reference. One small LLM call **decomposes the synopsis into discrete promised
beats** (input: the synopsis text alone); a second pass checks **coverage** — for
each beat, is it delivered in the chapter bodies/reviews? This is FActScore
inverted: *recall* of promised beats rather than precision of asserted facts. It
never asks one prompt "did the book deliver its synopsis?" over the whole text.

```python
class SynopsisDelivery(BaseModel):
    score: int                 # 1–5, = covered / promised
    promised: list[str]        # beats extracted from the synopsis
    undelivered: list[str]     # beats with no chapter coverage
```

### Stage 5 — Reduce: assemble the `BookReview` from structured evidence

A reduce node aggregates the slices into the final typed `BookReview`: per-chapter
`CriterionScore`s roll up into book-level criterion scores (mean, with the **min**
flagged), the `ContinuityReport` and `SynopsisDelivery` contribute their scores and
issue lists, and an `overall` + one-line `verdict` summarise. If a final LLM call
writes the verdict, it reads **only the compact aggregated findings** (a few hundred
tokens of scores + flagged issues) — **never** the raw manuscript — so even the
summary judge sits in the high-attention regime. No node in the graph ever receives
the whole concatenated book as its prompt context (the anti-almighty-prompt
invariant).

```yaml
# prompts/*.yaml each carry an inline Pydantic schema (Commandment 5)
#   chapter_review.yaml  -> ChapterReview
#   continuity.yaml      -> ContinuityReport (per pair)
#   synopsis_beats.yaml  -> SynopsisDelivery
#   verdict.yaml         -> the overall/verdict over aggregated findings
```

```python
class BookReview(BaseModel):
    overall: int                       # 1–5 holistic, computed + summarised
    verdict: str                       # one-line judgment
    criteria: list[CriterionScore]     # book-level, HANNA-derived
    continuity: ContinuityReport
    synopsis_delivery: SynopsisDelivery
    chapters: list[ChapterReview]      # the per-chapter detail, retained
```

Criteria are drawn from the **six HANNA criteria** (Relevance → synopsis delivery;
Coherence; Engagement; plus Prose craft and Character consistency as craft
sub-criteria) rather than an ad-hoc invented set — and each lands on the slice that
can actually judge it.

> **Not in scope:** "preserve every canonical BEAT" and "COMPOSE, do not invent"
> are generation contracts checkable only against the hidden beat list and played
> arc in `story.json` — which this example deliberately never reads. A
> manuscript-only reviewer has no ground truth for them, so they are **not** rubric
> criteria; they survive as distant inspiration for coherence/continuity, not
> claimed checks.

### How to run

The example is run through the framework CLI like any other graph, with the
manuscript path as a variable. A `load_manuscript` tool reads the file (Layer-3
side effect), then `parse_manuscript` → `lint_manuscript` → the **map** of
per-chapter reviews → the **map** of pairwise continuity checks → synopsis-delivery
→ the **reduce** that assembles the `BookReview` → `write_report`:

```bash
yamlgraph graph run examples/book_reviewer/graph.yaml \
    --var manuscript_path=outputs/dungeon-master/sample-courier/story.md --full
```

The typed `BookReview` and the `LintReport` are the graph's final state (shown by
`--full`); `review.md` is the human sidecar. The deterministic parse + lint
regression check lives in the **unit tests**, which call the pure tools directly —
there is no `--no-llm` CLI flag. The example is a **sibling** of
`book_translator`/`dungeon_master`, sharing no code with the generator beyond
YAMLGraph itself.

## Acceptance Criteria

- [ ] A new example directory `examples/book_reviewer/` exists with `graph.yaml`,
      `models.py`, `nodes/tools.py`, `prompts/review.yaml`, `tests/`, a
      `sample_book.md`, and a `README.md` (sibling layout to `book_translator`).
- [ ] `parse_manuscript(markdown) -> ParsedBook` (pure Python tool) recovers the
      tagline, synopsis, cast bullets, and ordered `ChapterSection`s (number,
      cleaned title, body) from a book-shaped `story.md` — no DM import, no JSON.
- [ ] `lint_manuscript(parsed, labels=...) -> LintReport` (pure) returns
      `ok=True, issues=[]` for `sample_book.md`, and a populated `issues` list (with
      the correct `code`s) for a manuscript deliberately carrying a leaked label, a
      doubled heading, a numbering gap, or an empty chapter body.
- [ ] Parse + lint run with **no LLM and no I/O beyond reading the `.md`** and are
      unit-tested in `examples/book_reviewer/tests/`.
- [ ] A **golden-sample** test uses `sample_book.md` (a captured `story.md`) and
      asserts `lint_manuscript(parse_manuscript(md)).ok is True` — so a future
      prompt/render drift that reintroduces an FR-495/FR-496 leak fails a check (the
      diary Seed, realised).
- [ ] Each LLM stage prompt defines an **inline Pydantic schema** (Commandment 5):
      `chapter_review.yaml`→`ChapterReview`, `continuity.yaml`→`ContinuityReport`,
      `synopsis_beats.yaml`→`SynopsisDelivery`, `verdict.yaml`→the overall/verdict.
      Criteria are drawn from the **six HANNA criteria**, not an ad-hoc set, and
      no criterion claims a `story.json`-only ground truth (no beat-list / no
      no-invention check).
- [ ] `graph.yaml` runs load → parse → lint → **map** per-chapter review → **map**
      pairwise continuity → synopsis-delivery → **reduce** → write_report, and the
      reduce node returns the typed `BookReview` (verified with a **mock-LLM** unit
      test — no live key). A parse recovering **zero chapters** raises rather than
      emitting an empty review (Commandment 6).
- [ ] **Anti-almighty-prompt invariant:** no LLM node receives the whole
      concatenated book as its context — each call sees one chapter, one chapter
      pair, or the synopsis alone. A test asserts the rendered chapter-review prompt
      contains exactly one chapter's body (per-chapter fan-out), and the verdict
      prompt contains the aggregated findings but **not** the full manuscript.
- [ ] `yamlgraph graph run examples/book_reviewer/graph.yaml --var manuscript_path=…`
      produces a `BookReview` and writes a `review.md` beside the manuscript. A live
      end-to-end run against the DM `sample-courier/story.md` is captured to a log.
- [ ] The example imports **only** YAMLGraph framework code — no
      `dungeon_master`/`session`/`render`/`story_doc` import and no `story.json`
      read (enforced by a test asserting the module's import set, or by the
      reviewer).
- [ ] The review is **advisory** — the example scores and reports; it does not gate
      anything. (A CI quality gate is a separate, later FR.)

## Open Question (for the Judge) — gate regime

**Resolved — see Judgment J1 below.** `book_reviewer` follows the `book_translator`
precedent: a first-class example with **no CAP file and no `@pytest.mark.req`
markers** (the req-coverage script scopes to the framework's own `tests/`, not
`examples/`). It is **not** folded under the FR-474 J3 DM exemption (it is not the
DM prototype), so its commits carry **no** `FR-474 J3` trailer and use honest
`feat(book-reviewer): FR-497 …` types with a changelog fragment + diary reflection.

## Alternatives Considered

- **Put the evaluator under `examples/dungeon_master/`.** Rejected per the revised
  target: a stand-alone *example* makes the decoupling structural, not just a
  convention — a separate directory cannot import DM internals by accident, and the
  example reads as a reusable "review any book" reference rather than a DM appendage.
- **Single LLM holistic score over the whole book (the "almighty prompt").**
  Rejected — this was the first plan's flaw. (1) Lost-in-the-Middle: a whole-book
  prompt positionally under-weights the middle chapters where continuity breaks
  hide. (2) FActScore: a holistic "is it consistent? (7/10)" is not actionable and
  cannot be verified. (3) HANNA: single automatic numbers correlate poorly with
  human judgment. The replan decomposes into per-chapter map + pairwise continuity +
  synopsis beats and **computes** the book-level score (BooookScore's chunk-then-
  merge). The deterministic parse+lint still runs always and catches mechanical
  regressions (a leaked label) an LLM would gloss over.
- **Read `story.json` for reference fields.** Rejected: that couples the example to
  the DM doc shape and lets it judge the author's intermediate state rather than the
  reader's artifact. Recover everything from the **parsed manuscript**; the synopsis
  section is the book's own stated intent.
- **Feed the review back into a generation revision loop.** Out of scope — that
  re-couples evaluation to generation and invites a runaway revise loop. Review the
  *finished* manuscript first; a revision loop is a separate FR once the rubric is
  trusted.
- **Generic `^[A-Z]+:` leak detector.** Rejected (the `regex_fourth_exclusion`
  slide, same as FR-496 J3): match a **configurable, known** label set explicitly;
  a generic stripper would false-positive on legitimate prose.
- **A full Markdown library (e.g. `markdown-it`) for the parse.** Likely
  unnecessary: the book shape is a flat list of H1 sections + a blockquote lead
  (FR-494), so a small line-walker suffices. Reach for a parser library only if a
  fourth section shape appears (`regex_fourth_exclusion`).

## Related

- [examples/book_translator](examples/book_translator) — the sibling example whose layout `book_reviewer` mirrors (text-in/text-out ↔ text-in/evaluation-out)
- [scripts/generate.py](examples/dungeon_master/scripts/generate.py) — produces the `story.md` used as the sample input (no shared code)
- [api/render.py](examples/dungeon_master/api/render.py) — defines the Markdown shape the parser recovers
- [prompts/final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml) / [prompts/synopsis.yaml](examples/dungeon_master/prompts/synopsis.yaml) / [prompts/character.yaml](examples/dungeon_master/prompts/character.yaml) — the craft contracts the rubric dimensions are inspired by
- FR-494 (full-story render), FR-495 (heading dedupe), FR-496 (cast gloss) — the invariants the lint re-asserts from the manuscript side
- **Research:** Lost in the Middle (arXiv:2307.03172), BooookScore (arXiv:2310.00785), FActScore (arXiv:2305.14251), HANNA / Of Human Criteria (arXiv:2208.11646) — the basis for the decomposed map/reduce design
- [docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md](docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md) — the **Seed** (golden-sample regression test) this example realises
- Sample input: `outputs/dungeon-master/sample-courier/story.md` (gitignored; copied into the example as `sample_book.md`)

## Judgment (2026-06-16)

> **SUPERSEDED by the 2026-06-16 decomposition replan — needs re-judge.** The
> rulings below were made against the *single-prompt* plan. The procedural rulings
> still hold and carry forward: **J1** (gate regime — first-class example, no
> CAP/REQ, not under FR-474 J3), **J3** (manuscript-only ground truth — no
> beat-list / no-invention checks), **J4** (no `--no-llm` CLI flag), **J5** (raise
> on zero parsed chapters), **J6** (configurable `leaked-label` set). What changed
> is **J2/the review architecture**: the single `BookReview` LLM node is replaced by
> a decomposed **map (per-chapter) → map (pairwise continuity) → synopsis-beats →
> reduce** pipeline (see Research). The Judge must re-freeze against the new
> architecture.

Scope **frozen**. The plan is internally consistent and minimal except for one
substance error in the rubric, corrected below. Enforce against these rulings.

**J1 — Gate regime: first-class example, no CAP/REQ ceremony.** The premise of the
"Open Question" was wrong on the facts. The sibling `examples/book_translator/` has
**no CAP file and no `@pytest.mark.req` markers**, and `scripts/req_coverage.py`
scopes requirement traceability to the framework's own `tests/`, not `examples/`.
So neither offered option is the precedent. Ruling: `book_reviewer` is a first-class
example carrying **no CAP and no REQ markers** (matching every example except the
self-contained `rtm-hello`, which demos the RTM feature itself). It is **not** the
DM prototype, so it is **not** under the FR-474 J3 exemption and its commits carry
**no** `FR-474 J3` trailer. Commits use honest `feat(book-reviewer): FR-497 …`
types accompanied by a `changelog/unreleased/` fragment and a diary reflection
(the FR-179 / diary gates apply to the *commit type*, not the directory). This
keeps the example "real" without inventing a capability for a demo.

**J2 — Manuscript in, sidecar out, via tools (no bespoke script).** The graph is
pure YAML orchestration over Layer-3 tools: `load_manuscript` (reads the `.md`
path; if a directory, looks for `story.md` inside) → `parse_manuscript` →
`lint_manuscript` → review node → `write_report` (writes `review.md` beside the
manuscript). No `scripts/` wrapper. `BookReview` + `LintReport` are the final
state; `--full` shows them.

**J3 — Rubric must only claim what the manuscript supplies (substance fix).** Two
proposed dimensions — "Plot/beat completeness" (`preserve every canonical BEAT`)
and "Internal consistency" (`COMPOSE, do not invent`) — claimed to verify
generation contracts whose ground truth lives **only in `story.json`** (the hidden
beat list and the played arc), which this example deliberately never reads. A
manuscript-only reviewer has **no ground truth** for "every canonical beat" or "did
not invent". Asserting them is the FR-496-J1 error class: a check the inputs cannot
support, producing a plausible-but-baseless score. The frozen dimension table now
judges **only** manuscript-recoverable properties (synopsis delivery, plot
*coherence*, *internal* consistency, character consistency, cross-chapter
continuity, pacing & climax, prose craft, ending). The dropped contracts survive as
distant inspiration, not claimed checks.

**J4 — No `--no-llm` CLI flag.** `yamlgraph graph run` has no such flag and inventing
one is out of scope (speculative interface — Purge). The deterministic parse + lint
regression check — the realised diary Seed — lives where a regression gate belongs:
the **unit tests**, calling the pure tools directly. The live graph always runs the
full parse → lint → review.

**J5 — Lint is advisory; empty review is forbidden.** Lint never gates the review
(linear graph, issues reported alongside). But a parse recovering **zero chapters**
must **raise**, not emit an empty `BookReview` (Commandment 6 — no plausible-wrong
fallback). A hand-written manuscript missing a tagline/synopsis/cast degrades
gracefully (those fields parse empty); only zero chapters is fatal.

**J6 — `leaked-label` keeps a configurable, explicit label set.** Endorsed as
planned — no generic `^[A-Z]+:` stripper (`regex_fourth_exclusion`), and the
line-walker parse stays until a fourth section shape actually appears.

**Authority granted** to implement under these six rulings. TDD: RED tests for
`parse_manuscript`, `lint_manuscript` (including the deliberately-defective
fixtures and the golden-sample `ok is True`), and the mock-LLM review graph, before
GREEN. The live end-to-end run is captured to a log; the example ships with a
changelog fragment and a diary reflection.
