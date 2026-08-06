# Judgement: FR-776 tool_call `on_error: fail`: Prerequisite Failures Fail the Graph

**Prior art:** FR-776-tool-call-on-error-fail.md is the FR under judgement (self-hit). FR-775 (gate-node workaround), FR-658 (agent error-text contract), and FR-772 (same node, args surface) are dispositioned in the FR's Prior art line and re-examined below.

**Verdict:** APPROVED WITH REVISIONS — the framework primitive is sound, but authority activates only after the FR makes `tool_call`'s supported `on_error` set load-time explicit, pins requirement ownership, and adds the repo-required diary evidence.

**Reviewed against:** `feature-requests/FR-776-tool-call-on-error-fail.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-775-book-summary-loop-redesign.md`; `feature-requests/FR-775-book-summary-loop-redesign.judgement.md`; `feature-requests/FR-658-graph-as-tool.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `yamlgraph/node_factory/tool_nodes.py`; `logs/book1-summary.log`; `yamlgraph/models/node_schema.py`; `yamlgraph/utils/validators.py`; `yamlgraph/linter/checks_semantic.py`; `yamlgraph/error_handlers.py`; `reference/graph-yaml.md`; `capabilities/CAP-05-tool-agent-integration.yaml`.

## What is sound

The problem is real and evidenced at the correct boundary. The witnessed run failed downstream in `summarize_pages` because `{state.split_result.result.chunks}` could not resolve, while the tool boundary had already produced the failed `split_result` envelope (`logs/book1-summary.log:1-9`). The current `create_tool_call_node` implementation confirms the cause: unknown tools and callable exceptions are always returned as `{"success": False, "error": ...}` envelopes and the graph continues (`yamlgraph/node_factory/tool_nodes.py:64-103`). FR-776 correctly applies the doctrine boundary rule: fail where the prerequisite fails, not three nodes later (`feature-requests/FR-776-tool-call-on-error-fail.md:26-46`; `.github/copilot-instructions.md:50-58`, `.github/copilot-instructions.md:71-79`).

The scope is minimal and correctly classed as a **Framework primitive**. FR-775 needed demo-local gate nodes solely because `tool_call` lacks a fail-at-source mode (`feature-requests/FR-775-book-summary-loop-redesign.md:82-89`, `feature-requests/FR-775-book-summary-loop-redesign.judgement.md:37-41`). FR-658's agent contract still requires tool errors to be returned as text so an agent loop does not crash (`feature-requests/FR-658-graph-as-tool.md:78-80`, `feature-requests/FR-658-graph-as-tool.md:154-169`), and FR-776 preserves that default instead of making `fail` universal (`feature-requests/FR-776-tool-call-on-error-fail.md:63-64`, `feature-requests/FR-776-tool-call-on-error-fail.md:111-112`). FR-772 already established `tool_call` as a deterministic pipeline-invocation surface as well as an agent-oriented one (`feature-requests/FR-772-tool-call-inline-dict-args.md:42-80`), so adding an explicit failure policy fits the existing abstraction rather than inventing another graph-local workaround.

The acceptance shape is mostly testable. AC-01 and AC-02 can be exercised directly against `create_tool_call_node`; AC-03 can pin the current envelope for no `on_error` and `on_error: skip`; AC-05's regression can reproduce the failed-envelope-then-map-resolution chain and prove `on_error: fail` stops at the tool node (`feature-requests/FR-776-tool-call-on-error-fail.md:83-103`). Documentation has a precise insertion surface: the `tool_call` property table currently lists only `tool`, `args`, and `state_key` (`reference/graph-yaml.md:730-738`).

## Required revisions

### R-1: Make the `tool_call` supported `on_error` set a graph-load contract

Fold this exact rule into the Proposed Solution and AC-04: for `type: tool_call`, only absent, `skip`, and `fail` are valid. `on_error: retry`, `on_error: fallback`, and any arbitrary invalid value must fail during graph load, not merely during graph lint, and the error message must name the valid set as `skip, fail`.

The current FR says "`retry`/`fallback` explicitly out" in the solution (`feature-requests/FR-776-tool-call-on-error-fail.md:77-78`), but AC-04 only names "Unknown `on_error` values" (`feature-requests/FR-776-tool-call-on-error-fail.md:93-94`). That leaves a real gap: the generic schema accepts any `ErrorHandler` value (`yamlgraph/models/node_schema.py:281-287`; `yamlgraph/utils/validators.py:151-156`), while the linter already classifies `retry`/`fallback` on non-LLM nodes as unsupported (`yamlgraph/linter/checks_semantic.py:289-300`). The load-time validator must close that gap for `tool_call`; a linter-only failure is not the FR's stated graph-load behavior.

### R-2: Pin requirement ownership to CAP-05

Replace AC-05's "new REQ under CAP-05 or the CAP owning tool_call" with a single instruction: add a new requirement under `capabilities/CAP-05-tool-agent-integration.yaml`, and mark all new/changed tests with that requirement ID. CAP-05 already owns `node_factory/tool_nodes` and the existing `tool_call` requirements (`capabilities/CAP-05-tool-agent-integration.yaml:1-28`); leaving an "or" in the acceptance criterion makes the traceability surface ambiguous.

### R-3: Add the required diary reflection artifact

Add a diary reflection to the acceptance criteria and scope. Repo doctrine requires a metacognitive entry for completed task lists (`.github/copilot-instructions.md:33`) and the branch protection description says `diary-gate` blocks `feat`/`fix` PRs with FR references unless a diary reflection exists in the diff (`.github/copilot-instructions.md:319-320`). FR-776 currently requires docs and changelog only (`feature-requests/FR-776-tool-call-on-error-fail.md:99-100`); add the diary artifact so enforcement does not discover a process failure after implementation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-776-tool-call-on-error-fail.md` revised to fold R-1 through R-3 before enforcement authority activates |
| D-2 | `yamlgraph/node_factory/tool_nodes.py` changed only to support `tool_call` `on_error: skip` default/envelope behavior and `on_error: fail` raising behavior |
| D-3 | Graph-load validation updated only so `type: tool_call` rejects `on_error` values outside absent/`skip`/`fail` |
| D-4 | Unit/regression tests for failing callable, unknown tool, default/skip envelope preservation, load-time rejection of `retry`/`fallback`/invalid values, and the downstream-map misleading-error regression |
| D-5 | `capabilities/CAP-05-tool-agent-integration.yaml` updated with a new requirement for this behavior; all new/changed tests carry `@pytest.mark.req` |
| D-6 | `reference/graph-yaml.md` updated for `tool_call.on_error`; changelog fragment and diary reflection added |

