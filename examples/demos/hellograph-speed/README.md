# HelloGraph Speed Demo

Copy of the hello demo with provider-specific graph configs to compare latency:
- Google consumer API
- Vertex API
- Azure AI Foundry

## Files

- `graph.google.yaml` - Hello graph using `provider: google`
- `graph.vertex.yaml` - Hello graph using `provider: vertex`
- `graph.azure.yaml` - Hello graph using `provider: azure`
- `prompts/greet.yaml` - Shared prompt
- `vars.yaml` - Fixed inputs for repeatable benchmarking
- `.env.google.example` - Minimal Google consumer API env
- `.env.vertex.example` - Minimal Vertex env (Express mode)
- `.env.azure.example` - Minimal Azure AI Foundry env
- `compare_speed.sh` - Runs available providers back-to-back with same workload

## Setup

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# Azure provider support
pip install -e ".[dev,azure]"
```

Then prepare env files in this demo directory:

```bash
cd examples/demos/hellograph-speed
cp .env.google.example .env.google
cp .env.vertex.example .env.vertex
cp .env.azure.example .env.azure
```

## Run Once Per Provider

```bash
yamlgraph graph run graph.google.yaml --var-file vars.yaml --full
yamlgraph graph run graph.vertex.yaml --var-file vars.yaml --full
yamlgraph graph run graph.azure.yaml --var-file vars.yaml --full
```

## Compare Speed

```bash
chmod +x compare_speed.sh
./compare_speed.sh 5
```

Argument `5` is run count per provider. Use a larger value (for example 10-20) for a more stable average.

## Minimal Required Env

Google consumer API (`.env.google`):
- `GOOGLE_API_KEY`

Vertex Express (`.env.vertex`):
- `VERTEX_API_KEY`

Azure AI Foundry (`.env.azure`):
- `AZURE_AI_ENDPOINT`
- `AZURE_AI_API_KEY`
- `AZURE_MODEL` (optional, default in graph is `gpt-4o`)

No extra variables are required for this hello demo because provider/model are set in each graph config.
