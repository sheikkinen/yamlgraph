---
type: fix
scope: ci
---
- **CI Test Fixes**
  - Fixed 15 failing unit tests in CI by mocking `load_prompt` instead of requiring external prompt files
  - `test_agent_nodes.py`: Added autouse fixture to mock load_prompt
  - `test_conversation_memory.py`: Added autouse fixture to mock load_prompt
  - `test_jinja2_prompts.py`: Use inline template constant instead of loading from file
