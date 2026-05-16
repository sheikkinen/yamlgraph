# Feature Request: FR-402 Prompt Theme Analyzer Demo Implementation

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-16

## Summary

Add a single YAMLGraph demo that reads prompt files, classifies each prompt into a concise theme with a map node, deterministically aggregates theme counts in Python, and writes a grouped markdown report.

## Value Statement

Graph authors get a concrete, architecture-aligned example of high-volume `map` fan-out with deterministic post-processing, reducing ambiguity around where to place normalization and aggregation logic.

## Problem

Issue #402 requests implementation of FR-393 with specific corrections. FR-393’s original draft mixes a valid demo objective with non-portable and non-deterministic details:

1. Prompt truncation is specified in unsupported simple-template format syntax (`{prompt_text:.2000}`).
2. Grouping receives raw per-item outputs instead of a bounded deterministic aggregate.
3. `source_dir` is shown with a machine-local default path instead of required runtime input.
4. Requirement traceability and diary obligations are not fully captured as acceptance gates.

Without corrections, the demo would be harder to run reproducibly and harder to verify.

## Research

### Topic source

- Requested source file `.chaplain/processing/gh-402.md` is not present in this worktree.
- Canonical topic was taken from GitHub issue #402:
  <https://github.com/sheikkinen/yamlgraph/issues/402>

### Existing patterns and constraints in this repository

1. **Prior FR scope and correction baseline**
   - `feature-requests/FR-393-prompt-theme-analyzer.md`
   - Already identifies the target demo and judge corrections.

2. **Closest production-shaped demo pattern**
   - `examples/demos/diary_index/graph.yaml`
   - `examples/demos/diary_index/tools.py`
   - Proven pattern: `list -> map(llm) -> deterministic python aggregate -> write`.

3. **Architecture requirements that directly constrain this FR**
   - `REQ-YG-040`, `REQ-YG-041`: map node compilation and reducer wiring.
   - `REQ-YG-055`: map fan-out cap behavior (`max_items`).
   - `REQ-YG-062`: lint warning for dynamic map input without explicit caps.
   - `REQ-YG-161`: append-only capability registry and requirement traceability.
   - `REQ-YG-257`: diary-index precedent using deterministic aggregation between map and write.

4. **Current capability index ceiling**
   - Highest existing capability in this branch is `CAP-148`, so `CAP-149` is available for planning.

## Objectives

1. Define a minimal, single-responsibility demo FR for prompt-theme analysis.
2. Freeze the corrected 5-node graph shape so implementation is judgeable.
3. Encode explicit, testable acceptance gates for boundary normalization, deterministic aggregation, and traceability artifacts.

## Constraints

1. Scope is limited to one demo package and directly coupled tests/docs.
2. `source_dir` is required input; no hardcoded local defaults.
3. Prompt truncation must occur at Python tool boundary before LLM prompt rendering.
4. Grouping input must come from deterministic aggregated theme counts, not raw per-item payloads.
5. Demo must follow existing `examples/demos/` conventions and include `demo-output.log`.
6. No framework-core primitive changes are included.

## Proposed Solution

### In scope

1. Add demo directory: `examples/demos/prompt_theme_analyzer/`
   - `graph.yaml`
   - `prompts/classify_theme.yaml`
   - `prompts/group_themes.yaml`
   - `tools.py`
   - `analyze.sh`
   - `README.md`
   - `demo-output.log`
2. Use corrected graph shape:
   - `list_prompts` (python)
   - `classify_themes` (map + llm)
   - `aggregate_themes` (python deterministic dedupe/count)
   - `group_themes` (llm over aggregated data)
   - `write_report` (python)
3. Add unit tests for tool boundary behavior and graph contract.
4. Add traceability artifacts:
   - `capabilities/CAP-149-prompt-theme-analyzer-demo.yaml`
   - New requirement entry `REQ-YG-359` in CAP-149.
5. Add diary reflection entry under `docs/diary/`.
6. Mark `FR-393` as superseded by FR-402 after FR-402 implementation is complete.

### Out of scope

1. Framework-level batching/chunking primitives.
2. Data migration or curation of external prompt corpus paths.
3. Provider optimization work beyond this demo’s declared defaults.

## Acceptance Criteria

