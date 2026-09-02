# Graph YAML Reference

This document explains all configuration options for graph YAML files. Graphs are typically located in `examples/demos/*/graph.yaml` or your project's graph directory.

## File Structure

```yaml
version: "1.0"                    # Schema version
name: my-pipeline                  # Graph identifier
description: What this graph does  # Human-readable description

defaults:                          # Default values for all nodes
  provider: mistral
  temperature: 0.7

data_files:                        # Optional: Load external YAML into state
  schema: schema.yaml

tools:                             # Optional: Tool definitions for agents
  tool_name: { ... }

nodes:                             # Required: Node definitions
  node_name: { ... }

edges:                             # Required: Edge definitions
  - from: START
    to: node_name

loop_limits:                       # Optional: Max iterations per node
  node_name: 3

loop_exits:                        # Optional: Custom exit target when loop limit hit
  node_name: post_loop_node

exports:                           # Optional: Export configuration
  state_key:
    format: markdown
    filename: output.md
```

---

## Top-Level Properties

### `version`
**Type:** `string`
**Default:** `"1.0"`

Schema version for the YAML format.

```yaml
version: "1.0"
```

### `name`
**Type:** `string`
**Default:** `"unnamed"`

Identifier for the graph, used in logging and display.

```yaml
name: content-pipeline
```

### `description`
**Type:** `string`
**Default:** `""`

Human-readable description of what the graph does.

```yaml
description: Content generation pipeline (generate → analyze → summarize)
```

### `defaults`
**Type:** `object`

Default configuration applied to all nodes unless overridden.

```yaml
defaults:
  provider: mistral       # Default LLM provider
  temperature: 0.7        # Default temperature
  thinking_budget: 8000   # Extended thinking budget (Anthropic: ≥1024; Google/Vertex: any positive int or -1 for auto, FR-071/FR-230)
  prompts_relative: true  # Resolve prompts relative to graph file
  prompts_dir: path/to   # Explicit prompts directory (optional)
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `provider` | `string` | env-based | Default LLM provider |
| `temperature` | `float` | `0.7` | Default temperature |
| `thinking_budget` | `int` | `None` | Extended thinking tokens. `anthropic`: `0` or `≥1024`, forces `temperature=1` (FR-071). `google`/`vertex`: any positive integer or `-1` for automatic mode; temperature not overridden (FR-230). |
| `prompts_relative` | `bool` | `false` | Resolve prompts relative to graph file |
| `prompts_dir` | `string` | `prompts/` | Explicit prompts directory path |

**Supported Providers:**

| Provider | Model Default | Env Variable | Notes |
|----------|---------------|--------------|-------|
| `anthropic` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` | Default. Best for complex reasoning |
| `google` | `gemini-2.0-flash` | `GOOGLE_API_KEY` | Fast, multimodal |
| `inception` | `mercury-2` | `INCEPTION_API_KEY` | Diffusion LLM, 660 t/s output. Ideal for schema-bound nodes |
| `mistral` | `mistral-large-latest` | `MISTRAL_API_KEY` | Good cost/quality balance |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` | Widely supported |
| `replicate` | varies | `REPLICATE_API_TOKEN` | Open models (Llama, etc.) |
| `xai` | `grok-beta` | `XAI_API_KEY` | Alternative provider |
| `lmstudio` | local | `LMSTUDIO_BASE_URL` | Local inference via LM Studio |

Provider selection priority: `node.provider` > `defaults.provider` > `PROVIDER` env > `"anthropic"`

**Prompt Resolution Order:**
1. If `prompts_dir` specified: `{prompts_dir}/{prompt_name}.yaml`
2. If `prompts_relative: true`: `{graph_dir}/{prompt_name}.yaml`
3. Default: `prompts/{prompt_name}.yaml`

**Example - Colocated prompts:**
```
questionnaires/
  audit/
    graph.yaml              # prompts_relative: true
    prompts/
      opening.yaml
      extract.yaml
  phq9/
    graph.yaml
    prompts/
      opening.yaml
```

```yaml
# questionnaires/audit/graph.yaml
defaults:
  prompts_relative: true

nodes:
  generate_opening:
    type: llm
    prompt: prompts/opening  # → questionnaires/audit/prompts/opening.yaml
```

---

### `data_files`
**Type:** `object`
**Default:** `{}`

Load external YAML files into graph state at compile time. Useful for:
- Schema definitions shared across prompts
- Configuration data (personas, categories, rules)
- Reference data that doesn't change between runs

```yaml
data_files:
  schema: schema.yaml           # Load as state.schema
  personas: data/personas.yaml  # Load as state.personas
```

**Paths are relative to the graph file**, not the working directory. This ensures portability.

**Security:** Path traversal (`../`) is blocked. Data files must be within the graph directory.

**Example - Survey with shared schema:**

```
surveys/
  satisfaction/
    graph.yaml
    schema.yaml        # Field definitions
    prompts/
      extract.yaml
```

```yaml
# surveys/satisfaction/graph.yaml
version: "1.0"
name: satisfaction-survey

data_files:
  schema: schema.yaml   # Loaded at compile time

nodes:
  extract:
    type: llm
    prompt: prompts/extract
    variables:
      fields: "{state.schema.fields}"  # Access loaded data
```

```yaml
# surveys/satisfaction/schema.yaml
fields:
  - name: satisfaction_score
    type: int
    range: [1, 10]
  - name: feedback
    type: str
    required: false
