# Common Patterns

This document showcases common patterns for building pipelines with the YAML-based graph system.

---

## Pattern 1: Linear Pipeline

Simple sequential processing with dependencies.

### Use Case
Content generation → analysis → summarization

### Graph Structure

```yaml
version: "1.0"
name: linear-pipeline

nodes:
  step1:
    type: llm
    prompt: step1
    state_key: step1_output

  step2:
    type: llm
    prompt: step2
    variables:
      input: "{state.step1_output.field}"
    state_key: step2_output
    requires: [step1_output]      # Explicit dependency

  step3:
    type: llm
    prompt: step3
    variables:
      data: "{state.step2_output}"
    state_key: final
    requires: [step1_output, step2_output]

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

### Key Points

- Use `requires` to enforce dependencies
- Use `state_key` to name outputs clearly
- Access nested fields: `{state.output.field}`

---

## Pattern 2: Conditional Routing

Route to different nodes based on LLM classification.

### Use Case
Customer support: route based on inquiry type or sentiment

### Graph Structure

```yaml
version: "1.0"
name: router-pattern

nodes:
  classify:
    type: router
    prompt: classify
    routes:
      type_a: handle_a
      type_b: handle_b
      type_c: handle_c
    default_route: handle_default
    variables:
      input: "{state.input}"
    state_key: classification

  handle_a:
    type: llm
    prompt: handler_a
    variables:
      input: "{state.input}"
    state_key: response

  handle_b:
    type: llm
    prompt: handler_b
    variables:
      input: "{state.input}"
    state_key: response

  handle_c:
    type: llm
    prompt: handler_c
    variables:
      input: "{state.input}"
    state_key: response

  handle_default:
    type: llm
    prompt: handler_default
    variables:
      input: "{state.input}"
    state_key: response

edges:
  - from: START
    to: classify
  - from: classify
    to: [handle_a, handle_b, handle_c, handle_default]
    type: conditional
  - from: handle_a
    to: END
  - from: handle_b
    to: END
  - from: handle_c
    to: END
  - from: handle_default
    to: END
```

### Router Prompt Pattern

```yaml
# prompts/classify.yaml
schema:
  name: Classification
  fields:
    category:
      type: str
      description: "Category: type_a, type_b, or type_c"
    confidence:
      type: float
      constraints:
        ge: 0.0
        le: 1.0

system: |
  Classify the input into one of these categories:
  - type_a: [description]
  - type_b: [description]
  - type_c: [description]

user: |
  Classify: {input}
```

### Key Points

- Router `routes` maps classification values → node names
- Use `default_route` for fallback
- All target nodes must be listed in conditional edge `to: [...]`

---

## Pattern 3: Self-Correction Loop (Reflexion)

Iterative refinement until quality threshold is met.

### Use Case
Essay writing, code generation with quality checks

### Graph Structure

```yaml
version: "1.0"
name: reflexion-pattern

nodes:
  draft:
    type: llm
    prompt: draft
    variables:
      topic: "{state.topic}"
    state_key: current_draft

  critique:
    type: llm
    prompt: critique
    variables:
      content: "{state.current_draft.content}"
      iteration: "{state._loop_counts.critique}"   # Track iteration
    state_key: critique
    skip_if_exists: false    # CRITICAL: Re-run each loop

  refine:
    type: llm
    prompt: refine
    variables:
      content: "{state.current_draft.content}"
      feedback: "{state.critique.feedback}"
    state_key: current_draft   # Overwrites draft
    skip_if_exists: false      # CRITICAL: Re-run each loop

edges:
  - from: START
    to: draft
  - from: draft
    to: critique
  - from: critique
    to: refine
    condition: critique.score < 0.8    # Continue if low score
  - from: critique
    to: END
    condition: critique.score >= 0.8   # Exit if high score
  - from: refine
    to: critique                       # Loop back

loop_limits:
  critique: 5                          # Prevent infinite loops
```

### Critical Configuration

| Setting | Value | Why |
|---------|-------|-----|
| `skip_if_exists` | `false` | Nodes must re-run each iteration |
| `loop_limits` | Set limit | Prevent infinite loops |
| `_loop_counts` | Access in variables | Track current iteration |

### Critique Prompt Pattern

```yaml
schema:
  name: Critique
  fields:
    score:
      type: float
      description: "Quality score 0.0-1.0 (0.8+ is acceptable)"
      constraints:
        ge: 0.0
        le: 1.0
    feedback:
      type: str
      description: "Specific improvements needed"

system: |
  You are a quality reviewer. Score the content 0.0-1.0.
  Score 0.8+ means it's ready, below 0.8 needs refinement.

