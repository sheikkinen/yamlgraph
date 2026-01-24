# Cost Router

> Route requests to different models based on complexity.

## Usage

```bash
yamlgraph graph run graph.yaml --var query="What is 2+2?"
```

```bash
yamlgraph graph run graph.yaml --var query="Explain the economic implications of quantum computing on global supply chains"
```

## Pipeline Flow

1. **classify_complexity** (router) - Analyze query complexity
2. Routes to: fast_model (simple), standard_model (medium), premium_model (complex)

## Patterns Used

- Router (cost optimization)

## Cost Optimization

- Simple queries → Haiku (fast, cheap)
- Medium queries → Sonnet (balanced)
- Complex queries → Opus (thorough)
