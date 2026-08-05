# 2026-08-05 — FR-775: The gate that fired on page 24

## Context

FR-775 redesigned the book-summary demo from a linear 10-page-excerpt
pipeline into a cursor loop: probe → 10-page fetch windows → per-page map →
page-identity accumulation → bounded exit. The operator's redesign verdict
was ~30 words; the judge added five revisions (R-1..R-5) before a line of
code existed; enforcement was RED (21 tests) → GREEN A (splitter + helpers)
→ authored graph → witness.

## The moment worth recording

The first 418-page witness run died in window 21-30: DeepSeek rejects
structured output, so all ~418 calls ride the FR-464 JSON-extraction
fallback, and one response returned JSON cut mid-string. The failure was
reported not by a stack trace deep in the map machinery but by my own
`accumulate` gate: *"page summary failed in window 21-30: ... could not
extract JSON ... page 24"*. R-4 (envelope gates) was judged in as an
error-hygiene nicety. In production it turned a silent `_error` entry —
which the old linear demo would have carried into `combine` as a hole in
the book — into a loud abort naming the window and the page.

Trap dodged: `plausible_wrong_answer`. Without the gate, the run would have
"succeeded" with 417 summaries and no one counting. The cure was one line
of config (`on_error: retry` on the map subnode), findable in minutes
because the failure was loud and located.

## Second observation: probability at scale is a design input

One malformed response in ~24 calls is an anomaly; one in 418 is a
certainty. The linear FR-774 demo made 42 LLM calls and never saw this.
Scaling call count by 10x converted a tail risk into a guaranteed abort.
Retry-per-subnode is not robustness decoration on a loop demo — it is the
minimum viable contract for any graph whose call count exceeds the
provider's malformed-response odds. The judge's R-4 and the framework's
`max_retries` composed exactly at the boundary where the provider's lie
(structured output claimed, fallback delivered) enters our state.

## Third observation: the loop_limits/loop_exits key riddle

`loop_exits` keys must match `loop_limits` keys (E009), tool_call nodes
silently ignore `loop_limit`, and the exit router must be the node with
conditional edges. Three constraints, one solution: `advance` — a python
node (limit support), the router source (exit support), and the budget
carrier. The lint's W012 cycle warnings then demanded limits on every loop
body node; the route agent added them mechanically. The design lesson: in
a cyclic graph, pick the loop-control node FIRST and hang everything on
it, rather than distributing loop semantics across the cycle.

## Contract evolution, honestly labelled

FR-773/774 artifact tests pinned the retired linear shape (`nodes.split`,
excerpt prompts, 418-page static map cap). They were evolved — not
deleted — to pin the same *intents* on the new shape: no-{} -collapse moved
to `fetch_batch`, the 418-page budget became loop_limits × window,
"prompts don't lie about granularity" flipped from excerpt-honesty to
per-page-honesty. A superseding FR owns the evolution of its
predecessors' artifact tests; the direct splitter tests survived untouched
because they pinned the boundary, not the artifact.

**Seed:** the malformed-response rate is measurable per provider (FR-464
fallback frequency is already logged). Could a lint rule estimate a graph's
total LLM call count (map fan-out × loop budget) and *require* `on_error:
retry` when calls × observed-failure-rate exceeds a threshold — turning
this diary's probability-at-scale lesson into a mechanical gate?
