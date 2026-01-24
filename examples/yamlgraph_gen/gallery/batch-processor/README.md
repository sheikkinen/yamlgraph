# Batch Processor

> Process items in parallel using the map pattern.

## Usage

```bash
yamlgraph graph run graph.yaml --var items='["Apple", "Banana", "Cherry"]'
```

## Pipeline Flow

1. **process_items** (map) - Process each item in parallel
2. **summarize** - Combine all processed results

## Patterns Used

- Map (parallel processing)
- Linear (aggregation)
