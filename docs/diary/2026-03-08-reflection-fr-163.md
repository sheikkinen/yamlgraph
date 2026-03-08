## 2026-03-08: FR-163 — Chaplain Inbox Instructions in CLAUDE.md

**Context:** Added a "Submitting Proposals" section to `CLAUDE.md` documenting the `.chaplain/inbox/` workflow, mirroring the canonical source in `.github/copilot-instructions.md`. This closes a discovery gap where Claude Code sessions could not find the autonomous proposal pipeline.

**Trap:** documentation_drift — Two AI instruction files (`.github/copilot-instructions.md` and `CLAUDE.md`) with asymmetric coverage of the same workflow. The chaplain inbox mechanism existed and was documented in one place but invisible to agents consuming the other. The fix was trivial (copy four lines), but the detection required an audit to notice the asymmetry. The real cost of drift is not the fix — it's the silent failure of agents that never discover the capability.

**Heuristic:** When a workflow is documented in one AI instruction file, check all instruction files for parity. Instruction file drift is a special case of the boundary normalization law: the boundary here is "where an agent reads its instructions." Normalize at every entry point, not just the first one discovered. The test (`test_matches_canonical_source`) enforces this structurally — if either file drifts, the test fails.

**Seed:** Could we generate a single canonical source for shared instructions (e.g., `reference/ai-instructions.yaml`) and have both `CLAUDE.md` and `.github/copilot-instructions.md` include from it, eliminating the possibility of drift entirely?
