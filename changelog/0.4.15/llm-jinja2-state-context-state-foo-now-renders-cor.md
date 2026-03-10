---
type: fix
scope: llm
---
- **LLM Jinja2 state context** - `{{ state.foo }}` now renders correctly in LLM node prompts (was passing state as variables only, not as Jinja2 context)