user: |
  Review this content (iteration {iteration}):

  {content}
```

---

## Pattern 4: Tool-Using Agent

Agent with shell command tools for research and analysis.

### Use Case
Code analysis, repository inspection, data gathering

### Graph Structure

```yaml
version: "1.0"
name: agent-pattern

tools:
  list_files:
    command: ls -la {directory}
    description: "List files in a directory"
    parse: text

  read_file:
    command: cat {filepath}
    description: "Read contents of a file"
    parse: text

  search_code:
    command: grep -r "{pattern}" {directory}
    description: "Search for pattern in code"
    parse: text

  run_tests:
    command: pytest {test_path} -v
    description: "Run tests and get results"
    parse: text

nodes:
  analyze:
    type: agent
    prompt: analyzer
    tools: [list_files, read_file, search_code, run_tests]
    max_iterations: 10
    state_key: analysis

  report:
    type: llm
    prompt: report
    requires: [analysis]
    variables:
      findings: "{state.analysis}"
    state_key: report

edges:
  - from: START
    to: analyze
  - from: analyze
    to: report
  - from: report
    to: END
```

### Agent Prompt Pattern

```yaml
# prompts/analyzer.yaml
system: |
  You are a code analyst with access to these tools:

  1. **list_files**: List directory contents
     - directory: Path to list

  2. **read_file**: Read a file
     - filepath: Path to the file

  3. **search_code**: Search for patterns
     - pattern: Regex pattern
     - directory: Where to search

  4. **run_tests**: Execute tests
     - test_path: Path to tests

  Your task:
  1. Explore the codebase
  2. Identify patterns and issues
  3. Provide actionable insights

user: |
  Analyze the repository and report on code quality.
```

### Key Points

- Tools are defined at graph level, referenced in nodes
- Use `{param}` placeholders in commands
- Agent decides which tools to call and with what parameters
- Set reasonable `max_iterations` to prevent runaway agents

---

## Pattern 5: Error Recovery

Handle LLM failures gracefully with fallbacks.

### Graph Structure

```yaml
version: "1.0"
name: resilient-pipeline

defaults:
  provider: mistral
  temperature: 0.7

nodes:
  primary:
    type: llm
    prompt: process
    on_error: fallback             # Try fallback on failure
    fallback:
      provider: anthropic          # Use different provider
    state_key: result

  # Alternative: retry with same provider
  retry_example:
    type: llm
    prompt: other_process
    on_error: retry
    max_retries: 3                 # Try up to 3 times
    state_key: other_result

  # Alternative: skip on failure (non-critical)
  optional_step:
    type: llm
    prompt: optional
    on_error: skip                 # Continue without output
    state_key: optional_data

edges:
  - from: START
    to: primary
  - from: primary
    to: retry_example
  - from: retry_example
    to: optional_step
  - from: optional_step
    to: END
```

### Error Handling Options

| `on_error` | Behavior | Use Case |
|------------|----------|----------|
| `fallback` | Try different provider | Primary provider rate limited |
| `retry` | Retry N times | Transient errors |
| `skip` | Continue without output | Optional/non-critical steps |
| `fail` | Stop pipeline | Critical steps |

---

## Pattern 6: Multi-Output to Single Input

Multiple steps feed into one consolidation step.

### Graph Structure

```yaml
version: "1.0"
name: multi-input

nodes:
  research_a:
    type: llm
    prompt: research_a
    variables:
      topic: "{state.topic}"
    state_key: research_a

  research_b:
    type: llm
    prompt: research_b
    variables:
      topic: "{state.topic}"
    state_key: research_b

  research_c:
    type: llm
    prompt: research_c
    variables:
      topic: "{state.topic}"
    state_key: research_c

  synthesize:
    type: llm
    prompt: synthesize
    variables:
      source_a: "{state.research_a.content}"
      source_b: "{state.research_b.content}"
      source_c: "{state.research_c.content}"
    state_key: synthesis
    requires: [research_a, research_b, research_c]

edges:
  - from: START
    to: research_a
  - from: START
    to: research_b
  - from: START
    to: research_c
  - from: research_a
    to: synthesize
  - from: research_b
    to: synthesize
  - from: research_c
    to: synthesize
  - from: synthesize
    to: END
```

### Key Points

- Multiple edges from START run concurrently (if supported)
- Use `requires` on consolidation node
- Access multiple sources in variables

---

## Pattern 7: Stateful Memory (AgentState)

Maintain conversation history across interactions.

### Graph Structure

```yaml
version: "1.0"
name: memory-pattern

