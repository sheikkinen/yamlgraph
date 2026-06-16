# Feature Request: FR-497 — `book-reviewer` stand-alone example

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-16
**Replanned:** 2026-06-16 — a new stand-alone **example** (`examples/book_reviewer/`), not a step in any pipeline

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

## Proposed Solution

A new example directory `examples/book_reviewer/`, structured like
[examples/book_translator](examples/book_translator):

```
examples/book_reviewer/
  README.md            # what it does, how to run
  graph.yaml           # parse → lint → review (LLM) orchestration
  models.py            # ParsedBook, ChapterSection, LintReport, BookReview (Pydantic)
  nodes/
    tools.py           # parse_manuscript + lint_manuscript (pure, no LLM)
  prompts/
    review.yaml        # LLM-judge prompt with inline BookReview schema
  tests/
    test_parse.py      # parse recovers structure from Markdown
    test_lint.py       # lint flags leaks / numbering gaps / empty chapters
    test_review.py     # mock-LLM: graph returns typed BookReview
  sample_book.md       # a captured story.md, the worked example input
```

The graph takes the manuscript text as input state and runs three stages, cheapest
first; nothing mutates the input. The example imports **only** YAMLGraph framework
code — no `dungeon_master` import, no `story.json`.

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

### Stage 2 — Narrative review (LLM-as-judge node)

The `graph.yaml` review node uses `prompts/review.yaml` with an **inline Pydantic
schema** (Commandment 5 — typed output, no untyped dicts). The judge is given the
**parsed** structure — the synopsis (the book's own stated intent), the cast list,
and the ordered chapter bodies — and scores each dimension 1–5 with a justification
and specific issues. The synopsis section stands in for an external premise: it is
the destination the manuscript itself declares, and the rubric asks whether the
chapters deliver it.

```yaml
# prompts/review.yaml (inline schema sketch)
schema:
  name: BookReview
  fields:
    overall: {type: int, description: "1–5 holistic score"}
    verdict: {type: str, description: "one-line summary judgment"}
    dimensions:
      type: list[Dimension]
      description: "per-dimension scores"
# Dimension: {name: str, score: int(1–5), justification: str, issues: list[str]}
```

Dimensions (generic book-review craft, with the DM contract that inspired each):

| Dimension | Origin |
|-----------|--------|
| Synopsis coherence | the parsed `# Synopsis` — chapters deliver the stated outline |
| Plot/beat completeness | `final_cut.yaml` "preserve every canonical BEAT" |
| Internal consistency (no contradiction) | `final_cut.yaml` "COMPOSE, do not invent" |
| Character consistency | the parsed `# Cast` glosses — characters act as introduced |
| Cross-chapter continuity | no fact contradicted between chapter bodies |
| Climax & pacing | `final_cut.yaml` "give each beat weight proportionate" |
| Prose craft | `final_cut.yaml` continuous prose, standing facts stated once |
| Ending | the final chapter resolves the synopsis' promise |

### How to run

The example is run through the framework CLI like any other graph, with the
manuscript path as a variable:

```bash
yamlgraph graph run examples/book_reviewer/graph.yaml \
    --var manuscript_path=outputs/dungeon-master/sample-courier/story.md --full
```

A thin `--no-llm` mode (or a separate `lint`-only invocation) runs parse + lint
alone for the cheap regression check. The typed `BookReview` plus the `LintReport`
are the graph's final state; the example writes a human `review.md` beside the
manuscript. The example is a **sibling** of `book_translator`/`dungeon_master`,
sharing no code with the generator beyond YAMLGraph itself.

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
- [ ] `prompts/review.yaml` defines an **inline Pydantic schema** (`BookReview`
      with `overall`, `verdict`, `dimensions[]`); the rubric dimensions are the
      eight above.
- [ ] `graph.yaml` runs parse → lint → review and the review node returns the typed
      `BookReview` over the parsed synopsis + cast + chapter bodies (verified with a
      **mock-LLM** unit test — no live key).
- [ ] `yamlgraph graph run examples/book_reviewer/graph.yaml --var manuscript_path=…`
      produces a `BookReview` and writes a `review.md`; a `--no-llm` (lint-only) mode
      runs parse + lint alone. A live end-to-end run against the DM
      `sample-courier/story.md` is captured to a log.
- [ ] The example imports **only** YAMLGraph framework code — no
      `dungeon_master`/`session`/`render`/`story_doc` import and no `story.json`
      read (enforced by a test asserting the module's import set, or by the
      reviewer).
- [ ] The review is **advisory** — the example scores and reports; it does not gate
      anything. (A CI quality gate is a separate, later FR.)

## Open Question (for the Judge) — gate regime

`examples/dungeon_master/` is exempt from CAP/REQ/CI gates under **FR-474 J3**.
This FR creates a **new** example *outside* that exemption, so by default
`book_reviewer` would be subject to the normal regime: a `CAP-XXX` capability file,
`@pytest.mark.req("REQ-YG-XXX")` on its tests, a changelog fragment, and a diary
reflection — and `feat`/`fix` commit types would be allowed (and required to
reference this FR). The Judge should decide one of:

1. **Full regime** — treat `book_reviewer` as a first-class example: add a `CAP`,
   REQ-tag its tests, write a changelog fragment, use `feat(book-reviewer): FR-497
   …` commits. (Most consistent with "examples are real"; most ceremony.)
2. **Extend the J3 exemption** — explicitly fold `book_reviewer` under the same
   prototype exemption as `dungeon_master` (it shares the sample and the lineage),
   keeping `docs`/`test`/`refactor`/`chore` commits and no CAP/REQ. (Least ceremony;
   requires an explicit judgment amending FR-474's scope.)

This is left **open for judgment**, not decided here.

## Alternatives Considered

- **Put the evaluator under `examples/dungeon_master/`.** Rejected per the revised
  target: a stand-alone *example* makes the decoupling structural, not just a
  convention — a separate directory cannot import DM internals by accident, and the
  example reads as a reusable "review any book" reference rather than a DM appendage.
- **Single LLM holistic score only.** Rejected: an opaque "7/10" is not actionable
  and cannot catch a mechanical regression (a leaked label) the LLM might gloss
  over. The cheap deterministic parse+lint must run always; the LLM stage adds the
  narrative judgment it cannot.
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
- [docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md](docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md) — the **Seed** (golden-sample regression test) this example realises
- Sample input: `outputs/dungeon-master/sample-courier/story.md` (gitignored; copied into the example as `sample_book.md`)
