# Feature Request: FR-496 — Cast lines leak the `SUMMARY:` field scaffolding

**Priority:** LOW
**Type:** Bug
**Status:** Implemented (2026-06-16)
**Effort:** 0.5 days
**Requested:** 2026-06-16

## Summary

The `# Cast` section of the full-story render emits each character's first card
paragraph verbatim — which, for a DM character card, is the literal
`SUMMARY: …` labeled field. The reader sees the field scaffolding, not prose:

```
- **Kaelen Vance** — SUMMARY: A military courier who must deliver a warning…
- **Marcus** — SUMMARY: An enemy scout lieutenant who wants to eliminate couriers…
- **Orla Thorne** — SUMMARY: Commander of Fort Solitude who must defend…
```

Observed in the first live stand-alone render (FR-494),
`outputs/dungeon-master/sample-courier/story.md`.

## Value Statement

The reader-facing cast list reads as a clean one-line gloss per character —
`**Kaelen Vance** — A military courier who must deliver a warning…` — instead of
exposing the internal `SUMMARY:` field label from the character sheet.

## Problem

The character card is, by design, a **dry labeled character sheet**, not prose:
`character.yaml` instructs the model to return
`SUMMARY: / ROLE: / ORIGIN: / APPEARANCE: / …` with
"EXACT uppercase section labels" (see
[prompts/character.yaml](examples/dungeon_master/prompts/character.yaml#L11-L26)).

`render._cast_lines` ([api/render.py](examples/dungeon_master/api/render.py#L25-L43))
takes the **first `\n\n`-split paragraph** of that sheet (FR-494 J2). For a sheet,
that first paragraph *is* the `SUMMARY:` line — so the render faithfully reproduces
the field label. The render did exactly what it was judged to do; the mismatch is
that **"first paragraph of a prose card" and "the SUMMARY field of a sheet card"
are not the same thing**, and the cast gloss wants the latter's *value*.

This is a **boundary-shape** issue: the card's structure (labeled fields) is known
at the point the cast line is built, so the `SUMMARY:` value should be extracted
there rather than the whole first paragraph passed through with its label.

## Proposed Solution

In `_cast_lines`, prefer the **value of the `SUMMARY:` field** when the card is a
labeled sheet; fall back to the first paragraph for a plain-prose card (so the
function stays general and the existing FR-494 tests still hold).

```python
def _summary_gloss(text: str) -> str:
    """The card's one-line gloss: the SUMMARY field value if labeled, else the
    first paragraph. Drops the 'SUMMARY:' label — it is sheet scaffolding, not
    manuscript."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("SUMMARY:"):
            return stripped[len("SUMMARY:"):].strip()
    return text.split("\n\n", 1)[0].strip()
```

Then:

```python
gloss = _summary_gloss(text)
lines.append(f"- **{name}** — {gloss}")
```

A plain-prose card (no `SUMMARY:` label) is unchanged — it still uses its first
paragraph. A labeled card contributes only the summary *value*.

## Acceptance Criteria

- [x] A character card whose `text` is a labeled sheet (`SUMMARY: …\nROLE: …`)
      renders as `- **Name** — <summary value>` with **no** `SUMMARY:` label and
      none of the other fields (`ROLE:`, `APPEARANCE:`, …).
- [x] A character card whose `text` is plain prose (no `SUMMARY:` label) is
      unchanged — still its first `\n\n` paragraph (FR-494 J2 preserved).
- [x] Empty-card and empty-roster behaviour is unchanged (cards/sections still
      drop — FR-494 J2).
- [x] The match is case-insensitive on the `SUMMARY:` label and tolerant of
      leading whitespace.
- [x] Deterministic unit test in `examples/dungeon_master/tests/test_render.py`
      covering the labeled-sheet, plain-prose, and label-absent cases (no live LLM).

## Alternatives Considered

- **Render all sheet fields as sub-bullets** (`SUMMARY / ROLE / DRIVE …`). Rejected
  for the cast gloss: the front-matter cast is a *one-line who's-who*, not the full
  character sheet. The full sheet already lives in `story.json` for anyone who
  wants it. (A richer "dramatis personae" could be a separate FR.)
- **Strip every `LABEL:` prefix generically.** Rejected as over-engineered for the
  cast line — only the `SUMMARY` value is wanted; a generic field-stripper invites
  the regex-special-case slide. Extract the one field that is the gloss.
- **Change `character.yaml` to emit prose.** Rejected: the dry labeled sheet is a
  deliberate, reusable design (`character_roster` / downstream consumers depend on
  the labeled shape). The render must adapt to the card, not the card to the render.

## Related

- [api/render.py](examples/dungeon_master/api/render.py#L25-L43) — `_cast_lines`
- [prompts/character.yaml](examples/dungeon_master/prompts/character.yaml#L11-L26) — the labeled sheet contract
- FR-494 J2 (cast line = first paragraph; this refines it for labeled sheets)
- Sample: `outputs/dungeon-master/sample-courier/story.md` (gitignored)
- FR-474 J3: DM prototype exempt from CAP/REQ/CI gates.

## Judgment (2026-06-16) — scope frozen

The cure is correct, but the **diagnosis understates the leak** — the Judge
resolves the factual error before freezing.

- **J1 — Factual correction: the whole sheet leaks, not just the `SUMMARY:` line.**
  The FR says "that first paragraph *is* the SUMMARY line." In the live sample the
  cast bullet carried `SUMMARY:` **and** `ROLE:`, `ORIGIN:`, `APPEARANCE:`, … —
  the *entire* sheet. Cause: the character sheet is **single-`\n`-separated** (no
  blank-line paragraph break), so `text.split("\n\n", 1)[0]` returns the whole
  sheet, not a one-line paragraph. The proposed `_summary_gloss` (extract the
  `SUMMARY:` field value) is the correct cure either way, and the existing AC
  "with **no** `SUMMARY:` label and none of the other fields" already encodes the
  true requirement. No change to the cure; the problem statement is corrected.
- **J2 — `SUMMARY` is a single-line value; stop at end-of-line.** `character.yaml`
  contracts `SUMMARY: one sentence`. Extract the `SUMMARY:` line's remainder to
  end-of-line. A multi-line/wrapped `SUMMARY` is not in the contract; do not build
  a field-spanning parser for a hypothetical shape (`regex_fourth_exclusion`).
- **J3 — One field, not a generic label stripper.** Match only `SUMMARY:`
  (case-insensitive, leading-whitespace tolerant). Do **not** add a general
  `^[A-Z]+:` stripper — that is the regex-special-case slide the FR already
  rejected, and it would silently mangle a plain-prose card that happens to start
  with an uppercase clause.
- **J4 — Plain-prose fallback preserves FR-494 J2.** When no `SUMMARY:` line is
  present, fall back to the first `\n\n` paragraph unchanged, so the existing
  FR-494 render tests (prose-card cast lines) stay green. The frozen test set adds
  the labeled-sheet case and a label-absent (plain-prose) case asserting the
  fallback.
- **J5 — Render adapts to the card; the sheet stays a sheet.** No change to
  `character.yaml`. The labeled sheet is the deliberate, reusable contract; the
  render extracts the gloss it needs.

**Frozen acceptance** = the FR's five criteria as written (they already require
"none of the other fields", which J1 confirms is the real target). The problem
statement is corrected per J1: the leak is the whole sheet because the sheet has
no `\n\n` break.

Status: Proposed → Judged (scope frozen).
