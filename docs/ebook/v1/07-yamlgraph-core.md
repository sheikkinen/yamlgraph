# Chapter 07: YAMLGraph Core

> *"The cheapest code is unwritten code."*

YAMLGraph is a YAML-first framework for building LLM pipelines using LangGraph. The key insight: 60–80% of AI workflows can be defined entirely in YAML — graphs, prompts, and schemas — without writing Python code. Built on LangGraph with multi-provider LLM support across Anthropic, Google, Mistral, OpenAI, Replicate, xAI, and local models via LM Studio.

This chapter is the technical core of the book. We will trace every step from a YAML file on disk to a running LangGraph pipeline, catalog every node type with real examples you can execute, and show how to extend the framework with new providers, tools, and deployment patterns.

The chapter is organized in three parts:

- **Part I: How It Works** — Architecture, compilation pipeline, state management
- **Part II: How to Use It** — Node types, expressions, patterns, CLI
- **Part III: How to Extend It** — Providers, tools, checkpointers, streaming, deployment

---

# Part I: How It Works

## The Three-Layer Architecture

YAMLGraph enforces a strict separation of concerns across three layers. This diagram, from the project's `CLAUDE.md`, is the foundational mental model:

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

Each layer has a clear responsibility:

**Presentation Layer** — Python CLI scripts, FastAPI routes, HTMX frontends. This layer handles argument parsing, terminal colors, interactive prompts, and HTTP routing. It is a thin wrapper around graph execution: call `app.invoke()`, format the output, and display it.

**Logic Layer** — YAML graphs and prompts. All LLM calls, routing decisions, state transitions, interrupt nodes, map nodes, and checkpointing live here. This is where the intelligence resides, and it is entirely declarative.

**Side Effects Layer** — Python tools for external API calls, file I/O, shell commands, image generation — anything that cannot be expressed in YAML. These are isolated, testable functions that the graph invokes through its `tools:` section.

Why this pattern? Graphs defined in YAML are testable, traceable via LangSmith, and resumable via checkpointers. Python handles UX concerns where YAML cannot (colors, stdin, WebSocket). Tools isolate non-deterministic operations. Each layer evolves independently.

The same pattern extends to web APIs:

```
┌─────────────────────────────────────┐
│  FastAPI / Flask                    │  ← HTTP: routes, auth, validation
├─────────────────────────────────────┤
│  YAML Graphs                        │  ← Logic: stateless or with threads
├─────────────────────────────────────┤
│  Python Tools + Storage             │  ← Persistence: DB, S3, queues
└─────────────────────────────────────┘
```

When building new features, the rule is simple:
- Put LLM orchestration in YAML graphs
- Put reusable prompts in YAML templates
- Put external integrations in Python tools

---

## The Compilation Pipeline

The journey from YAML on disk to a running LangGraph pipeline follows a deterministic compilation pipeline. Here is the flow, quoted from `CLAUDE.md`:

```
YAML file → load_graph_config() → GraphConfig (Pydantic)
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            build_state_class()  parse_tools()   compile_graph()
                    │                 │                 │
                    ▼                 ▼                 ▼
            Dynamic TypedDict   Tool Registry    StateGraph (LangGraph)
                                                       │
                                              graph.compile()
                                                       │
                                                       ▼
                                              CompiledGraph
```

Let's trace each step.

### Step 1: Load and Validate

`load_graph_config()` in `graph_loader.py` reads the YAML file, validates it against the GraphConfig Pydantic model, and resolves relative paths for prompts and data files. The result is a fully validated `GraphConfig` object — if your YAML has a typo, an invalid node type, or a missing required field, this is where the error is caught.

### Step 2: Build State Class

`build_state_class()` in `models/state_builder.py` scans all `state_key` fields across every node in the graph and generates a Python `TypedDict` at runtime. No manual state classes needed:

```yaml
nodes:
  generate:
    state_key: generated  # ← Creates state.generated field automatically
  analyze:
    state_key: analysis   # ← Creates state.analysis field automatically
```

The state builder also handles special cases: map nodes get `Annotated[list, operator.add]` reducers for their `collect` keys. Agent nodes get `Annotated[list[Any], add_messages]` for message accumulation.

### Step 3: Parse Tools

`parse_tools()` reads the `tools:` section and creates a registry of shell tools, Python tools, and web search tools. Shell tools get their command templates stored for later sanitized execution. Python tools get their module/function references resolved. The registry is passed to agent and tool nodes during compilation.

### Step 4: Compile Graph

`compile_graph()` orchestrates the final assembly. For each node in the graph, the `node_factory/` subpackage creates an appropriate node function based on the node's `type`. The key files in the factory:

