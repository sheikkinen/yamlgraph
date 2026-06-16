# Feature Request: FR-494 — Stand-Alone Story Generation (headless driver + JSON/Markdown export)

**Priority:** MEDIUM
**Type:** Enhancement (refactor + small feature)
**Status:** Implemented (2026-06-16)
**Effort:** 1 day
**Requested:** 2026-06-16
**Regime:** FR-474 J3 (DM prototype) — no CAP/REQ/CI-gates/changelog; diary required.

## Summary

Lift the witness's end-to-end **drive loop** into a reusable, headless
**story generator**, and give it two first-class serializations of the finished
story: the canonical machine `story.json` (already the source of truth) and a new
deterministic, human-readable `story.md` manuscript. The live witness
(`witness_book_compose.py`) becomes a thin caller of that generator — it stops
owning the drive loop and the intimate doc-shape walk, and keeps only its
substance assertions.

## Value Statement

A reader (or a downstream tool) gets a finished story as a publishable Markdown
document and as structured JSON from one headless command; the witness gets
smaller and the "how to drive a complete generation" knowledge gets a home that
is reused, not duplicated.

## Problem

The only code that sequences a *complete* story end-to-end —
synopsis → derive cast → accept each character → play every chapter to its
director-judged `scene_complete` → reach the Book gate — lives **inside**
`examples/dungeon_master/scripts/witness_book_compose.py`. Two costs follow:

1. **The drive loop is not reusable and the artifact is discarded.** The witness
   generates a whole novel into a `tempfile.mkdtemp` dir, prints 240-char
   fragments to stdout, and exits. There is no `generate me a story` entry point,
   and no human-readable output — only the machine `story.json` and console noise.
   The deterministic Book text (`compose_book_deterministic`) is computed only to
   be substring-checked, never written anywhere a reader could open it.

2. **The witness duplicates doc-shape knowledge the adapter already owns.** The
   drive loop reaches into `doc["chapters"]["cards"][cid]["turns"][n-1]["direction"]`
   and re-reads `story_doc` on every iteration to decide whether to keep accepting.
   That is the same `inventory_by_visibility` / duplication trap FR-466 just
   pruned elsewhere: a second copy of the play-loop's stop condition, drifting
   independently of `tree.all_chapters_played` and the adapter's own accept logic.

There is also no **full-story** Markdown rendering. `compose_book_deterministic`
renders only the played chapters' prose (`# Chapter N: title` + body). The
tagline, the synopsis, and the cast — everything the JSON holds — never reach a
reader-facing document.

## Proposed Solution

Two deliverables, split along the deterministic-vs-generative seam line the DM
example already enforces.

### Part 1 — `render_story_markdown(doc) -> str` (deterministic seam; pure)

A new pure function that renders the **whole** story doc as one standalone
Markdown manuscript — the human serialization beside the machine `story.json`.
No LLM, no I/O; unit-testable from a fixture doc (a visibility harness under the
J3 regime). Proposed location: a new `examples/dungeon_master/api/render.py`
(Adapter layer, pure reads) so `chapter_ops` is not bloated with presentation.

Shape (reuses `compose_book_deterministic` for the body — does **not**
reimplement chapter assembly). There is **no invented title** (the doc has no
title field; the tagline is a whole paragraph — see J1): the manuscript opens
with the tagline as a blockquote lead and renders all top-level sections at the
same H1 level the Book body already uses.

```markdown
> <tagline>

# Synopsis

<synopsis text>

# Cast            <!-- optional: omitted when the roster is empty -->

- **<name>** — <first paragraph of the character card>

---

# Chapter 1: <title>

<final prose>

# Chapter 2: <title>

<final prose>
```

- The **Book body** is `compose_book_deterministic(doc)` verbatim — one source of
  truth for chapter assembly. `render_story_markdown` only frames it with the
  front matter (title/tagline/synopsis/cast).
- It **raises** (not returns `""`) when no chapter has been played, mirroring
  `compose_book_deterministic` (Commandment 6: no silent fallback). The front
  matter alone is not a "story".
- The `world_state` forward-carry ledger never appears (it is plumbing, exactly
  as in the Book compose).

### Part 2 — headless generator + CLI (the extracted drive loop)

Extract the witness's drive loop into a reusable async function — proposed
`examples/dungeon_master/scripts/generate.py`:

```python
async def generate_story(
    premise: str,
    *,
    story_root: Path,
    session_id: str = "story",
    turn_cap: int = 24,
) -> dict:
    """Drive a DMSession to a complete book and return the finished doc.

    Synopsis → accept cast → play every chapter to scene_complete → Book gate.
    Persists story.json via the adapter (single source of truth). Raises if the
    book gate does not open within turn_cap (no half-finished story masquerading
    as done).
    """
```

