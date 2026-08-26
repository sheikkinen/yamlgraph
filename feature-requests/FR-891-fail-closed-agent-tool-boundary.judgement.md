# Judgement: FR-891 Fail-Closed Agent Tool Boundary

**Prior art:** dispositioned in FR-891's header (FR-660/FR-677 positive
precedent; FR-763/759/835/765 noun-matches only).

**Verdict:** APPROVED WITH REVISIONS - the fail-closed boundary is necessary and architecture-aligned, but authority activates only after the FR pins the exact agent finalization seam, completes the `search_web` no-error-string contract, and separates deterministic tests from live operational witnesses.

**Reviewed against:** `feature-requests/FR-891-fail-closed-agent-tool-boundary.md`; `feature-requests/FR-891.research.md`; `research/mercury-census/runs/run-grounded-FAILED-OPEN.log`; `research/mercury-census/findings.md`; `research/mercury-census/canary-fr-891.md`; `yamlgraph/tools/agent.py`; `examples/shared/websearch.py`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `feature-requests/FR-660-agent-tool-execution-unification.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and well witnessed. The incident log shows six `search_web` invocations followed by `✓ Agent completed after 5 iterations`, a successful summarize node, exit-style result output, and a summary whose own text admits `Error: ddgs package not installed` while proceeding to a general-knowledge market map (`research/mercury-census/runs/run-grounded-FAILED-OPEN.log:7-19`, `:30-49`). That is exactly the Scripture failure class: plausible output after a failed boundary (`.github/copilot-instructions.md:78`, `:241-243`).

The proposed fix location is mostly correct. The current agent loop already records a per-tool `success` flag (`yamlgraph/tools/agent.py:341-359`) and then passes the tool output into the next LLM message (`yamlgraph/tools/agent.py:361-362`). The framework therefore has a typed, deterministic signal before synthesis; using it is smaller and safer than adding a new graph node type or prompt instruction. FR-660 is direct precedent for unifying tool execution through `StructuredTool.invoke()` (`feature-requests/FR-660-agent-tool-execution-unification.md:29-58`), and FR-677 is direct precedent for moving verification to execution boundaries rather than advisory output (`feature-requests/FR-677-verification-first-class-dsl.md:49-87`).

The research record satisfies the current research-evidence gate. It preserves five distinct classes with disagreement rather than collapsing them (`feature-requests/FR-891.research.md:9-15`), names the withheld fail-fast canary (`research/mercury-census/canary-fr-891.md:6-9`), and the FR dispositions the rejected heavier/schema/per-tool/deletion/validation alternatives (`feature-requests/FR-891-fail-closed-agent-tool-boundary.md:90-95`). Strategic classification: **framework primitive**. Agent nodes are shared infrastructure, the defect applies to every agent tool consumer, and the fix reuses existing `PipelineError`/`on_error` primitives rather than inventing a new abstraction.

## Required revisions

### R-1: Move the all-failed check to every agent finalization path

Replace the ambiguous "after the iteration loop" wording with a precise helper invoked immediately before `_try_structured_output` in both places the agent currently finalizes: the no-more-tool-calls return path (`yamlgraph/tools/agent.py:306-328`) and the max-iterations path (`yamlgraph/tools/agent.py:364-383`). The witnessed incident finalized inside the loop when `response.tool_calls` became empty, so a check only after the loop would miss the exact failure (`research/mercury-census/runs/run-grounded-FAILED-OPEN.log:17-19`).

The helper must raise only when `tool_results` is non-empty and every entry has `success is False`; it must not treat zero tool calls as a failure. The `PipelineError` must carry node name, total calls, failed calls, tool names, and first failure output.

### R-2: Complete the `search_web` no-error-string contract

Fold the empty-query case into AC-04. The FR says no `"Error: ..."` string returns remain in `search_web` (`feature-requests/FR-891-fail-closed-agent-tool-boundary.md:107-110`), but the current tool also returns `"Error: Search query is empty"` (`examples/shared/websearch.py:46-47`). Require empty or whitespace query to raise `ValueError` at call time. Missing `ddgs` raises `ImportError`; transport/search exceptions propagate; genuinely empty result sets remain the data string `No results found...`.

### R-3: Specify the exception type contract without broad swallowing

Amend the agent-loop criterion to say the framework must raise a `PipelineError` for all-tool-call-failed runs and must not convert that `PipelineError` back into an `"Error: ..."` `ToolMessage`. Tool invocation exceptions may still be captured as failed tool results while the loop is collecting evidence, but the final all-failed aggregate is a node failure routed by the existing node `on_error` mechanism, not another tool-result string.

### R-4: Split deterministic regression tests from live-network witnesses

Keep unit tests for the framework boundary deterministic: stub LLM/tool calls must witness all-failed raising, partial failure preserving current behavior, no-tool-call/no-tool-result preserving current behavior, and max-iterations all-failed raising. Keep `ddgs`-absent behavior deterministic with import monkeypatching or module reload isolation.

Move live `ddgs`-present web success and the mercury-census redo into smoke/operational evidence with committed logs/artifact references, not unit-test gates. Live search and provider credentials are valid witnesses for the incident closure, but they must not make the local unit suite dependent on network state.

### R-5: Freeze demo-output expectations around one committed successful run

AC-05 currently asks for both a missing-dependency failure and a successful committed `demo-output.log` (`feature-requests/FR-891-fail-closed-agent-tool-boundary.md:111-114`). Amend it to require two artifacts: a recorded failing command/log showing ddgs-absent non-zero exit with no summary artifact, and the committed `examples/demos/web-research/demo-output.log` regenerated from a ddgs-present successful run with URL-bearing output. Do not commit a generated summary from the failing run.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/tools/agent.py` all-tool-call-failed aggregation before every final answer path |
| D-2 | Unit tests for all-failed, partial-failure, no-tool-call, and max-iteration agent behavior |
| D-3 | `examples/shared/websearch.py` raises for empty query, missing `ddgs`, and transport/search exceptions; preserves no-results data string |
| D-4 | Unit tests for `search_web` missing dependency, empty query, no results, and propagated exception behavior |
| D-5 | `examples/demos/web-research/demo-output.log` regenerated from a successful ddgs-present run with URL-bearing output |
| D-6 | Recorded ddgs-absent failing-run evidence showing non-zero exit and no summary artifact |
| D-7 | Mercury-census grounded redo evidence recorded in `research/mercury-census/findings.md` with URL-bearing artifact reference |
| D-8 | Changelog fragment, FR implementation-status update, and diary reflection |

