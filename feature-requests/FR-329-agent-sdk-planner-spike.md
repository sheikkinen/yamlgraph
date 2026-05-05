# Feature Request: FR-329 Agent SDK planner spike (phase 1 standalone)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-05

## Summary

Add a standalone feasibility spike at `examples/agent-sdk-planner/plan.py` that reproduces Chaplain Plan-step I/O (`topic file -> FR markdown`) using Anthropic Agent SDK, without changing YAMLGraph copilot runtime.

## Value Statement

Chaplain maintainers get evidence for whether an in-process Agent SDK path can provide deterministic FR numbering and exploration audit visibility before any copilot-node backend migration.

## Problem

Issue #329 requests a phase-1 planner spike with custom tools and hook visibility. Current planner execution is CLI-only and cannot provide those guarantees directly:

1. `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` uses `type: copilot` with `backend: cli`.
2. `yamlgraph/node_factory/copilot_node.py` executes `copilot --silent` subprocess and returns text metadata (`CopilotResult`), with no in-process custom tool contract.
3. `watcher-pipeline-v2` captures FR path after planning (`capture_fr`), which does not reserve FR numbers during planning.
4. `reference/graph-yaml.md` and schema mention `backend: sampling`, but docs also state it is not implemented; there is no `agent-sdk` backend path in runtime code.

Topic source was read from `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-329.md`.

## Research: Existing Patterns and Prior Art

1. **Planner flow is unified and copilot-node based today.**
   - `.chaplain/config/watcher-pipeline-v2.yaml` plan action runs one unified planning graph.
   - `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml` requires FR drafting + research + failing acceptance tests in one session.
2. **Copilot runtime seam exists, but only for current backends.**
   - `yamlgraph/models/graph_schema.py` exposes a copilot `backend` field.
   - `yamlgraph/node_factory/copilot_node.py` currently implements CLI execution only (`backend="cli"` in result envelope).
3. **Comparable deferred backend work exists and was intentionally constrained.**
   - `feature-requests/FR-082-sampling-backend.md` documents a dropped runtime backend expansion, supporting a minimal standalone spike before runtime changes.
4. **No existing in-repo planner spike for Agent SDK.**
   - Repository search finds no `claude-agent-sdk` integration path and no `examples/agent-sdk-planner/` implementation.

## Objectives

1. Validate a standalone planner script that accepts a topic file and writes an FR markdown file.
2. Validate deterministic FR number selection via explicit `next_fr_number` tool behavior (`max + 1` over `feature-requests/FR-*.md`).
3. Validate template fidelity via explicit `read_fr_template` tool behavior (`feature-requests/TEMPLATE.md` bytes).
4. Validate exploration visibility through a PostToolUse hook audit output.

## Constraints

1. Scope is phase-1 standalone spike only.
2. No changes to copilot runtime integration surfaces:
   - `yamlgraph/node_factory/copilot_node.py`
   - `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`
   - `.chaplain/config/watcher-pipeline-v2.yaml`
3. Output contract remains template-aligned and sets `**Status:** Draft`.
4. Keep single responsibility: planner-spike feasibility evidence for issue #329.

## Proposed Solution

### In scope

1. Create `examples/agent-sdk-planner/plan.py` that:
   - accepts one topic-file argument,
   - uses Anthropic Agent SDK,
   - writes `feature-requests/FR-XXX-<slug>.md`.
2. Add planner tool `next_fr_number`:
   - scan `feature-requests/FR-*.md`,
   - return deterministic next number (`max + 1`).
3. Add planner tool `read_fr_template`:
   - return exact bytes/content of `feature-requests/TEMPLATE.md`.
4. Add PostToolUse hook audit output listing touched/read paths.
5. Add minimal usage doc under `examples/agent-sdk-planner/README.md`.

### Out of scope

1. Adding `backend: agent-sdk` to copilot node runtime.
2. Migrating watcher plan/judge/enforce graphs to a new backend.
3. Refactoring YAMLGraph execution architecture beyond this standalone spike.

## Acceptance Criteria

- [x] **AC-01:** `examples/agent-sdk-planner/plan.py` exists and requires one topic-file argument.
- [x] **AC-02:** Script path works with `ANTHROPIC_API_KEY` and does not require `copilot` binary.
- [x] **AC-03:** `next_fr_number` deterministically returns `max + 1` from `feature-requests/FR-*.md`.
- [x] **AC-04:** `read_fr_template` returns content byte-identical to `feature-requests/TEMPLATE.md`.
- [x] **AC-05:** Script writes `feature-requests/FR-XXX-<slug>.md` with template sections and `**Status:** Draft`.
- [x] **AC-06:** PostToolUse hook emits exploration audit with file/tool traces.
- [x] **AC-07:** Invocation records a measurable per-run cost, with target `< $0.15` under the issue's normal-topic expectation.
- [x] **AC-08:** Focused RED tests exist at `tests/unit/test_fr329_agent_sdk_planner_spike.py`.
- [x] **AC-09:** No runtime copilot backend integration files are changed by this spike.

## Implementation Notes

1. Added standalone planner script at `examples/agent-sdk-planner/plan.py` using `claude-agent-sdk` with custom tools `next_fr_number` and `read_fr_template`.
2. Wired `PostToolUse` hook audit tracing and enforced per-run cost reporting with budget target validation (`< $0.15`).
3. Added usage docs at `examples/agent-sdk-planner/README.md` and registered the new top-level example in `examples/README.md`.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr329_agent_sdk_planner_spike.py`

Planned RED tests:

1. `test_ac01_planner_script_exists_and_requires_topic_argument`
2. `test_ac03_next_fr_number_tool_contract_is_present`
3. `test_ac04_read_fr_template_tool_contract_is_present`
4. `test_ac05_output_contract_requires_draft_status`
5. `test_ac06_post_tool_use_hook_contract_is_present`
6. `test_ac09_scope_isolation_contract`

RED command:

```bash
pytest tests/unit/test_fr329_agent_sdk_planner_spike.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
test -f examples/agent-sdk-planner/plan.py
test -f examples/agent-sdk-planner/README.md
rg -n "def next_fr_number|def read_fr_template|PostToolUse" examples/agent-sdk-planner/plan.py
```

## Alternatives Considered

1. **Keep current Copilot CLI planner only** — rejected; does not validate custom tools or exploration hooks requested by issue #329.
2. **Implement `backend: agent-sdk` directly in runtime now** — rejected; broad runtime change before phase-1 feasibility evidence.
3. **Add only FR-number shell helper to current planner** — rejected; solves numbering only, not template-tool and hook-audit objectives.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-329.md`
- GitHub issue #329: <https://github.com/sheikkinen/yamlgraph/issues/329>
- `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`
- `yamlgraph/node_factory/copilot_node.py`
- `yamlgraph/models/graph_schema.py`
- `reference/graph-yaml.md`
- `feature-requests/FR-082-sampling-backend.md`
