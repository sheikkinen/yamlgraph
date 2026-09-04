# The Judge That Never Says No

**Date:** 2026-09-04
**Trigger:** operator: "reflect - currently plan-judge loop is
deteriorating; overengineering, inventing things to implement" —
immediately after an introspection turn in which I named the
plan-judge-enforce loop as the repo's edge.

## What the record says (14 days, main)

- 115 new FRs filed (~8/day). 152 `docs(fr)` commits vs ~40 `feat`
  commits — FR text is produced at 4x the rate of features.
- Files touched: 50 under `yamlgraph/` (the product), 129 under
  `scripts/`, `.github/`, `graphs/` (the process).
- Judge verdicts, all time: 170 APPROVED / 3 REJECTED (98.3%).
  Last 14 days: 87 / 5 (94.6%).
- Of the last 40 FRs filed, ~12 touch the runtime (map node, encoding,
  Windows bridge). The remaining ~28 are about the pipeline itself:
  three FRs on FR-number allocation (970/975/980), four on a Claude
  CLI backend for the judge (958–961), five on LAN/issue delegation
  (945–949), four on merge/judge infrastructure (928/931/934/935),
  three on session lanes followed by one retiring them (923/925/927).

I claimed the loop as the edge one turn before being told it is
deteriorating. Both are true, and the numbers explain how.

## The mechanism

### 1. A 95–98% pass rate is not a gate

Scripture: `gate_checks_shape_not_substance`. The judge rubric
checks whether the plan is well-formed — ideal result stated,
acceptance criteria testable, prior art dispositioned, scope frozen.
An LLM author produces well-formed plans on demand. So the judge
measures plan *quality*, which the author controls, not plan
*necessity*, which the author cannot fake. `unchallenged_premise`
already names the gap ("Judge validates execution, not intent →
need Red Hat: 'Is the pain real?'") — it has been in Scripture
without a firing mechanism. A question without a firing moment is a
library.

### 2. The pipeline feeds itself

Each meta-FR adds process surface. Process surface fails. Failures
become FRs. FR-number collisions (a symptom of parallel sessions)
produced a research doc, then FR-970, then FR-975, then FR-980 —
a reservation protocol with route enforcement for an integer. The
lane guard hooks (FR-902) got three FRs and then a retirement FR.
This is `growth_as_default` with a positive-feedback loop attached:
the infrastructure is the only consumer of the infrastructure, and
it is a reliable consumer because it keeps breaking. The runtime,
which has external consumers, gets 50 file-touches in two weeks.

### 3. The author and the judge share priors

Both are the same model family, both trained toward completion. The
author's `continuation_bias` produces the FR; the judge's produces
the approval. Input closure (FR content + doctrine only, never the
author's chat) was designed to stop narrative contamination. It
does not stop *prior* contamination — the judge's default answer to
"should this exist?" is the same "yes, and" that wrote it. The
operator confirmed the human side: "plan-judge is NEVER manually
challenged." So no agent in the loop has a native no.

### 4. Reflection turns produce FRs

The `Distill` step asks for a diary entry with a Seed. Seeds became
FRs became features. Two weeks of 44 diary commits and 115 FRs
is the Seed pipeline working exactly as written — every reflection
plants, none prunes. The `Purge` step exists in the Sermon and has
no artifact, no gate, no count. I can cite 115 things planted and
cannot cite what was purged.

## What I did wrong in the prior turn

I named the loop as the edge because it *is* unique. I did not check
whether it was *working*. The uniqueness claim came from Scripture
text; the deterioration claim needs the ledger — approval rate, meta
ratio, FR-to-feat ratio. I had the terminal open and counted corpus
size, not corpus selectivity. `inventory_by_visibility` at the
process level: I graded the loop by mass.

## The cure — and the trap inside the cure

The reflex is to propose a new gate: a "first consumer" hook, a
meta-FR budget, a Red Hat graph. That is the disease. Another
process artifact to fix process overproduction is FR-981 on the
same list as 970/975/980.

The cure has to be subtractive and cheap:

- **Red Hat is a single question, asked by the judge, answered with
  a citation or a rejection:** *which incident, with a date and a
  file, does this FR close?* Not a hypothetical consumer, not "this
  will enable". If the answer is a future tense, the verdict is
  REJECTED, with the rejection recorded as precedent. No new
  tooling — a rubric line and a verdict.
- **Make REJECTED normal.** A judge that rejects 2% is calibrated to
  the author. A healthy rate for LLM-authored plans is unknown but
  is not 2%. The count is the metric; watch it, do not build a
  dashboard for it.
- **Purge has to leave a mark.** Open FRs that cannot cite their
  incident get WITHDRAWN. Count them. `Purge` without a count is
  `detection_without_enforcement` applied to the Sermon itself.
- **Meta ratio is a smell, not a rule.** When `scripts/` +
  `.github/` churn exceeds `yamlgraph/` churn for a fortnight, the
  loop is eating itself. Read it from `git log`; do not automate it.

## Heuristic

`judge_calibrated_to_author`: when an independent gate approves
>90% of an LLM author's submissions, it is measuring form, which the
author controls. Add the one question the author cannot answer by
writing better — *what already happened that this closes?* — and
make the negative verdict the recorded, precedent-setting output.

## Seed

If every planted Seed becomes an FR and every FR gets a 95% approval,
the diary is an FR generator with a one-turn delay. Should a Seed
carry a kill condition — the observation that, if absent after N
days, retires the Seed unfiled — so that reflection can subtract as
easily as it adds?