| File | Purpose |
|------|---------|
| `llm_nodes.py` | LLM and router node functions |
| `control_nodes.py` | Interrupt, passthrough nodes |
| `subgraph_nodes.py` | Nested graph composition |
| `tool_nodes.py` | Tool call nodes |
| `streaming.py` | Token streaming support |
| `base.py` | Shared utilities |

Edges are wired — linear edges become direct connections, conditional edges become router functions, and map nodes expand into dispatch + sub-node + collection patterns using LangGraph's `Send()` API.

The result is a LangGraph `StateGraph` that is then compiled into a `CompiledGraph` — the executable pipeline.

---

## Graph YAML Anatomy

Every graph YAML file follows this structure (from `reference/graph-yaml.md`):

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

exports:                           # Optional: Export configuration
  state_key:
    format: markdown
    filename: output.md
```

Let's see this in practice. Here is the complete `examples/demos/hello/graph.yaml` — the "Hello World" of YAMLGraph:

```yaml
# Hello World - Minimal YAMLGraph Example
# Demonstrates basic LLM call with variable substitution

version: "1.0"
name: hello-world
description: Simple greeting generator demonstrating basic LLM usage

prompts_relative: true
prompts_dir: prompts

defaults:
  temperature: 0.7

state:
  name: str
  style: str

nodes:
  greet:
    type: llm
    prompt: greet
    variables:
      name: "{state.name}"
      style: "{state.style}"
    state_key: greeting

edges:
  - from: START
    to: greet
  - from: greet
    to: END
```

This graph has one node (`greet`) of type `llm`. It reads two variables from state (`name` and `style`), passes them to the `greet` prompt template, and stores the LLM's response in `state.greeting`. The edges wire it up: `START → greet → END`.

You can run it:

```bash
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="holy see of code" --full
```

The `--full` flag shows the complete output without truncation.

---

## Prompt YAML Anatomy

Prompts are YAML files that define the system message, user message, and optionally a structured output schema. Here is the companion prompt for the hello demo — `examples/demos/hello/prompts/greet.yaml`:

```yaml
system: |
  You are a friendly assistant that generates personalized greetings.
  Adjust your greeting style based on the requested tone.

user: |
  Generate a greeting for "{name}" in a {style} style.

  The greeting should:

  - Match the requested tone ({style})
  - Be culturally appropriate
  - Be memorable and warm
