---
name: author-prompt
description: "Author YAMLGraph prompt YAML files. Use when: writing prompt templates, configuring inline schemas or output_schema, using Jinja2 templates, adding system/user messages, defining structured output fields, or using system_segments for prompt caching."
argument-hint: "prompt field, schema type, or 'Jinja2'"
---

# Author Prompt YAML

Create and configure YAMLGraph prompt files in `prompts/`. Canonical source: `reference/prompt-yaml.md`.

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

1. **Always include `description`** on schema fields — guides the LLM
2. **Use constraints** for bounded values (`ge`, `le`)
3. **Default empty lists** — `default: []` prevents null issues
4. **Keep system messages focused** — role + task + guidelines
5. **Use Jinja2 only when needed** — simple `{var}` suffices for most cases
