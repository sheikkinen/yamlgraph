# Reflection: FR-272 Router Node Race Candidates

**Date:** 2026-04-22
**FR:** FR-272
**Duration:** ~1 session

## What I built

Extended the `router` node type to accept a `candidates:` list, turning it into
a race-capable router that fires the same prompt to N providers concurrently and
uses the first valid result for routing resolution. Single-provider routers are
unchanged.

## Cognitive process

### The boundary insight was immediate

The prior FR chain (267→270→271) had already factored `_race_async`,
`_invoke_candidate_async`, and `_run_coro_sync_safe` into clean, importable
primitives in `race_node.py`. The implementation was literally: import those
primitives into `llm_nodes.py` and branch on `cfg.candidates`.

**The one-law was trivially satisfied:** normalize at the boundary where external
data enters. The race boundary was already race_node.py; I just routed the router
path through it.

### Trap caught by rubber duck: wrong execution branch placement

My initial plan said "add race branch after existing execution path." The rubber
duck caught this immediately: "by then `execute_prompt()` has already run." The
fix was to make `cfg.candidates` an early branch after variable resolution, before
any LLM call.

### Judgement amendment clarified AC3

The original acceptance criterion 3 said "malformed-JSON candidate disqualified."
But the Judgement amendment had already dropped winner disqualification. My first
test assumed disqualification (expected the good-JSON candidate to win). The test
failed, and the log showed the bad-JSON candidate winning and `_resolve_route`
falling to `default_route`.

This was the right behavior per the amendment. Updated the test to assert:
- bad JSON wins → `_route == default_route` (not fatal)
- `_race_winner` still recorded

The core "not fatal" guarantee was always the real AC3 intent.

### Patch target confusion

Tests patched `yamlgraph.node_factory.llm_nodes.create_llm` but `create_llm`
lives in `race_node.py`. Had to redirect patches to `race_node.create_llm`.
This is a recurring pattern: when delegating to a helper module, patch targets
must follow where the actual call happens.

## What worked well

- The existing factored primitives made the implementation a 40-line addition,
  not a rewrite.
- The compiler amendment (skip `_maybe_wrap_timeout`) was already documented
  in the Judgement, so I knew exactly what to do.
- TDD revealed the AC3 misalignment before it could become a confusing bug
  in production.

## What slipped

- The `candidates` field on `LLMNodeConfig` needed a `field(default=None)` to
  avoid breaking existing instantiation sites. The rubber duck flagged this;
  easy fix.
- I initially forgot to add `timeout` to `LLMNodeConfig` and used `hasattr`
  as a workaround. Cleaned up immediately.

## Heuristics

> When delegating execution to a helper module, test patching must follow
> the actual call site (in the helper), not the delegating module's namespace.

> Judgement amendments > original acceptance criteria. Re-read the Judgement
> before writing the first test, not after the test fails.

**Seed:** The router-race pattern now exists. `llm` and `copilot` nodes might
benefit from `candidates:` too (explicitly out-of-scope for FR-272). When that
need surfaces — which project will prove the pattern first, and what will the
"first-valid semantics" look like for a pure generation node vs. a routing node?
