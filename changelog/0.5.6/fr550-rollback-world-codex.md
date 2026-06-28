---
type: removal
scope: examples
---
- **FR-550 Roll back DM v2 World Codex (FR-548)**: Remove the synopsis-derived World Codex stage. It authored immutable world prose *before the action existed, from a plot synopsis* -- a placement defect that leaked non-roster characters and plot-derived "factions" into the codex (verified live in the 10034-BC story). Excised the `expand_codex`/`_normalize_codex`/`_codex_entries` boundary, the `_format_world_codex` Final Cut weave, the `world_codex.yaml` graph + prompt, and the `WORLD_CODEX_GRAPH` wiring. A permanent regression guard (`tests/test_no_world_codex.py`) condemns any re-introduction. The length/depth goal is re-earned soundly by FR-551 (supporting-cast tier) and FR-552 (world bible).