Not authorized: new node types; new graph-level validation schema; broad audit or rewrite of all Layer-3 tools returning `"Error:"`; changes to LangChain tool string conventions outside this agent boundary; changes to judge/review/author/research route doctrine; changing `on_error` taxonomy; deleting the web-research demo.

## Revised acceptance criteria

- [ ] AC-01: RED first - a deterministic agent-node test demonstrates that an agent with one or more tool calls whose recorded results all have `success=False` currently reaches final synthesis; GREEN raises `PipelineError` instead.
- [ ] AC-02: The all-failed check runs before `_try_structured_output` on both finalization paths: no-more-tool-calls completion and max-iterations completion.
- [ ] AC-03: The raised `PipelineError` includes node name, total tool-call count, failed count, involved tool names, and first failure output; it is routed by the node's existing `on_error` declaration.
- [ ] AC-04: Partial failure remains non-fatal: an agent run with at least one successful tool result and at least one failed tool result reaches the same finalization path as today.
- [ ] AC-05: No-tool-call runs remain non-fatal: an agent that never invokes tools can still produce a final answer.
- [ ] AC-06: `search_web` raises `ValueError` for empty/blank query, raises `ImportError` at call time when `ddgs` is absent, returns `No results found...` for genuinely empty result sets, and propagates transport/search exceptions without returning `"Error: ..."`.
- [ ] AC-07: Unit tests cover `search_web` missing dependency, empty query, no-results string, and propagated search exception without requiring live network.
- [ ] AC-08: `examples/demos/web-research` with `ddgs` absent exits non-zero and produces no summary artifact; the evidence is recorded as a log, not as a successful demo output.
- [ ] AC-09: `examples/demos/web-research/demo-output.log` is regenerated from a `ddgs`-present successful run and contains URL-bearing search output.
- [ ] AC-10: Round-8 mercury-census grounded redo is re-executed after the fix with `ddgs` present; `research/mercury-census/findings.md` records the command/log/artifact path and the resulting artifact carries real URL citations.
- [ ] AC-11: Changelog fragment, FR status/implementation update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-5 are folded into FR-891. | GATE |
| C-2 | The all-failed aggregate must be checked before structured-output parsing/final-answer synthesis, not only after the loop exits. | GATE |
| C-3 | Do not swallow `PipelineError` into an `"Error: ..."` tool message after the all-failed aggregate is known. | GATE |
| C-4 | Preserve partial-failure and no-tool-call behavior unless a separate FR authorizes stricter semantics. | GATE |
| C-5 | Do not make unit tests depend on live web search, provider credentials, or ambient optional extras. | GATE |
| C-6 | Do not broaden the fix into a repo-wide `"Error:"` string audit of unrelated tools. | GATE |

Authority granted: after the required revisions are folded, implement a fail-closed agent tool boundary and the `search_web` failure-mode correction within the frozen scope above.
