# Feature Request: FR-502 — Resume a partial generation (and the seed of arbitrary-chapter regeneration)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed — awaiting Judgement
**Effort:** 1–2 days
**Requested:** 2026-06-16

## Summary

The headless story generator
([scripts/generate.py](examples/dungeon_master/scripts/generate.py)) always drives
a story **from scratch**: it re-weaves the synopsis, re-derives the cast, re-derives
the chapter outline, and replays every chapter on every invocation — even when a
`story.json` for that session already exists with chapters fully played. Add a
**resume** mode that continues an existing generation from where it stopped:
keep the completed (reviewed) stages, and play only what remains. The same
machinery — "invalidate from chapter K and replay K..N" — is the foundation for a
later **arbitrary-chapter regeneration** (`--from-chapter K`).

## Value Statement

A six-chapter book is expensive: a synopsis call, a cast expansion, a per-character
draft, a chapter outline, and dozens of turn/director/recap LLM calls per chapter.
When generation fails partway (a runaway chapter before FR-501, a provider decline,
a transient API error, an interrupted process), the only recovery today is to throw
away **everything** — including correctly played early chapters — and start over.
Resume turns a partial `story.json` into a checkpoint: chapter 1 played well is
chapter 1 kept, not chapter 1 re-paid for. It also makes iteration on *late*
chapters cheap, which is the precondition for the editor loop (FR-500) and for
regenerating a single weak chapter without disturbing the rest.

## Problem

`generate_story` hard-codes the from-scratch walk and, critically, **re-weaves the
synopsis first**:

```python
await session.weave(text="", prompt=premise)   # overwrites the synopsis…
view = await session.accept()                  # …and re-derives the cast (expand_roster)
while view.stage.startswith("char:"):
    view = await session.accept()              # …and re-derives chapters (expand_chapters)
await session.navigate(f"chapter:{order[0]}")  # …and replays from chapter 1
```

Yet the document already records everything needed to resume:

- `story.json` is the **single source of truth** (FR-474); every entry carries a
  `reviewed` flag and the doc carries the current `stage`.
- `tree.cast_complete(doc)` and `tree.all_chapters_played(doc)` are pure gate
  predicates that already answer "how far did we get?".
- Each played chapter persists its end-of-chapter `world_state` ledger (FR-499A),
  so a later chapter can be played from the prior chapter's carried state **without
  replaying that prior chapter**.
- Per-chapter closure is now bounded (FR-501), so a resumed chapter is as bounded
  as a fresh one.

The information to resume exists; the generator simply never reads it. It is a
boundary defect: the drive loop assumes an empty document instead of inspecting the
one on disk.

Evidence: the run that motivated this FR
(`outputs/dungeon-master/10002-BC/story/story.json`) had chapter 1 fully played
(`reviewed=True`) and chapters 2–5 unplayed. Re-running discards the good chapter 1.

## Proposed Solution

### 1. A pure resume-point classifier

Add a pure function (no I/O, no LLM) that maps a loaded doc to the phase the drive
loop should re-enter:

```python
# resume.py (new, pure — Logic layer)
def resume_point(doc: dict) -> tuple[str, str | None]:
    """Where a drive loop should re-enter an existing story doc.

    ("fresh", None)      — no synopsis yet: drive from the top.
    ("cast",  char_id)   — synopsis ✓, cast incomplete: resume at this character.
    ("play",  cid)       — cast ✓, chapters remain: replay from this chapter.
    ("done",  None)      — every chapter played: nothing to do.
    """
```

Derived entirely from existing predicates: `synopsis.reviewed`,
`next_unreviewed_char`, `cast_complete`, the first chapter whose card is not
`reviewed`, and `all_chapters_played`.

### 2. A clean-chapter resume boundary

A partially-played chapter (turns present, `reviewed=False`) is **reset and
replayed from turn 1**, not continued mid-arc. Rationale: a half-played chapter
carries stale director phase/beat state and (pre-FR-501) possibly dozens of runaway
turns; the deterministic, auditable unit of resume is the *chapter*, not the turn.
Reset clears the first-unreviewed chapter's `turns`, `text`, and `world_state`
before replay. Completed chapters are untouched, and the chapter being replayed
inherits the **persisted** ledger of the chapter before it (FR-499A carry-forward)
— so resume needs no re-derivation of earlier chapters.

### 3. `generate_story(..., resume: bool = False)`

```python
async def generate_story(premise, *, story_root, session_id="story",
                         turn_cap=DEFAULT_TURN_CAP, resume=False) -> dict:
    ...
    if resume and doc_path(story_dir).exists():
        doc = story_doc.read(story_dir)
        phase, where = resume_point(doc)
        # branch: "done" → return; "play" → reset `where`, navigate, play loop;
        #         "cast" → resume cast acceptance then play; "fresh" → fall through
    else:
        # existing from-scratch walk (weave synopsis → cast → play)
```