# State auto-generated with messages reducer for agent

nodes:
  chat:
    type: agent
    prompt: chat
    tools: [search, calculate]
    state_key: response
    tool_results_key: _tool_results
    max_iterations: 5

edges:
  - from: START
    to: chat
  - from: chat
    to: END

exports:
  response:
    format: markdown
    filename: chat.md
  _tool_results:
    format: json
    filename: tool_log.json
```

### AgentState Definition

```python
# yamlgraph/models/state.py
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]  # Accumulates messages
    response: str
    _tool_results: list[dict]
```

---

## Pattern 8: Parallel Fan-Out (Map)

Process each item in a list in parallel and collect results.

### Use Case
- Transform multiple documents/panels/items simultaneously
- Generate images for each story panel
- Analyze multiple code files in parallel

### Graph Structure

```yaml
version: "1.0"
name: map-pattern

state:
  items: list
  processed_items: list

nodes:
  generate_items:
    type: llm
    prompt: generate_items
    state_key: items              # Returns a list

  process_items:
    type: map
    over: "{state.items}"         # List to iterate
    as: item                      # Variable name per item
    flatten_output: true          # FR-052: merge sub-key into items
    node:
      type: llm
      prompt: process_item
      state_key: processed_item
    collect: processed_items      # Collected results

  summarize:
    type: llm
    prompt: summarize
    variables:
      results: "{state.processed_items}"
    state_key: summary
    requires: [processed_items]

edges:
  - from: START
    to: generate_items
  - from: generate_items
    to: process_items
  - from: process_items
    to: summarize
  - from: summarize
    to: END
```

### Sub-Node Prompt Pattern

```yaml
# prompts/process_item.yaml
schema:
  name: ProcessedItem
  fields:
    result:
      type: str
      description: "Processed output"
    metadata:
      type: dict
      description: "Additional info"

system: |
  Process the given item and return structured output.

user: |
  Process this item: {item}
```

### Real-World Example: Animated Storyboard

```yaml
nodes:
  expand_story:
    type: llm
    prompt: expand_story
    state_key: story              # {title, panels: [...]}

  animate_panels:
    type: map
    over: "{state.story.panels}"  # List of panel descriptions
    as: panel_prompt
    node:
      type: llm
      prompt: animate_panel       # Convert to first/middle/last frames
      state_key: animated_panel
    collect: animated_panels

  generate_images:
    type: python
    tool: generate_images
    requires: [animated_panels]

edges:
  - from: START
    to: expand_story
  - from: expand_story
    to: animate_panels
  - from: animate_panels
    to: generate_images
  - from: generate_images
    to: END
```

### Key Points

- Use `type: map` for parallel list processing
- `over` specifies the list to iterate (supports nested access)
- `as` defines the variable name available in sub-node
- `collect` aggregates all results into a list
- Results include `_map_index` for ordering
- Sub-nodes can be `llm`, `router`, or `python` type

See [Map Nodes Reference](map-nodes.md) for comprehensive documentation.
For exhaustive analysis where every corpus item must be accounted for, see the
[Corpus Map-Reduce Pattern](patterns/corpus-map-reduce.md).

---

## Cheat Sheet

### Node Type Quick Reference

| Type | Purpose | Required Fields |
|------|---------|-----------------|
| `llm` | LLM call with optional structured output | `prompt` |
| `router` | Classification → routing | `prompt`, `routes` |
| `map` | Parallel fan-out over lists | `over`, `as`, `node`, `collect` |
| `python` | Custom Python function | `tool` |
| `agent` | Tool-using autonomous agent | `prompt`, `tools` |

### Common Variable Patterns

```yaml
variables:
  # Simple state access
  topic: "{state.topic}"

  # Nested object access
  content: "{state.generated.content}"

  # Loop counter
  iteration: "{state._loop_counts.node_name}"

  # List (auto-joined with ", ")
  tags: "{state.analysis.tags}"
```

### Edge Condition Patterns

```yaml
edges:
  # Simple linear
  - from: a
    to: b

  # Terminal
  - from: b
    to: END

  # Router conditional
  - from: classify
    to: [opt_a, opt_b, opt_c]
    type: conditional

  # Expression-based
  - from: critique
    to: refine
    condition: critique.score < 0.8
```

---

## Pattern 9: Soul Pattern (Agent Personality)

Give AI agents consistent personality using `data_files` to load a soul configuration.

### Use Case
- Customer service agents with brand-appropriate tone
- Multiple personality variants (friendly, formal, technical)
- A/B testing different communication styles

### Soul File Structure

```yaml
# souls/friendly.yaml
name: Friendly Helper

