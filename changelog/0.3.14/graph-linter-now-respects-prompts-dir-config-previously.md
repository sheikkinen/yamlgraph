---
type: fix
scope: graph
---
- **Graph linter now respects `prompts_dir` config** - Previously always looked in `prompts/`, now uses:
  - Graph's `prompts_dir` setting when present
  - Default `prompts/` folder otherwise
  - Fix suggestions show correct path based on config
