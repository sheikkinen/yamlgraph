# The Field That Was Never Read — 2026-06-06 (FR-470 follow-up)

## What happened

After the DM web UI v2 redesign shipped (synopsis → outline → beat), a granularity
question surfaced a smell hiding in plain sight: the synopsis was authored,
stored, edited, and rendered as **five structured fields** (logline, conflict,
themes, tone, arc) — but every downstream consumer (the plot, chapters, and cast
prompts) only ever interpolated `{{ synopsis }}` as **one opaque blob**. Worse,
because `state.synopsis` was a dict, that blob rendered as a Python `repr` inside
the prompts the model actually read.

So the five-field structure existed for exactly one consumer — the UI — and even
there it was ceremony: the DM just wants to read and reshape a paragraph. The fix
collapsed synopsis to a single prose string end to end: prompt emits a paragraph,
the preplan node stops parsing it as JSON (`parse_json: false`), `SynopsisView`
becomes `text: str`, and the edit route takes one `text` field. The downstream
Python-repr smell vanished as a free side effect.

## The trap

**Structure as default.** When the synopsis was first designed, "a synopsis has a
logline and themes and a tone" felt obviously true, so it got a schema. But schema
is a cost you pay at every boundary it crosses — generation, storage, the edit
form, five `name="…"` inputs, a `_themes` normalizer, and a view model with five
defaults. None of that structure was ever *consumed* structurally. The granularity
of a data shape should be set by its **consumers**, not by what feels well-modeled
in the abstract. Here the only structural consumer was a form I wrote myself, so
the structure was self-justifying — a closed loop of ceremony.

## The reuse that paid for itself twice

The same edit revealed a second instance of the boundary principle. The woven-beat
view already had a full-height parchment editor (`.beat-card` filling the
`dm-stage`). The synopsis needed exactly that — "make it consume height like the
beat view," as the request put it. Instead of duplicating the textarea + form +
actions, I extracted a `text_block` Jinja macro and pointed both views at it.
One component, two callers, identical height behavior — and the witness test
asserts the *same* `class="text-block"` renders in both the synopsis card and a
generated beat, so the sharing can't silently drift apart.

## Heuristic

> Let the consumer set the granularity. A data shape with five fields and one
> opaque consumer is four fields of cost and zero fields of benefit. Before adding
> structure, ask: who reads it structurally? If the answer is "only the form I'm
> about to write," store the plain value.

## Seed

The synopsis went from dict to string because no consumer needed the parts. How
many other `parse_json: true` nodes in the example graphs produce structured
state that is only ever re-serialized into a downstream `{{ var }}` blob? A lint
that flags "structured state_key consumed only as a flat template variable" could
turn this one-off insight into a mechanical smell detector.
