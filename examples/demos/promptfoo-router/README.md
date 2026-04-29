# Promptfoo Router Evaluation Demo

Evaluates the YAMLGraph tone router using [Promptfoo](https://www.promptfoo.dev/) — a Node.js LLM evaluation framework with deterministic assertions, LLM-as-judge rubrics, and a web UI for result exploration.

## Prerequisites

- **Node.js** (for Promptfoo): `npm install -g promptfoo` or use `npx promptfoo eval`
- **YAMLGraph** installed: `pip install -e ".[dev]"` from repo root
- **OPENAI_API_KEY** env var (router graph defaults to `provider: openai`), or set `PROVIDER` env var to override

## Quick Start

```bash
cd examples/demos/promptfoo-router
promptfoo eval
```

View results in the web UI:

```bash
promptfoo view
```

## What It Demonstrates

1. **Python Provider Bridge** — `provider.py` invokes a YAMLGraph graph via `invoke_graph()` and returns Promptfoo-compatible output
2. **Deterministic Assertions** — `icontains` checks for exact tone classification (positive/negative/neutral)
3. **LLM-as-Judge Rubrics** — `llm-rubric` evaluates response quality against natural language criteria
4. **Edge Cases** — Empty input, non-English, mixed sentiment handled gracefully

## Test Suites

| File | Cases | What It Tests |
|------|-------|---------------|
| `tests/classification.yaml` | 5 | Tone classification accuracy |
| `tests/response-quality.yaml` | 3 | Response tone-matching via LLM rubric |
| `tests/edge-cases.yaml` | 3 | Boundary conditions |

## Adapting for Other Graphs

1. Copy `provider.py` to your demo directory
2. Update `promptfooconfig.yaml`:
   - Set `config.graph` to your graph YAML path
   - Set `config.output_key` to the state key containing the final output
3. Write test cases matching your graph's input variables and expected outputs

## Provider Override

To use a different LLM provider (instead of the default `xai`):

```bash
PROVIDER=anthropic promptfoo eval
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Tone router graph (copy from `../router/`) |
| `prompts/` | Prompt templates for classification and response |
| `provider.py` | Promptfoo Python provider bridge |
| `promptfooconfig.yaml` | Promptfoo configuration and test discovery |
| `tests/` | Evaluation test suites |

## Learning Path

Prerequisite: [router](../router/) demo. See also: [verification-gate](../verification-gate/) for runtime verification.
