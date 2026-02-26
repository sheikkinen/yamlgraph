---
render_with_liquid: false
---

# Chapter 07: YAMLGraph Core

The previous chapters established a development philosophy—research before coding, TDD, structured ideation, continuous refinement. Now we meet the engine that makes it executable: **YAMLGraph**, a YAML-first framework for building LLM pipelines using LangGraph.

The key insight behind YAMLGraph: 60–80% of AI workflows can be defined entirely in YAML—graphs, prompts, and schemas—without writing Python code. When you do need Python, it lives in a separate layer, cleanly isolated from the pipeline logic.

This chapter is divided into two parts. Part I explains how YAMLGraph works internally—the architecture, the compilation pipeline, and the execution model. Part II is a hands-on catalog of every node type with real, runnable examples from the `examples/demos/` directory.

---

## Part I: How It Works

### The Three-Layer Architecture

Every YAMLGraph application follows a strict separation of concerns. From `ARCHITECTURE.md`:

```
┌─────────────────────────────────────┐
│  Python CLI (demo.py, run_*.py)     │ ← Presentation: colors, REPL, args
├─────────────────────────────────────┤
│  YAML Graphs (*.yaml)               │ ← Logic: LLM, state, checkpoints
├─────────────────────────────────────┤
│  Python Tools (nodes/*.py)          │ ← Side effects: API calls, files
└─────────────────────────────────────┘
```

**Presentation Layer** (Python CLI): Argument parsing, terminal colors, interactive prompts. A thin wrapper around graph execution—it calls `app.invoke()` and formats output.

**Logic Layer** (YAML Graphs): All LLM calls, routing, state transitions. Interrupt nodes for human-in-the-loop. Map nodes for parallel processing. Checkpointing and resume capability.

**Side Effects Layer** (Python Tools): External API calls, file I/O, image generation. Functions that can't be expressed in YAML live here.

Why this pattern? Graphs are testable, traceable, and resumable. Python handles UX where YAML can't. Tools isolate non-deterministic operations. Each layer can evolve independently.

The same pattern extends to web APIs:

```
┌─────────────────────────────────────┐
│  FastAPI / Flask                    │ ← HTTP: routes, auth, validation
├─────────────────────────────────────┤
│  YAML Graphs                        │ ← Logic: stateless or with threads
├─────────────────────────────────────┤
│  Python Tools + Storage             │ ← Persistence: DB, S3, queues
└─────────────────────────────────────┘
```

### The Compilation Pipeline

A YAML file doesn't run directly. It goes through a compilation pipeline that transforms declarative configuration into an executable LangGraph `CompiledGraph`. The core files that orchestrate this are documented in `reference/getting-started.md`:

| File | Purpose |
|------|---------|
| `yamlgraph/graph_loader.py` | Compiles YAML → LangGraph StateGraph |
| `yamlgraph/executor.py` | `execute_prompt()` — unified LLM call interface |
| `yamlgraph/node_factory.py` | Creates node functions from YAML config |
| `yamlgraph/utils/llm_factory.py` | Multi-provider LLM factory (anthropic/mistral/openai) |
| `yamlgraph/models/state_builder.py` | Dynamic state class generation |

The pipeline flows like this (from `CLAUDE.md`):

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

**Step 1: Load** — `load_graph_config()` reads the YAML file and validates it into a `GraphConfig` Pydantic model. Schema validation catches errors before execution.

**Step 2: Branch** — Three parallel transformations happen:
- `build_state_class()` generates a dynamic `TypedDict` by scanning all `state_key` fields across nodes.
- `parse_tools()` builds a tool registry from the `tools:` section.
- `compile_graph()` wires nodes and edges into a LangGraph `StateGraph`.

**Step 3: Compile** — The `StateGraph` is compiled into a `CompiledGraph`, ready for `invoke()` or `stream()`.

### Graph YAML Anatomy

Every graph YAML file follows a standard structure. From `reference/graph-yaml.md`:

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

Let's see this in practice. Here is the complete `examples/demos/hello/graph.yaml`—the simplest possible YAMLGraph pipeline:

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

This graph defines one node (`greet`) that makes a single LLM call. It reads `name` and `style` from state, passes them to a prompt template, and stores the result in `state.greeting`. The `edges` section wires it: START → greet → END.

Run it:

```bash
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="holy see of code" --full
```

### Prompt YAML Anatomy

Prompts live in separate YAML files. They define the system message, the user message (with variable placeholders), and optionally an inline schema for structured output.

From `reference/prompt-yaml.md`, the structure is:

