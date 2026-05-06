# Feature Request: FR-337 Context planner pre-node with relevance classifier (Tier 2 Medium)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-05-06

## Summary

Add a pre-node context planner to `.chaplain/graphs/watcher-enforce/enforce-session.yaml` that selects task-relevant files from the static module map, assembles a bounded context artifact, and injects it into the enforce copilot prompt.

## Value Statement

Enforce sessions start with task-relevant code context instead of blind exploration, reducing orientation churn and making first actions faster and more deterministic.

## Problem

FR-331/FR-335 delivered a static module map (`reference/module-map.md`), but enforce still receives one global index for every task. The current enforce graph is a single copilot node with no task-adaptive filtering step:

1. `.chaplain/graphs/watcher-enforce/enforce-session.yaml` wires only `START -> enforce -> END`.
2. The enforce prompt does not receive a pre-assembled codebase context payload.
3. No `context-planner` prompt or context-assembler tool exists in active watcher-enforce assets.

Result: each enforce run re-discovers scope with ad-hoc file search/read calls even when FR scope is narrow.

## Research: Existing Patterns and Prior Art

1. **Static Tier-2 orientation already exists (minimal phase).**
   - `feature-requests/FR-331-static-module-map-tier2-context.md`
   - `feature-requests/FR-335-compress-static-module-map.md`
   - `reference/module-map.md` (compressed deterministic map)

2. **Current enforce session is intentionally minimal and lacks pre-nodes.**
   - `.chaplain/graphs/watcher-enforce/enforce-session.yaml` contains only a single `copilot` node.
   - `tests/unit/test_enforce_simplify.py` currently encodes this single-node contract.

3. **The runtime already supports the needed primitives (no new node type required).**
   - `reference/graph-yaml.md` documents `type: llm` and `type: python`.
   - `.chaplain/graphs/philosopher/graph.yaml` shows established `tools:` + `type: python` usage with file-path function loading.

4. **`ast.parse()` extraction pattern is already accepted in repo tooling.**
   - `scripts/generate_module_map.py`
   - `scripts/req_coverage.py`
   - `scripts/hedging_check.py`

5. **No existing context-planner implementation is present.**
   - Repository search found no `context-planner` prompt, `context_assembler` tool, `plan_context` node, or tracked `docs/context/` outputs in active code paths.

6. **Design prior art exists as research, not implementation.**
   - `docs/diary/2026-05-05-research-context-building.md`
   - `docs/diary/2026-05-05-reflection-philosopher-agent-sdk-context-building.md`

## Objectives

1. Add a task-adaptive context selection step before enforce execution.
2. Produce deterministic, bounded context artifacts suitable for prompt injection and human review.
3. Keep scope to watcher-enforce context assembly only (single responsibility).

## Constraints

1. Preserve existing watcher FSM state topology (no new pipeline states in `watcher-pipeline-v2.yaml`).
2. Use existing YAMLGraph primitives (`llm` + `python` + prompt schema); no new runtime node/action types.
3. Keep planner cheap: lightweight model (`flash`/`haiku` class) and bounded output size.
4. Context assembler must be deterministic and stdlib-based (`ast.parse()`), with explicit token/size budget enforcement.
5. Scope limited to enforce-session surfaces and directly coupled tests/docs.

## Proposed Solution

### In scope

1. Add `context-planner` prompt under watcher-enforce prompts (template + `ContextPlan` schema):
   - `source_files: list[str]`
   - `test_files: list[str]`
   - `doc_sections: list[str]`
   - `key_symbols: list[str]`
   - `rationale: str`
2. Add a context assembler Python tool (watcher-enforce-local path, e.g. `.chaplain/graphs/watcher-enforce/tools.py` or equivalent) that:
   - reads selected source files and extracts signatures via `ast.parse()`,
   - reads selected test files and extracts `def test_*` names,
   - reads selected docs as bounded excerpts,
   - enforces a max context budget,
   - writes `docs/context/<fr-id>.md`,
   - returns `assembled_context` for state injection.
