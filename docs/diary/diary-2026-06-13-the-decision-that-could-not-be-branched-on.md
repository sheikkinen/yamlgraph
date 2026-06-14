# The Decision That Could Not Be Branched On

*2026-06-13 — FR-479, DM v2 director/narrator split*

## What happened

The per-turn graph was `intents → recap`. One `recap` node did two jobs fused
into a single prose blob: it *judged* the scene state (Has it opened? Is it
over? Did someone act who shouldn't have?) and it *wrote* the narration. Run
`1732b9c4` exposed the cost: the scene's END was satisfied by turn 16, but the
loop ran to turn 27, recycling the climax — because the judgement existed only
as prose. There was nothing the play loop could read to decide "stop here."

The fix was to split the judge from the writer: a structured `direct` node
emits `{phase, establishing, scene_complete, steer, continuity}`, and the
narrator `recap` consumes the parts it needs. Now `scene_complete` is a bool
the session code branches on; `establishing` is a string the recap opens with;
`continuity` is a list the template surfaces.

## The trap

**A decision that lives only as prose cannot be branched on.** The original
`recap` *did* decide the scene was over — it wrote "The New Leader" — but that
decision was trapped in natural language, invisible to control flow. The loop
couldn't act on a conclusion it couldn't parse. This is the inverse of the
`plausible_wrong_answer` trap: there the output passed a shape check but was
semantically wrong; here the output was semantically *right* but had no shape
at all, so no downstream code could consume it.

The cure is the same boundary law in a new dress: **structure the decision at
the moment it is made, not downstream where you wish you could act on it.** A
director that returns a typed verdict is branchable; a narrator that buries the
verdict in a paragraph is not.

## The secondary trap (avoided)

The shared `field` helper in `graph_app` coerces every value to `str`. Reaching
for it to normalize the director's output would have silently corrupted
`scene_complete` (bool → "True") and `continuity` (list → "['Naru...']"),
re-burying the structured decision in strings one layer down. I wrote a
type-preserving `_direction_dict` instead. The lesson: a "normalize" helper that
flattens types is a boundary that *destroys* structure — exactly what this FR
was built to *create*. Know what your normalizer normalizes.

## Heuristic

When a node both judges and acts, and the loop needs to act on the judgement,
the judge must emit a typed verdict the loop can read — splitting prose-judgement
into structure is not gold-plating, it is the difference between a loop that
terminates and one that recycles its climax forever.

**Seed:** Which other YAMLGraph nodes fuse a judgement with its narration —
where a downstream branch silently re-derives (or fails to derive) a conclusion
the node already reached but only spoke in prose? Could a lint detect "this
`llm` node's output is consumed by a router/condition but has no `output_schema`"
— a prose verdict feeding a branch that can only guess at it?
