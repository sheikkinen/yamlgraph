---
name: check-langsmith-trace
description: "Check LangSmith traces for YAMLGraph runs. Use when: debugging graph execution, reviewing LLM latency or token usage, investigating failed runs, verifying tracing config, querying recent traces, troubleshooting LangSmith connectivity."
argument-hint: "optional run ID, 'failed', 'status', or graph path to run first"
---

# Check LangSmith Trace

Inspect LangSmith traces for YAMLGraph graph runs — config verification, recent run listing, detailed trace analysis, and failure investigation.

## Procedure

### 1. Verify Configuration

Run the status check to confirm tracing is active:

```bash
cd /Users/sami.j.p.heikkinen/src/yamlgraph
source .venv/bin/activate
python scripts/langsmith_traces.py status
```

Expected: `Tracing active: True`, project name shown, latest run timestamp.

If tracing is not active, check `.env` for these variables:
- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY=lsv2_pt_...`
- `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`
- `LANGSMITH_PROJECT=pr-showcase`

### 2. Choose Action

Based on the user's argument:

| Argument | Action |
|----------|--------|
| _(none)_ | List latest 5 runs |
| `status` | Config check only (step 1) |
| `failed` | List recent failed runs |
| a UUID | Show detail + children for that run |
| a `.yaml` path | Run the graph first, then show its trace |

### 3. List Recent Runs

```bash
python scripts/langsmith_traces.py list --limit 5
```

For failures only:

```bash
python scripts/langsmith_traces.py list --failed
```

### 4. Inspect a Specific Run

Get full detail (inputs, outputs, tokens, latency):

```bash
python scripts/langsmith_traces.py detail <run-id-or-latest>
```

Show child node executions:

```bash
python scripts/langsmith_traces.py children <run-id-or-latest>
```

### 5. Run a Graph and Trace It

If the user provides a graph path, execute it and then inspect:

```bash
yamlgraph graph run <graph.yaml> --var key=value --full
```

The trace URL prints automatically (`🔗 Trace: ...`). Then query that run:

```bash
python scripts/langsmith_traces.py detail latest
python scripts/langsmith_traces.py children latest
```

### 6. Deep Dive (Python)

For ad-hoc queries not covered by the script, use the SDK directly:

```python
from dotenv import load_dotenv; load_dotenv()
from langsmith import Client
import json

client = Client()

# Latest run with full outputs
runs = list(client.list_runs(project_name="pr-showcase", is_root=True, limit=1))
run = runs[0]
print(f"Status: {run.status}, Latency: {run.latency}s, Tokens: {run.total_tokens}")
print(json.dumps(run.inputs, indent=2, default=str)[:2000])
print(json.dumps(run.outputs, indent=2, default=str)[:2000])

# Child runs with error details
children = list(client.list_runs(
    project_name="pr-showcase",
    filter=f'eq(parent_run_id, "{run.id}")',
))
for c in children:
    print(f"  {c.name} [{c.run_type}] {c.latency}s {c.total_tokens}tok {c.status}")
    if c.error:
        print(f"    ERROR: {c.error[:200]}")
```

### 7. Report

Summarize findings to the user:
- Run status (success/failure)
- Total latency and token usage
- Per-node breakdown (which node was slowest, which used most tokens)
- Any errors with root cause
- Trace URL for browser deep-dive

## Reference

- [Troubleshooting playbook](../../docs/context/langsmith-tracing.md)
- [LangSmith tools reference](../../reference/langsmith-tools.md)
- [Helper script](../../scripts/langsmith_traces.py)
- [Tracing utilities source](../../yamlgraph/utils/tracing.py)
- [ADR-002](../../docs/adr/002-langsmith-trace-url.md)

## Key Facts

- **Data region**: EU (`eu.api.smith.langchain.com`)
- **Default project**: `pr-showcase`
- **Browser**: [eu.smith.langchain.com](https://eu.smith.langchain.com)
- **CLI flag**: `--share-trace` creates a public link (no auth needed)
- All tracing functions are fail-safe — return `None` on error, never raise