Not authorized: implementing `retry` or `fallback` for `tool_call`; changing agent-node tool error handling or FR-658's agent-loop text-error contract; changing graph-tool callable behavior outside the direct effect of `tool_call` invoking it; migrating `examples/demos/book-summary` or FR-775's frozen graph scope; changing map, router, reducer, expression resolution, linter doctrine, hooks, CI, judge/review/authoring doctrine, or release process; adding new dependencies.

## Revised acceptance criteria

- [ ] AC-01: `on_error: fail` on a `tool_call` node raises at that node when the tool callable throws; the raised error contains the node name, tool name, and original exception message, and preserves exception chaining where applicable.
- [ ] AC-02: `on_error: fail` raises at that node for an unknown tool name; the raised error contains the node name, requested tool name, and "Unknown tool".
- [ ] AC-03: Default behavior with no `on_error`, and explicit `on_error: skip`, is byte-identical to today's envelope for both callable exceptions and unknown tools.
- [ ] AC-04: Graph load rejects `type: tool_call` with any `on_error` value outside `skip`/`fail`, including `retry`, `fallback`, and arbitrary invalid values; the error message names the valid set `skip, fail`.
- [ ] AC-05: Unit tests cover AC-01 through AC-04, including a regression that reproduces the witnessed shape: failed `tool_call` envelope plus downstream map gives a misleading resolution error, while `on_error: fail` names the prerequisite failure at the source.
- [ ] AC-06: A new requirement under `capabilities/CAP-05-tool-agent-integration.yaml` owns the behavior, and all new/changed tests carry `@pytest.mark.req` for that requirement.
- [ ] AC-07: `reference/graph-yaml.md` documents `tool_call.on_error` with `skip`/`fail` semantics and agent-vs-deterministic-pipeline guidance; a changelog fragment is added.
- [ ] AC-08: No changes are made to agent-node tool error handling, FR-658's agent error-text contract, or FR-775's frozen scope; the book-summary graph is not migrated here.
- [ ] AC-09: A diary reflection is included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-3 are folded into `feature-requests/FR-776-tool-call-on-error-fail.md`. | GATE |
| C-2 | `tool_call` supports only absent/`skip`/`fail` in this FR; `retry` and `fallback` behavior require a separate judged FR. | GATE |
| C-3 | The default and `on_error: skip` envelope shape must remain byte-identical for current callers, including unknown-tool envelopes. | GATE |
| C-4 | The unsupported-value rejection must occur at graph load, not only in `yamlgraph graph lint`. | GATE |
| C-5 | Agent-node tool loops and FR-658's "surface error text, do not crash the parent agent" contract must remain unchanged. | GATE |
| C-6 | FR-775's book-summary graph and gate-node workaround remain out of scope; this FR may only create the primitive for future consumers. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add `tool_call` `on_error: fail` with load-time `skip`/`fail` validation, tests, CAP-05 traceability, docs, changelog, and diary evidence, and nothing else.