```yaml
# Option 1: Native schema format
schema:
  name: OutputModel
  fields:
    field_name:
      type: str
      description: "Field description"

# System message (always required)
system: |
  You are a helpful assistant...

# User message (simple templates)
user: |
  Please process: {input}

# OR: Template (advanced Jinja2)
template: |
  {% for item in items %}
  {{ item.name }}
  {% endfor %}
```

Two template modes exist. **Simple mode** uses `{variable}` placeholders—Python's `str.format()` style. **Jinja2 mode** activates automatically when `{{` or `{%` appears, enabling loops, conditionals, and filters.

Here is the complete prompt for the hello demo, from `examples/demos/hello/prompts/greet.yaml`:

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

No schema defined—the LLM returns free-form text. When you need structured output, you add an inline schema. Here's the classification prompt from the router demo (`examples/demos/router/prompts/classify_tone.yaml`):

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

The `schema` section defines a Pydantic model at compile time. The LLM's output is validated against it—`tone` must be a string, `confidence` must be a float between 0.0 and 1.0. This is Commandment 5 in action: *Thou shalt sanctify thy outputs with types.*

Supported field types from the reference:

| Type String | Python Type | Example |
|-------------|-------------|---------|
| `str` | `str` | `"hello"` |
| `int` | `int` | `42` |
| `float` | `float` | `0.95` |
| `bool` | `bool` | `true` |
| `list[str]` | `list[str]` | `["a", "b"]` |
| `list[int]` | `list[int]` | `[1, 2, 3]` |
| `dict[str, str]` | `dict[str, str]` | `{"key": "value"}` |
| `dict[str, Any]` | `dict[str, Any]` | `{"key": ...}` |
| `Any` | `Any` | Any value |

### Dynamic State Management

Traditional LangGraph requires manually defining a state class:

```python
class MyState(TypedDict):
    topic: str
    generated: str  # Must manually add for each node
```

YAMLGraph generates state automatically. The state builder (`yamlgraph/models/state_builder.py`) scans all `state_key` fields across nodes and creates a `TypedDict` at runtime:

```yaml
nodes:
  generate:
    state_key: generated  # ← Auto-added to state
  analyze:
    state_key: analysis   # ← Auto-added to state
```

No manual state classes needed. The state always matches the graph definition.

From `ARCHITECTURE.md`, the design tradeoffs are explicit:

- ✅ Less boilerplate, faster iteration
- ✅ State always matches graph definition
- ❌ No static type checking in IDE
- ❌ Runtime errors instead of compile-time

You can also declare state fields explicitly for input variables:

```yaml
state:
  name: str
  style: str
```

### Node Execution Flow

Every node, regardless of type, follows the same execution sequence (implemented in the `node_factory/` modules):

1. **Pre-checks** — `check_requirements()` verifies required state keys exist (from the `requires` field)
2. **Loop protection** — `check_loop_limit()` prevents infinite cycles (from `loop_limits`)
3. **Resume support** — `skip_if_exists` check for checkpoint resumption (default: `true`)
4. **Execution** — `execute_prompt()` or custom logic depending on node type
5. **Return** — A dict with state updates (never mutate state directly)

This is a critical pattern from `CLAUDE.md`:

```python
# ❌ WRONG - Direct mutation
def node_fn(state):
    state["key"] = value
    return state

# ✅ CORRECT - Return update dict
def node_fn(state):
    return {"key": value}
```

LangGraph merges the returned dict into state.

---

## Part II: How to Use It

### Node Type Catalog

YAMLGraph provides twelve node types. Each encapsulates a common LLM pipeline pattern:

| Type | Purpose |
|------|---------|
| `llm` | Single LLM call with prompt |
| `router` | Classify → route to different nodes |
| `agent` | ReAct agent with tools |
| `tool` | Execute a registered tool |
| `tool_call` | Dynamic tool from state |
| `map` | Parallel execution over list |
| `python` | Custom Python function |
| `interrupt` | Human-in-the-loop pause/resume |
| `passthrough` | State transformation without LLM |
| `subgraph` | Nested graph execution |
| `interactive_tool` | Multi-turn conversation loop |
| `copilot` | Delegate task to Copilot CLI |

Let's walk through each type with real examples.

---

#### LLM Node

The most common node type. Makes a single LLM call with a prompt template and optional structured output.

The hello world demo (`examples/demos/hello/graph.yaml`) is a pure `llm` node:

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

