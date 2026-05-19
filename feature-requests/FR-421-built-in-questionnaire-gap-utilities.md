# Feature Request: FR-421 Built-in Questionnaire Gap Utilities

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-19

## Summary

Add framework-shipped questionnaire helper functions (`detect_gaps`, `normalize_extracted`) under `yamlgraph.tools.questionnaire` so schema-driven probing loops can reuse one tested implementation instead of project-local copies.

## Value Statement

Graph authors get deterministic gap detection behavior with less duplicated Python, reducing per-project drift in questionnaire probing logic.

## Problem

Schema-driven questionnaires in this repository already rely on Python gap detection, but the logic is not provided as a framework primitive:

1. `examples/questionnaire/tools/handlers.py` implements `detect_gaps(state)` as project-local code.
2. `examples/questionnaire/graph.yaml` wires that handler through `type: python` tool nodes.
3. `reference/probe-recap-questionnaire.md` describes shared handlers, but `yamlgraph/tools/` has no questionnaire module today.

This creates a reuse gap: teams must copy helper logic into each project instead of importing a stable framework utility.

## Research Findings

1. Requested source `.chaplain/processing/gh-421.md` is not present in this worktree snapshot; topic was read from `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-421.md`.
2. Existing runtime support already enables this feature shape:
   - `yamlgraph/tools/python_tool.py` loads arbitrary module functions for `type: python` tools.
3. Prior art exists but is project-scoped:
   - `examples/questionnaire/tools/handlers.py::detect_gaps`
   - `examples/questionnaire/tests/test_handlers.py` and `test_graph_integration.py`
4. The framework currently ships only generic tool infrastructure (`agent.py`, `nodes.py`, `python_tool.py`, `shell.py`) and no questionnaire utility module.
5. `feature-requests/FR-415-built-in-detect-gaps-questionnaire-utility.md` documents a related idea but remains non-Draft (`Status: AMEND`) and carries unresolved framing/dependency notes; this FR defines a minimal, judgeable scope.

## Objectives

1. Provide `detect_gaps(state: dict) -> dict` in `yamlgraph.tools.questionnaire`.
2. Provide `normalize_extracted(state: dict) -> dict` in `yamlgraph.tools.questionnaire`.
3. Keep this as reusable Python tools (no new node type, no graph runtime contract changes).

## Constraints

1. Single responsibility: only questionnaire helper utilities; no new orchestration/runtime features.
2. Independent contract: caller must provide `state["schema"]` with `fields[].id` and `fields[].required`; no FR dependency on schema-loading features.
3. Deterministic output: `detect_gaps` must return sorted gap IDs.
4. Pure utility behavior:
   - `detect_gaps` only returns `gaps` + `has_gaps`.
   - `normalize_extracted` only normalizes `extracted`.
5. No new node types, DSL syntax, or linter rules in this FR.

## Proposed Solution

Add `yamlgraph/tools/questionnaire.py` with:

```python
def detect_gaps(state: dict) -> dict:
    extracted = state.get("extracted") or {}
    schema = state.get("schema") or {}
    gaps = sorted(
        field["id"]
        for field in schema.get("fields", [])
        if field.get("required") and (extracted.get(field["id"]) is None or extracted.get(field["id"]) == "")
    )
    return {"gaps": gaps, "has_gaps": bool(gaps)}


def normalize_extracted(state: dict) -> dict:
    extracted = state.get("extracted")
    if isinstance(extracted, dict):
        return {}
    return {"extracted": {}}
```

Implementation notes:

1. Keep function signatures compatible with existing `type: python` tool contract (state in, partial state update out).
2. Document expected state contract and YAML usage snippet in questionnaire reference docs.
3. Optional convenience export via `yamlgraph/tools/__init__.py` is acceptable but not required for YAML module loading.

## Acceptance Criteria

- [x] **AC-01:** `yamlgraph/tools/questionnaire.py` exists and defines `detect_gaps` and `normalize_extracted`.
- [x] **AC-02:** `detect_gaps` returns `{"gaps": [...], "has_gaps": bool}` where `gaps` contains every required field ID missing from `state["extracted"]`.
- [x] **AC-03:** `detect_gaps` treats `None` and empty string values as missing.
- [x] **AC-04:** `detect_gaps` ignores non-required fields and returns gaps in sorted order.
- [x] **AC-05:** `detect_gaps` returns `{"gaps": [], "has_gaps": False}` when all required fields are present.
- [x] **AC-06:** `normalize_extracted` returns `{}` when `state["extracted"]` is already a dict.
- [x] **AC-07:** `normalize_extracted` returns `{"extracted": {}}` when `state["extracted"]` is missing or any non-dict type.
- [x] **AC-08:** A graph tool config using `module: yamlgraph.tools.questionnaire` + `function: detect_gaps` compiles and executes through existing `type: python` mechanism.
- [x] **AC-09:** Documentation includes a usage snippet for both helpers in questionnaire pattern docs.
- [x] **AC-10:** Tests are requirement-tagged and requirement registry entries are added for this capability.

