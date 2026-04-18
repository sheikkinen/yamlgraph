# Feature Request: Model & Provider Timing Comparison

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 3–4 days (phased)
**Requested:** 2026-04-18
**Approved:** 2026-04-18

## Summary

Add a `yamlgraph graph bench` CLI command that runs a graph against multiple provider/model combinations and displays a side-by-side comparison of execution time, token usage, and output for each.

## Value Statement

Graph authors can objectively compare speed, cost, and output quality across providers and models with a single command, eliminating manual re-runs and ad-hoc timing.

## Problem

Users currently have no way to compare models or providers within YAMLGraph. To evaluate whether `anthropic/claude-sonnet-4-20250514` or `openai/gpt-4o` produces better results faster, a user must:

1. Edit the YAML graph or set `PROVIDER` env var
2. Run the graph manually
3. Note the time with an external stopwatch
4. Repeat for each provider/model
5. Mentally compare truncated CLI output

This is tedious, error-prone, and produces no persistent record. The `--token-usage` flag shows aggregate tokens but not wall-clock time. FR-043 (Evaluation Framework) addresses quality scoring but not timing or multi-model comparison. FR-106 (OTel) addresses production observability but not developer-facing benchmarking.

**This FR fills the gap:** a lightweight, developer-facing benchmarking tool that requires no external infrastructure.

## Proposed Solution

### Phase 1: Execution Timing Callback (1 day)

Create `yamlgraph/utils/timing_tracker.py` following the `TokenUsageCallbackHandler` pattern:

```python
class ExecutionTimingCallbackHandler(BaseCallbackHandler):
    """Tracks wall-clock duration of each LLM call."""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._start_time = time.monotonic()

    def on_llm_end(self, response, **kwargs):
        elapsed = time.monotonic() - self._start_time
        self.total_duration += elapsed
        self.call_durations.append(elapsed)
        self.total_calls += 1

    def summary(self) -> dict:
        return {
            "total_duration_s": round(self.total_duration, 2),
            "call_count": self.total_calls,
            "mean_duration_s": round(self.total_duration / max(self.total_calls, 1), 2),
        }
```

Add `--timing` flag to `yamlgraph graph run` (mirrors `--token-usage`):

```
$ yamlgraph graph run examples/demos/hello/graph.yaml --var name=World --timing
...
⏱ Timing: 1.23s total (2 calls, 0.62s mean)
```

### Phase 2: Bench Command (2 days)

Add `yamlgraph graph bench` that runs a graph N times across M provider/model combos:

```bash
yamlgraph graph bench examples/demos/hello/graph.yaml \
  --var name="World" --var style="casual" \
  --models anthropic/claude-sonnet-4-20250514 openai/gpt-4o google/gemini-2.0-flash \
  --runs 1
```

Output:

```
┌────────────────────────────────┬──────────┬────────────┬────────────┬──────────┐
│ Model                          │ Duration │ Tokens In  │ Tokens Out │ Status   │
├────────────────────────────────┼──────────┼────────────┼────────────┼──────────┤
│ anthropic/claude-sonnet-4-20250514     │    1.23s │        312 │        187 │ ✓        │
│ openai/gpt-4o                  │    0.89s │        298 │        201 │ ✓        │
│ google/gemini-2.0-flash        │    0.45s │        305 │        195 │ ✓        │
└────────────────────────────────┴──────────┴────────────┴────────────┴──────────┘
```

With `--full`, append full output per model. With `--export bench.json`, save structured results:

```json
{
  "graph": "examples/demos/hello/graph.yaml",
  "variables": {"name": "World", "style": "casual"},
  "timestamp": "2026-04-18T07:00:00Z",
  "results": [
    {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "duration_s": 1.23,
      "tokens_in": 312,
      "tokens_out": 187,
      "status": "success",
      "output": {"greeting": "..."}
    }
  ]
}
```

**Model spec format:** `provider/model` parsed into `(provider, model)` tuple. The bench command overrides the graph's `metadata.provider` and `metadata.model` for each run.

