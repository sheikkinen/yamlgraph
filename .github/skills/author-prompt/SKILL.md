---
name: author-prompt
description: "Author YAMLGraph prompt YAML files. Use when: writing prompt templates, configuring inline schemas or output_schema, using Jinja2 templates, adding system/user messages, defining structured output fields, or using system_segments for prompt caching."
argument-hint: "prompt field, schema type, or 'Jinja2'"
---

# Author Prompt YAML

Create and configure YAMLGraph prompt files in `prompts/`. Canonical source: `reference/prompt-yaml.md`.

## One prompt = one subagent brief (read this first)

A prompt is a brief handed to a worker who **cannot push back, ask a clarifying question, or remember its prior calls.** That makes contract discipline *more* essential for a prompt than for a subagent, not less. Every fused responsibility and ambiguity is absorbed silently and degrades the output silently.

The project learned this the expensive way: four feature requests (FR-581–585) failed to lift a prompt's precision by *rewording* a single call that spanned **ten abstraction levels** (comprehend → causal → temporal-delta → salience → ontology → theory-of-mind → token-fidelity → serialization → self-correct). Rewording only shuffles load between levels; it never removes one. The fix was a **pipeline split** (FR-587): one node comprehends, code does the bookkeeping.

**The prompt contract (5 clauses):**

1. **One judgement / one abstraction level** — comprehension XOR encoding, not both.
2. **Closed inputs** — pass only the state the task needs (see the K4 scope gate in `examples/book_reviewer`).
3. **One output shape, fully validator-covered** — if the validator can't check a job, don't trust the model to do it alone. The uncovered fraction is where output floods.
4. **Stateless** — never "reuse the earlier token / remember what an earlier call did." A per-unit LLM call is stateless across units; externalize cross-unit state into the inputs or into **code**.
5. **Bounded** — explicit "do X, **not** Y" (e.g. "do not also serialize / self-correct your prior output").

**The rule:** if a prompt spans abstraction levels, it is a **pipeline to split, not a prompt to tune.** Move the mechanizable levels (delta, salience, serialization, cross-unit constraints) into code; leave the model one judgement. Two enforced invariants from FR-497: *no LLM call sees the whole corpus; no LLM emits a number* — numbers come from a deterministic reduce.

**Enforcement:** the `W026` lint rule ([yamlgraph/linter/checks_prompts.py](../../../yamlgraph/linter/checks_prompts.py)) flags prompts that fuse too many judgements — by inline-schema field count (≥ 4 top-level output fields) or curated multi-output / global-constraint prose phrases. [examples/abstraction_span](../../../examples/abstraction_span) is the calibration harness. Run `yamlgraph graph lint <graph>` and treat a W026 as a split signal, not a nuisance.

## File Structure

```yaml
# Schema for structured output (pick one format)
schema:
  name: OutputModel
  fields:
    field_name:
      type: str
      description: "Field description"

# System message (required)
system: |
  You are a helpful assistant...

# User message — simple substitution
user: |
  Process: {input}

# OR: Jinja2 template (auto-detected when {{ or {% present)
template: |
  {% for item in items %}
  {{ item.name }}
  {% endfor %}
```

## System Message

```yaml
system: |
  You are a [specific role].
  Your task is to [specific task].
  Guidelines:
  - Guideline 1
  - Guideline 2
```

### System Segments (Prompt Caching)

For Anthropic prompt caching optimization:

```yaml
system_segments:
  - content: |
      [Large stable context...]
    cache: true
  - content: |
      Current task: {task_description}
    cache: false
```

Other providers: cache flags ignored, segments flattened.

## User Message vs Template

**Simple substitution** — use `user:`:
```yaml
user: |
  Write about: {topic}
  Style: {style}
```

**Loops/conditionals** — use `template:` (Jinja2):
```yaml
template: |
  {% for item in items %}
  ### {{ loop.index }}. {{ item.title }}
  {% if item.tags %}Tags: {{ item.tags | join(", ") }}{% endif %}
  {% endfor %}
```

Jinja2 activates automatically when `{{` or `{%` appear in `system` or `user` too.

### Jinja2 Features

| Feature | Syntax |
|---------|--------|
| Variable | `{{ topic }}` |
| Loop | `{% for x in items %}...{% endfor %}` |
| Conditional | `{% if score > 0.8 %}...{% endif %}` |
| Filter | `{{ tags \| join(", ") }}` |
| Slice | `{{ content[:200] }}` |
| Default | `{{ val \| default("N/A") }}` |

Loop context: `loop.index` (1-based), `loop.index0`, `loop.first`, `loop.last`, `loop.length`.

## Inline Schema (Native Format)

Define structured output directly in the prompt:

```yaml
schema:
  name: Analysis
  fields:
    summary:
      type: str
      description: "Brief summary"
    score:
      type: float
      description: "Confidence 0-1"
      constraints:
        ge: 0.0
        le: 1.0
    tags:
      type: list[str]
      description: "Tags"
      default: []
    notes:
      type: str
      description: "Optional notes"
      optional: true
```

### Supported Types

| Type | Python | Example |
|------|--------|---------|
| `str` | `str` | `"hello"` |
| `int` | `int` | `42` |
| `float` | `float` | `0.95` |
| `bool` | `bool` | `true` |
| `list[str]` | `list[str]` | `["a", "b"]` |
| `list[int]` | `list[int]` | `[1, 2]` |
| `dict[str, str]` | `dict[str, str]` | `{"k": "v"}` |
| `dict[str, Any]` | `dict[str, Any]` | `{"k": ...}` |
| `Any` | `Any` | anything |

### Constraints

| Constraint | Types | Description |
|------------|-------|-------------|
| `ge` / `le` | int/float | Greater/less than or equal |
| `gt` / `lt` | int/float | Greater/less than |
| `min_length` / `max_length` | str/list | Length bounds |
| `pattern` | str | Regex pattern |

## JSON Schema Format (Alternative)

Use `output_schema:` instead of `schema:` for JSON Schema syntax:

```yaml
output_schema:
  type: object
  properties:
    sentiment:
      type: string
      enum: [positive, negative, neutral]
    themes:
      type: array
      items: { type: string }
  required: [sentiment, themes]
```

Both formats produce identical Pydantic models at runtime. `schema:` is better for constraints (ge/le), `output_schema:` for enums.

## Complete Example

```yaml
schema:
  name: GeneratedContent
  fields:
    title: { type: str, description: "Title" }
    content: { type: str, description: "Main text" }
    tags: { type: list[str], default: [] }

system: |
  You are a content writer.
user: |
  Write about: {topic}
  Style: {style}
```

## Best Practices

1. **One judgement per prompt** — honor the prompt contract above; a prompt spanning abstraction levels is a pipeline to split (W026), not a prompt to tune
2. **Always include `description`** on schema fields — guides the LLM
3. **Use constraints** for bounded values (`ge`, `le`)
4. **Default empty lists** — `default: []` prevents null issues
5. **Keep system messages focused** — role + task + guidelines
6. **Use Jinja2 only when needed** — simple `{var}` suffices for most cases
