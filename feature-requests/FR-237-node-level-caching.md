# Feature Request: FR-237 Node-Level Caching via CachePolicy

**Priority:** HIGH
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-18

## Summary

Add per-node result caching using LangGraph's native `CachePolicy` API. Nodes with identical inputs skip re-execution and return cached results, reducing API costs and iteration time.

## Value Statement

Graph authors can mark expensive or stable nodes as cached, eliminating redundant LLM calls during development iteration and repeated queries — reducing API costs by up to 80%.

## Problem

Every graph execution re-invokes all nodes, even when inputs are identical:

1. **Dev iteration**: Changing one node re-runs the entire pipeline, paying for unchanged nodes.
2. **Repeated queries**: Identical user questions trigger identical LLM calls at full cost.
3. **Expensive operations**: Embedding generation and web searches re-run unnecessarily.

The existing `skip_if_exists` mechanism only skips a node if its `state_key` already has a truthy value in the *current run's* state. It does not persist results across runs or support TTL-based expiry. It is a resume mechanism, not a cache.

## Proposed Solution

Expose LangGraph's `CachePolicy` (available since langgraph 0.2.24, confirmed in installed 1.1.6) through YAML node configuration. LangGraph's `StateGraph.add_node()` already accepts a `cache_policy` keyword argument — this FR wires it to YAML config.

### YAML Syntax

```yaml
# Boolean: cache indefinitely using default key (input hash via pickle)
nodes:
  expensive_analysis:
    type: llm
    prompt: analyze
    state_key: analysis
    cache: true

# With TTL: cache expires after N seconds
nodes:
  web_search:
    type: tool
    tool: tavily_search
    cache:
      ttl: 3600  # 1 hour
```

### Schema Addition

Add `cache` field to `NodeConfig` in `yamlgraph/models/graph_schema.py`:

```python
# Node-level caching (FR-237)
cache: bool | CacheConfig | None = Field(
    default=None,
    description="Cache policy for this node. true = cache forever, dict = {ttl: seconds}",
)
```

With a supporting model:

```python
class CacheConfig(BaseModel):
    """Cache configuration for a node."""
    ttl: int | None = Field(default=None, ge=1, description="TTL in seconds")
```

### Integration Point

In `yamlgraph/node_compiler.py`, each handler calls `ctx.graph.add_node(node_name, node_fn)`. The integration adds `cache_policy` when configured:

```python
from langgraph.types import CachePolicy

def _resolve_cache_policy(node_config: dict[str, Any]) -> CachePolicy | None:
    cache = node_config.get("cache")
    if cache is None:
        return None
    if cache is True:
        return CachePolicy()
    if isinstance(cache, dict):
        return CachePolicy(ttl=cache.get("ttl"))
    return None
```

Each handler changes from:
```python
ctx.graph.add_node(ctx.node_name, node_fn)
```
to:
```python
ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=_resolve_cache_policy(ctx.node_config))
```

### CLI Flag

Add `--no-cache` to `yamlgraph graph run` that strips all `cache` config before compilation:

```bash
# Normal run (caching active)
yamlgraph graph run pipeline.yaml

# Force fresh execution
yamlgraph graph run pipeline.yaml --no-cache
```

### Checkpointer Dependency

LangGraph's `CachePolicy` stores cached results in the checkpointer backend. Graphs using `cache` **must** have a checkpointer configured. The linter enforces this.

### Linter Checks

Add to `yamlgraph/linter/`:

| Code | Severity | Message |
|------|----------|---------|
| W080 | warning | Node `{name}` has `cache` but graph has no `checkpointer` — cache will have no effect |
| W081 | info | Node `{name}` has `cache: true` (no TTL) — cached results never expire |

## Acceptance Criteria

- [ ] `NodeConfig` accepts `cache: true` and `cache: {ttl: N}` — validated by Pydantic
- [ ] `cache: true` passes `CachePolicy()` to `add_node()`; `cache: {ttl: 3600}` passes `CachePolicy(ttl=3600)`
- [ ] `--no-cache` CLI flag disables all caching for the run
- [ ] Linter warns (W080) when `cache` is set but no `checkpointer` is configured
- [ ] Linter info (W081) when `cache: true` used without TTL
- [ ] `yamlgraph graph lint` and `yamlgraph graph validate` pass on graphs with `cache` fields
- [ ] Unit tests cover: schema validation (valid/invalid cache configs), cache policy resolution, linter checks, `--no-cache` flag
- [ ] Integration test: two identical invocations of a cached node — second returns cached result (requires checkpointer)
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-238")`
- [ ] Documentation updated in `reference/graph-yaml.md`

## Scope Exclusions

The following are explicitly **out of scope** for this FR:

