# Diary — 2026-06-25 — The cure that did not transfer

## What happened

FR-596 carried a clean hypothesis with a strong precedent: the L5 affect_recall
floor had been lifted by *per-agent decomposition* (FR-590/591) — stop asking one
LLM call to weigh the whole cast's salience at once; instead narrate one character's
arc at a time, encode it, and combine deterministically. L7 was stuck at the same
0.09 floor, model-invariant. The obvious move: transfer the cure. Map
`affect_throughline` over the agents, encode each, `combine_affects`, re-score.

The Judge had already armed the trap's tripwire — correction #1 forced the Gate-1
spike to map over the **GT** agent roster, not `extract_agents`, so a dropped
character could never masquerade as a framing failure. That isolation held: the
agent-coverage ceiling read 1.00. Recall was not roster-capped. And yet the official
gate read **0.09 — flat**. The cure did not transfer.

The sub-axis instrument (correction #2) is what turned a flat KILL into an *attributed*
one. Detection recall (op+char) read 0.55 — the arcs were landing on roughly the
right beats — but precision had **collapsed to 0.03**. Three numbers, one cause:
the LLM emitted 117 deltas against 33 in ground truth. A `Counter` over the GT
fixtures said the rest out loud: every genre authors its entire affect arc on a
single protagonist — Marren, Naima, Brynn, Eira, Mara. **L7 affect is
mono-perspective.** L5 world-state genuinely is multi-agent; L7 affect is one
character's throughline. Mapping over the cast did not surface signal — it
manufactured ~N× noise and buried the protagonist in it.

## The trap

`cure_transfer_without_ontology_check`: a decomposition that healed layer L is
assumed to heal layer L+1 because both share the same failure *number* (0.09) and
the same surface shape (per-beat typed deltas keyed by id). But the cure's validity
rests on the **ground truth's ontology** — *how the property is authored* — not on
the symptom. L5's GT distributes world-state across agents; L7's GT concentrates
affect on one protagonist. Same metric, opposite shape. The recency of the L5 win
(FR-590/591) made the transfer feel inevitable; it was the `working_system_inertia`
of a *neighbouring* success rather than the current one.

## What saved it

Two pre-committed instruments, both demanded by the Judge before any code:

1. **GT-agents isolation** removed the roster confound, so the KILL could only be
   about framing or encoding — not extraction.
2. **Additive sub-axes** decomposed the flat 0.09 into detection 0.55 / precision
   0.03, which is the entire diagnosis. Without them I would have read "0.09, still
   broken, scale the model" — exactly the lever correction #3 forbade. With them,
   the inflated detection (free `char` + over-generation) warned me *not* to read the
   framing as confirmed, and the precision collapse pointed at the cast-flood.

The single permitted in-scope wording iteration was *not* spent. A structural
mismatch (mapping N agents against a 1-protagonist GT) does not yield to prose. The
honest move was to record the attributed KILL and defer the protagonist-throughline
reframing to a new FR that re-enters Plan/Judge — `symptom_patch` avoided, frozen
scope respected.

## Heuristic

> Before transferring a decomposition cure across layers, check the **ground
> truth's ontology**, not the shared symptom. Ask: *does the next layer author the
> property the same way the cured layer did?* L5 multi-agent ≠ L7 protagonist-owned.
> A shared failure number is not a shared failure shape.

If this recurs a third time (a cure assumed-transferable on symptom alone), graduate
`cure_transfer_without_ontology_check` to Scripture under the `evaluation` boundary.

## Seed

The sub-axis instrument earned its keep by separating *detection* from *labeling*.
What if every layer's gate shipped with its decomposition baked in — not a single
recall scalar but a standing (detection / kind / relational) triple — so a flat
score could never again hide which axis is bleeding? Would the next "model-invariant
0.09" have been diagnosable on sight, before a single spike?
