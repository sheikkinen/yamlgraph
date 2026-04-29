# Feature Request: Promptfoo Evaluation Demo for Router Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-04-29
**Judged:** 2026-04-29

## Summary

Add a `examples/demos/promptfoo-router/` demo that wraps the existing router demo with a Promptfoo evaluation suite, proving YAMLGraph + Promptfoo integration end-to-end. No YAMLGraph core edits — demo-only, using the Python provider bridge.

## Value Statement

Graph authors get a working reference for LLM output evaluation using Promptfoo, filling the eval gap identified in the ninchat_voice × tt-bot-v2 architecture comparison.

## Problem

YAMLGraph has runtime verification gates (count range, non-empty, contains) but no pre-deployment LLM evaluation framework. The tt-bot-v2 project uses Promptfoo (Node.js) for systematic prompt testing with LLM-as-judge rubrics. There is no example showing how to use Promptfoo with a YAMLGraph graph via the native Python provider bridge.

Key gaps:
1. No reference implementation for `file://provider.py` → YAMLGraph graph invocation
2. No test cases demonstrating deterministic + LLM-as-judge assertions on graph outputs
3. No multi-provider comparison via Promptfoo (complement to `yamlgraph graph bench`)

## Proposed Solution

Create a self-contained demo in `examples/demos/promptfoo-router/` that reuses the existing router graph (symlinked or copied) and adds Promptfoo evaluation infrastructure.

### File Structure

```
examples/demos/promptfoo-router/
├── README.md                     # Setup, usage, what it demonstrates
├── graph.yaml                    # Copy of router graph (self-contained demo)
├── prompts/                      # Copy of router prompts
│   ├── classify_tone.yaml
│   ├── respond_positive.yaml
│   ├── respond_negative.yaml
│   └── respond_neutral.yaml
├── provider.py                   # Promptfoo Python provider bridge
├── promptfooconfig.yaml          # Promptfoo configuration
├── tests/
│   ├── classification.yaml       # Tone classification accuracy tests
│   ├── response-quality.yaml     # Response tone-matching tests
│   └── edge-cases.yaml           # Ambiguous, multilingual, empty input
└── demo-output.log               # Captured demo run output
```

### Python Provider Bridge (`provider.py`)

```python
"""Promptfoo Python provider for YAMLGraph graphs."""

from yamlgraph.graph_loader import invoke_graph


def call_api(prompt, options, context):
    """Promptfoo calls this for each test case."""
    config = options.get("config", {})
    graph_path = config.get("graph", "graph.yaml")
    output_key = config.get("output_key", "response")
    variables = context.get("vars", {})

    result = invoke_graph(graph_path, variables)

    # Return both classification and response for assertion flexibility
    output_parts = []
    if "classification" in result:
        classification = result["classification"]
        output_parts.append(f"TONE: {classification.get('tone', 'unknown')}")
        output_parts.append(f"CONFIDENCE: {classification.get('confidence', 0)}")
    if output_key in result:
        output_parts.append(f"RESPONSE: {result[output_key]}")

    return {
        "output": "\n".join(output_parts),
        "metadata": {
            "classification": result.get("classification"),
            "graph": graph_path,
        },
    }
```

### Promptfoo Config (`promptfooconfig.yaml`)

```yaml
description: "YAMLGraph Router - Tone Classification Evaluation"

providers:
  - id: "file://provider.py"
    label: "YAMLGraph Router"
    config:
      graph: graph.yaml
      output_key: response

prompts:
  - "{{message}}"   # Pass-through; actual prompt is in YAML graph

defaultTest:
  options:
    provider: "openai:chat:gpt-4o-mini"   # LLM-as-judge grader

tests: tests/*.yaml
```

### Test Cases

**`tests/classification.yaml`** — Deterministic tone classification:
```yaml
- description: Enthusiastic praise → positive
  vars:
    message: "I absolutely love this product! Best purchase ever!"
  assert:
    - type: icontains
      value: "TONE: positive"

- description: Angry complaint → negative
  vars:
    message: "This is broken again. Worst service I've ever experienced."
  assert:
    - type: icontains
      value: "TONE: negative"

- description: Factual question → neutral
  vars:
    message: "What are your store hours on Saturday?"
  assert:
    - type: icontains
      value: "TONE: neutral"

- description: Sarcastic praise → negative or neutral
  vars:
    message: "Oh great, another update that breaks everything. Wonderful."
  assert:
    - type: javascript
      value: "output.toLowerCase().includes('tone: negative') || output.toLowerCase().includes('tone: neutral')"

- description: Gratitude → positive
  vars:
    message: "Thank you so much for helping me resolve this quickly!"
  assert:
    - type: icontains
      value: "TONE: positive"
```

**`tests/response-quality.yaml`** — LLM-as-judge on response appropriateness:
```yaml
- description: Positive message gets warm response
  vars:
    message: "Your team was incredibly helpful today!"
  assert:
    - type: icontains
      value: "TONE: positive"
    - type: llm-rubric
      value: "The RESPONSE section is warm, enthusiastic, and matches the positive energy of the input"

- description: Negative message gets empathetic response
  vars:
    message: "I've been waiting 3 hours and nobody has helped me"
  assert:
    - type: icontains
      value: "TONE: negative"
    - type: llm-rubric
      value: "The RESPONSE section acknowledges frustration, shows empathy, and offers to help"

- description: Neutral message gets informative response
  vars:
    message: "Can you tell me about your return policy?"
  assert:
    - type: icontains
      value: "TONE: neutral"
    - type: llm-rubric
      value: "The RESPONSE section is helpful and informative without excessive emotion"
```

