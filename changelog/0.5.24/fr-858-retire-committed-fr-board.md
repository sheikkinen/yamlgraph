---
type: removal
scope: tooling
---
- **FR-858 Retire the committed FR board**: `docs/fr-board.md` is no longer tracked and the `fr-board-check` drift hook is gone. `python scripts/fr_board.py` now prints the board to stdout and writes nothing; `--out` and `--check` are removed. `scripts/vscode/now.py` computes plan state live. Follows the FR-179 precedent that de-tracked `CHANGELOG.md` to eliminate merge conflicts.