```

The `system:` section sets the LLM's persona. The `user:` section contains the actual instruction with `{variable}` placeholders that are filled at runtime from the node's `variables:` mapping.

### Template Syntax

YAMLGraph supports two template syntaxes:

**Simple substitution** — `{variable}` placeholders for basic value insertion. This is the default when the prompt contains no Jinja2 markers.

**Jinja2** — Auto-detected when the prompt contains `{{` or `{%`. Enables loops, conditionals, and filters:

```yaml
template: |
  {% for item in items %}
  ### {{ loop.index }}. {{ item.title }}
  **Content**: {{ item.content[:200] }}...
  {% endfor %}
```

### Inline Schemas

Prompts can define structured output schemas directly, making them self-contained:

```yaml
schema:
  name: ToneClassification
  fields:
    tone:
      type: str
      description: "Detected tone: positive, negative, or neutral"
    confidence:
      type: float
      description: "Confidence score 0-1"
      constraints:
        ge: 0.0
        le: 1.0
    reasoning:
      type: str
      description: "Explanation for the classification"
```

Supported types include `str`, `int`, `float`, `bool`, `list[str]`, `list[int]`, `dict[str, str]`, `dict[str, Any]`, and `Any`. Field constraints (`ge`, `le`, `gt`, `lt`, `min_length`, `max_length`, `pattern`) map directly to Pydantic validators.

An alternative `output_schema:` format uses standard JSON Schema syntax, which some teams prefer:

```yaml
output_schema:
  type: object
  properties:
    sentiment:
      type: string
      enum: [positive, negative, neutral]
    confidence:
      type: number
  required: [sentiment, confidence]
```

Both formats produce identical Pydantic models at runtime.

---

## Dynamic State Management

One of YAMLGraph's most distinctive features is automatic state generation. Traditional LangGraph requires manual `TypedDict` definitions:

```python
class MyState(TypedDict):
    topic: str
    generated: str  # Must manually add for each node
```

YAMLGraph eliminates this. The state builder scans all `state_key` fields and generates the `TypedDict` at runtime. When you write:

```yaml
nodes:
  generate:
    state_key: generated
  analyze:
    state_key: analysis
```

The framework automatically creates a state class with `generated` and `analysis` fields. Map nodes get list reducers for their `collect` keys, ensuring parallel results are properly aggregated.

The tradeoffs, as documented in `ARCHITECTURE.md`:

- ✅ Less boilerplate, faster iteration
- ✅ State always matches graph definition
- ❌ No static type checking in IDE
- ❌ Runtime errors instead of compile-time

---

## Node Execution Flow

Every node, regardless of type, follows the same execution pattern (implemented in `node_factory/`):

1. **Pre-checks** — `check_requirements()` verifies that all `requires` state keys exist and have truthy values
2. **Loop protection** — `check_loop_limit()` consults the `loop_limits:` config to prevent infinite cycles
3. **Resume support** — `skip_if_exists` checks whether the state key already has a truthy value (by default, `[]`, `""`, and `None` do *not* trigger a skip)
4. **Execution** — `execute_prompt()` for LLM nodes, tool dispatch for tool nodes, or custom logic for python/passthrough nodes
5. **Return** — A dict with state updates. Never mutate state directly.

This last point is a critical rule:

```python
# ❌ WRONG - Direct mutation
def node_fn(state):
    state["key"] = value
    return state

# ✅ CORRECT - Return update dict
def node_fn(state):
    return {"key": value}
```

LangGraph merges the returned dict into state automatically.

---

# Part II: How to Use It

## Node Type Catalog

YAMLGraph provides eleven node types, each serving a distinct purpose:

| Type | Purpose |
|------|---------|
| `llm` | Single LLM call with prompt |
| `router` | Classify → route to different nodes |
| `agent` | ReAct agent with tools |
| `tool` | Execute a registered tool |
| `tool_call` | Dynamic tool from state |
| `map` | Parallel execution over list |
| `python` | Custom Python function |
| `passthrough` | State transformation without LLM |
| `subgraph` | Nested graph execution |
| `interrupt` | Human-in-the-loop pause/resume |
| `copilot` | Delegate task to Copilot CLI |

Let's explore each with real examples from the `examples/demos/` directory.

---

### LLM Node — `type: llm`

The workhorse of YAMLGraph. Executes a single LLM call with a YAML prompt template and optional structured output.

**Real example** — `examples/demos/hello/graph.yaml`:

```yaml
nodes:
  greet:
    type: llm
    prompt: greet
    variables:
      name: "{state.name}"
      style: "{state.style}"
    state_key: greeting
```

Common properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `prompt` | `string` | — | Prompt file path (without `.yaml`) |
| `variables` | `object` | `{}` | Template variable mappings |
| `state_key` | `string` | node name | Where to store the result |
| `temperature` | `float` | from defaults | LLM temperature |
| `provider` | `string` | from defaults | LLM provider |
| `stream` | `bool` | `false` | Enable token-by-token streaming |
| `parse_json` | `bool` | `false` | Extract JSON from markdown-wrapped responses |
| `skip_if_exists` | `bool` | `true` | Skip if state key has truthy value |
| `thinking_budget` | `int` | from defaults | Anthropic extended thinking tokens |

**Extended thinking** — The thinking demo (`examples/demos/thinking/graph.yaml`) shows how to allocate reasoning tokens:

```yaml
version: "1.0"
name: thinking-demo
description: "Demonstrate extended thinking with configurable reasoning depth (FR-071)"

prompts_relative: true
prompts_dir: prompts

state:
  question: str

defaults:
  provider: anthropic
  # Extended thinking requires claude-3-5-sonnet-20241022 or newer
  thinking_budget: 8000               # Allocate 8000 tokens for internal reasoning
  temperature: 1                      # Required for extended thinking

nodes:
  deep_analysis:
    prompt: analyze
    state_key: analysis
    variables:
      question: "{state.question}"
    # Inherits thinking_budget: 8000 from defaults

  quick_response:
    prompt: respond
    state_key: response
    thinking_budget: 0  # Override: disable thinking for this node
    variables:
      analysis: "{state.analysis}"
      question: "{state.question}"

edges:
  - from: START
    to: deep_analysis
  - from: deep_analysis
    to: quick_response
  - from: quick_response
    to: END
```

Notice how `thinking_budget` can be set in `defaults:` and overridden per node. Setting it to `0` disables extended thinking for that node. When enabled, the framework automatically forces `temperature=1` as required by Anthropic.

---

### Router Node — `type: router`

Routes execution to different nodes based on LLM classification. The LLM classifies the input, and the `routes:` mapping determines which node runs next.

**Real example** — `examples/demos/router/graph.yaml`:

```yaml
# Tone Router Demo - YAML Graph Definition
# Routes responses based on detected message tone

version: "1.0"
name: tone-router-demo
description: Route responses based on detected message tone
prompts_relative: true
prompts_dir: prompts

defaults:
  provider: xai
  temperature: 0.7

nodes:
  classify:
    type: router
    prompt: classify_tone
    routes:
      positive: respond_positive
      negative: respond_negative
      neutral: respond_neutral
    default_route: respond_neutral
    variables:
      message: "{state.message}"
    state_key: classification

  respond_positive:
    type: llm
    prompt: respond_positive
    variables:
      message: "{state.message}"
    state_key: response

  respond_negative:
    type: llm
    prompt: respond_negative
    variables:
      message: "{state.message}"
    state_key: response

  respond_neutral:
    type: llm
    prompt: respond_neutral
    variables:
      message: "{state.message}"
    state_key: response

edges:
  - from: START
    to: classify

  - from: classify
    to: [respond_positive, respond_negative, respond_neutral]
    type: conditional

  - from: respond_positive
    to: END
  - from: respond_negative
    to: END
  - from: respond_neutral
    to: END
```

The router's prompt returns a structured classification. Here is `examples/demos/router/prompts/classify_tone.yaml`:

```yaml
# Tone Classification Prompt
# Classifies user message tone for routing

# Inline schema - makes this prompt self-contained
schema:
  name: ToneClassification
  fields:
    tone:
      type: str
      description: "Detected tone: positive, negative, or neutral"
    confidence:
      type: float
      description: "Confidence score 0-1"
      constraints:
        ge: 0.0
        le: 1.0
    reasoning:
      type: str
      description: "Explanation for the classification"

system: |
  You are a tone classifier. Analyze the user's message and classify its emotional tone.

  Respond with exactly one of these tones:
  - positive: Happy, grateful, excited, satisfied
  - negative: Frustrated, angry, disappointed, upset
  - neutral: Informational, questioning, matter-of-fact

user: |
  Classify the tone of this message:

  "{message}"

  Provide your classification with reasoning.
```

The LLM returns `{"tone": "positive", ...}` and the framework matches `tone` against the `routes:` keys to determine the next node. The `default_route` handles unrecognized classifications.

Key details:
- `routes:` maps classification values → node names
- All target nodes must appear in the conditional edge `to: [...]`
- The edge must have `type: conditional`

---

### Map Node — `type: map`

Processes each item in a list in parallel using LangGraph's `Send()` API. This is the fan-out/fan-in pattern.

**Real example** — `examples/demos/map/graph.yaml`:

```yaml
# Example graph demonstrating type: map for parallel processing
# Generates a list of ideas then expands each in parallel

name: map-demo
version: "1.0"
description: "Demonstrates parallel fan-out with type: map"
prompts_relative: true
prompts_dir: prompts

defaults:
  provider: mistral

nodes:
  generate:
    prompt: generate_ideas
    state_key: ideas
    variables:
      topic: "{state.topic}"

  expand:
    type: map
    over: "{state.ideas.ideas}"
    as: idea
    node:
      prompt: expand_idea
      state_key: expansion
      variables:
        idea: "{state.idea}"
    collect: expansions

  summarize:
    prompt: summarize_ideas
    state_key: summary
    variables:
      expansions: "{state.expansions}"

edges:
  - from: START
    to: generate
  - from: generate
    to: expand
  - from: expand
    to: summarize
  - from: summarize
    to: END
```

The `generate` node returns a list of ideas. The `expand` map node iterates over each idea, running the sub-node's prompt in parallel. Results are collected into `state.expansions`.

The prompt that generates the list — `examples/demos/map/prompts/generate_ideas.yaml`:

```yaml
schema:
  name: IdeasList
  fields:
    ideas:
      type: list[str]
      description: "List of 3 creative ideas"

system: |
  You are a creative idea generator. Generate exactly 3 simple, interesting ideas.

user: |
  Generate 3 creative ideas about: {topic}

  Return a list with exactly 3 short ideas (one sentence each).
```

Map node properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `over` | `string` | Yes | State expression for the list to iterate |
| `as` | `string` | Yes | Variable name injected into sub-node |
| `node` | `object` | Yes | Sub-node definition (llm, router, or python) |
| `collect` | `string` | Yes | State key where results are collected |
| `flatten_output` | `bool` | No | Merge wrapper contents into items |
| `max_items` | `int` | No | Fan-out cap (overrides `config.max_map_items`) |

How it works internally:
1. **Fan-out**: A dispatch node reads the list and uses `Send()` to dispatch each item
2. **Process**: The sub-node runs independently per item with `{state.<as>}` available
3. **Collect**: Results are aggregated using `Annotated[list, operator.add]` reducer, sorted by `_map_index`

Run it:
```bash
yamlgraph graph run examples/demos/map/graph.yaml --var topic="AI" --async
```

The `--async` flag is recommended for map-heavy graphs — it ensures parallel execution with all providers, including Mistral which runs sequentially in sync mode.

---

### Subgraph Node — `type: subgraph`

Embeds and executes another graph as a node. This enables modular composition — package reusable workflows (summarization, validation, classification) as standalone graphs and invoke them from parent graphs.

**Real example** — `examples/demos/subgraph/graph.yaml`:

```yaml
version: "1.0"
name: subgraph-demo
description: Demo of subgraph composition - parent graph calls a summarizer subgraph
prompts_relative: true
prompts_dir: prompts

defaults:
  provider: mistral
  temperature: 0.5

state:
  raw_text: str
  prepared_text: str
  summary: str
  final_output: str

nodes:
  prepare:
    type: llm
    prompt: prepare
    state_key: prepared_text

  summarize:
    type: subgraph
    mode: invoke
    graph: subgraphs/summarizer.yaml
    input_mapping:
      prepared_text: input_text
    output_mapping:
      summary: output_summary

  format:
    type: llm
    prompt: format
    state_key: final_output

edges:
  - from: START
    to: prepare
  - from: prepare
    to: summarize
  - from: summarize
    to: format
  - from: format
    to: END
```

And the child graph — `examples/demos/subgraph/subgraphs/summarizer.yaml`:

```yaml
version: "1.0"
name: summarizer
description: Reusable text summarization subgraph
prompts_relative: true
prompts_dir: prompts

defaults:
  provider: mistral
  temperature: 0.3

state:
  input_text: str
  output_summary: str

nodes:
  summarize:
    type: llm
    prompt: summarize
    state_key: output_summary

edges:
  - from: START
    to: summarize
  - from: summarize
    to: END
```

The critical concept is **state mapping**. The parent and child graphs have separate state spaces:

- `input_mapping` maps parent → child: `prepared_text` in the parent becomes `input_text` in the child
- `output_mapping` maps child → parent: `output_summary` in the child becomes `summary` in the parent

Subgraphs can be nested (subgraphs within subgraphs) and can be tested independently.

---

### Agent Node — `type: agent`

A ReAct agent with access to tools for multi-step reasoning. The LLM decides which tools to call and with what parameters.

```yaml
tools:
  recent_commits:
    command: git log --oneline -n {count}
    description: "List recent commits"
    parse: text

  commit_details:
    command: git show --stat {commit_hash}
    description: "Show details of a specific commit by hash"
    parse: text

nodes:
  analyze:
    type: agent
    prompt: git_analyst
    tools: [recent_commits, commit_details]
    max_iterations: 8
    state_key: analysis
```

Agent-specific properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `tools` | `list[str]` | `[]` | Tool names from graph's `tools` section |
| `max_iterations` | `int` | `10` | Maximum tool invocations |
| `tool_results_key` | `string` | — | State key for tool execution logs |

---

### Python Node — `type: python`

Execute an arbitrary Python function as a node. The function receives the full state dict and returns a dict of state updates.

```yaml
tools:
  generate_images:
    type: python
    module: examples.storyboard.nodes.image_node
    function: generate_images_node
    description: "Generate images for each story panel"

nodes:
  generate_images:
    type: python
    tool: generate_images
    state_key: images
    requires: [story]
```

The Python function signature:

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

---

### Passthrough Node — `type: passthrough`

Transforms state without external calls. Essential for loop counters, state accumulation, and simple data transformations.

```yaml
nodes:
  increment_turn:
    type: passthrough
    output:
      turn_number: "{state.turn_number + 1}"
      history: "{state.history + [state.current_action]}"
```

Passthrough nodes support arithmetic (`+`, `-`, `*`, `/`), list append, and dict append operations via the expression language. Only binary operations are supported — chained expressions like `{state.a + state.b + state.c}` are not.

---

### Tool Call Node — `type: tool_call`

Executes a tool where the name and arguments are resolved dynamically from state. This enables LLM-driven tool orchestration — the LLM decides which tool to call, and the tool_call node dispatches it.

```yaml
nodes:
  execute_tool:
    type: tool_call
    tool: "{state.selected_tool}"
    args: "{state.tool_arguments}"
    state_key: tool_result
```

Tool call nodes never raise exceptions. Errors are captured in a structured result:

```python
{
    "tool": "search_file",
    "success": True,        # or False
    "result": {...},        # on success
    "error": None           # or error message on failure
}
```

The primary use case is combining map + tool_call: an LLM generates a list of tool calls, then a map node executes them all in parallel.

---

### Interrupt Node — `type: interrupt`

Pauses execution to wait for human input. Requires a checkpointer for state persistence.

```yaml
checkpointer:
  type: memory

nodes:
  ask_name:
    type: interrupt
    message: "What is your name?"
    resume_key: user_name
```

When the graph hits an interrupt node, it saves state to the checkpointer and returns with an `__interrupt__` marker. Resumption passes user input via `Command(resume=value)`.

---

### Copilot Node — `type: copilot`

Delegates complex reasoning tasks to GitHub Copilot CLI, giving it access to the full project context, file system, and MCP tools.

```yaml
nodes:
  plan_feature:
    type: copilot
    prompt: plan
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      model: claude-sonnet-4
    variables:
      topic_file: "{state.topic}"
    state_key: plan_result
    timeout: 300
```

The node returns a `CopilotResult` with `output`, `exit_code`, `model`, and `backend` fields, accessible in subsequent nodes via `{state.plan_result.output}`.

---

## Expression Syntax

YAMLGraph has two expression systems, documented in `reference/expressions.md`.

### Value Expressions

Used in `variables:`, `output:`, and `over:`. Always wrapped in `{state.path}`:

```yaml
variables:
  name: "{state.name}"                     # Simple path
  score: "{state.critique.score}"          # Nested access
  iteration: "{state._loop_counts.node}"   # Loop counter

output:
  counter: "{state.counter + 1}"           # Arithmetic
  history: "{state.history + [state.item]}" # List append
```

Resolution order for each path segment: dict key lookup first, then object attribute (handles Pydantic models). Missing paths return `None`, not errors.

### Condition Expressions

Used in edge `condition:` fields. Different syntax — no braces, no `state.` prefix:

```yaml
edges:
  - from: critique
    to: refine
    condition: critique.score < 0.8

  - from: critique
    to: END
    condition: critique.score >= 0.8
```

Supported operators: `<`, `<=`, `>`, `>=`, `==`, `!=`

Compound conditions with `and`/`or`:

```yaml
condition: "has_gaps == true and probe_count < 10"
condition: "status == 'done' or retry_count >= 3"
```

Conditions are evaluated **without `eval()`** — parsed with regex only, preventing code injection.

---

## Common Patterns

### Linear Pipeline

Sequential processing: `START → step1 → step2 → step3 → END`. Each step stores its result in a state key, and the next step reads it.

### Router + Merge

Classify input, route to specialized handlers, all converge to `END`:

```yaml
edges:
  - from: START
    to: classify
  - from: classify
    to: [handle_a, handle_b, handle_c]
    type: conditional
  - from: handle_a
    to: END
  - from: handle_b
    to: END
  - from: handle_c
    to: END
```

### Self-Correction Loop (Reflexion)

Draft → critique → refine → critique again, until quality threshold is met:

```yaml
edges:
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
  critique: 5
```

Critical: nodes in loops must set `skip_if_exists: false` to re-run each iteration.

### Fan-Out / Fan-In (Map)

Generate a list, process each item in parallel, collect and summarize:

```yaml
edges:
  - from: START
    to: generate
  - from: generate
    to: process_items    # type: map
  - from: process_items
    to: summarize
  - from: summarize
    to: END
```

---

## CLI Commands

The `yamlgraph` CLI provides everything needed to develop, validate, and run graphs.

### Run a Graph

```bash
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="casual" --full
```

| Flag | Short | Description |
|------|-------|-------------|
| `--var VAR` | `-v` | Set state variable (key=value), repeatable |
| `--thread THREAD` | `-t` | Thread ID for state persistence |
| `--export` | `-e` | Export results to files |
| `--full` | `-f` | Show full output without truncation |
| `--async` | `-a` | Use async execution for parallel map nodes |
| `--share-trace` | | Share LangSmith trace publicly |

### Lint a Graph

```bash
yamlgraph graph lint examples/demos/hello/graph.yaml
```

Checks for missing state keys, unused tools, disconnected nodes, and other common issues.

### Validate a Graph

```bash
yamlgraph graph validate examples/demos/*/graph.yaml
```

Validates graph YAML against the schema — catches structural errors without running.

### Inspect a Graph

```bash
yamlgraph graph info examples/demos/router/graph.yaml
```

Shows graph structure, nodes, edges, and metadata.

### List Available Graphs

```bash
yamlgraph graph list
```

---

# Part III: How to Extend It

## Adding LLM Providers

The LLM factory (`yamlgraph/utils/llm_factory.py`) provides a unified `create_llm()` function that abstracts away provider differences. The factory supports seven providers:

```python
ProviderType = Literal[
    "anthropic", "google", "lmstudio", "mistral", "openai", "replicate", "xai"
]
```

Provider selection follows a priority chain:

1. Function parameter (`provider="anthropic"`)
2. YAML metadata (`defaults: provider: mistral`)
3. `PROVIDER` environment variable
4. Default: `anthropic`

Model selection follows a similar chain:

1. Function parameter (`model="gpt-4o"`)
2. `{PROVIDER}_MODEL` environment variable
3. Provider default from `config.py`

The factory implements thread-safe caching — LLM instances are cached by `(provider, model, temperature, max_tokens, thinking_budget)` tuple, so the same configuration is reused across nodes.

```python
from yamlgraph.utils.llm_factory import create_llm

# Use default Anthropic
llm = create_llm(temperature=0.7)

# Override provider
llm = create_llm(provider="mistral", temperature=0.8)

# Custom model
llm = create_llm(provider="openai", model="gpt-4o-mini")

# Enable extended thinking (Anthropic only)
llm = create_llm(provider="anthropic", thinking_budget=8000)
```

Never import provider SDKs directly:

```python
# ❌ WRONG
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3")

# ✅ CORRECT
from yamlgraph.utils.llm_factory import create_llm
llm = create_llm(provider="anthropic")
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic authentication |
| `GOOGLE_API_KEY` | Google Gemini authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `PROVIDER` | Default LLM provider |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith observability (true/false) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |

---

## Adding Custom Tools

Tools are defined in the graph's `tools:` section and come in three types.

### Shell Tools

Execute shell commands with parameterized substitution:

```yaml
tools:
  recent_commits:
    type: shell
    command: git log --oneline -n {count}
    description: "List recent commits"
    parse: text
```

**Security model** — All user-provided variables are sanitized with `shlex.quote()` to prevent shell injection. The command template itself is trusted (from YAML config), but all runtime variables are escaped:

```python
# From yamlgraph/tools/shell.py:
# command: "git log --author={author}"
# variables: {"author": "$(rm -rf /)"}
# → Executed: git log --author='$(rm -rf /)'  (safely quoted)
```

There is no `eval()` anywhere in the codebase. Condition expressions are parsed with regex only.

### Python Tools

Call Python functions directly:

```yaml
tools:
  generate_images:
    type: python
    module: examples.storyboard.nodes.image_node
    function: generate_images_node
    description: "Generate images for each story panel"
```

The function must accept `state: dict[str, Any]` and return a `dict` with state updates.

### Web Search Tools

Search the web via DuckDuckGo (no API key required):

```yaml
tools:
  search_web:
    type: websearch
    provider: duckduckgo
    max_results: 5
    description: "Search the web for current information"
```

Requires `pip install yamlgraph[websearch]`.

---

## Checkpointers

Checkpointers enable state persistence across graph executions. They are required for interrupt nodes and enable session resumption.

```yaml
checkpointer:
  type: memory    # In-memory (dev/testing)
```

| Type | Persistence | Best For |
|------|-------------|----------|
| `memory` | Lost on restart | Development, testing |
| `sqlite` | File-based | Single-server deployments |
| `redis` | Distributed | Multi-server, production |
| `redis-simple` | Distributed (plain Redis) | Upstash, Fly.io |

```yaml
# SQLite
checkpointer:
  type: sqlite
  path: "./sessions.db"

# Redis
checkpointer:
  type: redis
  url: "${REDIS_URL}"
  ttl: 60

# Redis Simple (no Redis Stack required)
checkpointer:
  type: redis-simple
  url: "${REDIS_URL}"
  ttl: 60
  prefix: "yamlgraph"
```

Session management via CLI:

```bash
# Start a new session
yamlgraph graph run graph.yaml --thread session-123 --var input=start

# Resume the same session
yamlgraph graph run graph.yaml --thread session-123

# Fresh start with new thread
yamlgraph graph run graph.yaml --thread session-456 --var input=start
```

Same `--thread` value = resume from checkpoint. New value = fresh start.

---

## Streaming

YAMLGraph supports token-by-token streaming at both the prompt level and the graph level.

### Prompt-Level Streaming

```python
from yamlgraph.executor_async import execute_prompt_streaming

async for token in execute_prompt_streaming("greet", {"name": "World"}):
    print(token, end="", flush=True)
```

### YAML Node Config

```yaml
nodes:
  generate:
    type: llm
    prompt: my-prompt
    stream: true
    state_key: response
```

### Graph-Level Streaming (FR-029)

Stream all LLM output from an entire graph using native LangGraph streaming:

```python
from yamlgraph.executor_async import run_graph_streaming_native

async for token in run_graph_streaming_native(
    graph_path="graph.yaml",
    initial_state={"input": "Hello!"},
):
    print(token, end="", flush=True)
```

### Server-Sent Events (SSE)

Stream to web clients with FastAPI:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from yamlgraph.executor_async import execute_prompt_streaming

app = FastAPI()

@app.get("/stream")
async def stream(prompt: str):
    async def generate():
        async for token in execute_prompt_streaming("chat", {"query": prompt}):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

Limitation: streaming bypasses Pydantic validation. Use `execute_prompt_async` with `output_model` for structured responses.

---

## Async Usage

The codebase uses a **sync-first with async wrappers** pattern. Core functions in `executor.py` are synchronous. Async versions in `executor_async.py` add streaming, concurrent execution, and web framework integration.

```python
import asyncio
from yamlgraph.executor_async import (
    execute_prompt_async,
    load_and_compile_async,
    run_graph_async,
)

async def main():
    # Single prompt
    result = await execute_prompt_async("greet", {"name": "World"})

    # Full graph
    app = await load_and_compile_async("graphs/my-graph.yaml")
    result = await run_graph_async(app, {"input": "hello"}, config)

asyncio.run(main())
```

For FastAPI integration:

```python
from fastapi import FastAPI
from langgraph.types import Command
from yamlgraph.executor_async import load_and_compile_async, run_graph_async

app = FastAPI()
graph_app = None

@app.on_event("startup")
async def startup():
    global graph_app
    graph_app = await load_and_compile_async("examples/demos/interview/graph.yaml")

@app.post("/chat/{thread_id}")
async def chat(thread_id: str, message: str):
    config = {"configurable": {"thread_id": thread_id}}
    result = await run_graph_async(graph_app, {"input": message}, config)

    if "__interrupt__" in result:
        return {"status": "waiting", "question": result["__interrupt__"][0].value}

    return {"status": "complete", "response": result.get("response")}
```

---

## MCP Server

YAMLGraph exposes graphs as tools for GitHub Copilot and other MCP-compatible AI assistants via `yamlgraph/mcp_server.py`.

### Setup

```bash
pip install -e ".[mcp]"
```

Configure VS Code (`.vscode/mcp.json`):

```json
{
  "servers": {
    "yamlgraph": {
      "command": ".venv/bin/python3",
      "args": ["yamlgraph/mcp_server.py"],
      "cwd": "/path/to/yamlgraph"
    }
  }
}
```

### Tools Exposed

**`yamlgraph_list_graphs`** — Lists all discovered graphs with names, descriptions, and required variables.

**`yamlgraph_run_graph`** — Runs a graph by name, passing required variables.

The server scans `examples/demos/*/graph.yaml` and `examples/*/graph.yaml` at startup. Any graph placed in a scanned directory is automatically available as an MCP tool.

---

## Prompt Deployment

YAMLGraph reads prompts from the filesystem at graph load time. For production deployments where prompts need to be updated without rebuilding, several patterns are documented in `reference/prompt-deployment.md`:

| Pattern | Update Speed | Best For |
|---------|-------------|----------|
| Volume mount | Minutes | Simple deployments |
| ConfigMap | Minutes | Kubernetes native |
| Git-sync sidecar | 1–5 min | GitOps workflows |
| S3 sync at startup | Restart | Cloud-native apps |
| Environment-based selection | Deploy | Multi-env testing |
| Runtime API | Instant | Rapid iteration |

The recommendation: start with volume mounts or ConfigMaps. For GitOps, use a git-sync sidecar. Avoid baking prompts into Docker images if you need flexibility.

---

## Anti-Patterns

From `CLAUDE.md`, the definitive list of what not to do:

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Hardcoded prompts in Python | YAML templates in `prompts/` |
| Direct provider imports | `create_llm()` factory |
| Untyped dicts | Pydantic models or inline YAML schemas |
| `state["key"] = value` | `return {"key": value}` |
| Silent exceptions | `PipelineError.from_exception()` |
| Files > 400 lines | Refactor into submodules |
| Skip tests | TDD red-green-refactor |

Error handling for YAML-defined nodes is automatic via `on_error`:

| `on_error` Value | Behavior |
|------------------|----------|
| `skip` | Log warning, continue without output |
| `retry` | Retry up to `max_retries` times |
| `fail` | Raise exception, halt pipeline |
| `fallback` | Try `fallback.provider` on failure |

---

## Closing Words

We began this chapter with a YAML file and traced its journey through validation, state generation, node compilation, and graph execution. We cataloged every node type — from the simple `llm` call to the composable `subgraph`, from the parallel `map` to the human-in-the-loop `interrupt`. We showed how the framework extends with new providers, tools, and deployment patterns.

The key insight remains: *60–80% of AI workflows can be defined entirely in YAML.* The remaining 20–40% — external integrations, custom processing, UX concerns — live in Python tools and presentation code, cleanly separated by the three-layer architecture.

We close with the **Agents' Prayer**, from the project's `.github/copilot-instructions.md` — a meditation on the discipline required to build systems that work:

> May I fix at the callsite, not the utility.
> May I kill the cheapest bug — the one in the spec.
> May I normalize at the boundary, trusting no provider's type.
> May I stream to reveal what batch conceals.
> May I understand every protection before I pass it.
> May I read thrice before I grant authority.
>
> When hooks feel slow, let that be the sign they guard.
> When I feel certain, let that be the sign to Judge.
>
> What survives the fire may merge.