Common properties for LLM nodes (from `reference/graph-yaml.md`):

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `type` | `string` | `"llm"` | Node type |
| `prompt` | `string` | varies | Prompt file path (without `.yaml`) |
| `variables` | `object` | `{}` | Template variable mappings |
| `state_key` | `string` | node name | State key to store result |
| `requires` | `list[str]` | `[]` | Required state keys before execution |
| `temperature` | `float` | from defaults | LLM temperature |
| `provider` | `string` | from defaults | LLM provider |
| `max_tokens` | `int` | from config | Maximum output tokens |
| `thinking_budget` | `int` | from defaults | Anthropic extended thinking tokens |
| `skip_if_exists` | `bool` | `true` | Skip if state key has truthy value |
| `stream` | `bool` | `false` | Enable token-by-token streaming |
| `parse_json` | `bool` | `false` | Extract JSON from LLM response |

**Extended thinking** is supported via the `thinking_budget` field. Here is the complete `examples/demos/thinking/graph.yaml`:

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

Notice the pattern: the `defaults` section sets `thinking_budget: 8000` for the entire graph, but the `quick_response` node overrides it to `0`. Per-node overrides always win.

---

#### Router Node

Classifies input and routes to different downstream nodes. The LLM output must match one of the `routes` keys.

Here is the complete `examples/demos/router/graph.yaml`:

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

The `classify` node uses the `classify_tone` prompt (shown earlier) to detect `positive`, `negative`, or `neutral` tone. The `routes` map connects each classification to its handler node. If the LLM returns something unexpected, `default_route` catches it.

The edge wiring is key: the conditional edge `to: [respond_positive, respond_negative, respond_neutral]` with `type: conditional` tells LangGraph this is a branch point. Only one path executes per run.

Run it:

```bash
yamlgraph graph run examples/demos/router/graph.yaml --var message="I love this product!" --full
```

---

#### Map Node

Processes each item in a list in parallel using LangGraph's `Send()` API. The fan-out/fan-in pattern:

```
[item1, item2, item3]  →  process each  →  [result1, result2, result3]
```

Here is the complete `examples/demos/map/graph.yaml`:

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

The `generate` node produces a list of ideas (using the `generate_ideas` prompt with its `IdeasList` schema). The `expand` map node fans out over `{state.ideas.ideas}`—each idea is processed in parallel by the `expand_idea` prompt. Results are collected into `state.expansions`. Finally, `summarize` consolidates everything.

The prompt that produces the list (`examples/demos/map/prompts/generate_ideas.yaml`):

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

And the per-item prompt (`examples/demos/map/prompts/expand_idea.yaml`):

```yaml
schema:
  name: ExpandedIdea
  fields:
    expansion:
      type: str
      description: "Expanded version of the idea"

system: |
  You expand on ideas with creative details.

user: |
  Take this idea and expand it into a short paragraph (2-3 sentences):

  Idea: {idea}

  Provide a creative expansion of this concept.
```

Map node properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `over` | `string` | Yes | State expression for the list to iterate |
| `as` | `string` | Yes | Variable name injected into sub-node |
| `node` | `object` | Yes | Sub-node definition (llm, router, or python) |
| `collect` | `string` | Yes | State key where results are collected |
| `max_items` | `int` | No | Maximum fan-out items |
| `flatten_output` | `bool` | No | Merge sub-key contents into items |

Run it:

```bash
yamlgraph graph run examples/demos/map/graph.yaml --var topic="space exploration" --async --full
```

---

#### Subgraph Node

Embeds and executes another graph as a single node. This enables modular composition—build reusable workflows and nest them.

Here is the complete `examples/demos/subgraph/graph.yaml`:

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

The `summarize` node doesn't run a prompt—it invokes an entire child graph. The `input_mapping` translates parent state keys to child state keys (`prepared_text` → `input_text`). The `output_mapping` translates results back (`output_summary` → `summary`).

The child graph (`examples/demos/subgraph/subgraphs/summarizer.yaml`):

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

The child graph is a complete, standalone graph with its own state, defaults, and prompts. It knows nothing about its parent. This is the power of subgraph composition—the summarizer can be used in any parent graph, or run independently.

Subgraph properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `graph` | `string` | Yes | Path to child graph YAML |
| `mode` | `string` | No | `invoke` (default) or `stream` |
| `input_mapping` | `dict` | No | Map parent state keys to child state keys |
| `output_mapping` | `dict` | No | Map child state keys to parent state keys |

---

#### Agent Node

An agent has access to tools and decides which ones to call through multi-step reasoning (the ReAct pattern).

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
| `tool_results_key` | `string` | - | State key for tool execution logs |

Tools come in three types:

