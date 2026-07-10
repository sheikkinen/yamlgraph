# The Floor Entry That Confessed Its Own Inference (FR-710)

**Date:** 2026-07-10
**Context:** FR-710 enforce — provider deadline floors; the fifth and smallest FR of the NC-361 lineage, spawned by FR-709's field finding within hours.

## The short arc

FR-709's first live run returned a provider contract no docstring carries
(google: deadline ≥ 10 s). Same day: FR filed, judged, enforced, shipping.
The pipeline's latency from field-fact to released guard is now measured in
hours — that is the doctrine working at its intended tempo.

## What the judgement caught in its own author, again

Two of the four findings were self-inflicted and structural:

- The promised error message ("got 5.0 via LLM_REQUEST_TIMEOUT") was
  **unimplementable as specced** — after `setdefault`, kwarg/env/default are
  indistinguishable. Source attribution had to move before the merge. A
  message is also an artifact (FR-705's lesson); designing its content
  without checking the data flow that feeds it is spec-time
  plausible_wrong_answer.
- The vertex floor entry had **no field evidence** — only google's 400 was
  observed. The FR invoked the pattern-freeze rule and violated it in the
  same section. Resolution worth naming: the entry ships, but it **confesses
  its own inference** in a comment ("backend-inferred; not independently
  field-verified"). An annotated guess is honest; a symmetric-looking map
  with one observed and one assumed entry is not.

## Heuristic

When a constraint map mixes observed and inferred entries, the inference
must be marked IN the artifact, not in the FR that nobody re-reads. The
confession lives where the next maintainer's eyes will be. (Same mechanism
as noqa confessions — the annotation travels with the code.)

**Seed:** the floors map, the wrapper param map (FR-708), and the model-id
rot (FR-709 finding 2) are all instances of "external facts hard-coded
locally." Should a periodic field-probe job (one cheap real request per
provider, weekly) verify these local copies of remote contracts — turning
rot detection from incident-driven to scheduled?
