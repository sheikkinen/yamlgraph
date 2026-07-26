---
type: feat
scope: deps
---
- **FR-760 Declare langchain-core as Explicit Dependency**: `langchain-core`
  is imported directly by core modules (`BaseChatModel`, message classes,
  `StructuredTool`, `BaseCallbackHandler`, `RunnableConfig`) but previously
  arrived only transitively via `langgraph` and the `langchain-*` provider
  packages. It is now declared in `[project.dependencies]` with a floor of
  `>=1.5.1` (the resolved version) and a substantive rationale entry in
  `docs/dependency-rationale.yaml`, so future `langgraph`/provider pin
  changes surface as an explicit dependency diff instead of silent drift.
  Also fixes `scripts/fr_board.py`'s `repo` column, which previously used
  the checkout directory's basename (mislabeling every row when
  regenerated from a git worktree) instead of the stable
  `pyproject.toml` project name.
  (Diary reflection renamed to match the `reflection-fr-NNN` gate pattern.)
