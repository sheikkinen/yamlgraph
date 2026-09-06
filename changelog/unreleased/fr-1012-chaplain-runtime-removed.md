---
type: removal
scope: chaplain
---
- **FR-1012 Chaplain runtime removed**: `.chaplain/` (the autonomous FSM pipeline: dispatcher, watcher graphs, inquisitor, inbox importer, 146 files) is gone from `main`, together with `.github/skills/chaplain-ops/`, `scripts/chaplain-prompts/`, the legacy ID-registry scripts and their `validate-id-registry` pre-commit hook, 41 test files that witnessed only the runtime, and 24 capability records now `status: retired` (`retired_by: FR-1012`) — exactly the sets decided by the model-assisted census in `docs/census/chaplain-test-disposition.jsonl`. Its source is preserved read-only: tag `chaplain-archive` → `0184a73d` and the private archived repository `sheikkinen/yamlgraph-chaplain` (split `b31f5849`, head `cf30d87f`), every file verified against a commit-object manifest. `docs/archive/chaplain.md` maps each retired piece to its replacement. Phase 2 of FR-1010.
