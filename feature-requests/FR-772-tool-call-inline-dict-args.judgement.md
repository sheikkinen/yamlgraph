# Judgement: FR-772 tool_call Inline Dict Args with Per-Value Resolution

**Prior art:** FR-772-tool-call-inline-dict-args.md is the FR under judgement (self-hit). FR-658 (tool_call origin), FR-252 (variables resolution), FR-771 (blocked consumer whose C-2 mandated this FR) are dispositioned in the FR's Prior art line and re-examined below.

**Verdict:** APPROVED WITH REVISIONS — the core capability is real, small, and aligned with existing resolver patterns, but authority activates only after the FR narrows its missing-placeholder guarantee and freezes the requirement registry surface.

**Reviewed against:** `feature-requests/FR-772-tool-call-inline-dict-args.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.md`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.judgement.md`; `feature-requests/FR-252-python-node-variables.md`; `feature-requests/FR-658-graph-as-tool.md`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/utils/expressions.py`; `reference/graph-yaml.md`; `tests/unit/test_tool_call_node.py`; `yamlgraph/linter/checks_semantic.py`; `tests/unit/test_linter_fr025.py`; `capabilities/CAP-05-tool-agent-integration.yaml`; `capabilities/CAP-06-routing-flow-control.yaml`; `capabilities/CAP-15-expression-language.yaml`; `capabilities/CAP-216-tool-manifests.yaml`; `capabilities/CAP-217-shared-vision-tool.yaml`.

## What is sound

