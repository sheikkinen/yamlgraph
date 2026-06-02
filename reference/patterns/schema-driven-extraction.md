# Schema-Driven Extraction Pattern

A **declarative convergence loop** for collecting structured data through conversation. Define the target shape (schema), observe the current shape (extract), compute the delta (detect gaps), reduce the delta (probe), and verify convergence (recap).

No new framework node type, action type, or primitive is required. Compose existing YAMLGraph primitives (`data_files` + `llm` + `interrupt` + `python` tools + conditional edges).

## The Loop

```
Define target shape (schema)
  → Observe current shape (extract)
    → Compute delta (detect_gaps)
      → Reduce delta (probe + interrupt)
        → Converged? ──NO──→ extract again
                      │
                      YES
                      ↓
                    Verify (recap + interrupt)
                      → Deliver (save / send)
```

This is the same structure as:
- **Terraform plan/apply** — desired state → current state → diff → apply → verify
- **PID controller** — setpoint → measurement → error → correction → measure again
- **TDD** — spec (red) → implement (green) → verify (refactor)

## Minimal Graph Structure

```yaml
data_files:
  schema: schema.yaml      # Target shape

nodes:
  extract:
    type: llm
    prompt: extract         # Jinja2 iterates schema.fields
    parse_json: true
    variables:
      schema: "{state.schema}"
      messages: "{state.messages}"
      extracted: "{state.extracted}"
    state_key: extracted

  detect_gaps:
    type: python
    tool: detect_gaps       # set(required) - set(extracted.keys())

  probe:
    type: llm
    prompt: probe
    variables:
      gaps: "{state.gaps}"
    state_key: response

  ask_probe:
    type: interrupt
    message: "{response}"
    resume_key: user_message

edges:
  - from: extract
    to: detect_gaps
  - from: detect_gaps
    to: probe
    condition: "has_gaps == true"
  - from: detect_gaps
    to: recap           # converged
    condition: "has_gaps == false"
  - from: probe
    to: ask_probe
  - from: ask_probe
    to: extract          # loop back
```

## The Schema File

A YAML file loaded via `data_files:`. Available in prompts as `{{ schema }}` and in Python tools via `state["schema"]`.

```yaml
name: intake-form
description: Collect patient callback information

fields:
  - id: chief_complaint
    description: Primary reason for the call
    required: true
    type: string

  - id: duration
    description: How long has the issue persisted?
    required: true
    type: string

  - id: medications
    description: Current medications
    required: false
    type: string
```

Optional schema features used in production:
- **`coding:`** — allowed values with descriptions (e.g., `low: "Not urgent"`)
- **`groups:`** — organize fields for recap display
- **`topic:`** — tag fields for multi-schema merging (flex_navigator)

## The Extraction Prompt

The prompt template iterates `schema.fields` via Jinja2 to build the LLM's extraction target dynamically:

```yaml
# prompts/extract.yaml
system: |
  Extract structured fields from the conversation.
  Fields:
  {% for field in schema.fields %}
  - {{ field.id }}: {{ field.description }}
  {% endfor %}

  Return ALL fields every time. Use null for unknown fields.

user: |
  Previously extracted:
  {% for key, value in extracted.items() %}
  - {{ key }}: {{ value if value else "null" }}
  {% endfor %}

  Conversation:
  {% for msg in messages %}
  {{ msg.role }}: {{ msg.content }}
  {% endfor %}

  Return JSON:
  { {% for field in schema.fields %}
    "{{ field.id }}": "value or null"{% if not loop.last %},{% endif %}
  {% endfor %} }
```

Key constraint: `parse_json: true` on the LLM node. The output is a plain dict, not a Pydantic model — the schema drives the prompt, not the type system.

## The Gap Detector

A Python tool (~15 lines) that computes `required_fields - extracted_keys`:

```python
def detect_gaps(state: dict) -> dict:
    schema = state.get("schema", {})
    extracted = state.get("extracted", {})
    fields = schema.get("fields", [])

    required_ids = {f["id"] for f in fields if f.get("required")}
    filled_ids = {k for k, v in extracted.items() if v is not None}
    gaps = sorted(required_ids - filled_ids)

    return {"gaps": gaps, "has_gaps": bool(gaps)}
```

## Scaling Dimensions

### Multi-Schema (additive merging)

When a conversation covers multiple topics, load and merge schemas dynamically:

```python
# Load schemas for newly detected topics, skip already loaded
for topic in new_topics:
    schema_data = load_yaml(SCHEMA_MAP[topic])
    for field in schema_data["fields"]:
        if field["id"] not in existing_ids:
            merged_fields.append({**field, "topic": topic})
```

Common fields (e.g., `patient_name`) are tagged `topic: _common` and deduplicated. Gap detection and probing work unchanged — they only see the merged field list.

### Multi-Provider (race candidates)

Use `type: race` with `candidates:` for extraction and probe nodes to get the fastest response from multiple LLM providers:

```yaml
extract_fields:
  type: race
  prompt: extract
  parse_json: true
  candidates:
    - { provider: vertex, model: gemini-2.5-flash }
    - { provider: azure,  model: gpt-4o-mini }
```

### Boundary Guard

LLM JSON output is not guaranteed to be a dict. Add a normalizer between extraction and gap detection:

```python
def normalize_extracted(state: dict) -> dict:
    extracted = state.get("extracted")
    if isinstance(extracted, dict):
        return {}  # no-op, keep current
    return {"extracted": {}}  # coerce non-dict to empty
```

This is `normalize at the boundary` — the LLM is an external system whose output format cannot be trusted.

## When to Use This Pattern

**Good fit:**
- Structured data collection from conversation (intake forms, assessments, config wizards)
- Schema is known at graph compile time (or loadable at init)
- Fields are independently extractable (no complex dependencies between answers)
- Convergence is measurable (required fields filled = done)

**Poor fit:**
- Open-ended exploration (no target shape → no convergence)
- Adversarial extraction (need consistency detection, not gap detection)
- Real-time schema mutation (fields change based on answers — need reactive state, not static schema)
- Single-shot extraction from documents (no probe loop needed — just extract + validate)

## Implementations

| Implementation | Location | Schema | Multi-topic | Transport |
|----------------|----------|--------|------------|-----------|
| **Questionnaire example** | `examples/questionnaire/` | `data_files` | No | CLI interrupt |
| **Flex-Navigator** | `projects/ninchat_voice/graphs/flex_navigator/` | Dynamic merge | Yes | FSM + voice |
| **Interview demo** | `examples/demos/interview/` | Inline | No | CLI interrupt |

The questionnaire example is the canonical reference. The flex_navigator is the production-scale variant with multi-topic merging, race nodes, and FSM integration.

## See Also

- [examples/questionnaire/](../../examples/questionnaire/) — Reference implementation with demo
- [LLM-as-Gate](llm-as-gate.md) — Complementary pattern for semantic validation
- [FSM-as-Conductor](fsm-as-conductor.md) — How the extraction loop integrates with FSM lifecycle
- [Prompt YAML reference](../prompt-yaml.md) — Jinja2 template syntax for schema injection