The play loop itself is unchanged — it already stops on `all_chapters_played` and
is bounded by `turn_cap` (outer) and `CHAPTER_TURN_CAP` (per chapter, FR-501).

### 4. CLI: `--resume`

```bash
PYTHONPATH="$PWD" python examples/dungeon_master/scripts/generate.py \
    --out outputs/dungeon-master/10002-BC --resume          # premise optional on resume
```

On resume, the **persisted synopsis is authoritative**; a `--premise` passed
alongside `--resume` is ignored with a logged warning (the cast and chapters were
derived from the stored synopsis — silently re-deriving from a new premise would
desynchronise the played chapters). When `--resume` is given but no `story.json`
exists, fall back to a fresh run.

### 5. The arbitrary-chapter seed (design only; not built here)

Regenerating chapter K is resume with the resume point **forced**: invalidate
chapters K..N (clear `turns`/`text`/`world_state`/`reviewed`), then run the same
`("play", K)` branch. Because chapter K inherits chapter K−1's persisted ledger,
K−1 need not be replayed. This FR factors the reset+replay machinery so a future
`--from-chapter K` is a thin CLI wrapper over it — but builds **only** the
first-unreviewed resume; the explicit `--from-chapter` is a follow-up FR.

## Acceptance Criteria

- [ ] `resume_point(doc)` returns `fresh` / `cast` / `play` / `done` correctly,
      proven by pure dict-in/tuple-out tests covering: empty doc, synopsis-only,
      partial cast, cast-complete-no-play, partial chapter, all-played.
- [ ] `generate_story(..., resume=True)` on a doc with chapter 1 played and 2–5
      unplayed **keeps** chapter 1's `turns`/`text`/`world_state` byte-for-byte and
      plays only 2–5 (witness over a fixtured doc; no real LLM needed for the
      keep-assertion).
- [ ] A partially-played first-unreviewed chapter has its `turns`/`text`/
      `world_state` reset before replay (no mid-arc continuation, no stale turns).
- [ ] `resume=True` on an already-complete doc returns immediately without any LLM
      call (assert no graph invocation).
- [ ] `resume=True` with a different `--premise` ignores the premise and logs a
      warning; the stored synopsis is unchanged.
- [ ] `--resume` with no existing `story.json` runs a fresh generation.
- [ ] Full DM suite green; the change touches only `examples/dungeon_master/`.
- [ ] Diary + changelog fragment.

## Alternatives Considered

- **Continue a partial chapter from its last turn instead of resetting it.**
  Resumes mid-arc with stale director phase/beat state and (pre-FR-501) a runaway
  tail; the resumed chapter's prose would stitch two generation epochs. Chapter-
  granular resume is cleaner and deterministic. Rejected.
- **A real checkpointer (LangGraph SQLite/Redis).** The story already persists to
  `story.json` as its single source of truth; a second persistence layer duplicates
  state and contradicts the FR-474 doc-is-truth design. The resume point is derived
  from the doc, not a separate checkpoint. Rejected for this scope.
- **Always resume (auto-detect, no flag).** Surprising: a user re-running with the
  same `--out` to regenerate from scratch would silently get the old chapters.
  Explicit `--resume` keeps from-scratch the default. Rejected.
- **Build `--from-chapter K` now.** Broader scope (invalidation policy, ledger
  preconditions for arbitrary K, UI exposure). Resume-from-first-unreviewed is the
  minimal, motivated slice; arbitrary K is a follow-up that reuses this machinery.

## Regime

Prototype-only under FR-474 J3: touches only `examples/dungeon_master/`, adds **no**
CAP file and **no** `@pytest.mark.req` markers, committed with an honest
`feat(dungeon-master): FR-502 …` plus the `FR-474 J3` trailer.

## Related

- FR-474 — `story.json` as the single source of truth (the doc resume reads)
- FR-499A — the persisted per-chapter `world_state` ledger that lets a later
  chapter be played without replaying earlier ones
- FR-501 — per-chapter turn budget; bounds a resumed chapter exactly as a fresh one
- FR-500 — book-editor example; resume/regenerate is the cheap-iteration substrate
  it builds on
- `examples/dungeon_master/scripts/generate.py`, `api/session.py`, `api/tree.py`
  (`cast_complete`, `all_chapters_played`), `api/navigation.py`
  (`next_unreviewed_char`)
- `outputs/dungeon-master/10002-BC/story/story.json` (live partial-doc evidence)