## Requirement Traceability Plan

Reserve and implement:

1. **REQ-YG-409** — Built-in `detect_gaps` utility contract (required-field detection, missing semantics, sorted output).
2. **REQ-YG-410** — Built-in `normalize_extracted` utility contract and `type: python` wiring example/verification.

Registry updates during enforcement:

1. Add `capabilities/CAP-153-questionnaire-gap-utilities.yaml` with REQ-YG-409 and REQ-YG-410.
2. Update `ARCHITECTURE.md` capability table with the new requirement rows.
3. Tag all new tests with `@pytest.mark.req("REQ-YG-409")` / `@pytest.mark.req("REQ-YG-410")`.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr421_questionnaire_gap_utilities_red.py`

Planned RED tests:

1. `test_ac02_detect_gaps_returns_required_missing_ids`
2. `test_ac03_detect_gaps_treats_none_and_empty_string_as_missing`
3. `test_ac04_detect_gaps_returns_sorted_gap_ids`
4. `test_ac05_detect_gaps_returns_no_gaps_when_complete`
5. `test_ac06_normalize_extracted_noop_when_dict`
6. `test_ac07_normalize_extracted_resets_nondict`
7. `test_ac08_yaml_module_wiring_compiles_and_runs_python_tool`
8. `test_ac01_module_exports_detect_gaps_and_normalize_extracted`

RED command:

```bash
pytest tests/unit/test_fr421_questionnaire_gap_utilities_red.py -q --no-cov
```

Expected RED state before implementation: import/module-not-found failures for `yamlgraph.tools.questionnaire` and behavior assertions not yet satisfied.

## Alternatives Considered

1. **Keep handlers project-local (status quo).**
   Rejected: duplicates logic and increases behavior drift across questionnaire graphs.
2. **Create a dedicated `detect_gaps` node type.**
   Rejected: unnecessary runtime surface expansion; existing `type: python` tools already solve integration.
3. **Embed gap logic in prompts/LLM output only.**
   Rejected: required-field completeness checks are deterministic and better implemented as Python utilities.

## Judgement

**Verdict:** APPROVE — scope frozen, authority granted to implement.

This FR qualifies as a **framework primitive**: 6+ identical implementations across ninchat_voice, and additional copies in `examples/questionnaire` and `projects/outcaller`. The `type: python` infrastructure is confirmed in place (`yamlgraph/tools/python_tool.py`). REQ-YG-409/410 are valid next available IDs (last assigned: REQ-YG-408). CAP-153 is confirmed next available (last: CAP-152).

**Pre-enforce notes (must address during enforcement, not blockers for authority):**

1. **FR-415 supersession**: After FR-421 lands, update `feature-requests/FR-415-built-in-detect-gaps-questionnaire-utility.md` status to `Superseded by FR-421`. Do not delete FR-415 — it contains the amendment history.

2. **`probe_count` divergence from example handler**: The existing `examples/questionnaire/tools/handlers.py::detect_gaps` also returns `probe_count`. The framework utility intentionally omits this — `probe_count` management belongs in the graph, not the utility. Add one inline comment in the new module noting this intentional divergence so migrators are not confused.

3. **RED tests before implementation**: Write `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` (8 planned test functions) as the first enforcement commit. Verify they fail for `ModuleNotFoundError` on `yamlgraph.tools.questionnaire`, not for fixture or infrastructure issues.

4. **AC-09 doc target**: Update `reference/probe-recap-questionnaire.md` and/or `reference/intent-questionnaire-pattern.md` with the YAML wiring snippet. Either file is acceptable; pick the one where the pattern is introduced.

**Scope freeze:**
- In scope: `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py`, ARCHITECTURE.md rows for REQ-YG-409/410, `capabilities/CAP-153-questionnaire-gap-utilities.yaml`, `changelog/unreleased/` fragment, one questionnaire reference doc snippet.
- Out of scope: `probe_count` management, FR-414, new node types, linter rules, any changes to example handler code.

---

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-421.md`
- Prior draft: `feature-requests/FR-415-built-in-detect-gaps-questionnaire-utility.md` (to be superseded)
- Existing prior art:
  - `examples/questionnaire/tools/handlers.py`
  - `examples/questionnaire/graph.yaml`
  - `examples/questionnaire/tests/test_handlers.py`
  - `examples/questionnaire/tests/test_graph_integration.py`
- Runtime integration path:
  - `yamlgraph/tools/python_tool.py`
  - `tests/unit/test_python_nodes.py`
- Architecture traceability source:
  - `ARCHITECTURE.md`
  - `capabilities/`
