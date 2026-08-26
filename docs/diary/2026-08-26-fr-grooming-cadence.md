# 2026-08-26 — Grooming is a rung, not a board read

**The operator's observation:** FR volume and content now exceed what
one human can hold in working memory. Ideas are filed as sparks that
made sense in the moment of filing; the spark's context evaporates
faster than the FR queue drains. The problem is sharpened, not eased,
by the fix for agent slowness — a single FR takes an agent hours to
enforce, so multiple agents run in parallel, which multiplies the
number of things filed and finished per unit of human attention rather
than reducing it. Throughput and trackability moved in opposite
directions from the same change.

**This is a recurrence, not a new finding.** `the-board-nobody-read`
(2026-07-16) proved `docs/fr-board.md` shipped with a write-side gate
and zero read-side integration — a view without a reader. `the-human-
skims` (same day) named the deeper shape: documents in this repo are
written for the next agent, not the human, and the human's actual
interface must be a tiny decision-shaped surface, front-loaded with
verdicts and open decisions. Today's instance narrows the claim
further: the missing rung isn't "a board exists," it's "grooming
happens at a scheduled MOMENT" — specifically session-END, once per
implementation pass, not on-demand when someone remembers to look.
`now.py` already owns session-START. Nothing owns session-END. Three
sightings of the same species (board, skim, cadence) is the threshold
this repo's own doctrine sets for graduation
(`diary_graduation_pipeline`) — noted, not yet acted on; the fourth
sighting is the trigger, or a deliberate FR now to preempt it.

**Trap named:** `attention_is_the_scarce_resource_not_compute` — the
system optimizes the wrong side of the ledger. Filing an FR costs an
agent minutes; grooming it costs the human seconds *if* the recap is
handed to them at the right moment, and costs them the whole idea's
context *if* it isn't. Parallelizing agents was the correct fix for
agent latency and the wrong fix for human trackability — it treated
the two as one problem.

**Heuristic:** end every implementation session with a recap, not a
report — 2-3 lines: what shipped, what's next, what's gone stale.
Never leave "check the board" as the retrieval mechanism for a human;
push the delta to them at the exact moment their attention is already
on the work. A recap that must be sought out is a diary entry that
will never be read, which is the same failure as the board.

## Seed

A session-end script/node that diffs `fr-board.md` against its state
at session start and emits the 2-3 line recap (shipped / next /
stale) as the LAST thing printed before context ends — not a new
document, an extension of the existing board generator's output. If
it survives one week of actual use, wire it into the session-end
convention repo-wide; if unused, the seed was cheaper than the
feature.
