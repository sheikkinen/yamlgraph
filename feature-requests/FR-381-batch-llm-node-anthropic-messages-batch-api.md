# Feature Request: FR-381 `batch_llm` node — Anthropic Messages Batch API integration

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 3 days
**Requested:** 2026-05-14

## Summary

Add a `batch_llm` node type that submits a list of items to the Anthropic Messages
Batch API (50% cost reduction), polls for completion via LangGraph's checkpointer,
and collects results back into graph state. Targeted at non-real-time, high-volume
fan-out workloads: Chaplain diary digests, changelog generation, bulk evaluations.

## Value Statement

Graph authors replace expensive parallel `map` node fan-outs with a single
`batch_llm` node that costs half as much per token and requires no thread pool
management — the Anthropic API handles the concurrency.

## Problem

Token pricing is diverging sharply: frontier models cost 3–25× more than task-
specific models, and the Anthropic Batch API offers an unconditional 50% discount
on *all* models for async workloads. YAMLGraph currently has no way to exploit this.

Existing workarounds all use full-price APIs:

- `type: map` fan-out runs N parallel `messages.create()` calls at standard rate
- `graph.batch([...])` (LangChain Runnable) runs N independent real-time calls
- `type: race` runs M providers simultaneously for the fastest — still full price

The Anthropic SDK exposes the Batch API directly:
```python
client.beta.messages.batches.create(requests=[...])   # submit → batch_id
client.beta.messages.batches.retrieve(batch_id)        # poll
client.beta.messages.batches.results(batch_id)         # fetch
```

LangGraph and `langchain-anthropic` do **not** wrap this API. Implementation must
be at the YAMLGraph node factory layer, using the `anthropic` SDK directly.

## Research

### Anthropic Batch API facts (confirmed, 2026-05-14)

| Model | Batch input | Batch output |
|-------|-------------|--------------|
| Opus 4.7 | $2.50/MTok | $12.50/MTok |
| Sonnet 4.6 | $1.50/MTok | $7.50/MTok |
| Haiku 4.5 | $0.50/MTok | $2.50/MTok |

- Max 100,000 requests per batch, 256 MB limit
- Most batches complete in <1 hour; expire at 24 hours
- Supports all Messages API features: tools, structured output, vision, multi-turn
- Results available for 29 days after creation
- Not eligible for Zero Data Retention

### LangGraph / LangChain batch support (confirmed absent)

`ChatAnthropic` in `langchain-anthropic 1.3.0` routes via `client.messages.create()`
or `client.beta.messages.create()` (for beta headers). Neither path touches
`client.beta.messages.batches`. LangGraph's `graph.batch([...])` is LangChain's
Runnable `.batch()` — parallel synchronous calls, full price.

### Constraint: Anthropic-only

The Batch API is Anthropic-specific. OpenAI has a separate Batch API; Google/Vertex
do not offer an equivalent at this time. This FR is scoped to Anthropic only.
Other providers use standard `map` fan-out or the `race` node.

### Workloads suitable for `batch_llm`

**Yes** (async, non-real-time, high volume):
- Chaplain diary digest: classify N FR diffs per pipeline run
- Changelog fragment generation: process N unreleased fragments
- Bulk evaluation / test case generation: score M scenarios in parallel
- Context planner: classify N files for relevance

**No** (real-time, latency-sensitive):
- ninchat_voice call handling (requires <1s)
- Interactive graph sessions
- Streaming nodes
- Any node inside a `map` that feeds a real-time output

## Proposed Solution

### YAML interface

```yaml
nodes:
  classify_items:
    type: batch_llm
    prompt: classify           # reuses existing prompts/*.yaml
    provider: anthropic        # required; only anthropic supported
    model: claude-haiku-4-5    # any active Anthropic model
    items: "{state.items}"     # list to fan-out over; each item → one batch request
    item_var: item             # variable name injected into prompt template (default: "item")
    state_key: classifications # list of results, order-preserving
    poll_interval: 30          # seconds between status checks (default: 30)
    timeout: 3600              # max wait in seconds (default: 3600 = 1 hour)
    on_error: fail             # fail | skip (skip stores null for failed items)
    temperature: 0.3
    max_tokens: 512
```

### Execution model

1. **Submit phase**: node builds one `MessageBatchRequestParam` per item, injects
   item into prompt template variables alongside any other state variables, calls
   `client.beta.messages.batches.create(requests=[...])`. Stores `batch_id` in
   state under `_batch_id_{node_name}`.

2. **Wait phase**: node raises LangGraph `NodeInterrupt` with the `batch_id`.
   The checkpointer persists state including `batch_id`. The calling process
   exits (or yields); no thread is held.

3. **Resume phase**: caller (CLI or graph runner) polls
   `client.beta.messages.batches.retrieve(batch_id)` at `poll_interval`.
   When `processing_status == "ended"`, resumes the graph via
   `graph.invoke(Command(resume={"batch_id": batch_id}))`.

4. **Collect phase**: node fetches `client.beta.messages.batches.results(batch_id)`,
   maps `custom_id` → result (preserving input order), applies prompt schema
   parsing (same `_parse_structured_output` path as `llm` nodes), writes
   `list[result]` to `state_key`.

### CLI integration

`yamlgraph graph run` gains a background poll loop when state contains
`_batch_id_*` keys. Prints progress every `poll_interval` seconds:

```
⏳ Batch submitted (batch_id: msgbatch_01...). Polling every 30s...
⏳ Batch in progress (32/100 complete)...
✅ Batch complete. 100/100 succeeded, 0 errored.
```

### Error handling

