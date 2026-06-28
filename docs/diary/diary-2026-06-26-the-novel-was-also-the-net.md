# The Novel Was Also the Net

**2026-06-26 · plot_modeller L7 · FR-598 enforce**

## What happened

FR-598 was the sharpest diagnosis in a long L7 arc: the `affect_throughline` prompt
asked haiku for *prose*, haiku wrote a *novel*, and the novelist's instincts invented
affect the beats never licensed. The Judgement granted authority and froze a clean
experiment: replace the prose with a terse per-beat classifier, **delete** the "every
arc that opens should close" mandate (the invention engine), collapse the two-pass into
one node, re-measure. The GO condition was explicit and honest: `kind | detection` must
RISE **with detection HELD ≥ 0.52**.

I executed the frozen scope exactly. The result:

| axis | prose | classifier |
|------|-------|-----------|
| `affect_recall` (gate) | 0.15 | **0.06** |
| `detection` | 0.52 | **0.24** |

Detection didn't hold. It **collapsed**. The format change made the gate *worse*.

## The trap I almost fell into

The aggregate said `KILL flavor = PROSE-MISSED`, and my reflex was to accept that label
and move on — "the framing is falsified, escalate." But the FR I had *just* graduated to
Scripture said: **read the raw output before you trust the aggregate.** So I did. And the
raw output told a completely different story than the label.

The classifier didn't *mis-place* arcs. It went **near-silent**. Marren — the sole
affect protagonist — emitted 2 operations against ground truth's 8. Most agents emitted
one or two. The prose version *flooded* (over-generated, many wrong-kind guesses); the
classifier *starved*.

## The insight

The metric is **recall** — how many GT deltas we reproduce. Recall rewards *shots on
goal*. The prose's flood was, accidentally, a coverage strategy: spray enough deltas and
some land. The Judgement correctly named the arc-closure mandate the **invention**
engine — but it was *also* a **coverage** engine. Deleting it removed the inventions and
the coverage in the same stroke, and against a recall gate the coverage loss dominated.

The two failure modes — flood and silence — **bracket** the real problem. Neither output
register hits recall, because the residual isn't register at all: it's beat-alignment
(the classifier and the prose *both* put Marren's loss on F2 where GT says F1) and
kind-discrimination. Tuning the wording moved the model from one side of the bracket to
the other without crossing the gate.

## The discipline that held

The stop rule fired exactly as the Judgement reserved it. One format iteration, spent,
refuted. **No second wording pass.** The honest conclusion is a real
beat-granularity / kind-discrimination ceiling → reserved escalation (model scale, or
revisit the six-kind taxonomy and the GT beat granularity). Recording a clean
*refutation* is a real deliverable; an experiment that returns NO is not a failure of
the experiment. Respect the RED.

## Heuristic

**A constraint can serve two functions; deleting it for the bad one can cost you the
good one.** Before removing an instruction because it causes one pathology (invention),
ask what *else* it was silently buying (coverage). On a recall gate, anything that
*increases volume* — even sloppily — is load-bearing, and a precision-motivated deletion
can crater recall.

**Corollary (read_raw_output_first, confirmed again):** the aggregate's auto-generated
KILL *label* (`PROSE-MISSED`) was wrong about the mechanism. Only reading five YAML files
revealed silence, not mis-placement. The label is a projection; the artifact is the
truth.

**Seed:** When a single lever couples two effects (here: invention ↑ and coverage ↑),
can the spike *decompose* the lever before the Judge freezes scope — e.g. require the FR
to name, for each deleted instruction, the metric it is expected to *lower* AND the
metric it might silently lower as collateral? Could a "collateral axis" column become a
standard part of any prompt-deletion FR, the way a blast-radius note guards a destructive
filesystem op?
