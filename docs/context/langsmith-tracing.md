# LangSmith Tracing — Troubleshooting Context

> Playbook for accessing, querying, and debugging LangSmith traces.
> Updated: 2026-05-22

## Configuration

Tracing is auto-detected from environment variables (set in `.env` or shell).

| Variable | Current Value | Purpose |
|----------|---------------|---------|
| `LANGSMITH_TRACING` | `true` | Enable tracing |
| `LANGSMITH_API_KEY` | `lsv2_pt_...` | API authentication |
| `LANGSMITH_ENDPOINT` | `https://eu.api.smith.langchain.com` | EU data region |
| `LANGSMITH_PROJECT` | `pr-showcase` | Default project name |

Legacy aliases (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_PROJECT`) also work — the LangSmith SDK accepts both.

### Verify configuration

```bash
python scripts/langsmith_traces.py status
```

## Accessing Traces

### 1. CLI (automatic)

Every `yamlgraph graph run` prints the trace URL when tracing is enabled:

```bash
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --full
# 🔗 Trace: https://eu.smith.langchain.com/o/.../r/...

# Public shareable link:
yamlgraph graph run graph.yaml --var topic=AI --share-trace
# 🔗 Trace (public): https://smith.langchain.com/public/.../r/...
```

### 2. Browser

Open [eu.smith.langchain.com](https://eu.smith.langchain.com) → project **pr-showcase** → click any run to see:
- Full run tree (root → nodes → LLM calls)
- System prompt + user message
- LLM response + structured output
- Token counts, latency per step
- Error details with stack traces

### 3. Helper script

```bash
# List latest 5 runs
python scripts/langsmith_traces.py

# List latest 20 runs
python scripts/langsmith_traces.py list --limit 20

# Show only failed runs
python scripts/langsmith_traces.py list --failed

# Detail view of latest run (inputs, outputs, tokens)
python scripts/langsmith_traces.py detail

# Detail view of specific run
python scripts/langsmith_traces.py detail 019e4ef6-02b9-7663-8aa5-2d44c1a69397

# Show child node executions
python scripts/langsmith_traces.py children
python scripts/langsmith_traces.py children 019e4ef6-02b9-7663-8aa5-2d44c1a69397

# Override project
python scripts/langsmith_traces.py --project my-project list
```

### 4. Python API

```python
from dotenv import load_dotenv; load_dotenv()
from langsmith import Client

client = Client()

# Latest runs
runs = list(client.list_runs(project_name="pr-showcase", is_root=True, limit=5))
for r in runs:
    print(f"{r.id}  {r.status}  {r.latency}s  {r.total_tokens} tok")

# Failed runs
failed = list(client.list_runs(project_name="pr-showcase", error=True, limit=10))

# Child runs (individual node executions)
children = list(client.list_runs(
    project_name="pr-showcase",
    filter=f'eq(parent_run_id, "{root_run_id}")',
))

# Share a run publicly
url = client.share_run(run_id)
```

## Architecture

| File | Role |
|------|------|
| `yamlgraph/utils/tracing.py` | 5 fail-safe functions: `is_tracing_enabled()`, `create_tracer()`, `get_trace_url()`, `share_trace()`, `inject_tracer_config()` |
| `yamlgraph/cli/graph_run_helpers.py` | Injects tracer into LangGraph config, prints trace URL after run |
| `reference/langsmith-tools.md` | Full reference: LangSmith tools for use in graphs, utility functions, exec tracing |
| `docs/adr/002-langsmith-trace-url.md` | ADR for the FR-022 design decision |
| `capabilities/CAP-13-langsmith-tracing.yaml` | Capability definition (REQ-YG-047) |
| `scripts/langsmith_traces.py` | CLI helper for querying traces |

### Execution flow

```
graph run CLI
  → _build_run_config()
    → create_tracer()        # returns None if not configured
    → inject_tracer_config() # appends to callbacks list
  → app.invoke(input, config)
  → _print_trace_url()      # prints 🔗 Trace: ...
```

All tracing functions are fail-safe — they return `None` on error, never raise. Tracing never breaks the pipeline it observes.

## Troubleshooting

### "No trace URL printed"

1. Run `python scripts/langsmith_traces.py status` — check if tracing is active
2. Verify `.env` has `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY=lsv2_...`
3. Check `langsmith` package is installed: `pip show langsmith`

### "Trace URL returns login page"

The trace URL is authenticated — you must be logged into [eu.smith.langchain.com](https://eu.smith.langchain.com) with the account that owns the API key. Use `--share-trace` for a public link that doesn't require auth.

### "Runs not appearing in the project"

- Check `LANGSMITH_PROJECT` matches the project you're looking at in the UI
- Verify `LANGSMITH_ENDPOINT` points to the correct region (EU vs US)
- Test connectivity: `python -c "from langsmith import Client; print(Client().list_runs(project_name='pr-showcase', limit=1))"`

### Querying from Copilot agents

Use the ad-hoc Python pattern from the troubleshooting session:

```python
from dotenv import load_dotenv; load_dotenv()
from langsmith import Client
import json

client = Client()
runs = list(client.list_runs(project_name="pr-showcase", is_root=True, limit=1))
run = runs[0]
print(f"Status: {run.status}, Latency: {run.latency}s, Tokens: {run.total_tokens}")
print(json.dumps(run.outputs, indent=2, default=str)[:2000])
```

## Key facts

- **Data region**: EU (`eu.api.smith.langchain.com`)
- **Default project**: `pr-showcase`
- **Provider**: Azure OpenAI (`azure/aaa-gpt-5.4-mini`)
- **Typical hello-graph latency**: ~2.3s, ~137 tokens
- **SDK detection**: `langsmith.utils.tracing_is_enabled()` — accepts both current and legacy env var names
