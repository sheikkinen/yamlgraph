# Copilot Node Demo

**FR-081:** Demonstrates the `copilot` node type for delegating to GitHub Copilot CLI.

## Overview

This example replicates the `.chaplain/watch.sh` Plan-Judge workflow as a YAMLGraph pipeline with an additional summarization step using a standard LLM node.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Plan (copilot)│────▶│  Judge (copilot)│────▶│ Summarize (llm) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Node Types

| Node | Type | Backend | Description |
|------|------|---------|-------------|
| `plan` | `copilot` | `cli` | Reads topic file, drafts feature request |
| `judge` | `copilot` | `cli` | Examines draft, renders APPROVE/AMEND/REJECT |
| `summarize` | `llm` | - | Creates executive summary |

## Usage

1. Create a topic file:
```bash
mkdir -p .chaplain/inbox .chaplain/drafts
echo "# Add caching to the LLM factory" > .chaplain/inbox/caching-idea.md
```

2. Run the workflow:
```bash
yamlgraph graph run examples/copilot/graph.yaml \
  --var topic_file=".chaplain/inbox/caching-idea.md" \
  --var drafts_dir=".chaplain/drafts" \
  --full
```

3. Check outputs:
```bash
cat .chaplain/drafts/*.md     # The drafted feature request
cat workflow_summary.md       # Executive summary
```

## Requirements

- GitHub Copilot CLI installed and in PATH (`copilot` command)
- Copilot CLI configured with workspace access

## Key Features Demonstrated

1. **`backend: cli`** - Invokes Copilot CLI with `--silent` flag
2. **`cli_flags`** - Configures `allow_all_paths`, `allow_all_tools`
3. **Variable substitution** - `{state.topic_file}` references
4. **Mixed node types** - Copilot nodes + standard LLM node
5. **Sequential workflow** - Plan → Judge → Summarize

## Configuration

```yaml
nodes:
  plan:
    type: copilot
    prompt: plan
    backend: cli              # Use Copilot CLI backend
    cli_flags:
      allow_all_paths: true   # Allow file system access
      allow_all_tools: true   # Allow all MCP tools
    variables:
      topic_file: "{state.topic_file}"
    state_key: plan_result
    timeout: 300              # 5 minute timeout
```

## CopilotResult

The copilot node returns a `CopilotResult` object:

```python
class CopilotResult(BaseModel):
    output: str      # Copilot's response
    exit_code: int   # Process exit code (0 = success)
    model: str | None  # Model used (if specified)
    backend: str     # "cli" or "sampling"
```

Access in subsequent nodes: `{state.plan_result.output}`

## See Also

- [FR-081](../../feature-requests/FR-081-copilot-node.md) - Feature request
- [.chaplain/graph.yaml](../../.chaplain/graph.yaml) - **Production consumer** (Plan→Judge, no summarize)
- [.chaplain/watch.sh](../../.chaplain/watch.sh) - Polling wrapper using this pattern
- [reference/graph-yaml.md](../../reference/graph-yaml.md#type-copilot---copilot-cli-delegation) - Full documentation
