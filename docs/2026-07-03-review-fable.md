# Codebase Review — 2026-07-03 (Fable)

Reviewer: Claude Fable 5 (agent session). Scope: full `yamlgraph/` package.
Method: automated tooling baseline (ruff, bandit, radon, vulture, import-linter,
module sizes) + two parallel exploration passes (core pipeline, peripheral layers)
+ manual verification of top claims. Analysis log: `logs/review-analysis.log`.

## Automated Baseline

| Tool | Result |
|------|--------|
| ruff | All checks passed |
| vulture | Clean (with whitelist) |
| import-linter | Both contracts KEPT (three-layer, linter LLM-free) |
| bandit | 1 High + 3 Medium, all confessed via `# noqa` + `docs/confessions.md` |
| TODO/FIXME | Zero in `yamlgraph/` |
| radon | 21 blocks at grade C, average complexity C (14.06) |
| Module sizes | 5 modules in the 435–450 band (hard ceiling 450) |

The hygiene gates are working. Remaining findings are structural.

## Issues (verified)

### 1. Dual `error`/`errors` state fields with divergent writers — HIGH → FR-668

`models/state_builder.py:66` declares singular `error` (last_value reducer)
alongside `errors` list (add reducer). Writers diverge:

- `node_factory/tool_nodes.py:75,86` writes singular `error`
- LLM nodes append `PipelineError` to `errors` list
- `storage/export.py:170` reads singular `error`

In parallel map fan-out, last-write-wins on `error` loses branch failures.
A user inspecting `state["error"]` after a map node sees only the last
branch's failure.

**Recommendation**: FR to deprecate singular `error`; converge on the
`errors` list everywhere. Correctness defect under parallelism.
Filed as `feature-requests/FR-668-converge-error-errors-state-fields.md`.

### 2. FR-464 structured-output fallback re-raises the wrong error — MEDIUM → FR-669

`executor.py:~186-196` (`_invoke_with_retry`): when structured output is
rejected and the code falls back to JSON extraction, `extract_json()` returns
the *original string* when no JSON is found (`utils/json_extract.py`). The
`isinstance(parsed, dict)` check fails and control falls through to `raise`,
re-raising the opaque provider `response_format` error instead of
"could not extract JSON from LLM response".

Not silent — but the diagnostic points at the wrong cause. Boundary
normalization gap at the schema boundary.

**Recommendation**: explicit raise with the extraction failure and a text
snippet when `parsed` is not a dict/list.
Filed as `feature-requests/FR-669-structured-fallback-raise-extraction-error.md`.

### 3. Silent empty-string fallback in A2A client — MEDIUM → FR-670

