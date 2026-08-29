---
type: fix
scope: examples
---
- **FR-899 corpus-census PDF dependency declared**: `pypdf` — imported by the corpus-census PDF extract adapter since FR-892 — was undeclared, and `examples/demos` is `extra-backed`, so the direct-import scan treated it as core-strict. It never blocked a commit because the hook only fires when the scanned paths or `pyproject.toml` change; the first release attempt, which always touches `pyproject.toml`, surfaced it. Declared as a `corpus-census` extra with its own taxonomy row.
