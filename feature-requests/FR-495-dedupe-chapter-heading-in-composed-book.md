# Feature Request: FR-495 — Deduplicate the chapter heading in the composed Book

**Priority:** LOW
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-06-16

## Summary

`compose_book_deterministic` heads each played chapter as `# Chapter {n}: {title}`,
but the chapter outline already emits a `title` that begins with its own
`"Chapter N — …"` label. The two stack, producing a doubled heading in the
manuscript:

```
# Chapter 1: Chapter 1 — The Frozen Crossing
# Chapter 2: Chapter 2 — The Fort Defended
```

Observed in the first live stand-alone render (FR-494),
`outputs/dungeon-master/sample-courier/story.md`.

## Value Statement

A reader opening the Book (or the exported `story.md`) sees clean chapter
headings — `# Chapter 1: The Frozen Crossing` — instead of a stuttered
`Chapter 1: Chapter 1 —`, so the deterministic manuscript reads as finished prose.

## Problem

There is **one numbering authority too many**. Two independent sources both
assert the chapter ordinal:

1. The **outline** (`chapter_ops.outline_chapters` → `character_roster.yaml` /
   `chapter_outline.yaml`) writes a free-text `title` that the model tends to
   open with `"Chapter N — "`.
2. The **composer** ([api/chapter_ops.py](examples/dungeon_master/api/chapter_ops.py#L111))
   prepends `# Chapter {n}: ` where `n` is the **position in `chapters.order`**
   (the stable, authoritative ordinal).

When both fire, the label doubles. The composer's `n` is the correct authority
(it stays stable when an earlier chapter is unplayed — see the docstring at
[api/chapter_ops.py](examples/dungeon_master/api/chapter_ops.py#L94)); the title's
self-asserted `"Chapter N — "` prefix is the redundant one and should not survive
into the heading.

This is a **boundary-normalisation** issue: the title is external (LLM-authored)
data whose ordinal claim must be stripped where it enters the heading, not left to
collide downstream.

## Proposed Solution

Normalise the title at the single composition seam — strip a leading
`"Chapter <ordinal><separator>"` prefix from `card["title"]` before interpolating
it, so only the composer's authoritative `n` numbers the chapter.

```python
import re

# A leading "Chapter 1 —", "Chapter 2:", "Chapter Three -", "Ch. 1 –", etc.
_LEADING_CHAPTER_LABEL = re.compile(
    r"^\s*ch(?:apter|\.)?\s+[\w-]+\s*[—–:\-.]\s*",
    re.IGNORECASE,
)

def _clean_chapter_title(title: str) -> str:
    """Drop a self-asserted 'Chapter N —' prefix; the composer owns the ordinal."""
    return _LEADING_CHAPTER_LABEL.sub("", title or "").strip()
```

Then in `compose_book_deterministic`:

```python
title = _clean_chapter_title(card.get("title", ""))
sections.append(f"# Chapter {n}: {title}\n\n{text}")
```

A title with **no** self-asserted prefix (e.g. `"The Frozen Crossing"`) passes
through untouched. A title that is *only* a label (`"Chapter 1"`) collapses to the
bare `# Chapter {n}:` — acceptable; the ordinal is still present once.

> **Scope note:** the doctrine warns against the *fourth* regex special case
> (`regex_fourth_exclusion`). This is the first, and it normalises a single,
> well-bounded prefix at one seam. If the title shapes prove varied enough to need
> a parser, that is a separate escalation — but the deterministic composer is the
> right place to keep this pure (no LLM).

## Acceptance Criteria

- [ ] `compose_book_deterministic` strips a leading `Chapter <ordinal><sep>`
      label from each chapter `title` so the heading reads `# Chapter {n}: {clean}`
      with the ordinal appearing exactly once.
- [ ] A title with no self-asserted prefix is unchanged (`The Frozen Crossing` →
      `# Chapter 1: The Frozen Crossing`).
- [ ] A title that is *only* a label collapses without error (`Chapter 1` →
      `# Chapter 1:` — single ordinal, no trailing junk).
- [ ] `render_story_markdown` inherits the fix automatically (it reuses the
      composer verbatim — FR-494 J3); no second normalisation in `render.py`.
- [ ] Deterministic unit test in `examples/dungeon_master/tests/` covering the
      doubled-label, clean-title, and label-only cases (no live LLM).
- [ ] No change to numbering authority: `n` is still the position in
      `chapters.order`; an unplayed earlier chapter does not shift later numbers.

## Alternatives Considered

- **Fix the prompt** (`chapter_outline.yaml`) to forbid the `"Chapter N — "`
  prefix. Rejected as the *sole* fix: LLM output is untrusted at this boundary —
  the composer must be robust to a re-prefixed title regardless of prompt drift.
  A prompt nudge may accompany the composer fix but cannot replace it.
- **Strip in `render.py`** instead of the composer. Rejected: it would diverge the
  UI Book (which calls the composer directly) from the exported `story.md`. The
  composer is the single shared seam (FR-494 J3) — normalise there.
- **Drop the composer's `# Chapter {n}:` and trust the title.** Rejected: the
  title's ordinal is LLM-authored and can be wrong, missing, or non-monotonic; the
  composer's `n` is the authority.

## Related

- [api/chapter_ops.py](examples/dungeon_master/api/chapter_ops.py#L87-L114) — `compose_book_deterministic`
- [api/render.py](examples/dungeon_master/api/render.py#L66) — reuses the composer body
- FR-492 (deterministic Book), FR-494 (stand-alone render that surfaced this)
- Sample: `outputs/dungeon-master/sample-courier/story.md` (gitignored)
- FR-474 J3: DM prototype exempt from CAP/REQ/CI gates.
