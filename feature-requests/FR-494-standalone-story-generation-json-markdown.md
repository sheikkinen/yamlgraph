# Feature Request: FR-494 — Stand-Alone Story Generation (headless driver + JSON/Markdown export)

**Priority:** MEDIUM
**Type:** Enhancement (refactor + small feature)
**Status:** Proposed
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
reimplement chapter assembly):

```markdown
# <title from tagline, or "Untitled">

> <tagline>

## Synopsis

<synopsis text>

## Cast            <!-- optional: omitted when the roster is empty -->

- **<name>** — <one-line or first paragraph of the character card>

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

A thin CLI wrapper writes **both** serializations to an output dir:

```bash
python -m examples.dungeon_master.scripts.generate \
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

- [ ] `render_story_markdown(doc)` exists, is **pure** (no LLM, no I/O), and
      renders title/tagline + synopsis + (optional) cast + the Book body, where
      the Book body is `compose_book_deterministic(doc)` reused verbatim.
- [ ] `render_story_markdown` **raises** (not `""`) when no chapter is played, and
      never emits the `world_state` ledger.
- [ ] A deterministic unit test renders a fixture doc and asserts the front
      matter + chapter headings + the absence of `world_state` (no live LLM).
- [ ] `generate_story(premise, *, story_root, session_id, turn_cap)` exists,
      drives synopsis → cast → play → Book gate **through the adapter only**, and
      uses `tree.all_chapters_played` as its stop condition (no duplicated
      per-turn `scene_complete` walk).
- [ ] `generate_story` raises when the Book gate does not open within `turn_cap`.
- [ ] A CLI entry point (`python -m …scripts.generate --premise … --out …`)
      writes both `story.json` and `story.md` to the `--out` dir.
- [ ] `witness_book_compose.py` calls `generate_story` and contains **no**
      `doc["chapters"]["cards"]…` drive-loop walk; it keeps its substance asserts
      and `sys.exit(1)`-on-FAIL.
- [ ] Docs updated: architecture module map gains a `render.py` row and names the
      generator; README mentions the stand-alone generation command.
- [ ] Diary reflection + **Seed**.

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

## Affected Files

- `examples/dungeon_master/api/render.py` (new — pure full-story Markdown)
- `examples/dungeon_master/api/chapter_ops.py` (reused, unchanged — Book body)
- `examples/dungeon_master/scripts/generate.py` (new — headless driver + CLI)
- `examples/dungeon_master/scripts/witness_book_compose.py` (thinned to a caller)
- `examples/dungeon_master/tests/test_render.py` (new — deterministic render test)
- `examples/dungeon_master/docs/architecture.md`, `README.md` (module map + usage)
- `docs/diary/` (reflection + Seed)