**`tests/edge-cases.yaml`** — Boundary conditions:
```yaml
- description: Empty message handled gracefully
  vars:
    message: ""
  assert:
    - type: llm-rubric
      value: "The output does not crash or produce an error; it provides some classification"

- description: Non-English input still classifies
  vars:
    message: "Tämä tuote on aivan mahtava!"
  assert:
    - type: javascript
      value: "output.toLowerCase().includes('tone: positive') || output.toLowerCase().includes('tone: neutral')"

- description: Mixed tone resolves to dominant sentiment
  vars:
    message: "The food was great but the service was terrible and the wait was ridiculous"
  assert:
    - type: javascript
      value: "output.toLowerCase().includes('tone: negative') || output.toLowerCase().includes('tone: neutral')"
    - type: llm-rubric
      value: "The response acknowledges the mixed nature of the feedback"
```

### README.md

Should cover:
1. Prerequisites: `npm install -g promptfoo` (or use `npx promptfoo eval`); `XAI_API_KEY` env var (router graph default provider)
2. Quick start: `cd examples/demos/promptfoo-router && promptfoo eval`
3. View results: `promptfoo view`
4. What it demonstrates (deterministic + LLM-as-judge + edge cases)
5. How to adapt for other YAMLGraph graphs (swap graph path + output_key in config)
6. Provider override: set `PROVIDER` env var to use a different LLM provider

## Acceptance Criteria

- [ ] `examples/demos/promptfoo-router/` directory with all files
- [ ] `provider.py` invokes YAMLGraph graph via `invoke_graph()` and returns Promptfoo-compatible response
- [ ] `promptfooconfig.yaml` configures Python provider and test discovery
- [ ] 3 test files: classification (5+ cases), response quality (3+ with llm-rubric), edge cases (3+)
- [ ] `promptfoo eval` runs successfully and produces results
- [ ] `README.md` with setup, usage, and adaptation instructions
- [ ] `demo-output.log` captured from successful run
- [ ] No changes to YAMLGraph core (`yamlgraph/` directory untouched)

## Alternatives Considered

1. **Promptfoo inside `tests/`** — Rejected: Promptfoo is not pytest; it's a separate eval framework. Belongs in examples as a pattern demo.
2. **Custom eval script** — Rejected: Promptfoo already exists, has web UI, and tt-bot-v2 proves it works. No need to reinvent.
3. **FR-043 (built-in evaluation framework)** — Complementary, not competing. FR-043 adds `--evaluate` CLI flag for inline eval. This FR shows external eval via Promptfoo. Both are useful.
4. **Verification gate demo only** — Rejected as first demo: verification gates are runtime checks, not pre-deployment eval suites. Router classification is more intuitive for Promptfoo because test cases have clear right/wrong answers.

## Related

- `examples/demos/router/` — Source graph being evaluated
- `tt-bot-v2/evaluations/` — Production Promptfoo setup (TypeScript provider)
- `feature-requests/043-evaluation-framework.md` — Built-in YAMLGraph eval (complementary)
- `projects/ninchat_voice/docs/context/tt-bot-architecture.md` — Part 4: Promptfoo vs YAMLGraph comparison
- `examples/demos/verification-gate/` — Runtime verification (complementary pattern)

## Judgement

**Verdict: APPROVED with amendments.**

### Assessment

The FR is well-scoped, demo-only (no core changes), and fills a documented eval gap surfaced in the ninchat_voice × tt-bot-v2 architecture comparison. The file structure follows existing demo conventions. Effort estimate (1 day) is realistic for a self-contained demo with 6 files + captured output.

### Required Amendments

**1. Fix `provider.py` API call (Critical)**

The proposed `compile_graph(graph_path)` is wrong — `compile_graph()` takes a `GraphConfig`, not a path string. Use `invoke_graph()` which is the convenience function designed for exactly this use case:

```python
from yamlgraph.graph_loader import invoke_graph

def call_api(prompt, options, context):
    config = options.get("config", {})
    graph_path = config.get("graph", "graph.yaml")
    output_key = config.get("output_key", "response")
    variables = context.get("vars", {})

    result = invoke_graph(graph_path, variables)

    output_parts = []
    if "classification" in result:
        classification = result["classification"]
        output_parts.append(f"TONE: {classification.get('tone', 'unknown')}")
        output_parts.append(f"CONFIDENCE: {classification.get('confidence', 0)}")
    if output_key in result:
        output_parts.append(f"RESPONSE: {result[output_key]}")

    return {
        "output": "\n".join(output_parts),
        "metadata": {
            "classification": result.get("classification"),
            "graph": graph_path,
        },
    }
```

**2. Fix Promptfoo installation instructions (Minor)**

Promptfoo is a Node.js tool. `pip install promptfoo` does not exist. README must state:
- `npm install -g promptfoo` or `npx promptfoo eval`
- Python bridge (`file://provider.py`) is built into Promptfoo; no Python package needed

**3. Verify Promptfoo assertion types (Minor)**

`assert-set` and `icontains-any` — verify these exist in current Promptfoo docs before implementation. If not, use multiple `icontains` assertions with `threshold` on the test level, or use `javascript` assertion type as fallback.

**4. Provider dependency (Minor)**

Router demo defaults to `provider: xai`. README prerequisites must list `XAI_API_KEY` (or document how to override provider via env var `PROVIDER`).

### Scope Freeze

- Demo files in `examples/demos/promptfoo-router/` only
- Zero changes to `yamlgraph/` directory
- Copy prompts into demo (no symlinks) — self-contained demos don't drift-track
- No new CAP or REQ needed — this is a documentation/demo pattern, not a capability

### Authority Granted

Proceed to Enforce. Write the provider bridge first, verify `promptfoo eval` runs, then capture `demo-output.log`.
