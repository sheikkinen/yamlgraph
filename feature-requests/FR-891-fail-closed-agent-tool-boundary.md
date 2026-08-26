# Feature Request: Fail-Closed Agent Tool Boundary — Kill the Fluent Failure

**Priority:** HIGH
**Type:** Bug
**Status:** Completed (enforced 2026-08-26 on worktree feat/fr-891; RED fefc875c, GREEN follows)
**Effort:** 1 day
**Requested:** 2026-08-26
**First consumer / first event:** the re-run of the mercury-census grounded
research round (round 8 redo) — `examples/demos/web-research` must exit
non-zero and emit no summary when `search_web` fails every call.
**Research:** [FR-891.research.md](FR-891.research.md)

**Prior art:** FR-890 (research sole route — its librarian R-4 fail-closed
boundary is the pattern this FR generalizes to the framework; its research/
judgement lifecycle produced this FR's siblings). FR-888 (worktree guard —
same-day precedent for main-checkout write protection; FR-888.research.md
is the sibling artifact convention followed here). FR-763 / FR-759 / FR-835
(noun-match "boundary" only — taxonomy-scan, OTel, and gitclaw boundaries
are unrelated surfaces; no overlap in mechanism or scope). FR-765
(graph-authoring skill — noun-match only; authoring route not touched).
FR-660 (tool execution unification — introduced the per-call `success`
flag this FR finally consumes; direct positive precedent, extended not
duplicated). FR-677 (verification at execution boundaries — precedent for
fail-closed placement; this FR applies it to the agent tool loop).

## Summary

An agent node whose tool calls ALL fail currently proceeds to synthesis and
exits 0 with a fluent, citation-free artifact. Add a fail-closed boundary:
the agent loop already computes per-call `success` flags
(`yamlgraph/tools/agent.py` line ~343) but nothing aggregates them — when
every tool invocation in an agent run failed, raise `PipelineError`
(routable by the existing `on_error` taxonomy) instead of handing error
strings to the LLM as research. Fix the `search_web` tool's
missing-dependency mode to raise instead of returning prose. Update the
web-research demo and its committed demo-output.log to witness the new
behavior.

## Value Statement

Every graph embedding an agent node stops being able to launder total tool
failure into plausible output — the run 8 incident class
(`run-grounded-FAILED-OPEN.log`) becomes mechanically impossible.

## Problem

Witnessed 2026-08-26 (`docs/mercury-census/runs/run-grounded-FAILED-OPEN.log`):

1. `ddgs` not installed (optional extra absent from venv) → `search_web`
   returned the STRING "Error: ddgs package not installed" — a silent
   fallback baked into the tool (Commandment 6 violation at Layer 3).
2. The agent loop invoked the tool 6 times, correctly computed
   `success=False` each time, stored the flags in `tool_results` — and
   acted on none of it. "✓ Agent completed after 5 iterations."
3. The summarize node synthesized a knowledge-cutoff market map from six
   error strings. Exit 0. Zero external citations (verified: all 7 `http`
   matches in the artifact are API log lines).
4. The model confessed in-text that search had failed; nothing mechanical
   consumed the confession. Only a human raw-read caught the run.

Contrast: FR-890's librarian wraps the identical tool and its LLM-free
reducer fails closed on error strings/missing URLs (R-4). The cure exists
in one graph; the framework leaves every other agent consumer exposed.

## Ideal Result

A tool-failure-saturated agent run cannot produce output: it raises a
typed error carrying the failure census (N calls, N failures, first error),
routed by the node's existing `on_error` declaration; the demo exits
non-zero with a truthful log; a missing optional dependency is
distinguished from a runtime search failure at raise-time. FR-890's
boundary discipline becomes the framework default, not a per-graph luxury.

## Proposed Solution

Per the research table (5 classes, disagreement preserved in
FR-891.research.md), the accepted class is the yamlgraph-native +
os-infra convergence — fail-fast at the framework boundary, reusing
existing primitives; no new node types, no LangChain string-convention
change:

1. **Tool (Layer 3, `examples/shared/websearch.py`)** (R-2): missing `ddgs` →
   `raise ImportError("ddgs not installed — pip install 'yamlgraph[websearch]'")`
   at call time (not import time); empty/blank query → `raise ValueError`;
   transport/search exceptions propagate. Genuinely empty results stay the
   data string "No results found...". No "Error: ..." string returns remain.
2. **Agent loop (framework, `yamlgraph/tools/agent.py`)** (R-1, R-3): a
   helper invoked immediately before `_try_structured_output` on BOTH
   finalization paths — the no-more-tool-calls return (~line 306–328, the
   path the witnessed incident took) and the max-iterations path
   (~line 364–383). It raises `PipelineError` only when `tool_results` is
   non-empty and every entry has `success is False`; zero tool calls is
   NOT a failure. The error carries node name, total calls, failed calls,
   tool names, first failure output; routed by existing `on_error`;
   never converted back into an "Error: ..." ToolMessage. Per-call
   exception capture during evidence collection is unchanged.
3. **Demo (`examples/demos/web-research`)** (R-5): no YAML change. Two
   artifacts: a recorded ddgs-absent failing run (non-zero exit, no
   summary) kept as log evidence, and demo-output.log regenerated from a
   ddgs-present successful URL-bearing run (demo-gate).
4. **Tests** (R-4): deterministic only — stubbed tool registries for
   all-failed / partial / no-tool-call / max-iterations cases; ddgs
   absence via import monkeypatching. Live-network runs (demo redo,
   mercury-census round-8 redo) are operational evidence with committed
   logs, never unit-test gates.

