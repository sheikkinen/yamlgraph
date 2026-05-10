# Promptfoo Evaluation Pattern

> **Systematic LLM prompt evaluation using [Promptfoo](https://www.promptfoo.dev/) — deterministic assertions and LLM-as-judge rubrics, without changing your graph.**

Two complementary strategies are supported. Use them independently or together.

---

## Strategies at a Glance

| | Strategy A — Graph Evaluation | Strategy B — Prompt Isolation |
|-|-------------------------------|-------------------------------|
| **Entry point** | `invoke_graph()` | `execute_prompt()` |
| **What's tested** | Full pipeline (routing, state, edges) | Individual prompt quality |
| **Assertions** | Combined output shape | Field-level JSON, rubric per prompt |
| **Speed** | Slower (full graph run) | Fast (one LLM call per test) |
| **Best for** | End-to-end routing demos | Production prompt regression suites |
| **Demo** | `examples/demos/promptfoo-router/` | `projects/ninchat_voice/evaluations/` |

---

## Prerequisites

```bash
# Node.js (Promptfoo)
npm install -g promptfoo     # or use npx promptfoo eval

# YAMLGraph installed
pip install -e ".[dev]"

# LLM API key
export OPENAI_API_KEY=...    # or ANTHROPIC_API_KEY, AZURE credentials
```

---

## Strategy A — Graph Evaluation

Invoke the full graph; assert on the final combined output.

### File Structure

```
my-demo/
├── graph.yaml
├── prompts/
├── provider.py          ← Promptfoo Python provider
├── promptfooconfig.yaml
└── tests/
    └── classification.yaml
```

### `provider.py`

```python
"""Promptfoo Python provider — full graph evaluation."""

from yamlgraph.graph_loader import invoke_graph


def call_api(prompt, options, context):
    config = options.get("config", {})
    graph_path = config.get("graph", "graph.yaml")
    output_key = config.get("output_key", "response")
    variables = context.get("vars", {})

    result = invoke_graph(graph_path, variables)

    # Combine state fields into a single string for assertion
    parts = []
    if "classification" in result:
        parts.append(f"TONE: {result['classification']}")
    if output_key in result:
        parts.append(f"RESPONSE: {result[output_key]}")

    return {
        "output": "\n".join(parts),
        "metadata": {"graph": graph_path},
    }
```

### `promptfooconfig.yaml`

```yaml
description: "My Graph — End-to-End Evaluation"

providers:
  - id: "file://provider.py"
    label: "my-graph"
    config:
      graph: graph.yaml
      output_key: response

prompts:
  - "{{message}}"   # Pass-through; actual prompts are inside the graph

defaultTest:
  options:
    provider: "openai:chat:gpt-4o-mini"   # LLM-as-judge grader

tests: tests/*.yaml
```

### Test Cases (`tests/classification.yaml`)

```yaml
- description: Enthusiastic praise classifies as positive
  vars:
    message: "I absolutely love this product!"
  assert:
    - type: icontains
      value: "TONE: positive"

- description: Complaint classifies as negative
  vars:
    message: "This is broken again. Worst service ever."
  assert:
    - type: icontains
      value: "TONE: negative"

- description: Response is warm for positive tone
  vars:
    message: "Your team was incredibly helpful!"
  assert:
    - type: icontains
      value: "TONE: positive"
    - type: llm-rubric
      value: "The RESPONSE is warm and enthusiastic, matching the positive input"
```

---

## Strategy B — Prompt Isolation

**This is the production-grade pattern.** Call `execute_prompt()` directly to test individual prompts in isolation — bypassing graph orchestration entirely.

### Why Prompt Isolation

- Regressions after model upgrades or prompt edits are caught before they reach production
- Tests run fast — one LLM call per assertion
- Domain-specific test data (e.g., Finnish medical language) can be injected precisely
- Schema fixtures are frozen — schema drift immediately breaks tests, not production calls

### File Structure

```
evaluations/
└── my_graph/
    ├── provider.py              ← Calls execute_prompt()
    ├── promptfooconfig.yaml
    ├── run-eval.sh              ← Activates venv, sources .env, runs npx promptfoo eval
    ├── fixtures/
    │   └── schema.json          ← Frozen copy of schema.yaml for test reproducibility
    └── tests/
        ├── extraction.yaml      ← Structured field extraction accuracy
        ├── probe-quality.yaml   ← Follow-up question naturalness (llm-rubric)
        ├── recap-quality.yaml   ← Summary naturalness (llm-rubric)
        └── recap-classify.yaml  ← Classification routing (deterministic)
```

### `provider.py`

```python
"""Promptfoo provider for prompt-level evaluation."""

import json
from pathlib import Path

from yamlgraph.executor import execute_prompt

# Point at the graph's own prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "graphs" / "my_graph" / "prompts"

# Load frozen schema fixture once at import time
SCHEMA = json.loads((Path(__file__).parent / "fixtures" / "schema.json").read_text())


def call_api(prompt, options, context):
    config = options.get("config", {})
    provider = config.get("provider", "openai")
    model = config.get("model", "gpt-4o-mini")
    variables = context.get("vars", {})

    # Prompt name comes from test var "prompt", fallback to provider config
    prompt_name = variables.pop("prompt", None) or config["prompt"]

    # Inject frozen schema so tests are independent of live schema.yaml
    variables["schema"] = SCHEMA

    # YAML test vars are strings; parse JSON-encoded objects back to dicts/lists
    for key in ("messages", "extracted", "gaps"):
        if key in variables and isinstance(variables[key], str):
            variables[key] = json.loads(variables[key])

    result = execute_prompt(
        prompt_name,
        variables=variables,
        provider=provider,
        model=model,
        prompts_dir=PROMPTS_DIR,
    )

    return {
        "output": result if isinstance(result, str) else json.dumps(result),
        "metadata": {"prompt": prompt_name, "provider": provider},
    }
```

### `promptfooconfig.yaml`

```yaml
description: "My Graph — Prompt Quality Evaluation"

providers:
  - id: "file://provider.py"
    label: "my_graph"
    config:
      provider: openai
      model: gpt-4o-mini

prompts:
  - "{{prompt}}"   # Prompt name is passed via test vars

defaultTest:
  options:
    provider: "openai:chat:gpt-4o-mini"   # LLM-as-judge grader

tests:
  - tests/extraction.yaml
  - tests/probe-quality.yaml
  - tests/recap-quality.yaml
  - tests/recap-classify.yaml
```

### `run-eval.sh`

```bash
#!/usr/bin/env bash
# Run promptfoo evaluation for my_graph prompts.
# Usage: ./run-eval.sh [--no-cache] [extra promptfoo args...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$SCRIPT_DIR"

source "$PROJECT_DIR/../../.venv/bin/activate"

set -a
source "$PROJECT_DIR/.env"
set +a

exec npx promptfoo eval "$@"
```

### Test Case Examples

#### Extraction — Deterministic (`tests/extraction.yaml`)

Test that structured fields are correctly extracted from free-form conversation.

```yaml
- description: Name extracted from greeting
  vars:
    prompt: extract_fields
    messages: '[{"role": "user", "content": "Hi, I''m Jane Smith from Acme Corp"}]'
    extracted: '{}'
  assert:
    - type: javascript
      value: "JSON.parse(output).name === 'Jane Smith'"

- description: Existing fields preserved when new info added
  vars:
    prompt: extract_fields
    messages: '[{"role": "user", "content": "Our org is Acme Corp"}]'
    extracted: '{"name": "Jane Smith"}'
  assert:
    - type: javascript
      value: "JSON.parse(output).name === 'Jane Smith'"
    - type: javascript
      value: "JSON.parse(output).organization !== null"

- description: Null for unmentioned fields
  vars:
    prompt: extract_fields
    messages: '[{"role": "user", "content": "Hi, I''m Jane"}]'
    extracted: '{}'
  assert:
    - type: javascript
      value: "let r = JSON.parse(output); r.name !== null && r.organization === null"
```

#### Response Quality — LLM-as-Judge (`tests/probe-quality.yaml`)

Test that generated follow-up questions are natural and relevant.

```yaml
- description: Asks for missing required field
  vars:
    prompt: generate_probe
    extracted: '{"name": null, "organization": null}'
    gaps: '["name", "organization"]'
  assert:
    - type: llm-rubric
      value: "The response is a natural, conversational question. It asks for the caller's name."

- description: References known fields when asking for missing ones
  vars:
    prompt: generate_probe
    extracted: '{"name": "Jane Smith", "organization": null}'
    gaps: '["organization"]'
  assert:
    - type: llm-rubric
      value: "The response references Jane by name and asks about her organization."
```

#### Classification Routing — Deterministic (`tests/recap-classify.yaml`)

Always use deterministic assertions for routing decisions — never `llm-rubric`.

```yaml
- description: Confirmation routes to confirm
  vars:
    prompt: classify_recap
    user_response: "Yes, that's all correct"
  assert:
    - type: javascript
      value: "JSON.parse(output).action_type === 'confirm'"

- description: Correction routes to correct
  vars:
    prompt: classify_recap
    user_response: "No, the organization is wrong — it's Globex, not Acme"
  assert:
    - type: javascript
      value: "let r = JSON.parse(output); r.action_type === 'correct' && r.corrections"
```

> **Safety-critical classifiers must never use `llm-rubric`.** If a misclassification can cause harm (e.g., crisis detection, medical routing), use `type: javascript` assertions only. A flaky LLM judge on a life-safety assertion is unacceptable.

---

## Freezing Schema Fixtures

Schema drift is a silent regression risk. Freeze your schema at evaluation time so tests break when the schema changes — not when production calls fail.

```bash
# Generate fixtures/schema.json from your graph's schema.yaml
python -c "
import yaml, json
schema = yaml.safe_load(open('graphs/my_graph/schema.yaml'))
print(json.dumps(schema, ensure_ascii=False, indent=2))
" > evaluations/my_graph/fixtures/schema.json
```

Add the fixture to version control. When `schema.yaml` changes, regenerate and commit the fixture — the diff is the audit trail.

---

## Running Evaluations

```bash
# From the eval directory
cd evaluations/my_graph
./run-eval.sh

# With options
./run-eval.sh --no-cache
./run-eval.sh --verbose

# View results in the web UI
npx promptfoo view
```

---

## Assertion Type Reference

| Type | When to use |
|------|-------------|
| `icontains` | Case-insensitive substring match — routing labels, keywords |
| `javascript` | Deterministic logic — JSON field checks, routing decisions, safety-critical paths |
| `llm-rubric` | Subjective quality — naturalness, tone, helpfulness. **Never for safety-critical paths** |
| `not-icontains` | Assert absence — no markdown bullets in spoken text, no error strings |
| `regex` | Pattern match — formats, codes |

---

## Provider Override

Run the same tests against a different model without changing test files:

```bash
PROVIDER=anthropic npx promptfoo eval
```

Or compare models side by side using Promptfoo's built-in comparison:

```yaml
# promptfooconfig.yaml
providers:
  - id: "file://provider.py"
    config: {provider: openai, model: gpt-4o-mini}
  - id: "file://provider.py"
    config: {provider: anthropic, model: claude-haiku-4-5}
```

---

## What to Test Per Graph

For graphs using the [Probe-Recap Questionnaire Pattern](probe-recap-questionnaire.md), four test files cover the full prompt surface:

| File | Focus | Assertion type |
|------|-------|----------------|
| `extraction.yaml` | Structured field extraction accuracy | `javascript` (deterministic) |
| `probe-quality.yaml` | Follow-up question naturalness | `llm-rubric` |
| `recap-quality.yaml` | Summary naturalness and completeness | `llm-rubric` + `not-icontains` |
| `recap-classify.yaml` | Action routing (confirm/correct/clarify) | `javascript` (deterministic) |

For routing/classification graphs, one file per decision point — always deterministic.

---

## See Also

- **Demo**: [`examples/demos/promptfoo-router/`](../examples/demos/promptfoo-router/) — Strategy A end-to-end
- **Production example**: `projects/ninchat_voice/evaluations/` — Strategy B, 7 suites, 70+ Finnish medical test cases
- [`probe-recap-questionnaire.md`](probe-recap-questionnaire.md) — the graph pattern these evals test
- [`prompt-yaml.md`](prompt-yaml.md) — YAML prompt authoring reference
- [Promptfoo docs](https://www.promptfoo.dev/docs/) — full assertion library, CI integration
