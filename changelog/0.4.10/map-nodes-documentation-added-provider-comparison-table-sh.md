---
type: feat
scope: map
---
- **Map nodes documentation** - Added provider comparison table showing parallel behavior
  - Anthropic/OpenAI: Parallel with both `invoke()` and `ainvoke()`
  - Mistral: Requires `ainvoke()` (or `--async` flag) for parallel execution
