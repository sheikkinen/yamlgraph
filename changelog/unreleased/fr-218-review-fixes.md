---
type: fix
scope: architecture
req: REQ-YG-218
---
- **FR-218 Import-Linter review fixes**: Add mcp_server/a2a_server/a2a_message to Layer 2 (were silently unmonitored); fix pre-commit hook to use `PATH="$PWD/.venv/bin:$PATH" lint-imports` instead of hardcoded `.venv/bin/`; fix test to use `Path(sys.executable).parent / "lint-imports"` instead of internal importlinter CLI API. (REQ-YG-218)