voice: warm, approachable, patient, and encouraging

principles:
  - Always acknowledge the person's situation before providing solutions
  - Use "we" language to create a sense of partnership
  - Explain technical concepts with everyday analogies
  - End responses with clear, actionable next steps

constraints:
  - Never blame the user for problems
  - Avoid jargon unless the user uses it first
  - Don't be condescending or overly simplistic
```

### Graph Configuration

```yaml
version: "1.0"
name: personality-agent

# Soul loaded via data_files - available as {{ soul }} in all prompts
data_files:
  soul: souls/friendly.yaml

nodes:
  respond:
    type: llm
    prompt: respond
    state_key: response
```

### Prompt Template

```yaml
# prompts/respond.yaml
system: |
  You are {{ soul.name }}.
  Your communication style is: {{ soul.voice }}

  Core principles:
  {% for principle in soul.principles %}
  - {{ principle }}
  {% endfor %}

  Things to avoid:
  {% for constraint in soul.constraints %}
  - {{ constraint }}
  {% endfor %}

user: |
  {{ message }}
```

### Switching Souls

Three ways to use different personalities:

| Method | When to Use |
|--------|-------------|
| Change `data_files.soul` path | Different builds/deployments |
| Pass `soul` as input | Runtime override (input wins) |
| Different graph files | Distinct product variants |

### Runtime Override Example

```bash
# Override soul at runtime via CLI
yamlgraph run graph.yaml \
  --var 'message=Hello!' \
  --var 'soul={"name": "Quick Bot", "voice": "brief", "principles": ["be fast"]}'
```

### Example

See [examples/demos/soul](../examples/demos/soul/) for a complete working example.
---

## Pattern 10: Batched Map Processing

Process large lists in controlled batches to avoid rate limits or memory pressure.

### Problem

Map nodes fan out **all items simultaneously**. For large lists (100+ items) or rate-limited APIs, this causes:
- API rate limit errors (429s)
- Memory pressure from parallel LLM calls
- Uncontrolled parallelism

### Solution: Pre-Chunking

Chunk the list in a prior node, then map over batches:

```yaml
version: "1.0"
name: batched-processing

tools:
  chunk_list:
    type: python
    module: myproject.tools
    function: chunk_list

  process_batch:
    type: python
    module: myproject.tools
    function: process_batch

  flatten_results:
    type: python
    module: myproject.tools
    function: flatten_results

nodes:
  # Split items into batches
  prepare_batches:
    type: python
    tool: chunk_list
    state_key: batches          # [[item1, item2, item3], [item4, item5, item6], ...]

  # Process each batch (batches run in parallel, items within batch are sequential)
  process_batches:
    type: map
    over: "{state.batches}"
    as: batch
    collect: batch_results
    node:
      type: python
      tool: process_batch       # Processes items in batch sequentially
      state_key: batch_result

  # Flatten results
  combine_results:
    type: python
    tool: flatten_results
    state_key: results

edges:
  - from: START
    to: prepare_batches
  - from: prepare_batches
    to: process_batches
  - from: process_batches
    to: combine_results
  - from: combine_results
    to: END
```

### Python Tools

```python
# myproject/tools.py
from typing import Any

def chunk_list(state: dict) -> dict:
    """Split items into batches of specified size."""
    items = state.get("items", [])
    batch_size = state.get("batch_size", 10)

    batches = [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]
    return {"batches": batches}

def process_batch(state: dict) -> dict:
    """Process items in a batch sequentially."""
    batch = state.get("batch", [])
    results = []

    for item in batch:
        # Process each item (with rate limiting if needed)
        result = process_single_item(item)
        results.append(result)

    return {"batch_result": results}

def flatten_results(state: dict) -> dict:
    """Flatten batch results into single list."""
    batch_results = state.get("batch_results", [])

    # Sort by _map_index to preserve order
    sorted_batches = sorted(batch_results, key=lambda x: x.get("_map_index", 0))

    flat = []
    for batch in sorted_batches:
        flat.extend(batch.get("batch_result", []))

    return {"results": flat}
```

### Key Points

| Aspect | Approach |
|--------|----------|
| **Chunking** | Done in Python tool before map node |
| **Parallelism** | Batches run in parallel via map |
| **Within-batch** | Items processed sequentially (rate-limit safe) |
| **Ordering** | Preserved via `_map_index` |
| **Flattening** | Post-processing combines results |

### Why Not Built-In `batch_size`?

We considered adding `batch_size` directly to map nodes but chose the pre-chunking pattern because:

1. **Simplicity** - No changes to core framework
2. **Flexibility** - Custom chunking logic (by type, size, priority)
3. **Visibility** - Explicit graph structure, no magic edges
4. **Testability** - Each tool is independently testable
5. **KISS** - The cheapest code is the code you don't write

### Rate Limiting Within Batches

```python
import time

