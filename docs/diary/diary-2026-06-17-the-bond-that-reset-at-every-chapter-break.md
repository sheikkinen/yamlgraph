# The Bond That Reset at Every Chapter Break

**Date:** 2026-06-17
**Context:** FR-513 enforcement (emotional state in the DM v2 world ledger)
**Incident:** Run 10019's book review found four continuity breaks — all emotional,
not mechanical. Lovers re-met as strangers; an alliance's tension-keeper vanished;
a resurrection had no bridge. The seam carried inventory and lifecycle perfectly,
yet relationships evaporated at the chapter boundary.

## The Trap

The world_state ledger already crossed chapter boundaries with `characters`,
`objects`, and `facts`. Mechanical continuity was airtight — dead stayed dead,
the wedged slab stayed wedged. So the seam *felt* complete.

But relationships were never *state*; they were *inferred* — derived each turn
from which characters happened to share the context window. When Ch3 turn-1 ran,
it saw "Hilde and Gunnar both alive at location X" and produced two functional
units, because nothing on the ledger said "lovers." The emotional arc restarted
from proximity every chapter.

The tempting fix was downstream: teach the turn loop to re-derive relationships
from recap history. That puts complex inference at the point where the symptom
shows, not where the data enters.

## The Cure: The Boundary Already Existed

The seam between chapters is the boundary. world_state is already "important state
the next chapter inherits." Relationships are important state — proven by the
review. So they belong *in the ledger*, extracted once at chapter close, grounded
in recap citations, and carried forward typed.

Three boundary decisions made it robust rather than a new hallucination vector:

1. **Grounding at parse, not at prompt.** `parse_world_state` drops any bond
   without `recap_citations` (or with fewer than two parties). The prompt *asks*
   for citations, but the boundary *enforces* them. A model that forgets to cite
   loses the bond — it cannot smuggle an invented romance into state.

2. **One ledger, two views.** The same `format_world_state` renders `"all"`
   (status-labelled — close carry-forward, so dormant bonds survive for revival)
   and `"active"` (compact, dormant/archived excluded — turn context, so stale
   tensions don't bloat or misdirect play). The selector lives at the formatter,
   not in two parallel ledgers.

3. **Compact prose, never a dict.** Turn context reads
   "Hilde and Gunnar: romantic_bond (tensions: clan_feud, public_secrecy)" — the
   same purity rule the structured ledger already obeyed (no `{'between'...}`
   leaking into a prompt or the manuscript).

## The Heuristic

When a quality defect is "X resets across a boundary," the question is never
"how do I re-derive X downstream?" It is "is X state, and does the boundary carry
it?" If the boundary carries inventory but not the thing that resets, the thing
that resets is also state — it was just implicit. Make it explicit at the seam,
ground it at the parse, and render it per-consumer.

**Seed:** Grounding is enforced for relationships (citations or drop). The
`facts` and `objects` arrays have no equivalent grounding gate — a close LLM can
still assert a fact the recaps never showed. Should *every* forward-carried ledger
field require a recap citation, turning world_state into a uniformly grounded
boundary rather than one with a single guarded lane?