| Type | Description | Example |
|------|-------------|---------|
| `shell` | Execute shell commands | `git log`, `ruff check` |
| `python` | Call Python functions | Custom processing |
| `websearch` | Web search via DuckDuckGo | Research agents |

All shell tool variables are sanitized with `shlex.quote()` to prevent shell injection.

---

#### Python Node

Executes an arbitrary Python function as a node. The function must accept `state: dict[str, Any]` and return a `dict` with state updates.

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

#### Passthrough Node

Transforms state without making external calls. Useful for counters, accumulators, and data reshaping.

```yaml
nodes:
  increment_turn:
    type: passthrough
    output:
      turn_number: "{state.turn_number + 1}"
      history: "{state.history + [state.current_action]}"
```

Passthrough nodes use the expression language for arithmetic and list operations. Only binary operations are supported (`left op right`). Chained operations like `{state.a + state.b + state.c}` do not work.

---

#### Tool Call Node

Dynamically resolves a tool name and arguments from state at runtime—the LLM decides what tool to call, and this node executes it.

```yaml
nodes:
  execute_tool:
    type: tool_call
    tool: "{state.task.tool}"
    args: "{state.task.args}"
    state_key: result
```

From `reference/tool-call-nodes.md`, the key distinction:

| Type | Description |
|------|-------------|
| `tool` | Executes a named shell tool deterministically |
| `tool_call` | Dynamically selects tool name from state |
| `agent` | LLM decides which tools to call |

---

#### Copilot Node

Delegates a complex reasoning task to GitHub Copilot CLI, giving it access to the full project context.

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

The node returns a `CopilotResult` with `output`, `exit_code`, `model`, and `backend` fields. Access in subsequent nodes via `{state.plan_result.output}`.

---

#### Interrupt Node

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

---

#### Interactive Tool Node

Packs a full multi-turn conversation loop into a single YAML node. It expands at compile time into `interrupt` and `python` nodes with automatic edge wiring:

```yaml
nodes:
  chat:
    type: interactive_tool
    start: chatbot_start
    step: chatbot_step
    end: chatbot_end
    resume_key: user_message
    response_key: bot_response
    loop_until: "state.session_done == True"
    max_iterations: 10
```

Expands into: `chat__start → chat__ask → chat__step ↺ → chat__end`

---

### Expression Syntax

YAMLGraph uses two expression systems for data flow between nodes, documented in `reference/expressions.md`.

**Value expressions** resolve state values. They appear in node `variables:`, passthrough `output:`, and map `over:`:

```yaml
variables:
  simple: "{state.field}"              # Direct field access
  nested: "{state.obj.attr}"           # Nested object access
  loop: "{state._loop_counts.node}"    # Access loop counter
```

The `state.` prefix is required. Missing paths return `None`.

**Arithmetic** is supported in value expressions:

```yaml
output:
  counter: "{state.counter + 1}"
  total: "{state.a + state.b}"
  scaled: "{state.value * 2}"
  history: "{state.history + [state.current_item]}"
```

**Condition expressions** are boolean tests for edge routing. They use a completely different syntax—no braces, no `state.` prefix:

```yaml
edges:
  - from: critique
    to: refine
    condition: critique.score < 0.8

  - from: critique
    to: END
    condition: critique.score >= 0.8
```

Conditions are evaluated **without `eval()`**—a regex-based parser supports only safe operations: comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`), compound expressions with `and`/`or`, and literal values.

| Feature | Value expressions | Condition expressions |
|---------|-------------------|----------------------|
| Braces | `{state.field}` | No braces |
| Prefix | `state.` required | No prefix |
| Purpose | Resolve values | Boolean tests |
| Quoting | N/A | Strings must be quoted |

---

### Common Patterns

Four patterns cover most YAMLGraph pipelines.

#### Linear Pipeline

The simplest pattern—sequential nodes connected by edges:

```yaml
edges:
  - from: START
    to: step1
  - from: step1
    to: step2
  - from: step2
    to: step3
  - from: step3
    to: END
```

Use `requires` to enforce dependencies. Use `state_key` to name outputs clearly. The hello demo is a single-node linear pipeline.

#### Router + Merge

Classification fans out to handler nodes, which all converge to END:

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

The router demo shows this pattern. Always include a `default_route` for fallback.

#### Fan-Out / Fan-In (Map)

Process a list in parallel, then consolidate:

```yaml
edges:
  - from: START
    to: generate
  - from: generate
    to: expand           # map node fans out
  - from: expand
    to: summarize        # consolidation
  - from: summarize
    to: END