def process_batch(state: dict) -> dict:
    batch = state.get("batch", [])
    delay_seconds = state.get("rate_limit_delay", 0.5)
    results = []

    for i, item in enumerate(batch):
        if i > 0:
            time.sleep(delay_seconds)  # Rate limiting
        result = process_single_item(item)
        results.append(result)

    return {"batch_result": results}
```

  For corpus-scale semantic analysis, batching alone is insufficient: freeze
  source identities, reconcile every result, and preserve primary findings as
  described in the [Corpus Map-Reduce Pattern](patterns/corpus-map-reduce.md).

---

## Pattern 11: Input Guardrails

Intercept user input with audit and validation nodes before the LLM responds.

### Problem

An LLM receives raw user input without any validation or audit trail. This creates risk:
- **No audit trail** — You can't trace what the model actually received
- **No content check** — Malicious, sensitive, or malformed input reaches the model unfiltered
- **No compliance** — Regulated industries need pre-processing records for every interaction

### Solution: Echo → Validate → Respond Pipeline

Insert Python tool nodes before the LLM node. Each tool performs a single concern:

1. **Echo** — Log and store raw input for audit trail
2. **Validate** — Check content, stamp validation status, flag unvalidated content
3. **Respond** — LLM generates response using validated (or flagged) content

### Graph Structure

```yaml
version: "1.0"
name: guardrails-pattern

state:
  input: str
  echo: str
  validation: str
  response: str

tools:
  echo_input:
    type: python
    module: myproject.guardrails
    function: echo_input
    description: "Echo the input for audit trail"

  validate_input:
    type: python
    module: myproject.guardrails
    function: validate_input
    description: "Validate input content"

nodes:
  echo:
    type: python
    tool: echo_input

  validate:
    type: python
    tool: validate_input

  respond:
    type: llm
    prompt: respond
    state_key: response

edges:
  - from: START
    to: echo
  - from: echo
    to: validate
  - from: validate
    to: respond
  - from: respond
    to: END
```

### Python Tools

```python
# myproject/guardrails.py
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def echo_input(state: dict[str, Any]) -> dict[str, Any]:
    """Echo the input for audit trail."""
    raw = state.get("input", "")
    logger.info(f"[echo] {raw[:200]}")
    return {"echo": raw}


def validate_input(state: dict[str, Any]) -> dict[str, Any]:
    """Validate input content. Stamps *validation missing* on unvalidated content."""
    raw = state.get("input", "")

    # Parse messages if JSON
    try:
        messages = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        messages = [{"role": "user", "content": raw}]

    # Stamp validation status
    validated_content = []
    for msg in messages:
        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
        validated_content.append(f"{content}\n\n*validation missing*")

    return {"validation": "\n---\n".join(validated_content)}
```

### Prompt Template

```yaml
# prompts/respond.yaml
system: |
  You are a helpful assistant.
  The user's message has been through a validation pipeline.
  Content marked with *validation missing* has not been validated.
  Treat such content with appropriate caution.

user: |
  {{validation}}
```

The prompt references `{{validation}}` — the output of the validate node. Content flagged with *validation missing* tells the LLM to apply extra caution.

### Key Points

| Aspect | Approach |
|--------|----------|
| **Audit** | Echo node stores raw input before any processing |
| **Validation** | Stamp approach — flag content rather than block it |
| **Extensibility** | Add more validation stages (PII, profanity, length) as additional Python tool nodes |
| **Separation** | Each concern is a separate node, independently testable |
| **LLM awareness** | Prompt tells the LLM about validation status |

### Extending the Pattern

Add validation stages by inserting nodes between `validate` and `respond`:

- **Content filtering** — Block or flag profanity, hate speech
- **PII detection** — Redact personal information before the LLM sees it
- **Rate limiting** — Throttle by user or session in a Python tool node
- **Schema validation** — Verify structured input matches expected format

Each extension is a Python tool node following the same `state → dict` pattern.

### Related

- [examples/openai_proxy/](../examples/openai_proxy/) — Production implementation as an OpenAI-compatible guardrail proxy
- [Pattern 12: Quality Gate](#pattern-12-quality-gate-for-map-output) — Complementary output-side validation
- [demos/safety-guards/](../examples/demos/safety-guards/) — Execution safety (recursion limits, map caps) — distinct from input guardrails

---

## Pattern 12: Quality Gate for Map Output

Validate map node outputs with LLM-as-judge review, filter failures, and optionally retry.

### Problem

Map nodes generate N items in parallel, but quality varies. Without validation:
- Low-quality items silently pass through
- No retry mechanism for failures
- No aggregate quality metrics

Only ~6% of YAMLGraph pipelines have quality gates. The pattern should be standard.

### Solution: Generate → Review → Filter

Three-stage pipeline with explicit wiring:

```yaml
version: "1.0"
name: quality-gate-pattern

