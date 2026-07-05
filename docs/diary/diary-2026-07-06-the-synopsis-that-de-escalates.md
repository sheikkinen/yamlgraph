# The Synopsis That De-Escalates

**Date:** 2026-07-06
**Context:** novel_fandom canon graded as a *story* (not as data) — "is the book worth writing / reading?"
**Trap:** candidate — `conflict_dissolution_bias`: LLM-generated plot resolves every tension in the direction of least resistance; the shape of a story survives, the pressure does not

## The Observation

Two consecutive reviews of the same 47-entity canon, one day apart:

- **Yesterday** (vertical depth, horizontal silence): the *data* review. Schema 100% valid, references 100% resolved, timeline coherent. Verdict: structurally complete, narratively unconnected.
- **Today**: the *story* review. Grade B−. The premise clears the bar (Njáls saga inverted — a feud narrative where the feud is what dies), the ledge crucible works, the saga voice is right, Arnulf is a genuinely good structural decision. And yet the book is not worth reading in its current shape.

The diagnosis is one sentence: **every conflict dissolves; none is defeated.**

- Heidrun speaks and knots untie. She is plot-solvent, not character.
- The camp splits twice; nobody with a grievance ever acts on it.
- The climax — Arnulf's three silent days and his dawn walk to the lake — happens off-page, unwitnessed, unmotivated.
- Two children and Berno die in one paragraph of summary. Costs are stated, not felt.
- The canon confirms it mechanically: zero characters carry `role: antagonist`.

## The Diagnosis

This is the *narrative* face of `plausible_wrong_answer`. The synopsis passes every shape check a pipeline can run: conflict introduced ✓, conflict resolved ✓, arc completed ✓, themes present ✓. But an LLM asked to continue a story reaches for the most probable continuation, and the most probable continuation of tension is *release*. Escalation is the low-probability path — it requires a character to act against the reader's (and the model's) desire for harmony. So generated plots systematically de-escalate: dissent produces a faction but never a face; refusal lasts exactly three days and then evaporates; the antagonist role stays untested because no entity is ever allowed to be *wrong on purpose and stay wrong*.

A human editor reads for resistance. A generation pipeline optimizes for coherence. Coherence and resistance are in tension — and only one of them keeps a reader past chapter four.

Note also what the grading itself required: no new metric. The verdict came from *reading the synopsis end-to-end as prose* — `read_raw_output_first`, applied not to a scorer's raw samples but to the story artifact itself. The three fixes (Heidrun must fail once; dramatize Arnulf's three days; the young men's faction must draw blood) were visible in one read. No entity-level field could have surfaced them, because de-escalation is a property of the *sequence*, not of any node — the same pairs-and-groups lesson as yesterday, one level up: yesterday it was relationships between entities, today it is pressure between events.

## Heuristic

**Grade generated stories by what refuses to resolve.** Shape checks (arc present, conflict closed, themes tagged) will always pass, because closure is the model's default. The scarce quantity in LLM fiction is *sustained opposition*: a character who stays wrong, a cost that stays felt, a dissent that produces action. A story-quality gate should therefore invert the usual polarity — count the tensions that survive each act, not the ones that resolve. If the count monotonically drops to zero by the midpoint, the synopsis is de-escalating and the book is not yet worth drafting.

## Seed

Could a `tension_ledger` pass make de-escalation measurable? Walk the event sequence, and at each event ask the LLM one question: "which open tensions does this event *raise*, which does it *release*?" A story whose ledger empties before the final act fails the gate — mechanically, before a single scene is drafted. The interesting design question: can the same ledger drive *generation* — i.e., forbid the drafting graph from releasing a tension unless a character paid a cost on-page in that same chapter?
