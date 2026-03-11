---
type: feat
scope: cli
---
- **CLI --async flag** - `yamlgraph graph run --async` for parallel map node execution
  - Uses `ainvoke()` for guaranteed parallel processing with all LLM providers
  - Particularly useful for Mistral provider which requires async for parallel execution
  - Short form: `-a`
  - Example: `yamlgraph graph run graph.yaml --var topic=AI --async`
