# Judgement: FR-1058 Restore RunnableConfig propagation and native `mode: direct` subgraphs

**Verdict:** APPROVED WITH REVISIONS — the defect and minimal repair are sound, but authority activates only after the research record, OTEL enablement criterion, canonical observability contract, and wrapper test matrix are made internally consistent and mechanically enforceable.

**Prior art:** the only noun-overlap hit is `FR-1058-subgraph-runnable-config-propagation.md` [Judged] — the FR this judgement governs, not independent prior art. Substantive prior art (FR-759, FR-797, rejected FR-210) is dispositioned in that FR's §Prior art table, folded as R-1.

**Reviewed against:** `feature-requests/FR-1058-subgraph-runnable-config-propagation.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-759-otel-observability-boundary.judgement.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.judgement.md`; `feature-requests/FR-210-subgraph-interrupt-state-commit.md`; `feature-requests/fix-subgraph-interrupt-output-mapping.md`; `feature-requests/030-subgraph-token-streaming.md`; `feature-requests/036-map-subgraph-subnodes.md`; `feature-requests/FR-103-ebook-judge-amend-subgraph.md`; `yamlgraph/compile/node_otel.py`; `yamlgraph/compile/subgraph_relay.py`; `yamlgraph/node_factory/subgraph_nodes.py`; `tests/unit/test_otel_observability.py`; `tests/unit/test_subgraph.py`; `reference/otel-observability.md`; `reference/getting-started.md`; `reference/development-operations.md`; `capabilities/CAP-11-subgraph-map.yaml`; `capabilities/CAP-212-otel-observability-boundary.yaml`; `ARCHITECTURE.md`. Issue #474 and its attached patch were not consumed; their claims were assessed only as represented in the committed FR.

## What is sound

The problem is real and the causal account matches the committed implementation. `_maybe_wrap_otel()` exposes only `otel_wrapped(state)` and calls `node_fn(state)` in both branches (`yamlgraph/compile/node_otel.py:16-43`), while invoke and relay subgraph functions explicitly accept `config` (`yamlgraph/node_factory/subgraph_nodes.py:210-216`, `:251-255`). The subgraph compiler also wraps the non-tuple value returned for direct mode before registration (`yamlgraph/compile/subgraph_relay.py:20-38`), even though direct mode returns the compiled graph object itself (`yamlgraph/node_factory/subgraph_nodes.py:196-200`). These facts support both reported failures without relying on the external issue.

The proposed boundary is minimal and architecture-aligned. Direct children should remain native compiled graphs, while separately invoked children should receive `RunnableConfig`; the existing child-config helper already derives `parent_thread:node_name` when a parent thread is present (`yamlgraph/node_factory/subgraph_nodes.py:71-97`). Preserving user configurable values while removing parent executor/checkpoint routing handles is also coupled to config restoration rather than an orthogonal feature: forwarding config without sanitizing those handles would cross the separately invoked child boundary that FR-797's relay deliberately owns (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:101-129`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:117-124`).

Scope and single responsibility are sound. The timeout wrapper is explicitly excluded after the FR demonstrates that no compiler-produced config-aware node reaches it (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:112-168`). Direct execution, invoke-mode thread identity, and relay resume isolation are three concrete uses of the same subgraph primitive, so the strategic classification is **Framework primitive**, not an example or documentation-only pattern. The existing requirements place the affected behavior at the subgraph and OTEL framework boundaries (`capabilities/CAP-11-subgraph-map.yaml:17-20`; `capabilities/CAP-212-otel-observability-boundary.yaml:25-47`; `ARCHITECTURE.md:729`, `:2709`).

The FR is testable in principle: it names behavioral witnesses for native direct invocation, durable direct-child interruption, config forwarding through a compiled graph, distinct child thread identities, and routing-key filtering (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:179-195`). The revisions below correct the remaining ambiguities rather than changing the chosen design.

## Required revisions

### R-1: Repair the committed research and prior-art audit trail

