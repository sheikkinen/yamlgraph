# The Preflight That Was Actually a Boundary

**Date:** 2026-08-28
**Context:** FR-899 org repo census with pinned-Azure delegation — plan, judge, enforce in one arc.

## What happened

The FR claimed Azure fail-fast came free from `llm_factory` ("missing
`AZURE_AI_ENDPOINT` aborts before any discover call"). The sole-route judge
falsified it by reading execution order: provider construction happens inside
LLM node execution, AFTER the gh discovery and extraction nodes have already
pulled corp data through the pipeline. The compliance boundary I thought I had
was a boundary in the wrong place — the run would abort, but only after the
data had transited.

## The trap

A variant of `downstream_fix` wearing a compliance costume: I placed the guard
where the *provider* enters (LLM construction) instead of where the *data*
enters (discovery). For a data-governance constraint, the boundary that matters
is the earliest node that touches the governed data, not the component that
uses the credential. The cure was mechanical once named: an explicit
`preflight` python node as the graph's first edge, witnessed by a test that
asserts discovery never runs when the env is missing.

Second observation: the judge caught this from the FR text + repo doctrine
alone (input closure — no chat narrative). The false claim was cited with file
and line (`llm_nodes.py:331-351`). An author-session self-review would likely
have nodded past it, because I wrote the claim believing it.

## Heuristic

For any compliance/data-locality constraint, ask: *what is the first node that
touches the governed data?* The guard belongs before that node — not at the
component that consumes the credential the constraint is named after. The
constraint's NAME (Azure pinning) points at the LLM; the constraint's SUBJECT
(corp repo data) enters at discovery.

## Seed

Seed: The judge falsified a factual claim about execution order by reading code
the author didn't cite. Could the judge graph mechanically extract every
"existing behavior X guarantees Y" claim from an FR and require a file:line
witness for each — a claim-evidence table the enforcer inherits as assertions?
