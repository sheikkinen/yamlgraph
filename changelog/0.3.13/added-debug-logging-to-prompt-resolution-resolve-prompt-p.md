---
type: feat
scope: added
---
- **Added debug logging to prompt resolution** - `resolve_prompt_path()` now logs:
  - Which resolution path was chosen (graph-relative, prompts_dir, default, fallback)
  - All tried paths on failure for easier debugging