The problem is real and already isolated by the governing consumer. FR-771 is explicitly blocked because current `tool_call` resolves `args` once, leaves inline dict values unresolved, and grants no authority to patch core under FR-771 (`feature-requests/FR-771-vision-demo-executes-manifest-tool.md:5`, `80-91`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.judgement.md:21-39`, `80-82`). FR-772 states the same concrete defect: `resolve_template(args_expr, state)` returns non-string values unchanged, so an inline dict reaches the tool with literal `"{state.image}"` inside (`feature-requests/FR-772-tool-call-inline-dict-args.md:28-33`; `yamlgraph/node_factory/tool_nodes.py:38-68`; `yamlgraph/utils/expressions.py:192-193`).

The proposed implementation is minimal and conforms to an existing abstraction. FR-772 reuses `resolve_node_variables()` instead of inventing a new resolver (`feature-requests/FR-772-tool-call-inline-dict-args.md:51-66`), and FR-252 established that function as the per-key variable-resolution mechanism for node configuration (`feature-requests/FR-252-python-node-variables.md:37-50`, `84-90`). The existing resolver preserves resolved value types (`yamlgraph/utils/expressions.py:241-265`), which directly supports AC-02 (`feature-requests/FR-772-tool-call-inline-dict-args.md:77-78`).

The scope is single-purpose: one node surface, one docs section, targeted tests, requirement traceability, and a changelog fragment (`feature-requests/FR-772-tool-call-inline-dict-args.md:72-90`). That is the right framework-primitive classification because FR-658 authorized `tool_call` as a direct invocation seam (`feature-requests/FR-658-graph-as-tool.md:28-30`, `73-75`), the current reference only documents whole-dict state args (`reference/graph-yaml.md:696-706`), and FR-771 supplies the first committed consumer (`feature-requests/FR-772-tool-call-inline-dict-args.md:8-9`).

The acceptance criteria are mostly mechanically testable. Existing unit tests already exercise dynamic tool and args resolution through `create_tool_call_node()` (`tests/unit/test_tool_call_node.py:47-188`), and the linter already extracts string values from dict-shaped `args` for state-reference validation (`yamlgraph/linter/checks_semantic.py:232-241`). That makes the requested tests feasible without broad graph-loader or linter redesign.

## Required revisions

### R-1: Align the unresolved-placeholder guarantee with the resolver actually being reused

Revise the Ideal Result and AC-04 so they do not promise broader behavior than `resolve_node_variables()` provides, unless the FR explicitly authorizes an additional validation branch.

The current FR says unresolved garbage kwargs are impossible and that no inline-args dispatch ever contains a literal `"{state."` string (`feature-requests/FR-772-tool-call-inline-dict-args.md:46-49`, `82-84`). But the proposed solution delegates to `resolve_node_variables()` (`feature-requests/FR-772-tool-call-inline-dict-args.md:56-66`), and that resolver delegates each value to `resolve_template()` (`yamlgraph/utils/expressions.py:259-265`). `resolve_template()` leaves missing embedded interpolation placeholders unchanged (`yamlgraph/utils/expressions.py:195-206`) while simple missing `{state.path}` expressions resolve through `resolve_state_path()` to `None` (`yamlgraph/utils/expressions.py:24-52`, `232-237`).

Fold one exact contract into the FR:

1. Narrow AC-04 to the supported FR-252 semantics: simple inline values like `image: "{state.image}"` must resolve per key, preserve non-string types, and must not pass the original literal when the state path exists; missing keys follow current `resolve_template()` behavior exactly; or
2. Authorize and specify a new inline-args validation rule that rejects any resolved inline arg still containing `"{state."`, with a test for embedded interpolation such as `"prefix {state.missing}"`. If this option is chosen, state that this validation applies only to the new inline-dict `tool_call.args` branch and does not change global `resolve_template()` behavior.

### R-2: Freeze the requirement registry destination

Replace AC-06's "new capability file (or CAP-06 routing/flow-control extension — enforcer picks per registry convention)" with one exact registry instruction. Delegating architecture classification to the enforcer is not a measurable acceptance criterion (`feature-requests/FR-772-tool-call-inline-dict-args.md:87-89`), and repo doctrine requires new tests to be tagged to a concrete requirement while new capabilities live in capability YAML (`.github/copilot-instructions.md:173-176`).

The strongest registry fit is CAP-05 Tool & Agent Integration because it already owns `node_factory/tool_nodes` and `REQ-YG-017` dynamic tool node creation (`capabilities/CAP-05-tool-agent-integration.yaml:1-18`). CAP-06 owns routing and flow control, not tool kwargs dispatch (`capabilities/CAP-06-routing-flow-control.yaml:1-32`). CAP-15 owns the expression resolver itself (`capabilities/CAP-15-expression-language.yaml:1-19`), but this FR reuses that resolver rather than changing its general contract. Revise AC-06 to require `REQ-YG-576` under CAP-05, unless the FR deliberately chooses a different exact CAP and explains why in the FR before enforcement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-772-tool-call-inline-dict-args.md` revised to fold R-1 and R-2 |
| D-2 | `yamlgraph/node_factory/tool_nodes.py` inline-dict branch for `tool_call.args` |
| D-3 | `tests/unit/test_tool_call_node.py` or a tightly scoped successor unit test file for inline dict args, type preservation, string-form regression, and missing-placeholder semantics |
| D-4 | `reference/graph-yaml.md` `tool_call` section documenting both string-form and inline-mapping forms |
| D-5 | `capabilities/CAP-05-tool-agent-integration.yaml` updated with `REQ-YG-576` unless the revised FR freezes a different exact CAP |
| D-6 | One changelog fragment under `changelog/unreleased/` with `req: REQ-YG-576` |

Not authorized: recursive deep resolution beyond current `resolve_node_variables()` semantics; global `resolve_template()` behavior changes; passthrough, python-node, graph-loader, manifest-loader, or shared-vision demo edits; linter rule changes except directly related tests if existing `args` dict validation must be documented; graph artifact edits under `examples/`; CI, hook, judge/review doctrine, or release-process changes.

## Revised acceptance criteria

- [ ] AC-01: `tool_call.args` accepts an inline YAML mapping and resolves each top-level value through `resolve_node_variables()` before dispatch; a recording callable proves templated values resolve from state, literals pass through unchanged, and the tool receives the resolved kwargs.
- [ ] AC-02: Inline dict arg values that resolve to non-string state values, including at least an int, list, and dict, are passed to the callable with their original types intact.
- [ ] AC-03: The existing string form `args: "{state.tool_arguments}"` still resolves once through `resolve_template()` and behaves as before, proven by a regression test alongside existing `tool_call` tests.
- [ ] AC-04: Missing or unresolved inline arg behavior matches the revised R-1 contract exactly, with tests for a simple missing state path and, if the FR chooses rejection, an embedded interpolation placeholder.
- [ ] AC-05: `reference/graph-yaml.md` documents both `args: "{state.tool_arguments}"` and inline mapping forms, including the deterministic `describe_image`-style example.
- [ ] AC-06: `REQ-YG-576` is added to the exact capability file frozen in the revised FR, and every new/changed test function is marked with `@pytest.mark.req("REQ-YG-576")`.
- [ ] AC-07: A changelog fragment is added under `changelog/unreleased/` with `req: REQ-YG-576`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 and R-2 are folded into `feature-requests/FR-772-tool-call-inline-dict-args.md`. | GATE |
| C-2 | The implementation must branch on the YAML shape of `args`: dict form uses per-value `resolve_node_variables()`, non-dict/string form keeps the existing `resolve_template()` path. | GATE |
| C-3 | The string-form behavior and its existing silent `{}` non-dict fallback are not to be broadened or repaired under this FR; any cleanup of that older behavior requires separate authority. | GATE |
| C-4 | If the enforcer chooses placeholder rejection under R-1 option 2, rejection must be explicit and tested for inline dict args only; do not change global `resolve_template()` interpolation semantics. | GATE |
| C-5 | No graph authoring or shared-vision demo enforcement is authorized here; FR-771 may resume only after this core capability lands. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add inline-dict `tool_call.args` per-value resolution, its directly related tests, documentation, requirement registry entry, and changelog fragment only.
