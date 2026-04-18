# Feature Request: Race Node Type

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-04-18

## Summary

Add a `type: race` node that fires the same prompt to N provider/model combinations concurrently and returns the first successful result, enabling sub-second LLM responses for latency-sensitive graphs.

## Value Statement

Graph authors serving latency-sensitive workloads (voicebot, autocomplete, live assist) can hedge across providers and receive the fastest successful response without writing Python concurrency code.

## Problem

LLM response latency varies unpredictably across providers: a request that takes 800ms on OpenAI might take 2s on Anthropic in the same moment, and vice versa the next. For latency-critical applications (voice bots, real-time assistants), the only reliable strategy is to race multiple providers concurrently and take whichever responds first.

Today, achieving this in YAMLGraph requires:
1. Writing a custom Python node with manual `concurrent.futures` or `asyncio` concurrency
2. Handling cancellation, error propagation, and the sync/async boundary manually
3. Losing the YAML-first declarative advantage

This is a natural extension of YAMLGraph's parallel processing capabilities (map nodes fan out over data; race nodes fan out over providers).

### Known pitfalls from prior analysis

1. **Race semantics bug**: A naive `FIRST_COMPLETED` implementation cancels pending tasks when the first completes — but that first result may have *failed*. The implementation must loop over completions until it finds a successful one.
2. **Sync/async boundary**: `asyncio.run()` raises `RuntimeError` when called inside an already-running event loop (e.g., from `run_graph_async()` / FastAPI). The implementation must detect the execution context and choose the correct concurrency primitive.

## Proposed Solution

### YAML Configuration

```yaml
nodes:
  fastest_response:
    type: race
    prompt: "generate_response"
    state_key: "response"
    candidates:
      - provider: anthropic
        model: claude-3-5-haiku-20241022
      - provider: openai
        model: gpt-4o-mini
      - provider: mistral
        model: mistral-small-latest
    timeout: 10          # Per-candidate timeout in seconds (optional, default: 30)
    temperature: 0.7     # Shared across all candidates (optional)
```

### Execution Semantics

1. Load and format the prompt once (via `prepare_messages()`).
2. Instantiate N LLMs via `create_llm(provider=..., model=...)` (cached by factory).
3. Submit all N invocations concurrently.
4. As each completes, check success:
   - **Success**: cancel remaining tasks, return result to `state_key`.
   - **Failure**: log warning, continue waiting for remaining candidates.
5. If all N fail, apply the node's `on_error` policy (default: `fail`).

### Concurrency Strategy

Use `concurrent.futures.ThreadPoolExecutor` with `as_completed()`. This works in both sync and async contexts because each LLM call is a blocking HTTP request running in its own thread — no event loop nesting.

```python
# Pseudocode (sync-safe, async-safe)
from concurrent.futures import ThreadPoolExecutor, as_completed

def race_node_fn(state: dict) -> dict:
    messages = prepare_messages(prompt_name, variables)
    llms = [create_llm(provider=c["provider"], model=c["model"]) for c in candidates]

    with ThreadPoolExecutor(max_workers=len(llms)) as pool:
        futures = {
            pool.submit(_invoke_llm, llm, messages, output_model, timeout): c
            for llm, c in zip(llms, candidates)
        }
        for future in as_completed(futures):
            candidate = futures[future]
            try:
                result = future.result()
                # Cancel remaining
                for f in futures:
                    f.cancel()
                return {state_key: result, "_race_winner": candidate}
            except Exception as e:
                logger.warning("Race candidate %s/%s failed: %s",
                               candidate["provider"], candidate["model"], e)

    # All failed
    raise AllCandidatesFailedError(errors)
```

### Winner Metadata

The winning candidate's `provider` and `model` are stored in a `_race_winner` dict on state for observability. This mirrors `_map_index` from map nodes.

### Integration Points

| Component | Change |
|-----------|--------|
| `yamlgraph/constants.py` | Add `RACE = "race"` to `NodeType` |
| `yamlgraph/node_compiler.py` | Register `_compile_race_node` in `NODE_TYPE_HANDLERS` |
| `yamlgraph/node_factory/race_node.py` | New module: race node builder |
| `yamlgraph/models/graph_schema.py` | Add `candidates` field to `NodeConfig` |
| `yamlgraph/models/state_builder.py` | Handle `_race_winner` metadata key |

