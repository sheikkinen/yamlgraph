# Baseline Checkpointing Demo

This demo demonstrates the baseline checkpointing functionality implemented in FR-277.

## Overview

Baseline checkpointing allows watcher2 to cache stable context sources (Scripture, ARCHITECTURE.md, etc.) across runs using deterministic hash-based invalidation. This reduces token costs and improves consistency.

## What This Demo Shows

1. **Manifest Configuration**: How to define sources with glob patterns and modes
2. **Deterministic Hashing**: Same sources produce same baseline ID  
3. **Cache Reuse**: Unchanged sources don't trigger rebuild
4. **Summary Caching**: Deterministic summary cache keys
5. **State Import**: Integration with --import-state

## Demo Files

- `manifest.yaml`: Baseline manifest configuration
- `graph.yaml`: Demo graph that uses baseline state
- `prompts/`: Demo prompts
- `sources/`: Sample source files to baseline

## Running the Demo

```bash
# Run the baseline demo
yamlgraph graph run examples/demos/baseline-checkpointing/graph.yaml --full

# Lint the demo graph  
yamlgraph graph lint examples/demos/baseline-checkpointing/graph.yaml
```

## Expected Output

The demo will:
1. Load manifest and sources
2. Compute baseline ID from source hashes
3. Generate baseline state with verbatim/summarized content
4. Show baseline state being imported and used

## Key Features Demonstrated

- ✅ Deterministic baseline ID generation
- ✅ Manifest-driven source configuration  
- ✅ Summary caching with cache keys
- ✅ State import/export compatibility
- ✅ Namespace enforcement (baseline_* prefix)