- [x] **AC-01:** `examples/demos/prompt_theme_analyzer/` exists with graph, prompts, tools, README, shell helper, and `demo-output.log`.
- [x] **AC-02:** `list_prompts` requires `source_dir`; missing input raises an explicit error.
- [x] **AC-03:** `list_prompts` truncates prompt text at tool boundary before map fan-out output.
- [x] **AC-04:** Graph contains deterministic Python `aggregate_themes` node between map classification and LLM grouping.
- [x] **AC-05:** `group_themes` consumes aggregated theme/count input, not raw full per-item payloads.
- [x] **AC-06:** Graph lints with `yamlgraph graph lint examples/demos/prompt_theme_analyzer/graph.yaml`.
- [x] **AC-07 (integration evidence):** Demo run with required vars and markdown report output is captured in committed `demo-output.log`.
- [x] **AC-08:** Unit tests cover source-dir requirement, truncation, filtering, deterministic aggregation, and report writing.
- [x] **AC-09:** `capabilities/CAP-149-prompt-theme-analyzer-demo.yaml` exists and declares `REQ-YG-359`; `ARCHITECTURE.md` includes manual rows for both `CAP-149` and `REQ-YG-359`.
- [x] **AC-10:** A diary reflection file is included in the change set.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr402_prompt_theme_analyzer_red.py`

Planned RED tests:

1. `test_ac01_demo_scaffold_files_exist`
2. `test_ac02_list_prompts_requires_source_dir`
3. `test_ac03_list_prompts_truncates_prompt_text_at_boundary`
4. `test_ac04_graph_has_python_aggregate_between_map_and_group`
5. `test_ac05_group_prompt_uses_aggregated_counts`
6. `test_ac08_list_prompts_filters_empty_or_invalid_inputs`
7. `test_ac08_aggregate_themes_is_deterministic_and_counts_correctly`
8. `test_ac08_write_report_produces_required_markdown_sections`
9. `test_ac09_capability_registry_contains_cap149_req359`

RED command:

```bash
pytest tests/unit/test_fr402_prompt_theme_analyzer_red.py -q --no-cov
```

Additional RED evidence commands (expected to fail pre-implementation):

```bash
test -f examples/demos/prompt_theme_analyzer/graph.yaml
test -f capabilities/CAP-149-prompt-theme-analyzer-demo.yaml
rg -n "REQ-YG-359|Prompt Theme Analyzer" capabilities/ ARCHITECTURE.md
```

**The RED test file must exist in the worktree before APPROVE can be granted.**
Create it, confirm `pytest tests/unit/test_fr402_prompt_theme_analyzer_red.py -q --no-cov` runs and all tests fail with `AssertionError` or `FileNotFoundError` (not `ImportError` or missing fixtures), then resubmit for judge.

## Judgement

**Verdict: AMEND** — four issues must be resolved before this FR can be APPROVED.

### Amendment Issues

1. **RED test file does not exist in the worktree (blocker).**
   The file `tests/unit/test_fr402_prompt_theme_analyzer_red.py` must be created with the nine test stubs listed above. Each test must fail for the right reason (missing implementation artifact — `AssertionError`, `FileNotFoundError`, `ImportError` from the demo module, not from the test harness itself). This is the established pattern for every FR in this repo (see `test_fr385_ci_copilot_trailer_gate_red.py`, `test_fr375_graph_run_json_stdout_red.py`). Without this file, APPROVE cannot be granted because the RED phase is unverified.

2. **"ARCHITECTURE.md regeneration" in AC-09 is inaccurate.**
   ARCHITECTURE.md is manually maintained — there is no regeneration script. `req_coverage.py` loads capabilities dynamically from `capabilities/CAP-*.yaml`, so adding `CAP-149-prompt-theme-analyzer-demo.yaml` is sufficient for the coverage tool. However, `req_coverage.py` also cross-checks that every requirement in the YAML registry has a row in `ARCHITECTURE.md`. The correct implementation steps are:
   - (a) Create `capabilities/CAP-149-prompt-theme-analyzer-demo.yaml` with `REQ-YG-359`.
   - (b) Manually add a `REQ-YG-359` row to the requirements table in `ARCHITECTURE.md`.
   - (c) Add a `CAP-149` row to the capabilities table in `ARCHITECTURE.md`.
   Replace "ARCHITECTURE.md regeneration is documented as an implementation step" with these explicit steps in AC-09.

3. **AC-10 has no corresponding RED test.**
   The failing-tests list covers AC-01 through AC-09 but omits AC-10 (diary reflection). Either add `test_ac10_diary_entry_exists` to the RED test file (checking that `docs/diary/` contains an entry newer than the FR date), or explicitly acknowledge AC-10 is CI-enforced via `diary-gate` only and does not need a unit test. The current omission creates a silent coverage gap.

4. **AC-07 integration scope is unqualified.**
   "Demo runs end-to-end with required vars and writes markdown report output" requires a live LLM API call. Mark it explicitly as an integration test (not run in unit CI) and note that it is satisfied by the committed `demo-output.log`. Without this qualification, a reader may expect it to pass in `pytest tests/unit/` — it will not.

### Approved Shape (do not change)

- 5-node graph: `list_prompts → classify_themes (map) → aggregate_themes (python) → group_themes (llm) → write_report`
- `source_dir` required, no default
- Truncation at Python boundary in `list_prompts`
- CAP-149 / REQ-YG-359 traceability
- `examples/demos/prompt_theme_analyzer/` location
- `demo-output.log` required in PR diff (demo-gate)

## Alternatives Considered

1. **Implement FR-393 unchanged.**
   Rejected: keeps unsupported truncation syntax and unbounded grouping payload.

2. **Pure Python/shell analysis without YAMLGraph.**
   Rejected: does not satisfy demo objective of showcasing YAMLGraph map/aggregate pattern.

3. **Single LLM pass for classify+group.**
   Rejected: weak determinism and poor scaling for large prompt sets.

## Related

- GitHub issue #402: <https://github.com/sheikkinen/yamlgraph/issues/402>
- `feature-requests/FR-393-prompt-theme-analyzer.md`
- `feature-requests/FR-254-diary-index-graph.md`
- `examples/demos/diary_index/graph.yaml`
- `examples/demos/diary_index/tools.py`
- `ARCHITECTURE.md` (REQ-YG-040/041/055/062/161/257)
