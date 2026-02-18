# Feature Request: JSON Run Logging (--log-json)

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 30–60 min
**Requested:** 2026-02-16

## Summary

Add `--log-json <file>` CLI flag to append structured JSON after each graph run. Lightweight alternative to full logbook (FR-037).

## Problem

No execution history between sessions. Users cannot:
- Compare runs of the same graph with different inputs
- Track duration/cost over time
- Audit batch processing results
- Debug failed runs (inputs not captured)

## Proposed Solution

```bash
yamlgraph graph run graph.yaml --var topic="AI" --log-json runs.jsonl
```

Appends one JSON line per run:

```json
{
  "timestamp": "2026-02-16T17:30:00Z",
  "graph": "toolkit.yaml",
  "inputs": {"topic": "AI", "style": "brief"},
  "success": true,
  "duration_s": 42.3,
  "token_usage": {"input": 1200, "output": 800},
  "trace_url": "https://smith.langchain.com/..."
}
```

## Use Cases

1. **Run comparison** — `jq 'select(.graph == "toolkit.yaml")' runs.jsonl`
2. **CI/CD metrics** — Extract duration/success for dashboards
3. **Batch audit** — `jq 'select(.success == false)' runs.jsonl`
4. **Cost tracking** — Aggregate token usage from `--token-usage` flag
5. **Debugging** — Reproduce failed runs with logged inputs
6. **Light session memory** — Agent reads `tail -1 runs.jsonl` for context

## Implementation

**1. `yamlgraph/cli/__init__.py`** (~5 lines)
```python
graph_run_parser.add_argument(
    "--log-json",
    type=str,
    default=None,
    dest="log_json",
    help="Append run metadata as JSON line to file",
)
```

**2. `yamlgraph/cli/graph_commands.py`** (~15 lines in `cmd_graph_run`)
```python
# After execution completes:
if args.log_json:
    from datetime import datetime
    import json

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "graph": str(graph_path),
        "inputs": initial_state,
        "success": not error_occurred,
        "duration_s": round(duration, 2),
    }
    if getattr(args, "token_usage", False) and tracker:
        log_entry["token_usage"] = tracker.summary()
    if trace_url:
        log_entry["trace_url"] = trace_url

    with open(args.log_json, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## Acceptance Criteria

- [ ] `--log-json runs.jsonl` appends JSON line after each run
- [ ] JSON includes: timestamp, graph, inputs, success, duration_s
- [ ] Optional: token_usage (if `--token-usage` enabled)
- [ ] Optional: trace_url (if tracing enabled)
- [ ] File created if doesn't exist
- [ ] Existing file appended (not overwritten)
- [ ] Unit test: verify JSON structure
- [ ] No outputs logged by default (privacy: avoid capturing sensitive content)

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| Full SQLite logbook (FR-037) | Structured queries, FTS | Complex, wrong layer |
| **JSON lines (chosen)** | Simple, unix-friendly, jq-compatible | No indexing |
| CSV | Spreadsheet-friendly | Poor for nested data |

## Security Notes

- **Inputs logged, outputs NOT logged** — avoids capturing credentials/PII in outputs
- If user needs output logging, they can redirect stdout or use `--export`

## Related

- FR-037 (full logbook) — deferred, replaced by this minimal approach
- `--token-usage` flag — integrates with log entry
- `--share-trace` flag — trace_url captured in log