Replace the claim that every alternatives row carries an executed probe (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:11-13`): alternative 1 is explicitly a mental application, not an executed probe (`:201`). Either replace that cell with a real executed witness or describe the table honestly as a mixture of executed probes and direct deductions from cited probes. Add the required `is_this_a_graph` answer: **No — this is a deterministic compiler/runtime bug fix with no per-item LLM work, multi-stage LLM pipeline, or agent fan-out; no existing graph applies.**

Add a `Prior art` field or subsection that mechanically dispositions FR-759, FR-797, and rejected FR-210 rather than only listing related identifiers. Fold these exact distinctions: FR-759 introduced the wrapper and its broad subgraph-span claim, which this FR narrows; FR-797 owns the invoke-mode commit-before-pause relay, which this FR preserves by stripping parent executor routing handles; FR-210's rejected monolithic relay/compiler plan is not reopened because this FR changes neither relay topology nor edge/state compilation.

### R-2: Correct the OTEL switch and update every canonical coverage claim

Replace `YAMLGRAPH_OTEL_ENABLED` in the direct-mode acceptance criterion (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:181-182`) with the actual two states: `YAMLGRAPH_OTEL_EXPORT` unset and `YAMLGRAPH_OTEL_EXPORT=otlp`. The repository consistently defines that switch in `reference/getting-started.md:195`, `reference/development-operations.md:131`, and `ARCHITECTURE.md:2709`.

The accepted loss of the synthetic outer span for direct subgraphs must update all canonical claims, not only `reference/otel-observability.md`. Amend `reference/otel-observability.md:87-88,104-108`, `capabilities/CAP-212-otel-observability-boundary.yaml:13-20`, and the REQ-YG-570 text in `ARCHITECTURE.md:2709` to distinguish invoke/relay subgraph functions, which retain an outer `yamlgraph.node.execute` span, from native direct subgraphs, whose child nodes remain instrumented but whose compiled-graph container has no synthetic outer node span.

### R-3: Freeze the wrapper behavior matrix

Expand the config-forwarding criterion into four behavioral cases exercised through compiled LangGraph execution:

1. config-aware node with OTEL disabled receives the non-`None` `RunnableConfig`;
2. config-aware node with OTEL enabled receives the same config and emits its node span;
3. state-only node with OTEL disabled remains callable and receives only state;
4. state-only node with OTEL enabled remains callable, receives only state, and emits its node span.

Assertions must inspect the called function's received payload, not only `inspect.signature`. This preserves FR-759's disabled no-op contract (`feature-requests/FR-759-otel-observability-boundary.md:57-64`) while proving that the new two-parameter wrapper does not leak `config=` into state-only callables. Keep the direct compiled graph outside `_maybe_wrap_otel`; no callable adapter around direct mode is authorized.

### R-4: Make child-config sanitization non-mutating and exact

Revise the `_build_child_config` criterion to assert all of the following in one table-driven test: outer `RunnableConfig` values such as `tags`, `metadata`, and callbacks are retained; ordinary user `configurable` keys are retained; the child thread id is derived as `{parent_thread}:{node_name}`; every `__pregel_*` key plus `checkpoint_id`, `checkpoint_ns`, and `checkpoint_map` is absent from the child `configurable`; and the input parent config is unchanged. The current tests prove only thread derivation and generic value retention (`tests/unit/test_subgraph.py:431-470`), so they cannot condemn accidental mutation or executor-handle leakage.

### R-5: Pin traceability and durable witnesses

