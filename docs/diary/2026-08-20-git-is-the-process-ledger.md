# 2026-08-20 — Git Is the Process Ledger

GitClaw began with a second process engine: four semantic prompts, a graph FSM,
session continuation, review remediation edges, and an append-only ledger. The
replacement trusted the artifacts already present in the development process:
issue request, FR, judgement, implementation commit, PR head, and review report.
One generic node could then use the real skills while scripts owned side effects.

**Trap: mechanizing the names of stages instead of their boundaries.** Plan,
judge, enforce, and review looked like states to encode. Their durable outputs
already were the state. Encoding both created two truths and made every policy
change a graph, prompt, ledger, and test migration.

**Heuristic:** let probabilistic work end at an artifact boundary. Verify that
artifact mechanically, then let deterministic code perform the external side
effect. Do not add a semantic state when Git/PR/issue reality already answers
the question.

Acceptance found the important defects: untracked directories were not concrete
artifacts; executor HEAD and PR head were incorrectly equated; canonical review
requires read-only GitHub evidence access; replan and implementation revision
need separate publication branches; and authoring evidence must be durable.
Each defect was at an artifact or side-effect boundary, not inside the one-node
graph.

**Outcome:** semantic orchestration shrank from 656 to 117 lines; 1,934 lines
were removed; Plan, Enforce, Replan, Review, and publisher flows were witnessed;
142 tests and remote CI passed.

**Seed:** once YAMLGraph consumes the generic issue executor, can Git operations
be extracted as a reusable Action whose only input is a signed execution report?