```

**Empty files** return `{}` (empty dict), not `null`.

**Glob patterns** (FR-629): When a value contains glob metacharacters (`*`, `?`, `[`),
all matching files are loaded into a dict keyed by filename stem:

```yaml
data_files:
  wiki: "wiki/*.yaml"   # → state.wiki = {"page1": {...}, "page2": {...}}
```

- **Zero matches** → empty dict (no error)
- **Sorted alphabetically** for deterministic ordering
- **Recursive `**` patterns are not supported** (raises error)
- Same path-traversal security as single files

This enables the read→write cycle with `write_data_file`: each run writes a
page to `wiki/<id>.yaml`, and the next run discovers all pages automatically.

**State collision:** If input provides a key that matches a `data_files` key, the input value wins.

---

### `config`
**Type:** `object`
**Default:** `{}`

Execution safety configuration. Controls resource limits and guard rails.

```yaml
config:
  recursion_limit: 50     # Max LangGraph super-steps (default: 50)
  max_map_items: 100      # Default fan-out cap for map nodes (default: 100)
  max_tokens: 4096        # Default max output tokens for LLM calls (default: provider default)
  timeout: 120            # Global execution timeout in seconds (default: none)
  tool_load_mode: strict  # Python tool loading policy: strict|warn (default: strict)
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `recursion_limit` | `int` | `50` | Maximum LangGraph recursion depth. Prevents infinite loops in cyclic graphs. |
| `max_map_items` | `int` | `100` | Default fan-out cap for map nodes. Can be overridden per-node with `max_items`. |
| `max_tokens` | `int` | provider default | Default max output tokens for LLM calls. Can be overridden per-node. |
| `timeout` | `int` | none | Global execution timeout in seconds. Covers the entire graph run including interrupt loops. |
| `tool_load_mode` | `string` | `strict` | Python tool load policy: `strict` fails compilation on import/symbol errors, `warn` logs warnings and compiles with a partial runtime tool registry. |

**CLI overrides:**
```bash
yamlgraph graph run graph.yaml --recursion-limit 25 --timeout 60
```

CLI values override YAML `config:` values, which override built-in defaults.

---

## Node Definition

Each node in the `nodes` section defines a processing step.

### Common Node Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `type` | `string` | `"llm"` | Node type: `llm`, `router`, `agent`, `tool`, `python`, `map`, `interrupt`, `passthrough`, `tool_call`, `subgraph`, `interactive_tool` |
| `prompt` | `string` | varies | Prompt file path (without `.yaml`) |
| `variables` | `object` | `{}` | Template variable mappings |
| `state_key` | `string` | node name | State key to store result |
| `requires` | `list[str]` | `[]` | Required state keys before execution |
| `temperature` | `float` | from defaults | LLM temperature |
| `provider` | `string` | from defaults | LLM provider |
| `max_tokens` | `int` | from config | Maximum output tokens for this node's LLM call |
| `thinking_budget` | `int` | from defaults | Extended thinking tokens. `anthropic`: `0` or `≥1024`, forces `temperature=1` (FR-071). `google`/`vertex`: any positive integer or `-1` for automatic mode; temperature not overridden (FR-230). |
| `skip_if_exists` | `bool` | `true` | Skip if state key has truthy value (FR-050: `[]`, `""`, `None` do NOT skip) |
| `parse_json` | `bool` | `false` | Extract JSON from LLM response |
| `stream` | `bool` | `false` | Enable token-by-token streaming |
| `route_field` | `string` | — | **Required for routers.** Schema field to extract route key from (FR-107) |
| `verification` | `object` | `null` | Verification gate: falsifiable prediction checked after execution (FR-164) |
| `guards` | `object` | `null` | Deterministic pre/post guard rules with explicit policy (FR-344) |
| `timeout` | `float` | `null` | Per-node execution timeout in seconds (FR-069). Wraps execution in a one-shot `ThreadPoolExecutor`. On timeout, a `PipelineError` with `error_type=TIMEOUT_ERROR` is returned. Works on all node types. |

### `type: llm` - Standard LLM Node

Basic LLM execution with structured output.

```yaml
nodes:
  generate:
    type: llm
    prompt: generate                 # prompts/generate.yaml
    temperature: 0.8
    variables:
      topic: "{state.topic}"
      word_count: "{state.word_count}"
    state_key: generated
    requires: []                     # No dependencies
```

**JSON Extraction:**

When LLMs wrap JSON in markdown code blocks, use `parse_json: true`:

```yaml
nodes:
  extract_fields:
    type: llm
    prompt: extract
    state_key: extracted
    parse_json: true                 # Auto-extract JSON from response
```

This extracts JSON from responses like:
```
```json
{"name": "test", "value": 42}
```

Reasoning: I extracted the structured data...
```

The node stores the parsed dict `{"name": "test", "value": 42}` instead of raw string.

**Streaming:**

For token-by-token output, use the CLI `--stream` flag:

```bash
yamlgraph graph run graph.yaml --var topic="AI" --stream
```

All LLM nodes stream automatically — no per-node config needed.

```yaml
  generate:
    type: llm
    prompt: generate                 # prompts/generate.yaml
    temperature: 0.8
    variables:
      topic: "{state.topic}"
      word_count: "{state.word_count}"
    state_key: generated
    requires: []                     # No dependencies
```

### `type: router` - Conditional Routing

Routes to different nodes based on LLM classification.

```yaml
nodes:
  classify:
    type: router
    prompt: router-demo/classify_tone
    route_field: tone                    # Schema field to extract route key from
    routes:                              # Maps classification → node
      positive: respond_positive
      negative: respond_negative
      neutral: respond_neutral
    default_route: respond_neutral       # Fallback if no match
    variables:
      message: "{state.message}"
    state_key: classification
```

**Required properties for routers:**
- `route_field`: The schema field name to extract the route key from (e.g. `intent`, `tone`, `decision`)
- `routes`: Map of classification values to target nodes
- Prompt must return an object with a field matching `route_field`

### `type: agent` - Tool-Using Agent

Agent with access to tools for multi-step reasoning.

```yaml
nodes:
  analyze:
    type: agent
    prompt: git_analyst
    tools: [recent_commits, commit_details]  # Tools from graph's tools section
    max_iterations: 8                         # Max tool calls
    state_key: analysis
```

**Agent-specific properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `tools` | `list[str]` | `[]` | Tool names from graph's `tools` section |
| `max_iterations` | `int` | `10` | Maximum tool invocations |
| `tool_results_key` | `string` | - | State key for tool execution logs |

### `type: tool` - Shell Tool Node

Execute a shell command tool deterministically (no LLM decision-making).

```yaml
nodes:
  fetch_commits:
    type: tool
    tool: recent_commits             # References tool from tools section
    variables:
      count: "{state.num_commits}"
    state_key: commit_data
```

**Tool node properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `tool` | `string` | required | Name of shell tool from `tools` section |
| `variables` | `object` | `{}` | Variable mappings for command substitution |
| `state_key` | `string` | node name | State key to store command output |
| `on_error` | `string` | `"fail"` | Error handling: `skip` or `fail` |

**Difference from related types:**

| Type | Description |
|------|-------------|
| `tool` | Executes a named shell tool deterministically |
| `tool_call` | Dynamically selects tool name from state |
| `agent` | LLM decides which tools to call |

**Example with tools section:**

```yaml
tools:
  recent_commits:
    command: "git log --oneline -n {count}"
  file_diff:
    command: "git diff {commit_hash}"

nodes:
  get_history:
    type: tool
    tool: recent_commits
    variables:
      count: "10"
    state_key: history
```

All user-provided variables are sanitized with `shlex.quote()` to prevent shell injection.

### `type: python` - Python Function Node

Execute an arbitrary Python function as a node.

```yaml
nodes:
  generate_images:
    type: python
    tool: generate_images            # References tool from tools section
    state_key: images
    requires: [story]                # Wait for story to be generated
```

**Python node properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `tool` | `string` | required | Name of Python tool from `tools` section |
| `state_key` | `string` | node name | State key to store result |
| `requires` | `list[str]` | `[]` | Required state keys before execution |
| `on_error` | `string` | `"fail"` | Error handling: `skip` or `fail` |

**Note:** The Python function must be defined in the `tools` section with `type: python`.

### `type: copilot` - Copilot Delegation

Delegate complex reasoning tasks to GitHub Copilot CLI (`backend: cli`), to Claude Code CLI (`backend: claude`, FR-959), or directly to provider APIs via YAMLGraph's prompt executor (`backend: api`).

**FR-081, FR-383, FR-959** | **CAP-30** | **REQ-YG-087, REQ-YG-089, REQ-YG-356, REQ-YG-357, REQ-YG-639, REQ-YG-640, REQ-YG-641**

```yaml
nodes:
  plan_feature:
    type: copilot
    prompt: plan                    # Prompt template
    cli_flags:
      allow_all_paths: true         # --allow-all-paths flag
      allow_all_tools: true         # --allow-all-tools flag
      model: claude-sonnet-4        # Optional model override
    variables:
      topic_file: "{state.topic}"
    state_key: plan_result
    timeout: 300                    # Timeout in seconds (default: 300)
```

**Copilot node properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `prompt` | `string` | required | Name of prompt template |
| `backend` | `string` | `"cli"` | Execution backend: `cli`, `api`, `sampling` (reserved), or `claude`. **Closed, case-sensitive set**: any other value (a typo, another casing, `""`, a non-string) fails at schema load, at compile, and in lint (`E-COPILOT-BACKEND-UNKNOWN`) — it never falls through to Copilot |
| `cli_flags` | `object` | `{}` | CLI flags (see below) |
| `timeout` | `int` | `300` | Timeout in seconds |
| `state_key` | `string` | node name | State key for CopilotResult |
| `variables` | `object` | `{}` | Variables for prompt template |
| `requires` | `list[str]` | `[]` | Required state keys |
| `on_error` | `string` | `"fail"` | Error handling: `skip`, `fail`, `retry` |

**CLI flags:**

| Flag | Type | CLI Argument | Description |
|------|------|--------------|-------------|
| `allow_all_paths` | `bool` | `--allow-all-paths` | Allow file system access |
| `allow_all_tools` | `bool` | `--allow-all-tools` | Allow all MCP tools |
| `model` | `string` | `--model <model>` | Override default model |
| `resume` | `string` | `--resume <id>` | Resume a specific session (FR-105) |
| `continue_session` | `bool` | `--continue` | Resume most recent session (FR-105) |

**Backend semantics (FR-383, FR-959):**
- `backend: cli` (default): runs `copilot --silent ...` subprocess and supports `cli_flags`.
- `backend: api`: runs through `execute_prompt()` (provider API path), supports prompt schemas/structured output, and returns `CopilotResult` with `backend="api"` and `session_id=None`.
- `backend: claude`: runs `claude -p <prompt> --output-format json` (Claude Code CLI, print mode) and returns `CopilotResult` with `backend="claude"` and the real Claude `session_id`. See the Claude section below.
- CLI-only flags (`allow_all_tools`, `allow_all_paths`, `resume`, `continue_session`) are invalid with `backend: api` (linter error). Claude-only flags (`tools`, `allowed_tools`, `max_turns`) are invalid with `backend: cli` and `backend: api` (linter error).

**Claude Code backend (FR-959, REQ-YG-639/640/641):**

```yaml
nodes:
  judge:
    type: copilot
    backend: claude
    cli_flags:
      model: opus                       # alias or full claude-* id
      tools: [Read, Glob, Grep, Write]  # AVAILABILITY: which tools exist   → --tools "Read,Glob,Grep,Write"
      allowed_tools: [Read, Glob, Grep, Write]  # APPROVAL: no permission prompt → --allowedTools "..."
      max_turns: 40                     # --max-turns 40
    prompt: judge
    state_key: judge_result
```

Claude flag table (typed; `backend: claude` validates `cli_flags` strictly — a string where a list is expected, `max_turns: "40"`, `max_turns: 0`, `max_turns: true`, or an unknown key is a schema, compile, and lint error `E-COPILOT-CLAUDE-FLAG-SHAPE`, never a silently dropped flag):

| Flag | Type | Claude argv | Meaning |
|------|------|-------------|---------|
| `model` | `str` | `--model <m>` | alias (`opus`, `sonnet`) or full id; Copilot-only names (`gpt-*`, `*-sol`) warn `W-COPILOT-CLAUDE-MODEL` |
| `resume` | `str` | `--resume <id>` | supports `{state.x.session_id}` (FR-105) |
| `continue_session` | `bool` | `--continue` | exclusive with `resume` |
| `tools` | `list[str]` | `--tools "A,B"`; `[]` → `--tools ""` | which built-in tools **exist** for the model (`[]` = none) |
| `allowed_tools` | `list[str]` | `--allowedTools "A,B"` | which existing tools run **without a permission prompt**; does **not** restrict availability — without `tools` every default tool stays available (`W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT`) |
| `allow_all_tools` | `bool` | `--dangerously-skip-permissions` | approve everything that exists; together with `allowed_tools` the narrow list is dead (`W-COPILOT-CLAUDE-TOOLS`) |
| `allow_all_paths` | `bool` | `--add-dir <cwd>` | filesystem access to the working directory |
| `max_turns` | `int > 0` | `--max-turns <n>` | agent turn limit (accepted by the pinned CLI; absent from its `--help`) |

Argv order is frozen exactly as the table order after `claude -p <prompt> --output-format json`. `provider:` on a claude node is an error (`E-COPILOT-CLAUDE-PROVIDER`): provider selection is an API-key payer signal.

*Per-invocation preflight, no cache.* Before **every** `-p` call the node runs, with the same sanitized environment: (1) `claude --version`, which must be exactly one of the supported versions — currently `2.1.255` only; any other version fails naming the observed and accepted versions; (2) `claude auth status`, which must exit 0 and report `loggedIn: true`, `apiProvider: "firstParty"`, and an `authMethod` in the subscription set (`claude.ai` for the browser login, `oauth_token` for a setup token; both pinned to raw captures). `none`, `api_key`, and `third_party` (Bedrock/Vertex/Foundry) all refuse before any agent prompt. The raw captures these rules are pinned to: [`feature-requests/evidence/FR-959-claude-auth-probe.md`](../feature-requests/evidence/FR-959-claude-auth-probe.md).

*Payer boundary.* The child environment (probes and agent alike) is `os.environ` minus `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`; `CLAUDE_CODE_OAUTH_TOKEN`, `PATH`, and the FR-363 OTel layering are kept. **Residual (accepted by the spend owner, FR-959 Option A):** Claude Code applies its own settings after launch, so a user, project, local, or managed settings `env` block, an `apiKeyHelper`, or enterprise cloud-provider settings can still change the payer between the preflight and the call. The preflight *detects* those states (a settings block alone reports `authMethod: api_key`); it cannot *prevent* a change made in that window. Never fall back to an API key when the login is missing.

*Result contract.* stdout must be one JSON object with `result: str`, `session_id: str`, and optional `is_error: bool`; it crosses a typed envelope before `CopilotResult`. `is_error: true` is a failure regardless of exit code (the envelope's `subtype` reads `"success"` even then). Non-zero exit, `is_error`, malformed envelope, non-JSON stdout, missing binary, and timeout all raise; only 0-versus-non-zero is interpreted, and there is no usage-limit classifier.

**Session continuation (FR-105):**

Use `resume` or `continue_session` to continue work within an existing Copilot session. This enables multi-task workflows where sequential nodes share context:

```yaml
nodes:
  plan:
    type: copilot
    prompt: plan
    cli_flags:
      allow_all_tools: true
    state_key: plan_result

  implement:
    type: copilot
    prompt: implement
    cli_flags:
      allow_all_tools: true
      resume: "{state.plan_result.session_id}"  # Continue plan's session
    state_key: implement_result
```

**Notes:**
- `resume` and `continue_session` are mutually exclusive (linter enforces this)
- `resume` supports state expressions like `{state.prev_result.session_id}`
- Session ID is extracted from CLI stderr and stored in `CopilotResult.session_id`

**Notes:**
- The `--silent` flag is always added automatically
- Command is executed as a list (no shell injection risk)
- The `sampling` backend remains reserved and is not implemented

**CopilotResult:**

The node returns a `CopilotResult` object in the state:

```python
class CopilotResult(BaseModel):
    output: str            # Copilot's response text
    exit_code: int         # Process exit code (0 = success)
    model: str | None      # Model used (if specified)
    backend: str           # "cli", "api", "sampling", or "claude"
    session_id: str | None # Session ID for resumption (FR-105)
```

Access in subsequent nodes:
```yaml
variables:
  plan_text: "{state.plan_result.output}"
```

**Example - Plan-Judge Workflow with Session Continuation:**

```yaml
# Based on .chaplain/watcher2.sh pattern
# FR-105: Judge resumes plan's session for context continuity
nodes:
  plan:
    type: copilot
    prompt: plan
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    variables:
      topic_file: "{state.topic}"
    state_key: plan_result

  judge:
    type: copilot
    prompt: judge
    backend: cli
    cli_flags:
      allow_all_paths: true
      resume: "{state.plan_result.session_id}"  # FR-105
    variables:
      draft_file: "{state.plan_result.output}"
    state_key: verdict
```

See [examples/copilot/](../examples/copilot/) for a complete demo.

### `type: map` - Parallel Fan-Out Node

Process each item in a list in parallel using LangGraph's `Send()` API.

```yaml
nodes:
  animate_panels:
    type: map
    over: "{state.story.panels}"     # List to iterate over
    as: panel_prompt                  # Variable name for each item
    node:                             # Sub-node executed per item
      type: llm
      prompt: animate_panel
      state_key: animated_panel
    collect: animated_panels          # State key for collected results
```

**Map node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `over` | `string` | Yes | State expression for the list to iterate |
| `as` | `string` | Yes | Variable name injected into sub-node |
| `node` | `object` | Yes | Sub-node definition (llm, router, or python) |
| `collect` | `string` | Yes | State key where results are collected |
| `max_items` | `int` | No | Maximum fan-out items (overrides `config.max_map_items`) |
| `timeout` | `float` | No | Per-branch timeout in seconds (FR-069). Each branch must complete within this limit. |
| `on_error` | `string` | No | Error handling: `skip` skips timed-out branches, `fail` (default) raises |

**How it works:**
1. Fan-out: Each item is dispatched via `Send()` for parallel processing
2. Process: Sub-node runs independently per item with `{state.<as>}` available
3. Collect: Results are aggregated using `Annotated[list, operator.add]` reducer

**Sub-node variable access:**
```yaml
as: panel_prompt
node:
  type: llm
  prompt: animate_panel
  variables:
    prompt: "{state.panel_prompt}"    # Access injected item
    context: "{state.story.title}"    # Access parent state
```

See [Map Nodes Reference](map-nodes.md) for detailed examples and patterns.

**Known limitation — thread leakage (FR-069):** When `Future.result(timeout=N)` raises `TimeoutError`, the submitted thread continues running until the callable returns naturally or the process exits. In a long-lived process, a high rate of timeouts may accumulate background threads. Cancellable futures are out of scope; a follow-on FR may address this using structured concurrency.

### `type: interrupt` - Human-in-the-Loop

Pause execution to wait for human input. Requires a checkpointer.

```yaml
checkpointer:
  type: memory

nodes:
  ask_name:
    type: interrupt
    message: "What is your name?"
    resume_key: user_name
```

**Interrupt node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `message` | `string/dict` | Yes* | Static interrupt payload |
| `prompt` | `string` | Yes* | Prompt name for dynamic payload |
| `state_key` | `string` | No | Where to store payload (default: `interrupt_message`) |
| `resume_key` | `string` | No | Where to store resume value (default: `user_input`) |

*Either `message` or `prompt` required.

See [Interrupt Nodes Reference](interrupt-nodes.md) for resume flow and Python API.

### `type: passthrough` - State Transformation

Transform state without external calls. Useful for counters and accumulators.

```yaml
nodes:
  increment_turn:
    type: passthrough
    output:
      turn_number: "{state.turn_number + 1}"
      history: "{state.history + [state.current_action]}"
```

**Passthrough node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `output` | `dict` | Yes | Map of state keys to expressions |

Supports arithmetic and list operations. See [Expression Language Reference](expressions.md) for full syntax.

See [Passthrough Nodes Reference](passthrough-nodes.md) for patterns and examples.

### `type: tool_call` - Dynamic Tool Execution

Execute a tool where name and arguments come from state (LLM-driven orchestration).

```yaml
nodes:
  execute_tool:
    type: tool_call
    tool: "{state.selected_tool}"
    args: "{state.tool_arguments}"
    state_key: tool_result
```

**Inline dict args (FR-772)** — deterministic invocation with mixed literal
and templated kwargs, resolved per value (FR-252 semantics):

```yaml
nodes:
  describe:
    type: tool_call
    tool: describe_image
    args:
      image: "{state.image}"        # templated — resolved from state
      instruction: "Title, 2-sentence description, and 8 DeviantArt tags."
      provider: google              # literal — passed through
    state_key: described
```

Inline values preserve non-string types; a simple missing path
(`"{state.missing}"`) resolves to `None`; a resolved value still containing
`{state.` (embedded interpolation of a missing path) raises `ValueError` at
node execution — garbage kwargs never reach the tool. An empty inline
mapping dispatches no kwargs. The string form above is unchanged.

**Tool call node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `tool` | `string` | Yes | Tool name or state expression resolving to it |
| `args` | `string \| dict` | Yes | State expression resolving to args dict, or inline mapping resolved per value |
| `state_key` | `string` | No | Where to store result |
| `parsed_key` | `string` | No | FR-810: state key exposing the **parsed dict** output of a graph-runtime tool, routable by edge conditions (see below). Graph tools only |
| `on_error` | `string` | No | `skip` (default): failure envelope `{success: false, error}` and the graph continues — for agent loops that must see error text. `fail`: raise at the node with the tool's actual error — for deterministic pipelines where a failed prerequisite must stop the run (FR-778). `retry`/`fallback` are rejected at graph load |

Use `on_error: fail` in deterministic pipelines: without it a failed tool
produces a success-shaped envelope that downstream nodes trip over at a
distance (e.g. a map resolving `chunks` from a failed split). Keep the
default envelope when an agent consumes the result.

**Router-visible tool outputs (`parsed_key`, FR-810)** — a graph-runtime
tool's output is normally a JSON string buried inside the wrapper under
`state_key`, invisible to edge conditions. `parsed_key` exposes the parsed
dict as its own state key so edges can route on its fields:

```yaml
tools:
  analyzer:
    type: graph
    path: child/graph.yaml
    output_key: findings

nodes:
  page_analysis:
    type: tool_call
    tool: analyzer
    args: {}
    state_key: page_analysis     # wrapper preserved unchanged
    parsed_key: page_findings    # parsed dict, routable
    on_error: fail

edges:
  - from: page_analysis
    to: sniff
    condition: "page_findings.is_spa == true"
  - from: page_analysis
    to: no_sniff
    condition: "page_findings.is_spa != true"
```

Contract: graph-runtime tools only (lint `W703` warns on statically known
shell/python misuse; dynamically resolved non-graph tools fail at runtime
per `on_error`). Dict outputs pass through; JSON-object strings parse;
anything else (invalid JSON, lists, scalars, missing output) is a parse
failure — never an empty-dict substitute. On failure, `on_error: fail`
raises and `skip` returns the failure envelope without setting
`parsed_key`. The wrapper under `state_key` keeps the raw output either way.

See [Tool Call Nodes Reference](tool-call-nodes.md) for agent integration patterns.

### `type: subgraph` - Nested Graph

Embed and execute another graph as a node. Enables modular composition.

```yaml
nodes:
  summarize:
    type: subgraph
    mode: invoke
    graph: subgraphs/summarizer.yaml
    input_mapping:
      prepared_text: input_text      # parent → child
    output_mapping:
      summary: output_summary        # child → parent
```

**Subgraph node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `graph` | `string` | Yes | Path to child graph YAML |
| `mode` | `string` | No | `invoke` (default) or `stream` |
| `input_mapping` | `dict` | No | Map parent state keys to child state keys |
| `output_mapping` | `dict` | No | Map child state keys to parent state keys |

See [Subgraph Nodes Reference](subgraph-nodes.md) for state mapping patterns and nesting.

### `type: interactive_tool` - Multi-Turn Conversation Loop

Packs a full multi-turn conversation (start → ask → step ↺ → end) into a
single YAML node. Expands at compile time into `interrupt` and `python` nodes
with automatic edge wiring — no manual routing needed.

```yaml
nodes:
  chat:
    type: interactive_tool
    start: chatbot_start           # Python tool: initialise session
    step: chatbot_step             # Python tool: process each turn
    end: chatbot_end               # Python tool: summarise (optional)
    resume_key: user_message       # State key for user input
    response_key: bot_response     # State key shown to user
    loop_until: "state.session_done == True"
    max_iterations: 10             # Safety guard (default: 10)
```

Expands into:

```
chat__start → chat__ask → chat__step ↺ → chat__end
                  ↑              │
                  └──────────────┘  (loops until condition met)
```

**Interactive tool properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `start` | `string` | Yes | Python tool name for session initialisation |
| `step` | `string` | Yes | Python tool name for processing each turn |
| `end` | `string` | No | Python tool name for session summary |
| `resume_key` | `string` | Yes | State key where user input is stored |
| `response_key` | `string` | Yes | State key for bot response (shown at interrupt) |
| `loop_until` | `string` | Yes | Condition expression (e.g. `state.done == True`) |
| `max_iterations` | `int` | No | Maximum loop iterations before forced exit (default: 10) |
| `on_error` | `string` | No | Error handling for expanded nodes |

Each tool receives the full state dict and returns a state update dict.
The `end` tool is optional — without it, the step node exits directly to
the next edge when `loop_until` fires.

See [examples/demos/interactive_tool/](../examples/demos/interactive_tool/) for a working trivia quiz demo.

### `type: pipeline` - Sequential Item Processing

Process a list of items through a series of stages sequentially. Expands at compile time into concrete nodes and edges — no Python needed.

```yaml
nodes:
  chapters:
    type: pipeline
    items:
      - name: ch1
        title: "The Beginning"
      - name: ch2
        title: "The Journey"
    stages:
      - name: draft
        type: llm
        prompt: draft_chapter
        variables:
          title: "{item.title}"
        state_key: draft_{item.name}
      - name: polish
        type: llm
        prompt: polish_chapter
        variables:
          draft: "{state.draft_{item.name}}"
        state_key: polished_{item.name}
```

### `type: race` - Race Multiple Providers

Fire the same prompt to multiple LLM provider/model candidates concurrently
and return the fastest successful response (FR-232). Useful for
latency-sensitive graphs where hedging across providers reduces tail latency.

```yaml
nodes:
  fastest_answer:
    type: race
    prompt: answer
    state_key: answer
    timeout: 15
    candidates:
      - provider: mistral
        model: mistral-small-latest
      - provider: openai
        model: gpt-4o-mini
      - provider: google
        model: gemini-2.0-flash
```

**Race node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `candidates` | `list[{provider, model}]` | Yes | Provider/model pairs to race (minimum 2) |
| `timeout` | `int` | No | Per-candidate timeout in seconds (default: 30) |
| `prompt` | `string` | Yes | Prompt template name |
| `state_key` | `string` | Yes | State key for the winning response |
| `temperature` | `float` | No | LLM temperature for all candidates |
| `parse_json` | `bool` | No | Extract JSON from LLM response (default: false) |

**How it works:**
1. All candidates are dispatched concurrently via `ThreadPoolExecutor`
2. The first candidate to return a successful response wins
3. Remaining in-flight candidates are cancelled
4. `state_key` receives the winning response text
5. `_race_winner` is set to a string identifying which candidate won (e.g. `"mistral/mistral-small-latest"`)

**Error handling:** When all candidates fail (timeout or exception), the node's
`on_error` policy applies (`skip`, `retry`, `fail`, or `fallback`).

See [examples/demos/race/](../examples/demos/race/) for a working demo.

### `type: pipeline` - Compile-Time Pipeline Templates

Define a sequence of stages once, iterate over a list of items, and expand
to concrete nodes and edges at compile time (FR-235). This is a meta-node —
it does not exist at runtime, only its expanded concrete nodes do.

```yaml
nodes:
  topics:
    type: pipeline
    items:
      - name: sun
        subject: "the Sun"
      - name: moon
        subject: "the Moon"
    stages:
      - name: draft
        type: llm
        prompt: draft
        variables:
          subject: "{item.subject}"
        state_key: draft_{item.name}
      - name: polish
        type: llm
        prompt: polish
        variables:
          draft: "{state.draft_{item.name}}"
        state_key: polished_{item.name}
```

**Pipeline node properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `items` | `list` | Yes | List of items to process (each must have `name`) |
| `stages` | `list` | Yes | Stage definitions executed per item in order |

**How it works:**
1. Each item is processed through all stages sequentially
2. `{item.field}` in stage configs is interpolated per item
3. Items execute sequentially: ch1 stages → ch2 stages → …
4. External edges are rewritten to the first/last expanded nodes

See [examples/demos/pipeline/](../examples/demos/pipeline/) for a working demo.

#### Accumulated State

When later items need context from earlier items, use a shared `state_key` with a reducer. The `add` reducer on a list field accumulates results across items instead of overwriting.

**State config with reducer:**

```yaml
state:
  glossary:
    type: list
    reducer: add

nodes:
  chapters:
    type: pipeline
    items:
      - name: ch1
        title: "The Beginning"
      - name: ch2
        title: "The Journey"
      - name: ch3
        title: "The Return"
    stages:
      - name: translate
        type: llm
        prompt: translate_chapter
        variables:
          title: "{item.title}"
          glossary: "{state.glossary}"
        state_key: translated_{item.name}
      - name: extract_terms
        type: llm
        prompt: extract_terms
        variables:
          translation: "{state.translated_{item.name}}"
        state_key: glossary
        skip_if_exists: false
```

**How accumulated state works:**

1. ch1's `extract_terms` writes `["term_a"]` to `glossary` — reducer appends to empty list
2. ch2's `translate` reads `glossary: ["term_a"]` — previous terms available as context
3. ch2's `extract_terms` writes `["term_b"]` — reducer appends, glossary is now `["term_a", "term_b"]`
4. ch3's `translate` reads the full accumulated glossary

**Why `{prev_item}` syntax is unnecessary:** The `add` reducer on a shared state key solves cross-item reads without new interpolation syntax. Each stage reads `{state.glossary}` — the reducer handles accumulation.

**Sequential execution constraint:** Accumulated state works because pipeline items execute sequentially (ch1 → ch2 → ch3). If pipelines ever support parallel item execution, cross-item dependencies become impossible. Sequential chaining is what makes accumulation work. This is a feature, not a limitation.

**`skip_if_exists: false` requirement (W021):** List-typed state keys with the `add` reducer are truthy after the first append. The default `skip_if_exists: true` on LLM nodes causes stages 2+ to skip. Accumulated state keys require explicit `skip_if_exists: false`. The linter warns about this (W021).

**Available reducers:**

| Reducer | Behavior | Use Case |
|---------|----------|----------|
| `add` | Append new items to list | Accumulating results across stages |
| `last_value` | Keep last written value | Safe concurrent fan-in |
| `sorted_add` | Append and sort by `_map_index` | Map node result ordering |
| `items` | `list[dict]` | Yes | List of item dicts; each must have a `name` field plus arbitrary fields |
| `stages` | `list[dict]` | Yes | List of node configs supporting `{item.field}` and `{state.field}` interpolation |

**Expansion semantics:**
- `N items × M stages = N×M` concrete nodes, chained sequentially per item
- External edges (e.g. `START → pipeline_node`, `pipeline_node → END`) are
  rewritten to point to the first and last expanded nodes respectively
- Expanded node names follow the pattern `<pipeline>_<item>_<stage>`

**Interpolation:**
- `{item.field}` — replaced with the item's field value in `prompt`, `variables`, `state_key`
- `{state.field}` — replaced at runtime with state values (use in `variables`)
- Non-string fields are copied verbatim (no interpolation)

**Lint checks:** E401 (empty items), E402 (empty stages), E403 (unresolved
`{item.xxx}` references), E404 (item missing `name` field).

See [examples/demos/pipeline/](../examples/demos/pipeline/) for a working demo.
### Error Handling Properties

All node types support error handling:

```yaml
nodes:
  generate:
    type: llm
    prompt: generate
    on_error: fallback               # skip | retry | fail | fallback
    max_retries: 3                   # For retry mode
    fallback:
      provider: anthropic            # Fallback provider for fallback mode
```

| `on_error` Value | Behavior |
|------------------|----------|
| `skip` | Log warning, continue without output |
| `retry` | Retry up to `max_retries` times |
| `fail` | Raise exception, halt pipeline |
| `fallback` | Try `fallback.provider` on failure |

### Verification Gates (FR-164)

Add a `verification` field to any LLM node to state a falsifiable prediction about its output. After execution, the framework checks the prediction using deterministic pattern matching.

```yaml
nodes:
  fetch_articles:
    type: llm
    prompt: search_articles
    state_key: articles
    on_error: skip
    verification:
      question: "Will return 3-10 documents about {topic}"
      on_fail: warn             # warn (default) | halt | retry

  summarize:
    type: llm
    prompt: summarize
    state_key: summary
    verification:
      question: "Will contain at least 100 characters"
      on_fail: halt
```

| Sub-field | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | `str` | — | **Required.** Falsifiable prediction. Supports `{var}` interpolation from state |
| `on_fail` | `str` | `warn` | Action on violation: `warn` (log + continue), `halt` (raise), `retry` (re-execute) |
| `max_retries` | `int` | `1` | Max retry attempts when `on_fail: retry`. Falls through to `warn` after exhaustion |

**Supported patterns:**

| Pattern | Example | Check |
|---------|---------|-------|
| Count range | `"Will return 3-10 items"` | `min <= len(result) <= max` |
| Non-empty | `"Will return non-empty"` | `bool(result)` |
| Contains | `"Will contain {keyword}"` | `keyword in str(result)` |
| Custom | Any other text | Annotation only (logged, no failure) |

**Lint rule W022:** Warns when a node uses `on_error: skip` without a verification question.

### Deterministic Node Guards (FR-344)

Add `guards.pre` and `guards.post` to assert deterministic constraints before and after node execution.

```yaml
nodes:
  enforce_inputs:
    type: llm
    prompt: summarize
    state_key: summary
    guards:
      pre:
        - check: "state.fr_path | file_exists"
          on_fail: halt
          message: "FR file not found"
      post:
        - check: "output | length < 500"
          on_fail: warn
        - check: "'summary' in output | keys"
          on_fail: retry
          max_retries: 2
```

| Path | Type | Description |
|------|------|-------------|
| `guards.pre` | `list[rule]` | Pre-execution guards. `on_fail`: `warn`, `halt`, `skip` |
| `guards.post` | `list[rule]` | Post-execution guards. `on_fail`: `warn`, `halt`, `retry` |
| `rule.check` | `str` | Deterministic expression (`state.*`, `output.*`, logic/comparisons, filters) |
| `rule.message` | `str \| null` | Optional custom failure message |
| `rule.max_retries` | `int` | Only valid for post guards with `on_fail: retry` (default `1`) |

Supported filters in guard expressions: `length`, `file_exists`, `dir_exists`, `type`, `keys`.

**Lint rule W025:** Warns when guard rules are syntactically valid YAML but not executable guard expressions.

**Lint rule W026 (prompt-monolith):** Warns when a prompt asks one LLM call to make too many independent judgements at once — the attention-overload anti-pattern where the hardest judgement starves under load (FR-584/FR-585). Warning severity only; it never changes lint exit status. Two complementary detectors:

- **W026-1 (inline-schema field count):** an inline `schema:`/`output_schema:` declaring `field_threshold` or more top-level `fields:` (default **4**). Nested fields under one parent count as one — the signal is the number of *independent top-level outputs*, not depth. The threshold is the `field_threshold` parameter of `check_prompt_complexity` (no lint-config file).
- **W026-2 (prose phrases):** a small curated set of phrases signalling enumerated multi-output (`assign FOUR slices`, `extract three sections`) or a global cross-unit constraint (`forward only`, `every … should … later`). The phrase list is deliberately small — precision over recall — and grows only with a fixture proving the addition is warranted.

Remedy: split discrimination from bookkeeping (FR-585 decode pattern) or push global cross-unit constraints to a deterministic post-pass.

---

### Graph-Level Verification (FR-677)

Node `guards` assert constraints on a *single* node. A top-level `verify:` block
asserts constraints on the *final graph state*, once, before the graph ends. It
is the graph-wide postcondition — an acceptance gate that reuses the same guard
expression language.

```yaml
nodes:
  compute:
    type: python
    function: mypkg.compute
    state_key: result
edges:
  - from: START
    to: compute
  - from: compute
    to: END

verify:
  - check: "state.result >= 100"
    on_fail: halt
    message: "result below acceptance threshold"
  - check: "state.warnings | length == 0"
    on_fail: warn
```

At load time a terminal `__verify__` node is inserted and every explicit `END`
destination (scalar edges, list fan-out/router edges, router `routes` and
`default_route`, and `loop_exits`) is redirected through it, then `__verify__`
connects to `END`. The rules run once against the final state:

| Path | Type | Description |
|------|------|-------------|
| `verify` | `list[rule]` | Graph-wide postconditions evaluated once before END |
| `rule.check` | `str` | Deterministic expression (`state.*`, logic/comparisons, filters) |
| `rule.on_fail` | `str` | `halt` (raise with the message) or `warn` (record a `PipelineError` in `state.errors` and continue) |
| `rule.message` | `str \| null` | Optional custom failure message |

`on_fail: retry` is **not** valid at the graph level — retrying the whole graph
is out of scope, so `retry` and `max_retries` are rejected at load. Graph-level
`verify:` expressions are validated by lint rule **W025**, the same executable
expression check applied to node guards.

### Lint Gate on Run (`--gate`, FR-677)

Lint findings are advisory unless enforced. `yamlgraph graph run --gate` lints
the graph *before* executing and refuses to run on any **error**-level finding
(exit code 1, the graph is never compiled). Warning-level findings (such as
W025/W026) are reported but do not block.

```bash
yamlgraph graph run graph.yaml --gate          # refuse to run on any error-level finding
yamlgraph graph run graph.yaml --gate --json   # machine-readable lint report (only on block)
```

With `--gate --json`, the lint report is emitted as JSON to stdout only when
the gate blocks; a clean or warning-only graph produces no decorative stdout.

---

## Variable Templates

The `variables` section maps prompt variables to state values.

### Syntax

```yaml
variables:
  simple: "{state.field}"              # Direct field access
  nested: "{state.obj.attr}"           # Nested object access
  loop: "{state._loop_counts.node}"    # Access loop counter
```

### Resolution

Templates are resolved at runtime by `node_factory.resolve_template()`:

1. `{state.field}` → `state.get("field")`
2. `{state.obj.attr}` → `state.get("obj").attr`
3. Lists are joined with `, ` for simple template placeholders

---

## Edge Definition

Edges define the flow between nodes.

### Linear Edge

Simple node-to-node connection:

```yaml
edges:
  - from: generate
    to: analyze
```

### Entry Point

Start the graph at a node:

```yaml
edges:
  - from: START
    to: generate
```

### Terminal Edge

End the graph after a node:

```yaml
edges:
  - from: summarize
    to: END
```

### Conditional Edge (Router)

For router nodes, specify multiple targets:

```yaml
edges:
  - from: classify
    to: [respond_positive, respond_negative, respond_neutral]
    type: conditional
```

### Parallel Fan-Out Edge

Run multiple target nodes concurrently after a single source completes (FR-234).
Use `to: [list]` **without** `type: conditional`:

```yaml
edges:
  # Fan-out: all three run concurrently after generate completes
  - from: generate
    to: [analyze, summarize, translate]

  # Fan-in: all three must complete before final runs
  - from: analyze
    to: final
  - from: summarize
    to: final
  - from: translate
    to: final
  - from: final
    to: END
```

Fan-out also works from START:

```yaml
edges:
  - from: START
    to: [branch_a, branch_b]
```

> **Note:** `to: [list]` with `type: conditional` is *conditional routing* (picks ONE target).
> `to: [list]` without `type: conditional` is *parallel fan-out* (runs ALL targets).

### Expression-Based Conditions

Route based on state values:

```yaml
edges:
  - from: critique
    to: refine
    condition: critique.score < 0.8    # Go to refine if low score

  - from: critique
    to: END
    condition: critique.score >= 0.8   # End if high score
```

**Supported operators:** `<`, `<=`, `>`, `>=`, `==`, `!=`

See [Expression Language Reference](expressions.md) for full condition syntax, compound expressions, and gotchas.

---

## Security Considerations

### Expression Evaluation Safety

Condition expressions are evaluated **without using `eval()`**. The expression parser only supports:

**Safe operations:**
- Field path resolution: `critique.score`, `result.status`
- Comparison operators: `<`, `<=`, `>`, `>=`, `==`, `!=`
- Compound expressions: `a > 1 and b < 2`, `x == "done" or y == "skip"`
- Literal values: integers, floats, booleans, quoted strings

**Not supported (by design):**
- Arbitrary Python code execution
- Function calls
- Import statements
- Assignment expressions

Example of validated expression parsing:

```python
# Safe - parsed with regex, not eval()
evaluate_condition("critique.score < 0.8", state)  # ✓
evaluate_condition("a > 1 and b == 'done'", state)  # ✓

# Not supported - will fail validation
"__import__('os').system('cmd')"  # ✗ Rejected
```

### Shell Tool Security

Shell commands use `shlex.quote()` for parameter sanitization. See the main README Security section for details.

---

## Tools Definition

Define tools for agent nodes in the `tools` section.

### Shell Tool

Execute shell commands:

```yaml
tools:
  recent_commits:
    type: shell                       # Optional, defaults to shell
    command: git log --oneline -n {count}
    description: "List recent commits"
    parse: text                       # Output format: text | json
```

**Parameterized commands:**
- Use `{param_name}` placeholders in commands
- Agent provides parameter values at runtime

### Python Tool

Execute Python functions directly:

```yaml
tools:
  my_python_tool:
    type: python
    path: tools.py                  # GRAPH-RELATIVE file — use for graph-local tools
    function: my_function

  generate_images:
    type: python
    module: examples.storyboard.nodes.image_node   # dotted IMPORT — needs importable package
    function: generate_images_node
    description: "Generate images for each story panel"
```

**Python tool properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | `string` | Yes | Must be `"python"` |
| `path` | `string` | One of `path`/`module` | Graph-relative Python file (e.g. `tools.py`) |
| `module` | `string` | One of `path`/`module` | Full dotted Python module path |
| `function` | `string` | Yes | Function name in the module |
| `description` | `string` | No | Human-readable description |

**`path:` vs `module:`:** graphs with a sibling `tools.py` (chaplain
graphs, standalone graph dirs) must use `path: tools.py`; `module:`
requires the module on `sys.path` and fails from graph directories as
`Cannot import module 'tools': No module named 'tools'` (strict mode
names the tool, not the fix). Field incident: FR-744 enforce,
2026-07-17 — the philosopher precedent (`path:`) is the working form.

**Function signature:**
The Python function must accept `state: dict[str, Any]` and return a `dict` with state updates:

```python
def generate_images_node(state: dict[str, Any]) -> dict:
    """Process state and return updates."""
    story = state.get("story")
    # ... do work ...
    return {
        "images": image_paths,
        "current_step": "generate_images",
    }
```

### Example Tools

```yaml
tools:
  commit_details:
    command: git show --stat {commit_hash}
    description: "Show details of a specific commit by hash"
    parse: text

  line_count:
    command: wc -l {file} | awk '{print $1}'
    description: "Count lines in a file"
    parse: text
```

### Tool Manifests (FR-768)

Declare a reusable tool once in a manifest file and reference it from any
graph. The manifest translates into the equivalent inline declaration at
graph load — the existing shell/python/graph runtimes execute it; there is
no separate manifest runtime.

```yaml
# In the graph — the entry may contain ONLY the manifest key
tools:
  reload_canon:
    manifest: nodes/reload_canon.tool.yaml   # resolved relative to the graph
```

```yaml
# nodes/reload_canon.tool.yaml
name: reload_canon        # must match the tool key in the graph
description: Reload canon pages from disk into state.
runtime:
  type: python
  path: reload_canon.py   # resolved relative to the MANIFEST file
  function: reload_canon
```

**Manifest schema:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Must equal the graph-local tool key; mismatch fails load |
| `description` | Yes | Tool description surfaced to agent LLMs |
| `runtime.type` | Yes | `shell`, `python`, or `graph` |

Per-runtime fields:

- `shell` — required `command`; optional `parse` (`text`/`json`/`none`,
  default `text`) and `timeout` (default 30).
- `python` — required `function` plus exactly one of `path` (resolved
  relative to the manifest file) or `module`; both or neither fails load.
- `graph` — required `path` (resolved relative to the manifest file);
  optional `input_mapping` and `output_key` with identical semantics to
  inline `type: graph` tools.

**Path semantics:** the `manifest:` value resolves relative to the
referencing graph; paths *inside* the manifest resolve relative to the
manifest file, so a manifest and its implementation travel together.

**Failure mode:** manifests are validated through typed models at graph
load. A missing manifest file, invalid YAML, unknown `runtime.type`,
unknown or conflicting fields, extra keys next to `manifest:` in the graph
entry, or a `name` mismatch all raise `ValueError` before any node runs —
never at invocation.

**Committed example:** `examples/demos/shared-vision-tool/graph.yaml`
consumes `examples/shared/describe_image.tool.yaml` (FR-770).

**Feeder pattern** — a manifest tool's output can drive map fan-out (FR-773):

```yaml
tools:
  split_document:
    manifest: ../../shared/split_document.tool.yaml
nodes:
  split:
    type: tool_call
    tool: split_document
    args: {path: "{state.pdf}", mode: page}
    state_key: split_result
  summarize_pages:
    type: map
    over: "{state.split_result.result.chunks}"
    as: chunk
```

Committed consumer: `examples/demos/book-summary/graph.yaml`.

### Tool Slots — Invocation-Time Binding (FR-892)

A graph may declare a tool as a **slot**: the declaration names the
contract, and the caller supplies the implementation as an FR-768 tool
manifest at invocation. This is how one pipeline graph serves many
corpora without re-authoring.

```yaml
# In the graph — the slot declares the contract, not the implementation
tools:
  discover:
    slot: true
    contract:
      runtimes: [python]     # optional allowlist: shell | python | graph
      args: [source]         # required inputs the implementation must accept
  extract:
    slot: true
    contract:
      args: [item]
```

```bash
# At invocation — bind each slot to a manifest (repeatable)
yamlgraph graph run examples/demos/corpus_census/graph.yaml \
  --tool discover=adapters/pdf-discover.tool.yaml \
  --tool extract=adapters/pdf-extract.tool.yaml \
  --var source=./my-library --var rubric="..." --var output_path=out/ledger.md
```

**Slot binding semantics:**

| Rule | Behavior |
|------|----------|
| Binding path resolution | Relative to the **caller's CWD** (the binding is the caller's input, not the graph author's) |
| Runtime types | All FR-768 runtimes allowed unless `contract.runtimes` narrows |
| Translation | Reuses FR-768 manifest translation exactly; no new execution engine; the manifest `name` need not match the slot name |
| Contract `args` (shell) | Each arg must appear as a `{placeholder}` in the manifest command |
| Contract `args` (python/graph) | Duck-typed at invocation; the runtime allowlist is the mechanical check |

**Failure modes (all typed `ToolSlotBindingError`, raised before any node
or LLM executes):** missing binding for a declared slot; `--tool` binding
for an undeclared slot; duplicate `--tool` for one slot; missing or
invalid manifest file; manifest runtime outside `contract.runtimes`;
contract args absent from a shell command.

**Committed consumer:** `examples/demos/corpus_census/` — the shared
discover–extract–map–reduce census pipeline; its `proofs/` directory
shows two corpora (PDF library, git history) served by manifest pairs
with zero graph changes. Map sub-nodes invoke slot tools through python
nodes; shell-runtime slots are only invocable from top-level `type: tool`
nodes (current map execution surface).

### Web Search Tool

Search the web using DuckDuckGo (no API key required):

```yaml
tools:
  search_web:
    type: websearch
    provider: duckduckgo
    max_results: 5
    description: "Search the web for current information"
```

**Web search tool properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `type` | `string` | required | Must be `"websearch"` |
| `provider` | `string` | `"duckduckgo"` | Search provider |
| `max_results` | `int` | `5` | Max results per query |
| `description` | `string` | - | Human-readable description |

**Installation:**
```bash
pip install yamlgraph[websearch]
```

### Tool Type Summary

| Type | Description | Example |
|------|-------------|---------|
| `shell` | Execute shell commands | `git log`, `ruff check` |
| `python` | Call Python functions | Custom processing |
| `websearch` | Web search via DuckDuckGo | Research agents |

---

## Loop Limits

Prevent infinite loops in self-correction patterns:

```yaml
loop_limits:
  critique: 3     # Node 'critique' runs at most 3 times
```

**Note:** Use with `skip_if_exists: false` on loop nodes.

## Loop Exits (FR-172)

By default, when a node hits its `loop_limit`, the expression router terminates the graph (`END`). Use `loop_exits` to route to a specific post-loop node instead:

```yaml
loop_limits:
  critique: 3

loop_exits:
  critique: distill_reflection  # When critique hits limit, go here instead of END
```

**Rules:**
- Each key in `loop_exits` must also appear in `loop_limits`
- Each value must be a valid node name (or `END`)
- Only applies to expression-based conditional edges (not `type: conditional` router edges)

---

## Observability (FR-723)

Opt in to the **route decision log** — one JSON line per routing decision
(simple router, expression match, loop-limit exit, map fan-out):

```yaml
observability:
  route_log: true   # enable at compile time (process-wide)
```

Or per run, without touching the YAML:

```bash
YAMLGRAPH_ROUTE_LOG=1 yamlgraph graph run graph.yaml ...            # logger only
YAMLGRAPH_ROUTE_LOG=route.jsonl yamlgraph graph run graph.yaml ...  # + JSONL file
YAMLGRAPH_ROUTE_LOG=outputs/routes/ yamlgraph graph run graph.yaml ...  # directory target -> outputs/routes/route.jsonl
```

Path contract:

- `1` emits on the `yamlgraph.route` logger only.
- Any other non-boolean value is treated as a path target.
- Existing directory path values write to `<dir>/route.jsonl`.
- Values ending with a trailing path separator are treated as directory intent, the directory is created, and output is written to `<dir>/route.jsonl`.
- File-path mode auto-creates parent directories (`mkdir -p` semantics).
- Relative paths resolve against the process working directory (CWD at run time).
- Invalid targets do not raise; one warning is emitted and route logging continues on the logger-only path.

Line grammar (frozen):

```json
{"event":"route","node":"critique","value":"critique.score < 0.8","target":"refine","thread_id":"t-1"}
```

- `value` is the matched condition, route key, `loop_exit`, `no_match`, or `default` — framework metadata, never state content.
- Map fan-out decisions add `"fan_out": <count>` and carry the map-node name as target (never `Send` payloads).
- `thread_id` is the invoking thread id, or `null` when the run has none — never fabricated.
- The `yamlgraph.route` logger namespace is **public API**: attach handlers/filters there downstream.
- Zero overhead when off; emission never raises.

Render routes with `yamlgraph graph export --mermaid --overlay route.jsonl` — see [CLI Reference](cli.md).

### Route evidence record

An opted-in graph run writes a JSONL evidence record, not bare route lines:

1. `event: run` binds the record to a UUIDv7 `run_id`, graph path, YAMLGraph
  version, optional judgement reference, and `artifact_hash`.
2. Each `event: route` keeps the original `event`, `node`, `value`, `target`,
  and `thread_id` contract and adds an ISO-8601 UTC `ts`.
3. `event: run_end` reports the best-effort `dropped_events` count.

`artifact_hash` is SHA-256 over canonical JSON containing the graph YAML and
every resolved prompt YAML path plus each file's raw-byte SHA-256. Missing
referenced prompts fail hash generation; an incomplete identity is never
emitted. `graph export --overlay` requires exactly one leading run header and
refuses missing, malformed, duplicate, or graph-mismatched headers.

The default posture remains non-strict: route evidence delivery failures are
counted but do not fail graph execution. FR-808's regulated profile is the
separate policy layer that may make evidence loss fatal.

### Regulated evidence profile

```yaml
observability:
  profile: regulated
  route_log_sink: logs/routes
  judgement_ref: FR-123
  strict_evidence: true  # optional; default false
```

The profile implies route logging and requires a filesystem directory sink plus
a judgement reference. Each run preflights the directory and writes exactly one
`<run_id>.route.jsonl`. Missing fields, `route_log: false`, a file-valued or
non-writable sink, or profile fields outside `profile: regulated` fail before
graph execution and before a run header is emitted.

`YAMLGRAPH_ROUTE_LOG=0` alone is ignored under the profile and emits a warning.
Together with `YAMLGRAPH_ROUTE_LOG_OVERRIDE=1`, it records an exception and
disables emission only when `strict_evidence` is false. Strict runs reject every
disable request at startup. If an enabled strict run loses evidence, it first
attempts `run_end`, then raises `EvidenceLossError` carrying a structured
`PipelineError` record with the dropped count and sink. Non-strict runs preserve
FR-807 behavior: complete normally and expose the counted loss.

This profile implements an engineering evidence posture. It does not establish
AI Act compliance, conformity, retention sufficiency, or legal adequacy.

---

## Exports

Configure automatic result export:

```yaml
exports:
  response:
    format: markdown
    filename: review.md

  _tool_results:
    format: json
    filename: tool_outputs.json
```

**Supported formats:** `markdown`, `json`, `text`

---

## Complete Examples

### Linear Pipeline

```yaml
version: "1.0"
name: yamlgraph

nodes:
  generate:
    type: llm
    prompt: generate
    variables:
      topic: "{state.topic}"
    state_key: generated

  analyze:
    type: llm
    prompt: analyze
    variables:
      content: "{state.generated.content}"
    state_key: analysis
    requires: [generated]

edges:
  - from: START
    to: generate
  - from: generate
    to: analyze
  - from: analyze
    to: END
```

### Self-Correction Loop

```yaml
version: "1.0"
name: reflexion-demo

nodes:
  draft:
    type: llm
    prompt: reflexion-demo/draft
    state_key: current_draft

  critique:
    type: llm
    prompt: reflexion-demo/critique
    variables:
      content: "{state.current_draft.content}"
      iteration: "{state._loop_counts.critique}"
    state_key: critique
    skip_if_exists: false           # Re-run each iteration

  refine:
    type: llm
    prompt: reflexion-demo/refine
    variables:
      content: "{state.current_draft.content}"
      feedback: "{state.critique.feedback}"
    state_key: current_draft
    skip_if_exists: false

edges:
  - from: START
    to: draft
  - from: draft
    to: critique
  - from: critique
    to: refine
    condition: critique.score < 0.8
  - from: critique
    to: END
    condition: critique.score >= 0.8
  - from: refine
    to: critique

loop_limits:
  critique: 3
```

### Router Pattern

```yaml
version: "1.0"
name: router-demo

nodes:
  classify:
    type: router
    prompt: router-demo/classify_tone
    route_field: tone
    routes:
      positive: respond_positive
      negative: respond_negative
      neutral: respond_neutral
    default_route: respond_neutral
    variables:
      message: "{state.message}"

  respond_positive:
    type: llm
    prompt: router-demo/respond_positive
    variables:
      message: "{state.message}"
    state_key: response

  # ... other response nodes

edges:
  - from: START
    to: classify
  - from: classify
    to: [respond_positive, respond_negative, respond_neutral]
    type: conditional
  - from: respond_positive
    to: END
```
