# Diary — 2026-06-20 — The Backstory That Came Too Early

**FR-550 / FR-551 / FR-552** — rolling back the synopsis-derived World Codex (FR-548), and
re-decomposing its goal into a supporting-cast tier and a sound world bible.

## What happened

Yesterday I judged FR-548 carefully, fixed five mechanical defects in its spec, and shipped it
GREEN. Today the user asked: "should 548 be reversed?" The honest reflex was to defend shipped,
tested work. I ran the causal check instead.

The codex — faction/location backstory derived from the accepted synopsis — had leaked. Roster was
`[hilde, gunnar, arnulf, wenda]`, but the codex named **Reinmar**, a character not in the roster.
Its "factions" included "Wenda's people" and "the combined survivors" — plot groupings, not
institutions. Every breaking character appeared in the codex text. The stage I had judged sound was
authoring an un-precedenced character-state source the continuity witnesses could not see — the exact
multi-source drift FR-534's precedence hierarchy exists to forbid.

The first instinct was a patch: a name-blocklist in `expand_codex` to drop entries naming roster
members. The user's questions pushed deeper — "should backstories be post-processing, different from
action? should cast be regenerated? supporting cast?" — and the patch dissolved under them. The
defect was not content. It was **placement**.

## The trap

`working_system_inertia`, and underneath it a placement blindness I had no name for. "It works"
(390 tests green, length grew 1,400 words) blocked seeing that *where* the stage sat was the bug.
The codex authored **prose, before the action existed, from a plot summary** — the worst corner of
two axes at once:

- **Declaration vs prose.** A names-and-roles declaration is cheap and constrains generation. Prose
  is rich but speculative. The codex chose prose.
- **Pre-action vs post-action.** Pre-action grounding constrains; post-action grounding is additive
  and cannot contradict what it summarizes. The codex chose pre-action.

Prose + pre-action + sourced-from-plot is speculation that can drift from, and leak into, the text
that follows. And the deepest error was the source: **the synopsis IS plot.** Asking a plot summary
for "factions and locations" pulls plot in because plot is all it contains. There was never a clean
world/plot seam to extract at that boundary. The Reinmar leak and the "combined survivors" faction
were not a one-off bug — they were the inevitable output of asking plot to describe a standing world.

## What saved it

Refusing the patch. A name-blocklist would have passed its unit test (`gate_checks_shape_not_substance`)
while leaving a speculative pre-action prose stage in the tree, maintained, still drifting. Reading
the actual pipeline — `doc_ops.expand_roster`, `_normalize_chapter_cast` (which already drops unknown
chapter-cast names), `session.weave`'s synopsis-accept branch — showed the sound shape: declarations
can be speculated cheaply (they only constrain); prose must be either **ground-truth input** or
**post-action grounded**, never pre-action speculation.

That principle decomposed the one bad stage into three sound FRs: **FR-550** removes the codex as a
judged `removal` (not a raw revert — the lesson must be recorded); **FR-551** adds a declared
supporting-cast tier (the coherence lever — it makes the Reinmar leak impossible *by construction*,
because a supporting character is a tracked roster member, and it brings the arc's single most
recurring defect class — non-roster NPCs across 10028/10030/10034 — into deterministic view for the
first time); **FR-552** re-earns the length goal from a sound source, forcing a deliberate choice
between ingested world-bible input and post-action grounding rather than building both and
reproducing the two-masters confusion.

The recurring shape across this whole arc: the cheapest bug is the one killed in the spec, but the
*deepest* bug is the one in the placement — and placement is invisible while the thing still runs.

## The heuristic

**Speculate only on declarations; make prose either ground-truth input or post-action grounded.**
A stage that authors prose ahead of the action it describes, from a source that does not contain the
thing it claims to extract (plot summary → "world"), will drift and leak by construction. When asked
"should this be reversed?", run the causal check before defending — `working_system_inertia` makes
"it works" feel like "it is correct," and they are different claims.

**Seed:** The deterministic witnesses read the committed structured ledger; the reviewer reads prose;
10034-BC showed them in total disagreement (0 gaps vs 7 breaks) because prose can self-contradict
without touching the ledger. If placement is the invisible axis for *features*, is there an
equivalent invisible axis for *detectors* — a witness sitting at the wrong boundary (reading state
when the truth lives in prose), passing its unit test while structurally blind to the headline
defect? What would a witness that reads *both* boundaries and emits their disagreement reveal?