- **Custom key functions**: `key_func` stays at LangGraph's `default_cache_key` (pickle-based input hash). Custom key functions would require Python callables in YAML — a separate concern.
- **Wildcard node matching** (`"*": {cache: true}`): Non-standard YAML pattern. Use graph-level `defaults:` if needed (separate FR).
- **CLI cache management** (`yamlgraph cache clear`): Clearing is a checkpointer-level operation — use the checkpointer's native tooling.
- **Storage backend selection**: Cache storage is the checkpointer's responsibility. Memory, SQLite, Redis already supported via `checkpointer:` config.
- **Cache-level defaults in `defaults:`**: Graph-level default caching for all nodes. Separate FR if pattern proves useful.

## Alternatives Considered

### 1. Application-level memoization

Wrap node functions with `functools.lru_cache` or `cachetools`. Rejected: doesn't persist across runs, doesn't integrate with LangGraph's checkpointer, requires Python code per node.

### 2. Extend `skip_if_exists`

Add TTL and cross-run persistence to the existing skip mechanism. Rejected: `skip_if_exists` is a resume mechanism (does the key exist in *this run's* state?), not a cache (was this computation done before with the same inputs?). Different semantics, different implementation.

### 3. External cache layer (Redis/Memcached)

Add a standalone cache outside LangGraph. Rejected: LangGraph already provides `CachePolicy` with checkpointer integration — building a parallel cache adds complexity with no benefit.

## Implementation Plan

1. **Schema** (0.5 day): Add `CacheConfig` model and `cache` field to `NodeConfig` in `graph_schema.py`. Add `cache` to JSON schema export.
2. **Node compiler** (0.5 day): Add `_resolve_cache_policy()` helper. Update all `add_node()` calls in handler functions to pass `cache_policy`.
3. **CLI flag** (0.25 day): Add `--no-cache` to `graph run` command. Strip `cache` from node configs when set.
4. **Linter** (0.25 day): Add W080 and W081 checks.
5. **Tests** (0.5 day): Unit tests for schema, resolver, linter, CLI flag. Integration test for cache hit.

## Architecture Notes

### Requirement

| ID | Description | Modules |
|----|-------------|---------|
| REQ-YG-238 | Node-level `cache` field in YAML (bool or `{ttl: N}`) compiles to LangGraph `CachePolicy` via `add_node(cache_policy=...)`; `--no-cache` CLI flag disables; linter W080 warns on missing checkpointer (FR-237) | `models/graph_schema`, `node_compiler`, `cli/graph_commands`, `linter` |

### Files Modified

| File | Change |
|------|--------|
| `yamlgraph/models/graph_schema.py` | Add `CacheConfig` model, `cache` field to `NodeConfig` |
| `yamlgraph/node_compiler.py` | Add `_resolve_cache_policy()`, pass to all `add_node()` calls |
| `yamlgraph/cli/graph_commands.py` | Add `--no-cache` flag |
| `yamlgraph/linter/checks.py` or new `checks_cache.py` | W080, W081 checks |
| `reference/graph-yaml.md` | Document `cache` field |
| `ARCHITECTURE.md` | Add REQ-YG-238, capability row |

## Related

- **LangGraph CachePolicy**: `langgraph.types.CachePolicy` — native API, already in installed version 1.1.6
- **skip_if_exists**: `yamlgraph/node_factory/llm_nodes.py` — resume mechanism, different semantics
- **Checkpointer**: `yamlgraph/storage/checkpointer_factory.py` — required backend for cache storage
- **Node compiler**: `yamlgraph/node_compiler.py` — integration point for `add_node()` calls

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Date:** 2026-04-19

**Findings:**

1. **Scope:** Clear and minimal. Single concern (wiring existing LangGraph `CachePolicy` to YAML config) with well-defined exclusions. No speculative extensibility.
2. **Contradictions:** None found. `skip_if_exists` distinction (resume vs cache) is correctly articulated.
3. **Acceptance criteria:** All 10 criteria are measurable and testable. Schema, compiler, CLI, linter, and integration test coverage specified.
4. **Feasibility:** All technical claims verified against the installed codebase:
   - `CachePolicy` importable from `langgraph.types` (LangGraph 1.1.6) ✓
   - `StateGraph.add_node()` accepts `cache_policy` kwarg ✓
   - `node_compiler.py` has 12 `add_node()` call sites across 10 handlers — integration point is real ✓
   - `NodeConfig` in `graph_schema.py` has no `cache` field yet — clean insertion point ✓
   - Linter infrastructure supports the proposed W080/W081 pattern ✓
   - FR-237 and REQ-YG-238 are the next available identifiers ✓
5. **Architecture alignment:** Follows YAML-first pattern, Pydantic schema validation, three-layer architecture. No new dependencies.
6. **Single responsibility:** Schema + compiler + CLI flag + linter are tightly coupled facets of one feature. No orthogonal concerns to split.

**Note for implementer:** The `_compile_interrupt_node()` handler has two `add_node()` calls (prepare + interrupt). Decide whether cache applies to the prepare node or only the interrupt node — document the decision in the FR during implementation.
