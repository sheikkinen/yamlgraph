# Feature Request: FR-368 watcher2 multi-project MVP routing for `ninchat_voice`

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-11

## Summary

Add a second watcher2 project lane for `ninchat_voice` by introducing an explicit project manifest and wiring project contract fields through dispatcher, worktree setup, plan prompt context, validate gate, and FR capture, while preserving existing yamlgraph intake behavior.

## Value Statement

Chaplain can govern `ninchat_voice` proposals with deterministic project-specific setup and validation, without regressing current yamlgraph watcher2 operation.

## Problem

Watcher2 is still single-project coupled across the pipeline:

1. `.chaplain/config/watcher-dispatcher.yaml` scans only `.chaplain/inbox/*.md` and emits only `topic_file`.
2. `.chaplain/lib/watcher/worktree_setup.sh` hardcodes branch/worktree policy (`feat/watcher2-...`).
3. `.chaplain/actions/validate_gate_action.py` runs fixed `pre-commit run --all-files` and has no project-scoped test command hook.
4. `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` and `prompts/plan-unified.yaml` accept only `topic_file/worktree_dir/branch`, and the system text is hardcoded to "YAMLGraph framework."
5. `.chaplain/config/watcher-pipeline-v2.yaml` `capture_fr` hardcodes `feature-requests/FR-*.md`.
6. No `projects/ninchat_voice/chaplain.yaml` contract exists yet.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Context propagation path already exists and is the right extension point.**
   - `watcher-pipeline-v2.yaml` already maps `setup_done` context (`wt_dir`, `wt_branch`, `main_dir`) and passes vars into plan/judge/enforce.
2. **Deterministic gate behavior is centralized.**
   - `ValidateGateAction` is the canonical point for CI-parity checks, so project-specific pre-commit/test wiring belongs there.
3. **Plan step variable passing exists but is under-scoped.**
   - `step-plan-unified.yaml` already passes variables into the prompt; adding project contract paths follows existing pattern.
4. **FR capture is currently fixed-path and must be project-aware.**
   - `capture_fr` currently searches only `feature-requests/FR-*.md`, so non-root project FR paths are not discoverable.
5. **No existing multi-project watcher contract in repo.**
   - Search found no manifest schema keys (`branch_prefix`, `precommit_config`, `test_cmd`, `fr_template`, `architecture_doc`) outside this FR topic; the capability is not already implemented.
6. **Topic source expected by planner is absent in this snapshot.**
   - `.chaplain/processing/gh-368.md` is missing; issue #368 plus in-repo watcher2 artifacts were used as canonical planning input.

## Objectives

1. Add explicit `ninchat_voice` intake lane in watcher2.
2. Define one manifest contract for project-specific execution policy.
3. Propagate manifest fields end-to-end (dispatch -> setup/plan/validate/capture).
4. Preserve yamlgraph lane behavior in MVP.

## Constraints

1. **MVP only:** exactly two projects (`yamlgraph`, `ninchat_voice`).
2. **Single responsibility:** project routing and contract wiring only.
3. **Yamlgraph intake contract preserved:** keep `.chaplain/inbox/*.md` lane behavior unchanged.
4. **`ninchat_voice` lane additive:** `.chaplain/inbox/ninchat_voice/*.md`.
5. **GitHub issue import routing unchanged in MVP:** `inbox_sync.sh` keeps importing labeled issues into yamlgraph lane.
6. **Deterministic validation contract:** existing commit-title/freshness/diary checks remain active; project-specific checks are additive, not replacing them.
7. **No dynamic discovery:** Phase-2 generalization is out of scope.

## Proposed Solution

### Manifest contract (required schema)

Create `projects/ninchat_voice/chaplain.yaml`:

| Field | Type | Required | Validation | Example |
| --- | --- | --- | --- | --- |
| `project` | `str` | yes | literal `ninchat_voice` in MVP | `ninchat_voice` |
| `branch_prefix` | `str` | yes | non-empty | `feat/nv-` |
| `work_dir` | `str` | yes | repo-relative path | `projects/ninchat_voice` |
| `test_cmd` | `str` | yes | non-empty shell command | `pytest projects/ninchat_voice/tests/ -q --no-cov` |
| `precommit_config` | `str` | yes | repo-relative path | `projects/ninchat_voice/.pre-commit-config.yaml` |
| `fr_template` | `str` | yes | repo-relative path | `projects/ninchat_voice/feature-requests/TEMPLATE.md` |
| `architecture_doc` | `str` | yes | repo-relative path | `projects/ninchat_voice/README.md` |

### In scope

1. Add lane directory `.chaplain/inbox/ninchat_voice/`.
2. Update dispatcher to scan both lanes and emit project contract fields.
3. Update dispatcher `processing_topic` to forward all project fields in `--initial-context`.
4. Update `worktree_setup.sh` to derive branch/worktree from context (`branch_prefix`, `work_dir`) with yamlgraph fallback.
5. Update `validate_gate_action.py` to:
   - run pre-commit as `pre-commit run --all-files --config <precommit_config>` when provided,
   - run `<test_cmd>` as an additional deterministic check when provided,
   - keep commit-title, branch-freshness, and diary-parity checks active.