The driver sequences the **same adapter methods the HTTP routes call**
(`weave` / `accept` / `navigate`) — it adds no new doc-shape coupling. Its stop
condition is `tree.all_chapters_played(doc)`, the existing public gate, not a
hand-rolled per-turn `scene_complete` walk.

A thin CLI wrapper writes **both** serializations to an output dir, invoked the
same way the witness is (direct script path, not `-m` — see J4):

```bash
PYTHONPATH="$PWD" python examples/dungeon_master/scripts/generate.py \
    --premise "A lone courier crosses a frozen river…" \
    --out outputs/dungeon-master/courier \
    --turn-cap 24
# writes outputs/dungeon-master/courier/story.json   (machine, via the adapter)
#        outputs/dungeon-master/courier/story.md      (reader, render_story_markdown)
```

### Part 3 — witness becomes a thin caller

`witness_book_compose.py` is rewritten to:

1. `doc = await generate_story(PREMISE, story_root=tmp, turn_cap=TURN_CAP)`
2. Run only its **substance asserts** against the returned doc and the two pure
   renders (`compose_book_deterministic`, `render_story_markdown`): book
   non-empty, every chapter heading present, `world_state` not leaked, the
   Markdown front matter present.

The witness keeps its `sys.exit(1)`-on-FAIL honesty (FR-492 hardening) but sheds
the drive loop and the `doc["chapters"]["cards"]…` walk.

## Acceptance Criteria

- [x] `render_story_markdown(doc)` exists, is **pure** (no LLM, no I/O), and
      renders the tagline (blockquote lead, **no invented title** — J1) +
      `# Synopsis` + optional `# Cast` + the Book body, where the Book body is
      `compose_book_deterministic(doc)` reused verbatim and all top-level
      sections sit at H1 (J1).
- [x] `render_story_markdown` lets the `compose_book_deterministic` raise
      propagate when no chapter is played (J3 — no second guard, no `""`), and
      never emits the `world_state` ledger.
- [x] Each cast line is `**name** — <first \n\n-split paragraph of the card
      text>`; a character with empty card text is omitted, and the whole `# Cast`
      section is omitted when the roster is empty (J2). Deterministic, no LLM.
- [x] A deterministic unit test renders a fixture doc and asserts the front
      matter + chapter headings + the absence of `world_state` (no live LLM).
- [x] `generate_story(premise, *, story_root, session_id, turn_cap)` exists,
      drives synopsis → cast → play → Book gate **through the adapter only**, and
      uses `tree.all_chapters_played` as its stop condition (no duplicated
      per-turn `scene_complete` walk).
- [x] `generate_story` raises when the Book gate does not open within `turn_cap`
      (no partial doc returned — J5).
- [x] A CLI entry point — `PYTHONPATH="$PWD" python
      examples/dungeon_master/scripts/generate.py --premise … --out …` (direct
      script path, not `-m`; `load_dotenv()` inside `main()` — J4) — writes both
      `story.json` and `story.md` to the `--out` dir. No new `__init__.py`.
- [x] `witness_book_compose.py` calls `generate_story` and contains **no**
      `doc["chapters"]["cards"]…` drive-loop walk; it keeps its substance asserts
      and `sys.exit(1)`-on-FAIL (J5).
- [x] Docs updated: architecture module map gains a `render.py` row and names the
      generator; README mentions the stand-alone generation command.
- [x] Diary reflection + **Seed**.

## Alternatives Considered

- **Book-only Markdown (no front matter).** `compose_book_deterministic` already
  emits the chapter prose; we could just write *that* to `.md`. Rejected as the
  primary path: the JSON holds the tagline, synopsis, and cast, and "both json
  and markdown version" implies parity — the Markdown should be the whole story a
  reader opens, not only the chapter bodies. (The Book-only string remains
  available as the body the renderer frames.)
