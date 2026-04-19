---
type: fix
scope: chatterbox
---
- **FR-239 speak.py fix**: Validate `--ref` file existence before importing `torch`, preventing `ModuleNotFoundError` on environments without torch installed.