### Graph Lint / Validation Rules

- `candidates` must contain ≥ 2 entries (single candidate = use regular `llm` node).
- Each candidate must have at least `provider` or `model` specified.
- `prompt` is required (same as `llm` node).

## Acceptance Criteria

- [ ] `type: race` node fires prompt to all candidates concurrently
- [ ] Returns first *successful* result (not just first-to-complete)
- [ ] Remaining candidates are cancelled after first success
- [ ] All-candidates-fail triggers the node's `on_error` policy
- [ ] Works in sync context (`graph.invoke()`)
- [ ] Works in async context (`run_graph_async()` / FastAPI)
- [ ] `_race_winner` metadata stored in state with provider/model of winner
- [ ] `timeout` per-candidate is respected
- [ ] `candidates` validated: ≥ 2 entries, each has provider or model
- [ ] `graph lint` validates race node configuration
- [ ] Structured output (`schema:` in prompt YAML) works with race nodes
- [ ] Unit tests with mock LLMs (varying latency, partial failures)
- [ ] Integration test with ≥ 2 real providers
- [ ] Documentation: reference page and example graph
- [ ] Requirement traceability: REQ-YG-233+ tagged on all tests

## Alternatives Considered

### 1. Extend map node with `race: true` flag

Map nodes fan out over *data items* with a shared LLM. Race fans out over *LLMs* with shared data. The semantics are inverted — overloading map would confuse the mental model and complicate the map compiler. Separate type is cleaner.

### 2. Use LangGraph Send with conditional edges

Send collects *all* branch results before continuing — it has no short-circuit / first-success semantic. A race node that waits for all candidates defeats its purpose.

### 3. asyncio.as_completed with nest_asyncio

Adding `nest_asyncio` as a dependency to allow `asyncio.run()` inside running loops is fragile and has known bugs with cancellation. `ThreadPoolExecutor` avoids the event loop entirely and is safe in all contexts.

### 4. Fallback chains (sequential, not concurrent)

The existing `on_error: fallback` mechanism retries sequentially: provider A fails → try provider B. This adds latency (worst case: sum of all timeouts). Race is complementary: it trades compute cost for guaranteed minimum latency.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Date:** 2026-04-18

### Evaluation

| Criterion | Assessment |
|-----------|------------|
| Scope clarity | ✓ Single new node type, well-bounded |
| Minimality | ✓ No bundled orthogonal concerns |
| Contradictions | ✓ None found |
| Acceptance criteria | ✓ All 14 criteria are measurable and testable |
| Feasibility | ✓ All 11 integration-point claims verified against codebase |
| Architecture alignment | ✓ Follows node_factory, NODE_TYPE_HANDLERS, state metadata patterns |

### Notes for Implementation

1. **Cancellation semantics**: The pseudocode's `f.cancel()` won't cancel already-running threads (all start immediately when `max_workers=len(llms)`). The `with ThreadPoolExecutor` block also calls `shutdown(wait=True)` on exit, blocking until all tasks complete. The implementation must handle this — e.g., `shutdown(wait=False, cancel_futures=True)` (Python 3.9+) or manual pool management. The AC "Remaining candidates are cancelled" is the contract; interpret as "abandoned / not awaited" for thread-based concurrency.

2. **Streaming**: Explicitly out of scope for this FR. Streaming from a race node (forwarding only the winner's token stream) is a natural follow-up but is a separate concern.

3. **Per-candidate LLM parameters**: The current design shares `temperature` across all candidates. Per-candidate overrides (e.g., different temperatures or max_tokens) can be a follow-up FR if needed.

## Related

- **Map node**: `yamlgraph/map_compiler.py` — parallel fan-out pattern (data-parallel, not provider-parallel)
- **LLM factory**: `yamlgraph/utils/llm_factory.py` — `create_llm(provider, model)` for multi-provider instantiation
- **Executor async**: `yamlgraph/executor_async.py` — `execute_prompts_concurrent()` for parallel prompt execution
- **Node compiler**: `yamlgraph/node_compiler.py` — `NODE_TYPE_HANDLERS` registry for type dispatch
- **on_error fallback**: Sequential provider fallback (complementary, not competing)