3. Update enforce session graph to wire:
   - `START -> plan_context (llm) -> assemble_context (python) -> enforce (copilot) -> END`.
4. Update enforce prompt to consume injected assembled context (`codebase_context` variable).
5. Add focused unit coverage for prompt schema contract, graph wiring contract, assembler behavior contract, and context artifact path contract.
6. Update/realign enforce-graph contract tests that currently hardcode the single-node shape.

### Out of scope

1. Extending context planner to judge/validate/sanity or other graphs.
2. Replacing static module-map generation.
3. Vectorstore/RAG retrieval stack or cross-run learning loop.
4. Copilot backend/runtime redesign.

## Acceptance Criteria

- [x] **AC-01:** `.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml` exists with `ContextPlan` schema fields (`source_files`, `test_files`, `doc_sections`, `key_symbols`, `rationale`).
- [x] **AC-02:** Context assembler Python tool exists in watcher-enforce scope and uses `ast.parse()` for source/test signature extraction.
- [x] **AC-03:** `.chaplain/graphs/watcher-enforce/enforce-session.yaml` wires `plan_context -> assemble_context -> enforce` between `START` and `END`.
- [x] **AC-04:** Planner node uses a lightweight model class (`flash` or `haiku`) and passes FR/module-map inputs required for relevance selection.
- [x] **AC-05:** Enforce prompt accepts injected assembled context and includes it in enforce instructions.
- [x] **AC-06:** Assembler writes `docs/context/<fr-id>.md` and enforces a bounded context budget before injection.
- [x] **AC-07:** Tests cover AC-01..AC-06 and existing enforce-session contract tests are updated to the new pre-node architecture.
- [x] **AC-08:** No changes are made to watcher-pipeline state machine topology beyond using the updated enforce graph.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr337_context_planner_pre_node.py`

Planned RED tests:

1. `test_ac01_context_planner_prompt_exists_with_contextplan_schema_fields`
2. `test_ac02_context_assembler_tool_exists_and_uses_ast_parse`
3. `test_ac03_enforce_session_graph_wires_plan_context_then_assemble_then_enforce`
4. `test_ac04_planner_node_uses_lightweight_flash_or_haiku_model`
5. `test_ac05_enforce_prompt_references_injected_codebase_context_variable`
6. `test_ac06_context_artifact_contract_targets_docs_context_fr_id_and_budget`
7. `test_ac07_enforce_contract_tests_reflect_pre_node_architecture`
8. `test_ac08_pipeline_v2_state_topology_unchanged_for_enforce_session_integration`

RED command:

```bash
pytest tests/unit/test_fr337_context_planner_pre_node.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
test -f .chaplain/graphs/watcher-enforce/prompts/context-planner.yaml
rg -n "plan_context|assemble_context" .chaplain/graphs/watcher-enforce/enforce-session.yaml
rg -n "codebase_context" .chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml
test -d docs/context
```

## Alternatives Considered

1. **Keep static module-map only (no pre-node planner)**
   - Rejected: does not solve task-adaptive selection.

2. **Inject the full module-map directly into enforce prompt every run**
   - Rejected: still global/noisy and not FR-specific.

3. **Implement full retrieval stack (vector DB/RAG) now**
   - Rejected: exceeds medium scope and introduces unnecessary infrastructure for this phase.

4. **Do context selection inside enforce copilot prompt only**
   - Rejected: non-deterministic and hard to audit compared with explicit pre-node + artifact.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-337.md`
- GitHub issue #337: <https://github.com/sheikkinen/yamlgraph/issues/337>
- `feature-requests/FR-331-static-module-map-tier2-context.md`
- `feature-requests/FR-335-compress-static-module-map.md`
- `reference/module-map.md`
- `.chaplain/graphs/watcher-enforce/enforce-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`
- `tests/unit/test_enforce_simplify.py`
- `docs/diary/2026-05-05-research-context-building.md`
- `docs/diary/2026-05-05-reflection-philosopher-agent-sdk-context-building.md`