Tag wrapper/observability witnesses with `REQ-YG-570` and subgraph behavior/config witnesses with `REQ-YG-042`; a cross-boundary end-to-end witness may carry both markers. Add `python scripts/req_coverage.py --strict` to the acceptance commands. Preserve the durable direct-child witness exactly as a close/reopen test using `SqliteSaver`; an in-memory saver or uninterrupted connection is not equivalent to the persistence claim at `feature-requests/FR-1058-subgraph-runnable-config-propagation.md:183-184`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/compile/node_otel.py`: config-transparent OTEL wrapper for callable nodes |
| D-2 | `yamlgraph/compile/subgraph_relay.py`: native, unwrapped registration for direct compiled subgraphs; existing invoke/relay wrapping retained |
| D-3 | `yamlgraph/node_factory/subgraph_nodes.py`: non-mutating child-config derivation and parent executor/checkpoint routing-key removal |
| D-4 | Focused unit/integration witnesses for direct invocation, durable direct-child resume, wrapper behavior, child-config filtering, and independent parent-thread relay |
| D-5 | `reference/otel-observability.md`, `capabilities/CAP-212-otel-observability-boundary.yaml`, and `ARCHITECTURE.md` coverage wording |
| D-6 | FR-1058 revision/status record and a `type: fix` changelog fragment |

Not authorized: changes to `yamlgraph/node_timeout.py` or `_maybe_wrap_timeout()`; new timeout-wrapper tests; relay topology, edge compilation, state-field synthesis, or interrupt semantics from FR-797; graph or prompt artifact creation/modification; LangGraph dependency changes; new configuration flags; OTEL span-schema changes beyond accurately narrowing direct-subgraph coverage; streaming/async subgraph expansion; or changes to unrelated node types.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-5 are folded into FR-1058 before enforcement begins, including an honest research-evidence statement, the explicit `is_this_a_graph` answer, and dispositions of FR-759, FR-797, and FR-210.
- [ ] AC-02: A parent with a direct child compiles and invokes successfully with `YAMLGRAPH_OTEL_EXPORT` unset and with `YAMLGRAPH_OTEL_EXPORT=otlp`; registration preserves the native compiled graph rather than wrapping it in a callable adapter.
- [ ] AC-03: With OTEL enabled, a direct subgraph emits no synthetic outer subgraph-node span, while its executed child nodes remain instrumented.
- [ ] AC-04: A direct child that interrupts is resumed successfully through `SqliteSaver` after the saver connection is closed and reopened, proving preservation of the native checkpoint namespace.
- [ ] AC-05: Through compiled LangGraph execution, config-aware and state-only callables satisfy all four enabled/disabled wrapper cases in R-3, with assertions on received arguments and emitted spans.
- [ ] AC-06: Two parent thread ids, `parent-a` and `parent-b`, invoking the same invoke/relay subgraph produce `parent-a:child` and `parent-b:child`, then resume independently without reading or corrupting the other checkpoint.
- [ ] AC-07: A table-driven `_build_child_config` witness proves preservation, derivation, filtering, and non-mutation exactly as specified in R-4.
- [ ] AC-08: `reference/otel-observability.md`, CAP-212, and REQ-YG-570 distinguish invoke/relay outer spans from native direct-subgraph child-node-only instrumentation.
- [ ] AC-09: `yamlgraph/node_timeout.py` and `_maybe_wrap_timeout()` are unchanged; no hand-composed timeout-plus-OTEL test is introduced.
- [ ] AC-10: Focused tests pass, every new test carries the governing `REQ-YG-042` and/or `REQ-YG-570` marker, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: A RED commit containing the condemning behavioral witnesses precedes the GREEN implementation commit, and `changelog/unreleased/` contains a `type: fix` fragment naming FR-1058 and the governing requirements.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the committed FR before implementation authority activates. | GATE |
| C-2 | Register direct compiled subgraphs natively; do not recover the lost outer span with `RunnableLambda`, another callable wrapper, or any adapter that hides the compiled graph type. | GATE |
| C-3 | Do not forward parent `__pregel_*` or checkpoint routing fields into separately invoked children, and do not mutate the parent config while filtering them. | GATE |
| C-4 | Preserve FR-797's relay topology and commit-before-pause behavior; timeout, edge, state-builder, and interrupt-flow changes require separate authority. | GATE |
| C-5 | Update the reference, CAP, and architecture requirement together so shipped observability claims match the accepted direct-mode span narrowing. | GATE |
| C-6 | Do not create or modify graph/prompt artifacts for witnesses under this authority; construct fixtures in tests or use existing committed artifacts unchanged. | GATE |

Authority granted: after the required revisions are folded into FR-1058, the enforcer may restore `RunnableConfig` propagation for OTEL-wrapped callable nodes, register direct subgraphs natively, sanitize separately invoked child configs, and add only the frozen tests, contract updates, and changelog evidence above.
