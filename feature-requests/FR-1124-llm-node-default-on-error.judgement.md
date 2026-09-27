# Judgement: FR-1124 An LLM node without `on_error` gets a named, documented default

**Verdict:** APPROVED WITH REVISIONS — defaulting top-level `llm` nodes to `fail` is a sound framework primitive, but authority activates only after the FR pins the actual resolution seam, corrects the shared-dispatch cleanup and failure witness, and makes the migration evidence reproducible.

**Reviewed against:** `feature-requests/FR-1124-llm-node-default-on-error.md`; `feature-requests/FR-1124.research.md`; `feature-requests/FR-1083-exit-code-reflects-errors.md`; `feature-requests/FR-1066-exit-code-reflects-errors.judgement.md`; `feature-requests/FR-1097-graph-run-completed-errors-exit-3.md`; `feature-requests/FR-1098-stream-error-event-exit-status.md`; `feature-requests/FR-778-tool-call-on-error-fail.md`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1073-map-result-contract.md`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/llm_execution.py`; `yamlgraph/error_handlers.py`; `yamlgraph/constants.py`; `reference/graph-yaml.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/adapters/README.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and bounded. The FR identifies a concrete silent-success incident, a repository population of 224 undeclared top-level `llm` nodes, and the exact record-and-continue fall-through (FR-1124:8-15, 38-49, 58-84). The chosen default follows the repository's fail-loud doctrine and leaves explicit `skip`, `retry`, and `fallback` available (FR-1124:86-95, 223-232; `.github/copilot-instructions.md:196).

The research is substantive: it preserves `skip` as dissent, distinguishes `tool_call`'s agent-envelope contract, adopts the existing graph-default-plus-node-override shape, and answers `is_this_a_graph` separately for the deterministic default and corpus classification (`FR-1124.research.md:29-58`). Rejected FR-1066 is dispositioned rather than ignored, while FR-1097/FR-1098 and FR-1073 remain separately owned.

Strategically this is a **framework primitive**: the witnessed application and the 134-graph repository population provide more than three use cases, the existing four-value error abstraction fits, but no existing resolution rule names the absent `llm` value. The default, graph override, documentation, witnesses, and migration are one responsibility: replacing one implicit error policy with an explicit policy without silently changing repository graphs. The direction is feasible and directly testable after the seam corrections below.

## Required revisions

### R-1: Resolve the default at the actual top-level `llm` compiler seam

Replace S-1's claim that `yamlgraph/models/node_schema.py` resolves `node value -> defaults.on_error -> "fail"`. `NodeConfig` owns only the node value and currently defaults it to `None` (`node_schema.py:73-86,307`); graph defaults are a separate untyped field validated by `GraphConfigSchema` (`graph_schema.py:94,127-133`).

Freeze the implementation as follows:

1. `GraphConfigSchema` validates `defaults.on_error` against the four `ErrorHandler` values and names the offending value.
2. `_compile_llm_node` computes an effective copy for an authored top-level node whose declared type is exactly `llm`: explicit node `on_error` -> `ctx.effective_defaults["on_error"]` -> `"fail"`, then passes that copy to `create_node_function`.
3. The shared `llm`/`router` compiler must condition this normalization on declared type `llm`; router remains unchanged (`node_compiler.py:251-263,296`).
4. Map sub-nodes remain unchanged. They enter `create_node_function` through `compile_map_node`, not `_compile_llm_node` (`map_compiler.py:255-318`).
5. Race and every other node type remain unchanged.

Amend S-1, S-2, the Not in scope list, and AC-2/AC-3 to state that exact boundary. Add witnesses proving top-level `llm` resolution and proving that an undeclared router and an undeclared map `llm` sub-node retain their current behavior. Do not infer top-level status from a generated node-name prefix.

### R-2: Correct the failure witness and retain the shared default fallback

Remove the requirement that the propagated exception itself names the node. `handle_fail` logs the node and re-raises the original exception unchanged (`error_handlers.py:91-105`); changing that shared contract is neither necessary nor authorized. The RED/GREEN witness must instead assert that the original exception propagates and that the downstream node does not execute.

Delete the claim that FR-1083 paths P2, P3, and P5 call `handle_default`. Retry exhaustion and fallback failure construct their own `PipelineError`, while missing `requires:` returns one directly; the only code call to `handle_default` is the shared `handle_error` fall-through (`llm_execution.py:127-166`; `error_handlers.py:108-181`). Because routers and map `llm` sub-nodes are excluded by R-1, retain `handle_default` and its shared fall-through. Replace AC-2's deletion/vulture requirement with a reachability witness: an authored top-level `llm` can never reach the fall-through after resolution, while an explicitly excluded node kind still can.

### R-3: Make the migration ledger exhaustive, reproducible, and honest about `skip`

Replace the fixed “every one of the 224 nodes” gate with a deterministic current-population reconciliation:

1. Record the exact discovery command or committed discovery script, roots, inclusion rule (“authored top-level node with declared/default type `llm`”), exclusions, git SHA, discovered total, and comparison with the filing baseline of 224.
2. Require one ledger row for every discovered eligible node and mechanically assert that the discovered identity set equals the ledger identity set with no duplicates or omissions.
3. Each row must contain graph path, node name, `state_key`, downstream reader or terminal edge, A/B class, source evidence, and resulting policy.
4. Define A as “adopts the new fail default; no graph edit.” Define B as “the author intentionally chooses tolerated continuation”; B receives explicit node `on_error: skip`, or graph `defaults.on_error: skip` only when every eligible `llm` in that graph is B. Do not describe B as preserving record-and-continue: `skip` deliberately changes the error to tolerated and adds skip state markers.
5. Reconcile the census graph's classification claims against the deterministic inventory before authoring. Empty, duplicate, or unknown identities fail the migration.
6. For every B edit, cite a committed authoring brief and record the adapter report's required validation outcome in the FR implementation record. The report itself remains the route artifact at `tmp/draft-authoring-report.md`, as required by graph-authoring doctrine (`doctrine.md:61-89`); do not require that transient file to be committed.

