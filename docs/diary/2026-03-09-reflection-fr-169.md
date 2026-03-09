## 2026-03-09: FR-169 — Enforce Pipeline Reflexion Loop

**Context:** Added a critique → refine reflexion loop to the enforce pipeline between test_and_demo and precommit_check. Three new copilot nodes (critique, refine, distill_reflection) with dedicated prompts, bounded by loop_limits and loop_exits (FR-172). Also added a skip-if-exists guard in finalize_merge.sh to preserve pipeline-generated diary reflections.

**Trap:** `quick_confidence` — The FR specified the exact graph YAML, prompts, and edges. The temptation was to skip the RED phase and paste the solution directly. But TDD (Commandment 7) demands the failing test first. Writing 45 tests before any implementation exposed a subtle gap: the finalize_merge.sh `cat >` unconditionally overwrites files, which the tests proved by catching the overwrite of a pre-existing reflection. Without the RED phase, this would have been a "plausible wrong answer" — the script would silently destroy pipeline-generated content.

**Heuristic:** When the FR hands you the solution, the tests are the real implementation. The graph YAML is configuration; the tests are the contract. Write the contract first, then validate the configuration satisfies it.

**Seed:** Could the critique node's score threshold (0.85) be calibrated from historical PR review data? If we tracked how many revision cycles each PR needed, we could tune the threshold to match the team's actual quality bar.
