# The Verdict I Almost Shipped Without Measuring

**Date:** 2026-08-04
**Context:** FR-768 (tool manifests) + FR-769 (shared vision tool) — from four
draft docs in docs/tmp/ to two enforced FRs in one arc.

## The near-miss

Asked to reflect on four proposal drafts, I rendered a verdict in one pass:
"manifest idea = indirection without pain, no named consumer — kill it." The
verdict was well-formed, cited prior art (FR-658, CAP-111, FR-044), and was
wrong. The user pushed back with one sentence: *analyze the examples first.*
A 30-line scan script later: 333 tool declarations, 26 signatures duplicated
verbatim, a production agent trio (planner/enforcer/judge) carrying a
byte-identical toolkit block, and a shared Python module re-wrapped by four
example families because there was no way to declare it once.

The trap was `inventory_by_visibility` wearing a new coat: I judged the
proposal by the absence of a *named* consumer **in the document**, instead of
measuring whether unnamed consumers existed **in the repo**. The graveyard
check (FR-044's rejections) made the kill verdict feel researched — but FR-044
rejected *code* abstraction where implementations diverged; the manifests
dedup *declarations* that are byte-identical. Citing case law from an adjacent
jurisdiction is not the same as measuring the current one.

## What the measurement changed

Everything downstream. The judge (sole-route graph, gpt-5.5) classified
FR-768 as a framework primitive *because* of the numbers, and both FRs went
APPROVED WITH REVISIONS with revisions that were all mechanically checkable —
schema tables, per-runtime equivalence tests, provider allowlists, six exact
test cases. Boring enforcement followed: the only implementation surprises
were repo-plumbing, not design (module-map budget, vulture false positives on
Pydantic discriminators, the FR-756 process-boundary marker, a demo-proof gate
whose success markers only LLM nodes emit — a python-only demo cannot satisfy
it without an exit-status-conditioned echo).

## The staged-index self-collision

One genuine incident: my GREEN commit attempt failed on an unrelated test,
leaving the whole GREEN set staged. I then "fixed and committed just the
test" — and swept the entire FR-768 implementation into a commit labeled
`fix(tests)`, under SKIP=pytest. `one_session_one_repo`'s staged-check ritual
exists for *parallel sessions*; this proved a single session can interleave
with **itself** across a failed hook run. The staged-check-empty-before-add
ritual applies after every failed commit, not just around foreign sessions.
Caught by `git show --stat` audit (the ritual's second half), split cleanly
via soft reset before push.

## Also witnessed

- FR-766's env-only runpod default broke REQ-YG-043's "all defaults non-empty"
  test on any machine without RUNPOD_MODEL — an enforced FR whose test
  alignment shipped without the test. The changelog-first diagnostic named it
  in one `git log` read.
- The authoring sole-route (FR-767) held: the demo graph went through
  author.sh, the sub-agent found the ambient `PROVIDER=azure` conflict I
  would have hit later, and pinned the provider in the wrapper. The route
  that felt like ceremony caught a real boundary bug.

## Heuristic

A kill verdict over a proposal is a **measurement claim** — "no consumer
exists" is falsifiable by a grep, so run the grep before rendering it. The
cheapest correct verdict is one scan script away from the cheapest wrong one.
Corollary for prior-art citation: check that the precedent's *rejection
reason* transfers, not just its nouns.

**Seed:** The demo-proof gate accepts only markers that LLM nodes emit —
python-only demos need a shell-level appended marker, which is exactly the
kind of side-channel evidence the gate was built to prevent. Should
`graph run` itself emit `✓ Graph execution completed successfully` on exit 0,
making the proof first-party for every node type?
