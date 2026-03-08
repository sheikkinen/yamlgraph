# Copilot Node Demo

**FR-081:** Demonstrates the `copilot` node type for delegating to GitHub Copilot CLI.
**FR-098:** Consolidated from `.chaplain/graph.yaml` — now the canonical Plan→Judge→Diary workflow.

## Overview

This example implements the complete Plan-Judge-Diary workflow as a YAMLGraph pipeline. It combines copilot nodes (delegating to GitHub Copilot CLI) with a standard LLM summarize node and a Python tool for diary append.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Plan (copilot)│────▶│  Judge (copilot)│────▶│ Summarize (llm) │────▶│ Write Diary (py)│
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Node Types

| Node | Type | Backend | Description |
|------|------|---------|-------------|
| `plan` | `copilot` | `cli` | Reads topic file, drafts feature request |
| `judge` | `copilot` | `cli` | Examines draft, renders APPROVE/AMEND/REJECT |
| `summarize` | `llm` | - | Creates DiaryEntry (theme, body, seed) |
| `write_diary` | `python` | - | Appends entry to docs/diary/ |

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
  --var date="$(date +%Y-%m-%d)" \
  --var diary_prefix="Chaplain" \
  --full
```

3. Check outputs:
```bash
cat .chaplain/drafts/*.md     # The drafted feature request
tail -30 docs/diary/        # Diary entry appended
```

Or use the polling wrapper:
```bash
.chaplain/watch.sh            # Watches .chaplain/inbox/ for topics
```

## Requirements

- GitHub Copilot CLI installed and in PATH (`copilot` command)
- Copilot CLI configured with workspace access

## Key Features Demonstrated

1. **`backend: cli`** - Invokes Copilot CLI with `--silent` flag
2. **`cli_flags`** - Configures `allow_all_paths`, `allow_all_tools`
3. **Variable substitution** - `{state.topic_file}` references
4. **Mixed node types** - Copilot nodes + LLM node + Python tool
5. **4-stage workflow** - Plan → Judge → Summarize → Write Diary
6. **Diary append** - Automatic entry creation via `examples.shared.diary`

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
    timeout: 500              # 8+ minute timeout for complex planning
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

Access in subsequent nodes:
- **Full object**: `{state.plan_result}` — stringifies via `__str__`, includes exit code and backend
- **Output only**: `{state.plan_result.output}` — just the response text

The summarize prompt uses the full object with Jinja2 `default()` filters for graceful degradation.

## See Also

- [FR-081](../../feature-requests/FR-081-copilot-node.md) - Copilot node feature request
- [FR-098](../../feature-requests/FR-098-consolidate-watch-graph.md) - Consolidation feature request
- [.chaplain/watch.sh](../../.chaplain/watch.sh) - Polling wrapper using this graph
- [reference/graph-yaml.md](../../reference/graph-yaml.md#type-copilot---copilot-cli-delegation) - Full documentation