nodes:
  # Stage 1: Generate all items
  generate_all:
    type: map
    source: topics
    prompt: generate_lesson
    state_key: lessons
    flatten_output: true  # FR-052: simplifies downstream processing

  # Stage 2: Review each item with LLM-as-judge
  review_all:
    type: map
    source: lessons
    prompt: review_lesson
    state_key: reviews
    flatten_output: true

  # Stage 3: Filter by score threshold
  filter_passed:
    type: python
    tool: filter_by_score
    state_key: passed_lessons

  # Stage 4: Report quality metrics
  report_quality:
    type: python
    tool: quality_report
    state_key: quality_summary

edges:
  - from: START
    to: generate_all
  - from: generate_all
    to: review_all
  - from: review_all
    to: filter_passed
  - from: filter_passed
    to: report_quality
  - from: report_quality
    to: END
```

### Review Prompt Schema

Standard schema for LLM-as-judge:

```yaml
# prompts/review_lesson.yaml
schema:
  name: ReviewResult
  fields:
    score:
      type: float
      description: "Quality score 0.0-1.0"
      constraints:
        ge: 0.0
        le: 1.0
    passed:
      type: bool
      description: "Meets quality threshold (score >= 0.7)"
    issues:
      type: list[str]
      description: "Specific issues found"
    suggestions:
      type: list[str]
      description: "Improvement suggestions"

system: |
  You are a quality reviewer. Evaluate the lesson content.
  Score 0.7+ means acceptable quality.

user: |
  Review this lesson:

  Title: {{ title }}
  Content: {{ content }}

  Evaluate for:
  - Accuracy and correctness
  - Clarity and structure
  - Completeness
```

### Filter Tool Implementation

With `flatten_output: true`, the filter tool is simpler — no `get_map_result()` unwrapping needed:

```python
# nodes/quality_tools.py

def filter_by_score(state: dict) -> dict:
    """Filter items by review score threshold."""
    reviews = state.get("reviews", [])
    lessons = state.get("lessons", [])
    threshold = state.get("quality_threshold", 0.7)

    passed = []
    failed = []

    for i, review in enumerate(reviews):
        lesson = lessons[i] if i < len(lessons) else None
        # With flatten_output: true, score is at top level
        score = review.get("score", 0)

        if score >= threshold:
            passed.append({"lesson": lesson, "review": review})
        else:
            failed.append({"lesson": lesson, "review": review})

    return {
        "passed_lessons": passed,
        "failed_lessons": failed,
        "pass_count": len(passed),
        "fail_count": len(failed),
    }


def quality_report(state: dict) -> dict:
    """Generate quality summary."""
    pass_count = state.get("pass_count", 0)
    fail_count = state.get("fail_count", 0)
    total = pass_count + fail_count

    return {
        "quality_summary": {
            "total": total,
            "passed": pass_count,
            "failed": fail_count,
            "pass_rate": pass_count / total if total > 0 else 0,
        }
    }
```

### With Retry Loop

Add retry for failed items:

```yaml
nodes:
  # ... generate_all, review_all, filter_passed as above ...

  # Retry failed items (up to 2 times)
  retry_failed:
    type: map
    source: failed_lessons
    prompt: regenerate_lesson    # Include feedback from review
    state_key: retry_results
    condition: fail_count > 0    # Only if failures exist

  review_retries:
    type: map
    source: retry_results
    prompt: review_lesson
    state_key: retry_reviews
    condition: fail_count > 0

  merge_results:
    type: python
    tool: merge_passed_and_retried
    state_key: final_lessons

edges:
  - from: filter_passed
    to: retry_failed
    condition: fail_count > 0
  - from: filter_passed
    to: report_quality
    condition: fail_count == 0
  - from: retry_failed
    to: review_retries
  - from: review_retries
    to: merge_results
  - from: merge_results
    to: report_quality

loop_limits:
  retry_failed: 2    # Max 2 retry attempts