6. Update `step-plan-unified.yaml` + `prompts/plan-unified.yaml` to pass/use `project`, `fr_template`, and `architecture_doc`:
   - system text must use `{{ project }}` instead of hardcoded "YAMLGraph framework."
7. Update `watcher-pipeline-v2.yaml` `capture_fr` to derive FR glob from `fr_template` directory (project-scoped), not fixed root path.

### Out of scope

1. Dynamic N-project discovery.
2. Auto-routing GitHub issue imports into `ninchat_voice` lane.
3. `outcaller` / `voice_runtime` manifests.
4. Venv isolation redesign.

## Acceptance Criteria

- [x] **AC-01:** Dispatcher discovers topics from `.chaplain/inbox/*.md` and `.chaplain/inbox/ninchat_voice/*.md`.
- [x] **AC-02:** Dispatcher emits project context keys: `project`, `branch_prefix`, `work_dir`, `test_cmd`, `precommit_config`, `fr_template`, `architecture_doc`.
- [x] **AC-03:** Dispatcher `processing_topic` includes all project keys in pipeline `--initial-context`.
- [x] **AC-04:** `worktree_setup.sh` derives branch/worktree from manifest context (`<branch_prefix><topic_slug>` + `work_dir`) for `ninchat_voice`; yamlgraph default behavior remains intact.
- [x] **AC-05a:** For yamlgraph topics, validate gate deterministic checks remain behaviorally unchanged (pre-commit, commit-title contract, branch freshness, diary parity).
- [x] **AC-05b:** For `ninchat_voice` topics, validate gate runs pre-commit with `--config <precommit_config>` and executes `<test_cmd>` as an additional check while still enforcing title/freshness/diary checks.
- [x] **AC-06a:** Plan-unified graph/prompt passes `project`, `fr_template`, `architecture_doc`; prompt system text uses `{{ project }}`.
- [x] **AC-06b:** `capture_fr` derives FR search directory from `fr_template` path (e.g., `projects/ninchat_voice/feature-requests/FR-*.md`) rather than fixed `feature-requests/FR-*.md`.
- [x] **AC-07:** yamlgraph lane contract remains unchanged (flat-root inbox pickup and existing import behavior).
- [x] **AC-08:** `projects/ninchat_voice/chaplain.yaml` schema requires all fields above and enforces repo-relative path strings.
- [x] **AC-09:** RED state for AC-08 is explicit: before manifest exists, schema test fails on missing/invalid manifest fixture.

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr368_chaplain_multi_project_ninchat_voice_routing_red.py`

Planned RED tests (must fail before implementation):

1. `test_ac01_dispatcher_scans_yamlgraph_root_and_ninchat_lane`
2. `test_ac02_dispatcher_emits_project_contract_context_keys`
3. `test_ac03_processing_topic_initial_context_propagates_project_keys`
4. `test_ac04_worktree_setup_uses_manifest_branch_prefix_and_work_dir`
5. `test_ac05a_validate_gate_yamlgraph_checks_unchanged`
6. `test_ac05b_validate_gate_ninchat_uses_project_precommit_config_and_test_cmd`
7. `test_ac06a_plan_unified_passes_project_template_archdoc_and_project_system_text`
8. `test_ac06b_capture_fr_searches_project_fr_directory_from_template_path`
9. `test_ac07_yamlgraph_flat_root_lane_contract_unchanged`
10. `test_ac08_manifest_schema_requires_fields_and_repo_relative_paths_with_red_precondition`

RED command:

```bash
pytest tests/unit/test_fr368_chaplain_multi_project_ninchat_voice_routing_red.py -q --no-cov
```

## Alternatives Considered

1. **Dynamic manifest discovery now (N-project generalization).**
   - Rejected for MVP: larger blast radius than issue scope.
2. **Infer project from topic text/body.**
   - Rejected: ambiguous, non-deterministic routing.
3. **Migrate yamlgraph lane to `.chaplain/inbox/yamlgraph/` in this FR.**
   - Rejected: unnecessary migration risk; keep current yamlgraph lane contract stable first.
4. **Only change branch naming without gate/plan/capture wiring.**
   - Rejected: leaves core multi-project coupling unresolved.

## Related

- GitHub issue #368: <https://github.com/sheikkinen/yamlgraph/issues/368>
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/lib/watcher/worktree_setup.sh`
- `.chaplain/actions/validate_gate_action.py`
- `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`
- `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/lib/watcher/inbox_sync.sh`

## Topic Source Note

Requested source `.chaplain/processing/gh-368.md` is not present in this worktree snapshot; planning source used: GitHub issue #368 plus in-repo watcher2 artifacts listed above.
