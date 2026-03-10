---
type: fix
scope: promptsrelative
---
- **prompts_relative bug (partial)** - Added path params to executor API
  - Added `graph_path`, `prompts_dir`, `prompts_relative` params to `execute_prompt()`
  - Added same params to `PromptExecutor.execute()` method
  - 3 new unit tests for executor path resolution