```

### Key Points

| Aspect | Recommendation |
|--------|----------------|
| **Review schema** | Standardize on `score`, `passed`, `issues` fields |
| **Threshold** | 0.7 is reasonable default; tune per use case |
| **Retry limit** | 2-3 attempts max; diminishing returns after |
| **Cost** | Flash-tier review costs ~$0.001/item |
| **Parallelism** | Generate and review maps run in parallel |

### When to Use

| Scenario | Quality Gate? |
|----------|---------------|
| One-off generation | Optional |
| Production pipeline | **Recommended** |
| User-facing content | **Required** |
| Internal analysis | Optional |
| High-stakes output | **Required** with human review |

### Anti-Patterns

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Review inside generation | Separate generate and review stages |
| Silent filter (no report) | Always emit quality metrics |
| Infinite retry loop | Use `loop_limits` |
| Review without schema | Use structured `ReviewResult` |
| Trust LLM unconditionally | Add quality gate for production |

### Related

- [Pattern 3: Self-Correction Loop](patterns.md#pattern-3-self-correction-loop-reflexion) — Single-item refinement
- [Pattern 8: Parallel Fan-Out](patterns.md#pattern-8-parallel-fan-out-map) — Map node basics
- [FR-052: Map Output Flattening](../feature-requests/052-map-output-flattening.md) — `flatten_output: true` simplifies downstream processing
- [map-nodes.md](map-nodes.md#output-flattening-fr-052) — Output flattening documentation

---

## Pattern 13: Monitoring No-Op Pipelines

Pipelines with conditional routing can silently produce no useful output (e.g., "no relevant articles today"). This is operationally valid but can mask failures.

### Problem

A scheduled pipeline runs daily but produces nothing for a week. Is this:
- **Expected** — Quiet news week, nothing relevant
- **Broken** — Filter threshold too high, API failing silently

You need to detect consecutive no-op runs without embedding monitoring logic in the graph itself.

### Solution: External Canary Checks

Keep monitoring concerns outside the graph. Three approaches:

#### 1. Shell Wrapper (Simplest)

```bash
#!/bin/bash
# run_with_canary.sh

OUTPUT_FILE="/path/to/diary.md"
LAST_MODIFIED_BEFORE=$(stat -f %m "$OUTPUT_FILE" 2>/dev/null || echo 0)

yamlgraph graph run graphs/diary_digest.yaml

LAST_MODIFIED_AFTER=$(stat -f %m "$OUTPUT_FILE" 2>/dev/null || echo 0)

if [ "$LAST_MODIFIED_BEFORE" = "$LAST_MODIFIED_AFTER" ]; then
    echo "$(date): No output produced" >> /var/log/yamlgraph_noop.log

    # Alert after N consecutive no-ops
    NOOP_COUNT=$(tail -7 /var/log/yamlgraph_noop.log | grep -c "No output")
    if [ "$NOOP_COUNT" -ge 7 ]; then
        # Send alert (email, Slack, etc.)
        echo "ALERT: 7 consecutive no-op runs" | mail -s "Pipeline Alert" ops@example.com
    fi
fi
```

#### 2. Git-Based Detection

For pipelines that commit outputs:

```bash
#!/bin/bash
# Check if last N commits touched the output file

OUTPUT_FILE="docs/diary.md"
DAYS_TO_CHECK=7

LAST_TOUCH=$(git log -1 --format="%ci" -- "$OUTPUT_FILE" 2>/dev/null)

if [ -z "$LAST_TOUCH" ]; then
    echo "WARNING: Output file never committed"
    exit 1
fi

DAYS_SINCE=$(( ($(date +%s) - $(date -j -f "%Y-%m-%d" "${LAST_TOUCH:0:10}" +%s)) / 86400 ))

if [ "$DAYS_SINCE" -gt "$DAYS_TO_CHECK" ]; then
    echo "ALERT: No output for $DAYS_SINCE days (threshold: $DAYS_TO_CHECK)"
fi
```

#### 3. LangSmith Dashboard

Use LangSmith's built-in analytics:

1. **Tag runs** with outcome: Add `tags: ["output:yes"]` or `tags: ["output:no"]` based on result
2. **Dashboard filter**: Create view showing runs tagged `output:no`
3. **Alert rule**: Trigger when `output:no` count exceeds threshold in time window

```python
# In your runner script
from langsmith import Client

client = Client()

# After graph execution
output_produced = bool(state.get("diary_entry"))
tag = "output:yes" if output_produced else "output:no"