Rejected classes (dispositioned in the research record): schema field
`tool_result_type` + validation node (heavier, new contract for the same
signal the success flag already carries); per-tool wrapper scripts
(process boundary in the wrong layer); demo deletion (subtractionist —
the demo becomes the fix's witness instead); multi-agent validation layer
(librarian precedent noted; disproportionate to the defect).

## Acceptance Criteria (revised per judgement — supersede the original set)

- [ ] AC-01: RED first — deterministic agent-node test shows an all-failed run currently reaches final synthesis; GREEN raises `PipelineError` instead.
- [ ] AC-02: The all-failed check runs before `_try_structured_output` on BOTH finalization paths: no-more-tool-calls completion and max-iterations completion.
- [ ] AC-03: The raised `PipelineError` includes node name, total tool-call count, failed count, tool names, first failure output; routed by the node's existing `on_error`.
- [ ] AC-04: Partial failure (≥1 success) remains non-fatal — same finalization path as today, witnessed by test.
- [ ] AC-05: No-tool-call runs remain non-fatal — witnessed by test.
- [ ] AC-06: `search_web` raises ValueError on empty/blank query, ImportError at call time when ddgs absent, returns "No results found..." for empty result sets, propagates transport exceptions; no "Error: ..." returns remain.
- [ ] AC-07: Deterministic unit tests cover missing dependency, empty query, no-results string, propagated exception — no live network.
- [ ] AC-08: ddgs-absent demo run exits non-zero with no summary artifact; recorded as log evidence, not as demo output.
- [ ] AC-09: demo-output.log regenerated from a ddgs-present successful run with URL-bearing output.
- [ ] AC-10: Mercury-census round-8 redo executed post-fix; findings.md records command/log/artifact path; artifact carries real URL citations.
- [ ] AC-11: Changelog fragment, FR status update, diary reflection.

## Out of Scope

- Generalizing fail-closed to non-agent node types (llm/map error handling
  already governed by `on_error`).
- Auditing other Layer-3 tools for "Error: ..." string returns (follow-up
  census candidate, not this fix).
- Any new node type, schema field, or validation-node pattern (rejected
  classes above).

## Alternatives Considered

See [FR-891.research.md](FR-891.research.md) — five classes from the sole
research route (first real consumption); disagreement preserved as rows.
Canary (fail-fast propagation, precommitted in
docs/mercury-census/canary-fr-891.md, withheld from the brief) was
independently recalled by two personas — run valid.

## Related

- `docs/mercury-census/runs/run-grounded-FAILED-OPEN.log` (incident)
- `docs/mercury-census/findings.md` (rounds 6–8, instrument-bias finding)
- FR-890 (librarian R-4 fail-closed precedent), FR-660 (tool invoke
  unification — introduced the success flag), FR-677 (post-guards)
- Scripture: Commandment 6, `plausible_wrong_answer`,
  `gate_checks_shape_not_substance`, `normalize at the boundary`

## Implementation Record (2026-08-26)

Enforced on worktree `feat/fr-891` (FR-888 route). TDD: RED fefc875c
(9 witnesses, SKIP=pytest), GREEN in the following commit. Judgement
R-1..R-5 all implemented.

**Deliverables:**

- D-1: `yamlgraph/tools/agent.py` — `AllToolCallsFailedError` (mirrors
  race_node's `AllCandidatesFailedError` precedent) +
  `_check_all_tools_failed()` invoked before `_try_structured_output` on
  BOTH finalization paths (no-more-tool-calls and max-iterations, R-1).
  Census message carries node name, counts, tool names, first failure.
- D-2: `tests/unit/test_fr891_fail_closed_agent.py` — 10 deterministic
  tests (R-4): both raising paths, census content, partial-failure and
  no-tool-call non-fatal paths, full search_web contract. Two legacy
  FR-660 tests in test_agent_nodes.py amended: they asserted the
  fail-open completion by name; now assert the raise with format
  preserved in the census.
- D-3: `examples/shared/websearch.py` — ValueError on empty query (R-2),
  ImportError at call time for missing ddgs, transport exceptions
  propagate, "No results found..." data string kept; no "Error: ..."
  returns remain (witnessed by source-inspection test).
- D-4: covered in D-2 (deterministic, importorskip-free monkeypatching).
- D-5: `examples/demos/web-research/demo-output.log` created from a live
  ddgs-present run; 29 non-log URL citations.
- D-6: ddgs-absent evidence
  `docs/mercury-census/runs/run-grounded-redo-ddgs-absent.log`:
  exit 1, no summary, full census in the error.
- D-7: round-8 redo recorded in `docs/mercury-census/findings.md`;
  artifact `runs/run-grounded-redo.log`, 26 non-log URL citations.
- D-8: changelog fragment + diary
  `docs/diary/diary-2026-08-26-the-guard-that-already-knew.md`.

**Decisions / deviations:**

- The judgement's "raise a PipelineError" is implemented as
  `AllToolCallsFailedError(Exception)` — `PipelineError` is a Pydantic
  model, not raisable; the exception mirrors the in-repo
  `AllCandidatesFailedError` precedent and converts to `PipelineError`
  via `from_exception` at handler boundaries (C-3 honored: never
  re-swallowed into a ToolMessage).
- Stale-code tripwire hit during D-6: console script resolved to the
  main checkout's editable install; first evidence run showed the
  impossible exit-0-with-summary. Cured with `PYTHONPATH=$PWD`;
  provenance verified before all committed evidence.
