# Feature Request: Iterable Text Card (Iterate + Accept)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented — GREEN (2026-06-06)
**Effort:** 0.5 day
**Requested:** 2026-06-06

## Summary

Refactor the shared editable-prose component (`text_block.html`) used by the
dungeon-master synopsis and beat views into an **iterable text card**: it shows
the current text in edit mode, adds a small **3-line prompt** textarea, and
exposes two actions — **Iterate** and **Accept**. *Iterate* sends the current
textarea contents plus the prompt to an LLM ("apply `<prompt>` to `<text>`"),
replaces the text with the result, and re-renders the same card. *Accept* keeps
its existing meaning (synopsis → advance to outline; beat → commit prose).

## Value Statement

The DM refines prose conversationally — "make it grimmer", "cut the second
sentence", "add a sensory detail" — instead of hand-editing every change, on one
reusable component shared by synopsis, beats, and any future prose field.

## Problem

The current card is edit-only (autosave). Any rewrite is fully manual. The
synopsis "Regenerate" and the beat "Re-roll" buttons throw the current text away
and start over from the premise/stub — they cannot *revise* what the DM already
has. There is no way to apply a directed change while keeping the existing text
as the base.

## Proposed Solution

One shared `refine` prompt (plain text in, plain text out) and a generalized
`text_block` macro with a prompt textarea + Iterate/Accept row.

```yaml
# examples/dungeon_master/prompts/refine.yaml
system: |
  You are a precise editor. Apply the requested change to the text and return
  ONLY the revised text — no commentary, no labels, no quotes.
user: |
  Change to apply: {{ instruction }}

  Text:
  {{ text }}

  Return only the full revised text.
```

```jinja
{# text_block(field_name, value, hidden, iterate_action, accept_action, accept_label) #}
<form class="text-block-form">
  {# hidden fields #}
  <textarea name="{{ field_name }}" class="text-block">{{ value }}</textarea>
  <textarea name="prompt" rows="3" class="iterate-prompt"
            placeholder="Describe a change…"></textarea>
  <div class="card-actions">
    <button hx-post="{{ iterate_action }}" hx-include="closest form"
            hx-target="#app-body">↻ Iterate</button>
    <button hx-post="{{ accept_action }}" hx-include="closest form"
            hx-target="#app-body" class="primary">✓ {{ accept_label }}</button>
  </div>
</form>
```

Session layer adds a boundary-normalized `_refine(text, instruction)` helper and
two thin methods, `iterate_synopsis(text, prompt)` and
`iterate_beat(chapter, beat, text, prompt)`. An empty prompt degrades to a pure
save (no LLM call), preserving the current autosave behavior. Routes add
`POST /story/synopsis/iterate` and `POST /story/beat/iterate`.

### Scope decisions

- **Drop synopsis "Regenerate".** Iterate ("rewrite from scratch in a new
  direction") subsumes it.
- **Keep planned-beat "Generate".** A planned beat has no text to revise; it
  still uses the richer `weave-beat.yaml`. Once prose exists, the iterable card
  replaces the old "Re-roll" button — Re-roll becomes Iterate.

## Acceptance Criteria

- [ ] `prompts/refine.yaml` returns the full revised text (plain text, no schema).
- [ ] `text_block.html` renders the text in edit mode, a `rows="3"` prompt
      textarea (`name="prompt"`), and an **Iterate** + **Accept** action row.
- [ ] Manual text edits **autosave** on change (`hx-trigger="change"`,
      `hx-swap="none"`); Iterate/Accept use the live (possibly unsaved) textarea
      contents via `hx-include="closest form"` (J1).
- [ ] `POST /story/synopsis/iterate` applies the prompt and persists the revised
      synopsis to `story.json`; the re-rendered card clears the prompt field.
- [ ] `POST /story/beat/iterate` applies the prompt to the woven beat and persists;
      **Iterate always yields status `generated`**, whether the beat was previously
      `generated` or `committed` (J2). Iterate does **not** touch the chapter file.
- [ ] Empty prompt ⇒ pure save (text unchanged, no LLM call/marker).
- [ ] Accept **ignores** the `prompt` field; labels are pinned: synopsis Accept =
      `"Accept"`, beat Accept = `"Accept & commit"` (J3).
- [ ] The macro's `{% call %}` extra-button slot is removed (no remaining caller).
- [ ] Synopsis and beat views share the one component (witness test).
- [ ] Tests added (RED→GREEN), `req_coverage --strict` clean, `lint-imports` KEPT.
- [ ] Demo + `demo-output.log` show an Iterate step; changelog + diary added.

## Judgment (2026-06-06)

**Approved with binding amendments.**

- **J1 — Autosave retained.** The text textarea keeps its `change`/`hx-swap=none`
  autosave from the prior change; Iterate/Accept additionally include the live
  form, so both persist with no conflict. No manual edit is lost on navigation.
- **J2 — Iterate yields a draft.** `append_beat_to_chapter` opens the chapter
  file in append mode, so re-committing a beat would double-append. Ruling:
  Iterate always sets a beat back to status `generated` and never writes the
  chapter file (only Accept does). The broader "Accept of an already-committed
  beat double-appends" defect is **out of scope** here — a separate fix FR.
- **J3 — Accept ignores prompt; labels pinned.** Accept includes the whole form;
  the server ignores `prompt` on the accept path. Synopsis Accept label =
  `"Accept"`, beat Accept label = `"Accept & commit"`. The macro drops its unused
  `{% call %}` slot.

**Frozen scope:** full-text replace only (no diff/patch); no Regenerate, no
Re-roll, no third action; no streaming work beyond an optional cosmetic
`htmx-indicator`.

## Alternatives Considered

- **Separate per-card components** — rejected; the whole point is one shared,
  iterable card.
- **Keep Regenerate alongside Iterate** — rejected; redundant and adds a third
  action to a row the user wants minimal.
- **Inline-diff / patch application** — over-engineered; full-text replace from
  the model is simpler and matches the "apply changes to text" framing.

## Related

- Extends `CAP-170` (Dungeon Master Web UI v2) with new `REQ-YG-471`.
- Builds on FR-470 (synopsis text), FR-472 (beat generation).
- Files: `examples/dungeon_master/api/templates/components/text_block.html`,
  `synopsis_card.html`, `beat.html`, `api/session.py`, `api/routes/story.py`,
  `prompts/refine.yaml`, `tests/unit/test_dungeon_master_web.py`.