### Integration with existing infrastructure

- **Token tracker**: Reuse `TokenUsageCallbackHandler` — inject alongside timing callback
- **LLM factory**: Use existing `create_llm(provider=..., model=...)` override parameters
- **Graph compilation**: Compile once, invoke N times with different LLM configs (via `configurable` override or recompilation per provider)
- **Timeout**: Respect existing `--timeout` flag per run
- **Error handling**: Catch per-model errors; report failures in table without aborting other models

## Acceptance Criteria

### Phase 1 — Timing Callback
- [x] `yamlgraph/utils/timing_tracker.py` tracks per-call and total wall-clock LLM duration
- [x] `--timing` flag on `yamlgraph graph run` displays timing summary after execution
- [x] Timing callback follows `TokenUsageCallbackHandler` pattern (callback injection, no node modification)
- [x] Unit tests with mock LLM verify timing accumulation
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-231")`

### Phase 2 — Bench Command
- [x] `yamlgraph graph bench` runs a graph across `--models provider/model ...` list
- [x] Results displayed in a formatted comparison table
- [x] `--export <path>` saves structured JSON results
- [x] `--full` includes complete output per model in display
- [x] `--runs N` repeats each model N times and reports mean/min/max duration
- [x] Per-model errors reported gracefully without aborting other models
- [x] Unit tests for CLI argument parsing and result formatting
- [x] Integration test (1 model, mock LLM) verifies end-to-end bench flow
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-232")`
- [x] Documentation updated in `reference/getting-started.md`

## Scope Boundaries

**In scope:**
- Wall-clock timing of LLM calls
- Multi-model comparison table
- JSON export of bench results

**Out of scope (covered by other FRs):**
- Quality/semantic evaluation of outputs → FR-043
- Production latency metrics and histograms → FR-106
- Cost estimation → future FR
- Automated regression detection → FR-043 Phase 2

## Alternatives Considered

1. **Extend `graph run` with `--provider` override only** — simpler but requires manual re-runs and external timing. Doesn't solve the comparison problem.
2. **Build on FR-106 (OTel)** — OTel provides production observability but requires infrastructure (Jaeger/Grafana). This FR targets zero-dependency developer workflow.
3. **Shell script wrapper** — `time yamlgraph graph run ... && time yamlgraph graph run ...` — no token tracking, no structured output, no table formatting.
4. **Jupyter notebook** — viable for power users but breaks CLI-first philosophy.

## Related

- `yamlgraph/utils/token_tracker.py` — pattern to follow for timing callback (REQ-YG-064)
- `yamlgraph/utils/llm_factory.py` — `create_llm()` with provider/model override
- `yamlgraph/cli/graph_commands.py` — CLI arg handling, `_display_result()`, token display
- FR-043 — Evaluation Framework (quality scoring, complementary)
- FR-106 — OTel Observability (production metrics, complementary)

## Requirements

- **REQ-YG-231**: Execution timing callback tracks per-call and total wall-clock LLM duration, exposed via `--timing` flag
- **REQ-YG-232**: `yamlgraph graph bench` command runs a graph across multiple provider/model combinations and displays comparison table

## Judgement Notes (2026-04-18)

**Verdict: APPROVED.** Scope frozen.

**Provider/model override strategy:** The FR says "overrides the graph's `metadata.provider` and `metadata.model`", but nodes read `cfg.provider` from `LLMNodeConfig` at runtime (`llm_nodes.py:383`), not graph metadata. Implementation must override at the node-config level — either deep-copy `GraphConfig` and patch all `LLMNodeConfig.provider`/`model` fields, or add a graph-level override that propagates through `_build_run_config()`. Compile-once-invoke-many is preferred over recompilation per provider.

**Effort:** Adjusted from 3 to 3–4 days. The exploration validated feasibility but bench command error isolation and table formatting add half a day.

**Scope boundaries confirmed:** No overlap with FR-043 (quality evaluation) or FR-106 (production observability). This FR targets zero-infrastructure developer benchmarking only.