- **Put `render_story_markdown` in `chapter_ops`.** Rejected: `chapter_ops` owns
  chapter *graph calls* and the Book assembly; full-story presentation spanning
  synopsis + cast is a distinct concern. A dedicated pure `render.py` keeps
  `chapter_ops` from drifting over the size gate (FR-493's lesson).
- **An LLM voice/continuity pass over the assembled book.** Out of scope — that is
  the deferred FR-492 Phase 4 revision seam. This FR composes deterministically
  only; the generator emits the *first* book, never a model-revised one.
- **A FastAPI "export" route instead of a CLI.** Deferred. The HTTP surface stays
  the interactive workbench; stand-alone generation is a headless concern and the
  witness already runs from the command line.

## Out of Scope (deferred — return to Plan if desired)

- LLM revision of the assembled manuscript (FR-492 Phase 4).
- Any new persisted `book` or `markdown` entry in `story.json` — the Markdown is
  **derived on demand**, exactly like the Book (FR-492: no stored book).
- PDF/EPUB or other export formats; per-chapter file splitting.
- Parameterising character/chapter counts at generation time (still emergent).

## Judgment (2026-06-16) — scope frozen

The plan is sound and minimal; three ambiguities and one factual defect are
resolved below. Scope is frozen to Parts 1–3.

### J1 — No invented title; flat H1 hierarchy (kills a deterministic title heuristic)

The doc has **no title field**, and `doc["tagline"]` *is* the premise — a whole
paragraph ([session.py L228–L230](../examples/dungeon_master/api/session.py#L228-L230)).
Deterministically "deriving a title from the tagline" means extracting a title
from prose with no LLM — a `plausible_wrong_answer` heuristic that will look right
and read wrong. **Ruling:** render no `# <title>`. The manuscript opens with the
tagline as a blockquote lead (no heading), then `# Synopsis`, optional `# Cast`,
a `---` rule, then the Book body. All top-level sections sit at **H1** — the same
level `compose_book_deterministic` already emits for chapters — so the body is
reused verbatim (J3) without demoting its headings. The plan's original
`# title` + `## Synopsis` example (H2 synopsis above H1 chapters) was an inverted
hierarchy and is struck.

### J2 — Cast line is the first paragraph; empty cards and empty rosters drop out

Each cast entry is `**<name>** — <first \n\n-split paragraph of the card text,
stripped>`. A character whose card `text` is empty is omitted (not a dangling
bullet); the whole `# Cast` section is omitted when the roster is empty. Pure,
deterministic — no LLM summarisation of the card.

### J3 — Reuse, don't reimplement; inherit the raise

The Book body is `compose_book_deterministic(doc)` **verbatim**;
`render_story_markdown` only prepends the front matter. The renderer adds **no**
second "no chapter played" guard — it lets the existing `ValueError` propagate
(Commandment 6, one source of truth). The front matter alone is not a story.

### J4 — CLI matches the witness invocation, not `-m` (factual defect fixed)

`examples/dungeon_master/` and `scripts/` are **not packages** (no `__init__.py`);
the witness runs as a direct script path under `PYTHONPATH="$PWD"`. **Ruling:** the
generator CLI is invoked the same way —
`PYTHONPATH="$PWD" python examples/dungeon_master/scripts/generate.py …` — **not**
`python -m …`. No new `__init__.py` or package layout is introduced. `load_dotenv()`
is called **inside `main()`** (not at module top) so imports stay top-level and no
E402 noqa-confession is needed (the witness already dodges this the same way).

### J5 — One drive loop, owned by the generator; raise on cap, never a partial doc

`generate_story` is the **single** owner of the synopsis→cast→play→Book sequence.
Its stop condition is the public `tree.all_chapters_played`; when `turn_cap` is
reached before the gate opens it **raises** (it does not return a half-played doc
that a caller might mistake for finished). `witness_book_compose.py` is rewritten
to call `generate_story` and retain **only** its substance asserts +
`sys.exit(1)`; no `doc["chapters"]["cards"]…` walk survives in the witness.

### J6 — Markdown is derived, never stored

No new `story.json` field. `story.md` is written by the CLI from
`render_story_markdown` on demand and is regenerable — mirroring FR-492's
no-stored-book rule. The JSON stays the single source of truth.

### J7 — Pure render is unit-tested; live generation stays witness-only

`test_render.py` is the J3-regime visibility test for the pure renderer (no
markers, no req). The live end-to-end generation is exercised by the **witness**,
not a mocked unit test — a mocked end-to-end would be the `mock_escape_hatch`
(a unit test wearing an E2E costume). The generator's wiring is proven live.

**Authority granted.** Proceed RED→GREEN: the pure `render.py` + `test_render.py`
first (deterministic, fast), then the `generate.py` extraction, then thin the
witness, then docs + diary.

## Affected Files

- `examples/dungeon_master/api/render.py` (new — pure full-story Markdown)
- `examples/dungeon_master/api/chapter_ops.py` (reused, unchanged — Book body)
- `examples/dungeon_master/scripts/generate.py` (new — headless driver + CLI)
- `examples/dungeon_master/scripts/witness_book_compose.py` (thinned to a caller)
- `examples/dungeon_master/tests/test_render.py` (new — deterministic render test)
- `examples/dungeon_master/docs/architecture.md`, `README.md` (module map + usage)
- `docs/diary/` (reflection + Seed)