- `on_error: fail` (default): any errored or expired request raises `PipelineError`
- `on_error: skip`: errored items produce `None` in the result list; logged as warnings
- Batch expiry (24h exceeded): always raises regardless of `on_error`

## Acceptance Criteria

- [ ] AC-01: `type: batch_llm` accepted by graph linter without error when
  `provider: anthropic` and `items` are set
- [ ] AC-02: submitting a batch of N items calls
  `client.beta.messages.batches.create` once with N `requests` entries,
  not N separate `messages.create` calls
- [ ] AC-03: `batch_id` is persisted in graph state between submit and collect
  phases (checkpointer survival)
- [ ] AC-04: results in `state_key` preserve input order regardless of batch
  processing order
- [ ] AC-05: structured output (prompt `schema:`) parses correctly across all
  N results using existing `_parse_structured_output`
- [ ] AC-06: `on_error: fail` raises `PipelineError` when any item has
  `result_type: errored` or `result_type: expired`
- [ ] AC-07: `on_error: skip` stores `None` for failed items, logs warning,
  does not raise
- [ ] AC-08: `timeout` exceeded raises `PipelineError` with batch_id and item
  count in message
- [ ] AC-09: non-anthropic provider raises `ConfigurationError` at graph
  compile time (linter check, not runtime)
- [ ] AC-10: CLI prints polling progress to stderr (not stdout), honoring
  `--json` mode stdout purity (FR-375)
- [ ] AC-11: existing `type: llm` and `type: map` nodes are unaffected
- [ ] AC-12: demo in `examples/demos/batch-llm/` runs end-to-end with
  `demo-output.log` committed (demo-gate)
- [ ] Tests added with `@pytest.mark.req("REQ-YG-XXX")`
- [ ] New requirement added to `ARCHITECTURE.md` and `scripts/req_coverage.py`
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary reflection in `docs/diary/`

## Implementation Notes

### Files to create / modify

| File | Change |
|------|--------|
| `yamlgraph/constants.py` | Add `BATCH_LLM = "batch_llm"` to `NodeType` |
| `yamlgraph/node_factory/batch_llm_node.py` | New module (~150 lines) |
| `yamlgraph/graph_loader.py` | Register `batch_llm` node factory |
| `yamlgraph/models/graph_schema.py` | Validate `batch_llm` constraints |
| `yamlgraph/linter/checks_providers.py` | AC-09 compile-time provider check |
| `yamlgraph/cli/graph_commands.py` | Polling loop for `_batch_id_*` state keys |
| `reference/graph-yaml.md` | Document `batch_llm` node |
| `examples/demos/batch-llm/` | Demo graph, prompt, demo.sh, demo-output.log |
| `tests/unit/test_batch_llm_node.py` | Unit tests (mock SDK) |
| `ARCHITECTURE.md` | REQ-YG-XXX |
| `scripts/req_coverage.py` | Extend ALL_REQS, CAPABILITIES |
| `changelog/unreleased/FR-381-batch-llm.md` | Changelog fragment |

### SDK dependency

`anthropic>=0.75.0` already in `pyproject.toml` (confirmed installed).
`client.beta.messages.batches` is stable in this version.

### Mock pattern for unit tests

```python
@pytest.fixture
def mock_batches(mocker):
    m = mocker.patch("anthropic.Anthropic")
    m.return_value.beta.messages.batches.create.return_value = Mock(id="msgbatch_test")
    m.return_value.beta.messages.batches.retrieve.return_value = Mock(
        processing_status="ended"
    )
    m.return_value.beta.messages.batches.results.return_value = [...]
    return m
```

### Polling without holding a thread

The cleanest approach for the initial implementation: poll synchronously in the
`graph_commands.py` CLI loop (blocking, but expected for batch workloads). A
future FR can add webhook/async resume. Mark the synchronous poll as a known
limitation in the implementation notes.

## Constraints

1. Scope: `batch_llm` node + CLI polling + one demo. No webhook resume, no
   multi-provider batch (future FRs).
2. `type: map` is not changed. `batch_llm` is additive.
3. No new required dependencies (anthropic SDK already present).
4. Node name `_batch_id_{node_name}` state keys are internal; must not conflict
   with user-defined state keys (linter check: reject user state keys matching
   `^_batch_id_`).
5. `--json` stdout purity (FR-375) must be preserved: all polling output goes
   to stderr.

## Alternatives Considered

### LangChain `.batch()` / `map` node fan-out
Parallel real-time calls. Full price. Already implemented. Remains the correct
choice for latency-sensitive workloads and non-Anthropic providers.

### OpenAI Batch API
OpenAI also offers a Batch API with 50% discount. Out of scope for this FR —
separate FR when validated against a real workload.

### Per-node `cache: true` (FR-032)
Result caching avoids re-computation for identical inputs. Complementary, not
alternative: cache hits skip the call entirely; Batch API reduces cost when the
cache misses.

### Prompt caching (`system_segments`)
Reduces cost of repeated stable context in individual calls. Complementary:
can be used *inside* batch requests via the standard `cache_control` header.
The Anthropic docs recommend 1-hour cache duration for batch workloads.

## Related

- Anthropic Message Batches API: https://docs.anthropic.com/en/docs/build-with-claude/batch-processing
- FR-032: Per-node result caching (`cache: true`)
- FR-219: Anthropic prompt caching (`system_segments`)
- FR-375: `--json` stdout mode (stdout purity constraint)
- `examples/demos/race/` — complementary pattern for latency-optimized routing
- `examples/cost-router/` — complementary pattern for tier-based routing
- Issue #378 (vulture dead code) — unrelated, parallel track
