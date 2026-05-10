---
type: feat
scope: fsm
---
- **FR-292 Pipeline Path Alignment**: Align 9 graph path references in watcher-pipeline.yaml with actual disk paths under `.chaplain/graphs/`. Remove 2 phantom states (splitting, committing_tests). Convert changelog_gen to inline bash. Fix asyncio event loop pollution in FR-291 tests.