Amend S-5, S-6, AC-5, and AC-6 accordingly. The census artifact remains committed; class B graph edits still use `scripts/author.sh`, lint, and the narrowest honest smoke attempt.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `GraphConfigSchema` validation for `defaults.on_error` |
| D-2 | Top-level authored `type: llm` effective-policy resolution at `_compile_llm_node` |
| D-3 | Unit witnesses for fail default, graph override, node override, invalid default, downstream non-execution, and excluded node kinds |
| D-4 | `reference/graph-yaml.md` common-node, value, and defaults tables |
| D-5 | Deterministic inventory plus committed A/B census ledger |
| D-6 | Governed class B graph edits, committed briefs, validation records, and implementation counts |
| D-7 | Requirement traceability, changelog fragments, FR implementation record, and Distill diary entry |

Not authorized: router, race, map sub-node, `tool_call`, python, tool, copilot, agent, subgraph, or guard default changes; a fifth error strategy; changes to `handle_fail` exception identity; deletion of the shared `handle_default` fall-through; CLI tally/exit semantics; FR-1097/FR-1098 expectation changes; map-result policy changes; broad caller migrations; CI, hooks, judge/review doctrine, or authoring doctrine changes.

## Revised acceptance criteria

- [ ] AC-01: RED first: a two-node graph whose first authored top-level `llm` has no `on_error` and whose stub provider raises returns normally with one untolerated error on main; after GREEN the original exception propagates and the downstream node is not invoked. RED and GREEN are separate commits.
- [ ] AC-02: Resolution tests prove explicit node value -> `defaults.on_error` -> `fail` for authored top-level `llm` nodes, and the resolved `LLMNodeConfig.on_error` is one of the four `ErrorHandler` values.
- [ ] AC-03: `defaults.on_error` accepts exactly `skip`, `retry`, `fail`, and `fallback`; an invalid value fails graph load naming `defaults.on_error` and the value; an explicit node value overrides it.
- [ ] AC-04: An undeclared router, race node, and map `llm` sub-node retain their current policies; `defaults.on_error` does not alter them.
- [ ] AC-05: The shared `handle_default` fall-through remains available to excluded callers, while a test proves an authored top-level `llm` cannot reach it after effective-policy resolution.
- [ ] AC-06: `defaults.on_error: skip` on a top-level `llm` records exactly one tolerated error, sets the existing skip markers, and permits the downstream node; explicit node `fail` under that default propagates the original exception.
- [ ] AC-07: `reference/graph-yaml.md` documents the top-level `llm` default and priority in the common-node, `on_error` value, and `defaults` tables, and does not present record-and-continue as a supported authored mode.
- [ ] AC-08: A deterministic inventory at the implementation SHA emits every eligible top-level repository `llm` identity; the committed census ledger has exactly the same identity set, no duplicates, A/B counts, evidence, and resulting policy, and reconciles any difference from the filing baseline of 224.
- [ ] AC-09: Every B row has explicit `on_error: skip`, or belongs to a graph using `defaults.on_error: skip` whose every eligible `llm` is B. Each edited graph cites a committed authoring brief and has a verified adapter report, passing lint, and a narrow smoke attempt or an exact blocked-validation record.
- [ ] AC-10: No A graph is edited solely to restate `fail`; no graph outside the B ledger is changed by the migration.
- [ ] AC-11: Focused FR-1124 tests, FR-1097/FR-1098 error-status regressions, the full unit suite, strict requirement coverage, and lint over the deterministic graph inventory pass.
- [ ] AC-12: All new tests carry the governing REQ ID; the implementation record names the RED/GREEN commits, inventory SHA and counts, A/B counts, authoring runs, validation outcomes, and deviations.
- [ ] AC-13: Separate `removal` and `feat` changelog fragments describe the removed implicit policy and `defaults.on_error`; a Distill diary entry contains `**Seed:**`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-1124 before production or graph changes begin; authority is inactive until the fold is recorded in the FR. | GATE |
| C-2 | The effective default applies only to authored top-level `type: llm` nodes; excluded node kinds retain current semantics. | GATE |
| C-3 | Do not change or wrap the exception re-raised by shared `handle_fail`, and do not delete the shared `handle_default` path. | GATE |
| C-4 | The deterministic inventory and census ledger must reconcile exactly before any class B authoring run. | GATE |
| C-5 | Every class B graph edit must use the sole graph-authoring route with a committed brief and honest lint/smoke evidence. | GATE |
| C-6 | RED precedes GREEN; framework behavior lands before migration, and the full inventory is re-run after migration to detect drift. | GATE |
| C-7 | Any need to change router, race, map sub-node, CLI, or shared error-handler semantics requires a separate judged FR. | GATE |

Authority granted: after R-1 through R-3 are folded, implement the top-level `llm` fail default, its graph-level override, documentation and witnesses, then perform only the reconciled class B migration and its required records.
