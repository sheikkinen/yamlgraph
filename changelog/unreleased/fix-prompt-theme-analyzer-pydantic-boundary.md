---
type: fix
scope: demos
---
- **prompt_theme_analyzer**: normalize Pydantic model returned by `group_themes` LLM node via `.model_dump()` at the `write_report` boundary; add curated fixture dataset and `demo.sh` for reproducible demo runs.