`contrib/a2a_client.py:49-67` (`_extract_text_from_result`): returns `""`
when neither artifacts nor status message contain text parts. Direct
Commandment 6 violation ("when a filter yields nothing, raise — never
substitute"). Caller cannot distinguish empty response from malformed
response.

**Recommendation**: raise `ValueError("A2A response contains no text parts")`.
Filed as `feature-requests/FR-670-a2a-client-raise-on-empty-response.md`.

### 4. MCP `_handle_run_graph` swallows exceptions unlogged — MEDIUM → FR-671

`mcp_server.py:315-321` returns `{"error": f"Graph execution failed: {e}"}`
with no `logger.error(..., exc_info=True)`. The outer tool handler at
`mcp_server.py:247` *does* log with `exc_info=True` — inconsistency between
the two handlers. Provider auth failures, compile errors, and runtime
failures all become an opaque JSON string with no trace.

**Recommendation**: add `logger.error(..., exc_info=True)` before returning.
Filed as `feature-requests/FR-671-mcp-log-graph-execution-failures.md`.

### 5. Untyped `node_config` dicts flow through node compilation — MEDIUM → FR-673

`node_compiler.py` hands raw `dict[str, Any]` node configs to node factories
(`node_factory/llm_nodes.py:46`, `copilot_node.py:197`). A YAML typo
(`promtp:` instead of `prompt:`) defaults to `None` and only fails at node
execution time. The `NodeConfig` Pydantic schema exists in
`models/graph_schema.py` but is used for validation only — it is not the
object passed to the factories.

**Recommendation**: pass validated `NodeConfig` instances (or validate shape
at the `node_compiler` boundary). Classic normalize-at-the-boundary gap.
Filed as `feature-requests/FR-673-node-config-boundary-validation.md`.

## Refactoring Opportunities

### Module-size band (one edit from the 450 ceiling) → FR-674

| Module | Lines | Suggested split |
|--------|-------|-----------------|
| `node_compiler.py` | 447 | Extract `NODE_TYPE_HANDLERS` dispatch + per-type compile helpers |
| `models/state_builder.py` | 442 | Extract `generate_typeddict_code` → `models/codegen.py` |
| `models/graph_schema.py` | 441 | Extract guard/verification configs → `models/guard_schema.py` |
| `linter/checks_semantic.py` | 435 | Split cycle checks from cross-reference checks |
| `executor_async.py` | 435 | Shrinks naturally with retry extraction (below) |

Split proactively, not mid-feature when the ceiling forces it.
Filed as `feature-requests/FR-674-proactive-module-splits.md`.

### Sync/async retry duplication → FR-672

`_invoke_with_retry` retry/backoff/schema-hint logic exists in both
`executor.py` and `executor_async.py`. Drift risk: resilience characteristics
can silently diverge between sync and async callers. Extract a shared retry
policy into `executor_base.py` (which already holds shared message prep).
Filed as `feature-requests/FR-672-extract-shared-retry-policy.md`.

### Guard evaluation duplication

Pre/post guard evaluation loops duplicated in `node_factory/llm_nodes.py`
(`_evaluate_pre_guards` / `_evaluate_post_guards`) and inlined again in
`node_factory/copilot_node.py`. Consolidate into `node_factory/guard_runtime.py`.

### `cli/graph_run_helpers.py` module boundary

271 lines, exports nothing, consumed via `_underscore` names from
`graph_commands.py`. Load-bearing module masquerading as private. Promote
names + add `__all__`, or fold into `cli/helpers.py`.

### Var-parsing boilerplate

`load_var_file` + `parse_vars` merge repeated in `cmd_graph_run`
(`cli/graph_commands.py:89-90`) and `cmd_graph_bench`
(`cli/bench_commands.py:264-283`). One `load_all_variables(args)` in
`cli/helpers.py`.

### Complexity hotspots (radon grade C, avg 14)

Worst-first candidates: `utils/llm_providers.dispatch_provider`,
`utils/llm_factory.create_llm`, `cli/bench_commands.cmd_graph_bench`,
`diary/importer.import_scheduled_entries`, `utils/fsm/graph_runner._resolve_event`
and `run_and_dispatch`. The FSM modules carry the highest incident density
per the diary (incident_density_ranking) — highest-value decomposition target.

## Extension Opportunities

1. **Open node-type registration** — `NODE_TYPE_HANDLERS` in
   `node_compiler.py` is a closed dict. A `register_node_type()` API lets
   applications add node types without forking. Fits "build for agents first".
2. **Sync compiled-graph cache** — async path caches via `graph_cache`; sync
   `invoke_graph()` recompiles every call. Matters for MCP server throughput
   (each tool call recompiles the graph).
3. **New linter checks**: recursive subgraph cycle detection;
   declared-but-never-written state fields; `tool_call` arg schema vs. tool
   signature validation.
4. **`ProviderCapabilities` model** — provider differences (caching, vision,
   thinking budgets) are scattered `if provider ==` logic in `llm_factory` /
   `llm_providers` (both grade-C). A capability registry flattens both
   hotspots and normalizes at the provider boundary.
5. **CLI ergonomics**: `--watch` re-run for iterative graph development;
   `yamlgraph tool info <name>` introspection.

## Priority Order

1. FR-668 (`error`/`errors`) — correctness under parallelism
2. FR-669, FR-670, FR-671 — boundary/fallback defects, small fixes
3. FR-672 (sync/async retry extraction) — drift prevention; sequence after
   or fold in FR-669
4. FR-673 (node config boundary validation), FR-674 (module splits) —
   FR-674 before or interleaved with FR-668/672/673
5. Extensions as demand-driven FRs (not yet filed)

## Filed Feature Requests

| FR | Finding | Priority |
|----|---------|----------|
| FR-668 | Converge dual `error`/`errors` state fields | HIGH |
| FR-669 | Raise extraction failure in FR-464 fallback | MEDIUM |
| FR-670 | Raise on empty A2A response | MEDIUM |
| FR-671 | Log MCP graph execution failures | MEDIUM |
| FR-672 | Extract shared retry policy to `executor_base` | MEDIUM |
| FR-673 | Node config `extra="forbid"` at load boundary | MEDIUM |
| FR-674 | Proactive module splits (435–450 band) | LOW |

Guard-evaluation dedup, `graph_run_helpers` boundary, var-parsing
consolidation, complexity hotspots, and all extension opportunities remain
unfiled — demand-driven.
