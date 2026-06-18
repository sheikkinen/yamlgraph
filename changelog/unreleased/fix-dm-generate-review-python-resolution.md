---
type: fix
scope: examples
---
- **DM `generate_and_review.sh` interpreter resolution**: The convenience script no longer requires a pre-activated venv — it resolves a Python interpreter via `$PYTHON` override, then the repo-local `.venv/bin/python`, then `python3`/`python`, fixing the `python: command not found` (exit 127) failure when run from a fresh shell.
