---
type: fix
scope: chaplain
---
- **Convert forensic graph to copilot node**: Replace blind LLM call + broken tool node with agentic copilot node that has full tool access to read logs, inspect git state, and write diary entries directly. Removes hardcoded `provider: anthropic`.
