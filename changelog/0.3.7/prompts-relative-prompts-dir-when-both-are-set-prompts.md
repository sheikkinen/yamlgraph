---
type: fix
scope: promptsrelative
---
- **prompts_relative + prompts_dir** - When both are set, prompts_dir is now resolved relative to graph_path.parent
  - Fixed `yamlgraph/utils/prompts.py` resolve_prompt_path() to combine graph_path.parent with prompts_dir
  - New resolution order: graph-relative + prompts_dir takes precedence over standalone prompts_dir
  - Added `test_prompts_relative_with_prompts_dir_combines_paths()` regression test
  - All 16 unit tests and 2 integration tests pass
