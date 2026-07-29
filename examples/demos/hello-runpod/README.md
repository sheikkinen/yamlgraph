# Hello World (RunPod) Demo

Minimal YAMLGraph example running against a **RunPod OpenAI-compatible
endpoint** via the `runpod` provider (FR-766). Same pipeline as
`examples/demos/hello`, with two RunPod-specific adaptations:

- `provider: runpod` declared in the graph (no `PROVIDER` env needed)
- `temperature: 1.0` pinned — reasoning-model endpoints (e.g. `kimi-k3`
  on the Public API) return a bare HTTP 500 for any other value

## Prerequisites

```bash
export RUNPOD_API_KEY="your-key"
# Full base URL: Public API model slug or serverless vLLM endpoint id
export RUNPOD_ENDPOINT="https://api.runpod.ai/v2/moonshot-kimi/openai/v1"
export RUNPOD_MODEL="kimi-k3"
```

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/hello-runpod/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/hello-runpod/graph.yaml \
  --var name="World" --var style="holy see of code" --full
```

Serverless cold starts can take tens of seconds; the factory's bounded
retries (FR-708) absorb transient startup errors.

## What It Does

1. Takes `name` and `style` as input
2. Generates a structured greeting with:
   - `greeting` (message text)
   - `emoji` (tone marker)
   - `formality_level` (style classification)

## Pipeline

```
START → greet → END
```

## Key Concepts

- **`provider: runpod`** - Graph-level provider selection
- **Endpoint constraints** - an "OpenAI-compatible" surface may still
  reject standard parameter values; the status code is provider output
  crossing the same boundary as the body (see
  `docs/diary/diary-2026-07-29-runpod-provider-status-code-lie.md`)
- **`type: llm`** - Basic LLM node
- **Variable substitution** - `{state.name}` syntax
- **`prompts_relative: true`** - Prompts relative to graph file

## Files

```
hello-runpod/
├── graph.yaml          # Graph definition (provider: runpod, temp 1.0)
├── prompts/
│   └── greet.yaml      # Prompt with inline schema
└── README.md
```
