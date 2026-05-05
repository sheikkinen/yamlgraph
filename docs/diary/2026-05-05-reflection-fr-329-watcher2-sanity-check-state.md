# Reflection: FR-329 watcher2 sanity-check state

**Date:** 2026-05-05
**FR:** FR-329 agent-sdk-planner-spike (phase 1 standalone)
**Reviewer:** watcher2 (post-validate)

## Trap

`working_system_inertia` + `plausible_wrong_answer` — Static contract tests
(text-presence assertions) are fast and CI-safe, but they confirm the contract
was *declared*, not that the algorithm works. The `next_fr_number` pure function
was not tested with a mocked filesystem, leaving the `max + 1` logic
unverified at unit level.

## What Happened

FR-329 adds a standalone Anthropic Agent SDK spike at
`examples/agent-sdk-planner/plan.py`. Six RED tests cover AC-01, AC-03–AC-06,
and AC-09 as static contract checks (string presence in source, subprocess
`--help`, file existence). All 6 tests pass cleanly in 0.41 s.

Scope isolation is clean: no runtime copilot backend files modified.
Changelog fragment, diary, and FR document are all present and committed.

## Root Cause

The mild gap is intentional design for a spike: static assertions are
sufficient feasibility evidence for CI without requiring an API key. However,
the risk is that a rename or inline-lambda refactor could break the contract
silently. The tests would need to import and call the pure helpers directly
to close this gap fully.

## What Worked

- All 9 AC items marked [x] in the FR, all corresponding code present.
- Diary entry with all required sections was committed alongside the feature.
- Scope boundary enforced: single commit, `examples/` only, no runtime changes.
- Cost guard (`>= $0.15` raises RuntimeError) and FR collision guard
  (`FileExistsError` on overwrite) are defensive-programming wins beyond the
  AC surface.

## Seed

Can the `next_fr_number` and `read_fr_template` pure functions be extracted to
a shared `yamlgraph/tools/fr_tools.py` module so both the Agent SDK spike and
a future `copilot_node.py` MCP path share one tested implementation—rather than
requiring duplicate coverage in each integration layer?
