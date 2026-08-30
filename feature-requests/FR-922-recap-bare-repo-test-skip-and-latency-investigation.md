# Feature Request: Skip and Investigate `test_bare_repo_recap_no_hallucinated_conventions` (283s Single Test)

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days (skip: minutes; investigation: rest)
**Requested:** 2026-08-30
**First consumer / first event:** any developer or CI lane running `pytest tests/` with `ANTHROPIC_API_KEY` set — first event is the next full-suite run, which currently spends 34% of its wall clock inside this one test.
**Research:** in-body measurement record and dispositioned alternatives table (full-suite clock run, main @ ca44832b, 2026-08-30)
**Prior art:** FR-700 created the recap demo and this test; FR-704 moved orphan detection out of the model (cheapening one assertion but not the invocation). No prior FR addresses recap graph latency; the investigation-then-fix split follows the FR-371→FR-372 precedent (investigation_before_fix).

## Summary

`tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions` took **282.98s** in the 2026-08-30 clock run — 34% of the entire 826s sequential suite, 17× the next-slowest integration test. Operator directive: **skip it now** and open an **investigation task for the rationale** — why does one recap invocation on a 3-commit bare repo take ~5 minutes, and is the test's cost/value ratio defensible in any tier.

This is an investigation-first FR per `investigation_before_fix`: the skip is the
immediate mitigation; the investigation produces the causal chain; a follow-up
fix FR (if warranted) inherits the investigation's harness as its regression
suite.

## Value Statement

Returns ~5 minutes to every keyed full-suite run immediately, and replaces a
"the LLM is slow" shrug with a measured causal chain for the recap graph's
latency.

## Problem

Measured on main @ ca44832b (2026-08-30, sequential full run):

- This test: **282.98s**. Next-slowest integration test: 16.31s.
- The test builds a 3-commit temp repo, compiles `examples/demos/recap/graph.yaml`,
  and invokes it once against Anthropic. Nothing in the test body explains
  a ~5-minute wall time for that workload.
- Unknowns (the investigation's subject): number of LLM calls the recap graph
  actually makes for a 3-commit repo; model and `max_tokens` configured;
  retries/timeouts consumed silently (`on_error: retry`?); whether prompt
  assembly scans beyond the temp repo; whether the 283s is stable or was a
  one-off degraded-API sample (single witness so far — are_the_witnesses_one_phenomenon).

The guarded behavior (REQ-YG-531: no hallucinated FR references on a
conventions-free repo) is real and worth keeping — the cost is the defect,
not the assertion.

## Proposed Solution

Two stages, both in this FR's scope:

**Stage 1 — Skip (immediate mitigation):**

```python
@pytest.mark.skip(
    reason="FR-922: 283s single-test wall time under investigation; "
    "REQ-YG-531 coverage suspended pending rationale"
)
```

Applied to the one test method. The skip reason must cite this FR so the
suspended REQ coverage is traceable, and `scripts/req_coverage.py` output for
REQ-YG-531 must be checked and its status recorded in this FR.

**Stage 2 — Investigation (the rationale):**

Deliverable is a causal chain, not a fix. Instrument one invocation of the
recap graph against the same 3-commit fixture and answer:

1. How many LLM calls, with what model, token counts, and per-call latency?
   (LangSmith trace or `YAMLGRAPH_ROUTE_LOG` + executor logging; cite trace IDs
   per Commandment 9.)
2. Is time spent in the model, in retries, or in the graph runtime?
3. Is 283s reproducible (≥3 samples) or was the clock run a degraded sample?
4. Disposition: (a) fix graph/prompt config and un-skip; (b) re-tier the test
   behind an explicit opt-in env gate with the cost documented; or (c) replace
   with a cheaper witness (e.g. haiku-class model, or record/replay) that still
   proves REQ-YG-531. The disposition is recorded in this FR and, if (a) or (c),
   spawns the follow-up fix FR.

## Acceptance Criteria

- [ ] Skip applied with FR-922-citing reason; full keyed suite no longer executes the test
- [ ] REQ-YG-531 coverage status after skip recorded in this FR (`scripts/req_coverage.py`)
- [ ] Investigation record: per-call LLM breakdown (count, model, tokens, latency) with cited LangSmith trace IDs
- [ ] Reproducibility verdict from ≥3 timed invocations
- [ ] Explicit disposition (fix / re-tier / replace witness) with rationale written into this FR
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Delete the test | Rejected — REQ-YG-531 (anti-hallucination on bare repos) loses its only witness; the assertion is sound |
| Mark `slow` only (already is) | Insufficient — `slow` does not exclude it from the full/CI keyed runs where the 283s lands |
| Fix immediately without investigation | Rejected — no causal chain yet; symptom_patch. `investigation_before_fix` applies: >15 min to even write the condemning test |
| Cheaper model swap now | Premature — may be the outcome of Stage 2 disposition (c), but choosing it before measuring is quick_confidence |

## Related

- `tests/integration/test_recap_demo_integration.py` (lines 63–92)
- `examples/demos/recap/graph.yaml`
- FR-700 (recap demo origin), FR-704 (code-owned orphan detection)
- REQ-YG-531
- FR-923 (suite latency umbrella)
