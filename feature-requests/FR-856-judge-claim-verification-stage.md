# Feature Request: Claim-Verification Research Artifact in the Judge Pipeline

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-22
**First consumer / first event:** the judge graph on its next run over
an FR whose claims cite code/tests — the verification findings arrive as
a citable artifact instead of ad-hoc subagent narrative.

## Summary

Give the judge pipeline a research stage that verifies an FR's factual
claims (cited files, test names, prior art, status assertions) and emits
a findings artifact the judgement cites — replacing the recurring
ad-hoc "verify FR-XXX claims" subagent launches.

## Value Statement

Judgements gain input closure on their research: claims are verified by
a traceable pipeline stage, not by chat-narrative subagents the doctrine
already forbids as a judging route.

## Problem

Census evidence: cluster C2 "FR claim verification" fired 9× across 6
sessions through 07-28 (`docs/2026-07-29-research-subagent-promotion.md`)
and the 08-22 delta census confirmed a 10th ("Audit FR 784 onward",
2026-08-15). The judgement itself was absorbed by the judge-fr adapter
(FR-758) and status reading by `scripts/fr_board.py`, but pre-judgement
claim verification still fires as ad-hoc subagents. This is the exact
input-closure violation class: research feeding a judgement arrives as
requester narrative instead of a citable artifact. Live demonstration
2026-08-22: the FR-854 judgement missed governing prior art
(`docs/2026-07-29-research-subagent-promotion.md`) because no
verification stage searched for it — the verdict had to be suspended
post-hoc.

## Ideal Result

`scripts/judge.sh <fr>` produces, alongside the draft judgement, a
`tmp/draft-claim-verification.md`: each factual claim in the FR
(cited paths exist, quoted line facts hold, prior-art search ran with
named queries and hits dispositioned) marked verified/refuted/unchecked.
The judgement's "Reviewed against" section cites it. A judgement over
refuted claims cannot read as clean.

## Proposed Solution

A research node (or pre-stage) in the judge graph — precedent: the
chaplain research step (CAP-113) — that runs before the verdict node:

1. Extract claims from the FR (cited paths, FR references, "verified by
   grep" style assertions).
2. Mechanically check path existence and reference resolution; run the
   prior-art noun search the FR-738 gate uses, at judge time.
3. Emit the findings artifact; the judge node receives it as input and
   must disposition refuted claims in the verdict.

Touches the judge graph — itself judged scope; any graph edit goes
through the governed authoring route.

## Acceptance Criteria

- [ ] Judge runs emit a claim-verification findings artifact alongside
      the draft judgement
- [ ] Cited-path existence and FR-reference resolution checked
      mechanically (no LLM for checkable facts)
- [ ] Prior-art noun search (FR-738 mechanism) executed at judge time
      and its hits included in the findings
- [ ] Judge prompt requires dispositioning refuted/unchecked claims in
      the verdict
- [ ] Graph changes authored via scripts/author.sh with authoring report
- [ ] Tests with `@pytest.mark.req(...)` for claim extraction and the
      mechanical checks

## Alternatives Considered

- **Keep ad-hoc research subagents**: forbidden trajectory — manual
  sister-session/subagent judgement inputs are the class the sole route
  exists to kill.
- **Human pre-verification**: does not scale; the human skims.

**Prior art:** `docs/2026-07-29-research-subagent-promotion.md`
recommendation 2 (C2) — filed verbatim after 24 days dormant; FR-758
judge adapter — extended, not modified in verdict semantics; CAP-113
chaplain research step — pattern precedent; FR-738 prior-art gate —
its noun search is reused at judge time rather than commit time only.

## Related

- docs/2026-07-29-research-subagent-promotion.md (census, cluster C2)
- .github/skills/judge-fr/doctrine.md
- feature-requests/FR-854-subagent-call-classification-graph.md (the
  suspension incident this stage would have prevented)