# LangSmith auto-tags if LANGCHAIN_TAGS env var is set
# Or manually tag via run metadata
```

### launchd Integration (macOS)

For scheduled pipelines using launchd:

```xml
<!-- com.yamlgraph.diary-digest.plist -->
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yamlgraph.diary-digest</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/run_with_canary.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardErrorPath</key>
    <string>/var/log/yamlgraph/diary-digest.err</string>
    <key>StandardOutPath</key>
    <string>/var/log/yamlgraph/diary-digest.log</string>
</dict>
</plist>
```

### Key Points

| Aspect | Recommendation |
|--------|----------------|
| **Location** | Outside the graph (shell, cron, monitoring system) |
| **Detection** | File modification, git history, or LangSmith tags |
| **Alerting** | After N consecutive no-ops, not on first occurrence |
| **Threshold** | Depends on pipeline frequency (daily=7, hourly=24) |

### Why Not In-Graph?

1. **Separation of concerns** — Graph defines _what_, monitoring defines _when to alert_
2. **No state pollution** — Graph state shouldn't track historical run outcomes
3. **Flexibility** — Different environments need different alerting (dev vs prod)
4. **Testability** — Graph tests shouldn't depend on monitoring logic

### Related

- [FR-051: Output Shape Contracts](../feature-requests/051-output-shape-contracts.md) — In-graph validation (complementary)
- [reference/scheduling-agents.md](scheduling-agents.md) — launchd setup guide

---

## Pattern 14: Boundary Coercion (Trust No Provider's Type)

Normalize structured values **at the boundary where they enter your code**, not
downstream where the mismatch manifests (FR-059, "the one law").

### Problem

An `llm` node stores the executor's *dynamically built* schema instance — a class
distinct from your own model despite sharing a name. So a downstream reducer that
calls `MyModel.model_validate(that_instance)` rejects it. The same boundary appears
wherever a value might arrive as **either** a Pydantic instance **or** a plain dict
(map collection, guard rules, FSM state, serialization).

### The family of coercions (name the seam, don't unify it)

There is no single "coerce" helper, because the correct behavior depends on the
seam. Pick the variant deliberately:

| Variant | Junk / scalar handling | Use when |
|---------|------------------------|----------|
| **dict-or-empty** | non-dict → `{}` | A reducer needs a dict to validate; junk should vanish |
| **dict-or-None** | non-dict → `None`, guarded by `if d is not None` | Absence is meaningful (skip vs. empty) |
| **scalar-preserving** | scalar wrapped as `{"value": x}` or original kept | Map collection must not lose non-dict sub-node returns |
| **recursive serialize** | primitives pass through, recurse into lists/dicts | Making a whole tree JSON-safe (`to_serializable`, `json_safe`) |
| **exclude-none rule dict** | `model_dump(exclude_none=True)` | Optional fields must not appear as `null` keys |

### Example: dict-or-empty (the reducer boundary)

```python
def _as_dict(value: object) -> dict:
    """Collapse an LLM-node output to a plain dict before validating (FR-059).

    The executor's dynamically built schema instance is a foreign class; collapse
    to a dict first so MyModel.model_validate() accepts it. Map nodes already emit
    dicts, so they pass through unchanged.
    """
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}  # junk swallowed at the boundary
```

### Key Points

| Aspect | Recommendation |
|--------|----------------|
| **Where** | At the entry boundary (reducer input, state read), not at the symptom |
| **Detection signal** | `hasattr(x, "model_dump")` — a Pydantic-or-dict seam |
| **Do not over-unify** | The variants above have *different* contracts; a single shared helper silently corrupts one caller to serve another (scalar→`{}` loses data; `str`→`{}` breaks recursion) |
| **Keep example-local** | Until ≥3 examples reinvent the *exact same* variant, keep the helper local — it is application glue, not framework infrastructure |

### Why Not a Core `as_dict()` Utility?

This was evaluated (FR-549, **rejected**). Auditing the `hasattr(x, "model_dump")`
callsites in core showed they are **not** semantic duplicates — `map_compiler`
preserves scalars, `fsm/helpers` returns `None`, `guard_runtime` uses
`exclude_none`, `json_safe` recurses. Collapsing them into one function would
introduce bugs, not remove duplication. The reusable artifact is **this pattern
note**, not a shared function. (Compare `to_serializable()` in
[contrib/utils.py](../yamlgraph/contrib/utils.py) — the recursive-serialize variant,
already provided for that specific seam.)

### Related

- FR-059 (Trust No Provider's Type) — the boundary law
- `the_one_law` / `false_duplicate` in `.github/copilot-instructions.md`
- [contrib/utils.py](../yamlgraph/contrib/utils.py) `to_serializable()` — recursive variant
