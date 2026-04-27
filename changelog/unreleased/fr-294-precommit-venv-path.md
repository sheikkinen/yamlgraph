---
type: fix
scope: ci
req: REQ-YG-012
---
- **FR-294 Pre-commit venv PATH isolation**: Prepend `.venv/bin` to PATH in pytest hook so subprocess calls to venv-installed tools succeed. (REQ-YG-012)
