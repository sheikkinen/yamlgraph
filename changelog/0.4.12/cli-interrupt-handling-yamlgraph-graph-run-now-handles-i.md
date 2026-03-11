---
type: feat
scope: cli
---
- **CLI interrupt handling** - `yamlgraph graph run` now handles interrupt nodes interactively
  - Detects `__interrupt__` in graph state and prompts for user input
  - Resumes with `Command(resume=input)` for human-in-the-loop flows
  - Helper `_get_interrupt_message()` extracts display message from interrupt payload
