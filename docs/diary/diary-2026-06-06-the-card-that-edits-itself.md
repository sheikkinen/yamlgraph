# The Card That Edits Itself — 2026-06-06 (FR-473)

## What happened

The shared prose card (synopsis, woven beat) became *iterable*: text in edit
mode, a 3-line prompt box, and **Iterate** / **Accept**. Iterate sends the live
text plus the prompt through one generic `refine` prompt — "apply `<prompt>` to
`<text>`" — and swaps the result back in. The synopsis *Regenerate* and beat
*Re-roll* buttons (which threw the current text away) are gone; Iterate subsumes
them by *revising* what's already there.

## The trap the judge caught

The FR said "Iterate keeps status generated" — fine for a generated beat. But the
committed-beat case hid a defect: `append_beat_to_chapter` opens the chapter file
in **append mode**. Wiring the autosave textarea to `/story/beat/accept` (the only
beat write path I had) would have appended the whole beat to the chapter file on
every blur. The cure was a boundary one: separate the *draft* write from the
*commit* write. I added `save_beat` (autosave: persists prose, status `generated`,
no file) and made Iterate also return to `generated`. Only Accept ever touches the
chapter file. The synopsis had no such trap because its autosave route
(`/story/synopsis/edit`) was already a pure document write.

## The seam that made one component serve two masters

Two textareas in one form: the prose (autosaves on `change`, `hx-swap="none"`) and
the prompt (consumed only by Iterate). Both Iterate and Accept `hx-include` the
whole form, so they always act on unsaved edits — but Accept's server param list
simply omits `prompt`, so including it is harmless. That asymmetry — autosave for
the text, explicit action for the prompt, server-side ignore for the irrelevant
field — let a single macro drive synopsis (Accept → outline) and beat (Accept →
commit) with nothing but four URLs and a label.

## Heuristic

> When one write path has two meanings (draft vs. commit), give each its own
> endpoint before wiring any trigger to it. An append-mode side effect behind a
> "save" button is a double-write waiting for a second keystroke.

## Seed

`refine` is a generic "apply an instruction to text" prompt — it has nothing to do
with dungeons. Every prose field in every YAMLGraph example could share it. Should
`refine` (and the iterable `text_block` macro) graduate from `examples/` into a
reusable UI kit, so iterate-on-text is a framework primitive rather than a
dungeon-master one-off?