```

The map demo shows this pattern. For large lists (100+ items), use the batched map pattern: chunk the list in a prior Python node, then map over batches.

#### Self-Correction Loop (Reflexion)

Iterative refinement until a quality threshold is met:

```yaml
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
    to: critique                       # Loop back
```

Critical settings for loops:
- `skip_if_exists: false` on loop nodes—they must re-run each iteration
- `loop_limits` to prevent infinite loops
- `{state._loop_counts.node_name}` to track current iteration

---

### CLI Commands

The `yamlgraph` CLI provides everything needed to develop, validate, and run graphs.

#### Run a graph

```bash
yamlgraph graph run <graph_path> [options]
```

| Flag | Short | Description |
|------|-------|-------------|
| `--var VAR` | `-v` | Set state variable (key=value), repeatable |
| `--thread THREAD` | `-t` | Thread ID for state persistence |
| `--export` | `-e` | Export results to files |
| `--full` | `-f` | Show full output without truncation |
| `--async` | `-a` | Use async execution for parallel map nodes |
| `--share-trace` | | Share LangSmith trace publicly |

Examples:

```bash
# Basic run
yamlgraph graph run examples/demos/hello/graph.yaml -v name="World" -v style="casual"

# Parallel map execution
yamlgraph graph run examples/demos/map/graph.yaml -v topic=AI --async

# Full output for debugging
yamlgraph graph run examples/demos/router/graph.yaml -v message="I love this!" -f
```

#### Inspect a graph

```bash
yamlgraph graph info examples/demos/router/graph.yaml
```

Shows structure and metadata—nodes, edges, tools, required variables.

#### Validate against schema

```bash
yamlgraph graph validate examples/demos/*/graph.yaml
```

Checks YAML structure against the graph schema.

#### Lint for issues

```bash
yamlgraph graph lint examples/demos/*/graph.yaml
```

Catches common problems: missing state keys, unused tools, broken edge references.

---

### Anti-Patterns

From `CLAUDE.md`, these are the patterns to avoid:

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Hardcoded prompts in Python | YAML templates in `prompts/` |
| Direct provider imports | `create_llm()` factory |
| Untyped dicts | Pydantic models or inline YAML schemas |
| `state["key"] = value` | `return {"key": value}` |
| Silent exceptions | `PipelineError.from_exception()` |
| Files > 400 lines | Refactor into submodules |
| Skip tests | TDD red-green-refactor |

Each anti-pattern traces to a commandment. Hardcoded prompts violate Commandment 3 (*Thou shalt not utter code in vain*). Untyped dicts violate Commandment 5 (*Thou shalt sanctify thy outputs with types*). Silent exceptions violate Commandment 6 (*Thou shalt bear witness of thy errors*).

### Error Handling

All node types support the `on_error` field:

| `on_error` Value | Behavior |
|------------------|----------|
| `skip` | Log warning, continue without output |
| `retry` | Retry up to `max_retries` times |
| `fail` | Raise exception, halt pipeline |
| `fallback` | Try `fallback.provider` on failure |

```yaml
nodes:
  primary:
    type: llm
    prompt: process
    on_error: fallback
    fallback:
      provider: anthropic
    state_key: result
```

### Security

Two security properties are enforced by design:

**Expression evaluation safety** — Condition expressions are parsed with regex, not `eval()`. Only comparisons, compound `and`/`or`, and literal values are supported. No function calls, no imports, no arbitrary code.

**Shell injection protection** — All user-provided variables in shell tool commands are sanitized with `shlex.quote()`. Command templates are trusted; runtime variables are escaped.

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `PROVIDER` | Default LLM provider |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith observability (`true`/`false`) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |

Provider selection follows a priority chain: node-level `provider` > graph `defaults.provider` > `PROVIDER` env var > `"anthropic"` default.

---

## Summary

YAMLGraph inverts the usual relationship between code and configuration. Instead of writing Python that happens to use YAML for settings, you write YAML that happens to use Python for side effects.

The framework's power comes from three properties working together: **declarative graphs** that separate pipeline logic from business logic, **typed prompts** that validate LLM outputs through Pydantic schemas, and **dynamic state** that eliminates boilerplate while keeping the graph definition as the single source of truth.

Twelve node types cover the full spectrum of LLM pipeline patterns—from simple prompts to parallel fan-out, from conditional routing to nested subgraphs, from tool-using agents to human-in-the-loop interrupts. And when YAML isn't enough, the three-layer architecture gives Python a clean place to live without contaminating the pipeline logic.
