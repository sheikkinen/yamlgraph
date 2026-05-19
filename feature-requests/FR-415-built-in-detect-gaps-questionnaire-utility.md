# FR-415: Built-in detect_gaps Questionnaire Utility

**Status:** AMEND — see amendment notes below before implementing

---

## Problem

Every schema-driven questionnaire graph in ninchat_voice re-implements the same `detect_gaps()` function: iterate schema fields where `required: true`, check which are missing from `state.extracted`, return sorted gap list. The logic is 15-20 lines of pure Python with zero domain coupling — identical across 6+ graphs.

Similarly, `normalize_extracted()` (coerce non-dict race output to `{}`) is duplicated verbatim.

## Proposal

Provide these as framework-shipped reusable tool functions:

```yaml
tools:
  check_gaps:
    type: python
    module: yamlgraph.tools.questionnaire
    function: detect_gaps
    # reads: state.schema.fields (required=true), state.extracted
    # writes: state.gaps (list[str]), state.has_gaps (bool)

  normalize:
    type: python
    module: yamlgraph.tools.questionnaire
    function: normalize_extracted
    # reads: state.extracted
    # writes: state.extracted (coerced to dict)
```

Not a new node type — just reusable tool functions shipped with the framework, following the existing `yamlgraph.tools.*` pattern.

## Implementation

```python
# yamlgraph/tools/questionnaire.py

def detect_gaps(state: dict) -> dict:
    extracted = state.get("extracted") or {}
    schema = state.get("schema") or {}
    gaps = sorted(
        f["id"] for f in schema.get("fields", [])
        if f.get("required") and not extracted.get(f["id"])
    )
    return {"gaps": gaps, "has_gaps": bool(gaps)}

def normalize_extracted(state: dict) -> dict:
    extracted = state.get("extracted")
    if isinstance(extracted, dict):
        return {}
    return {"extracted": {}}
```

## Acceptance Criteria

- [ ] `yamlgraph/tools/questionnaire.py` is created with `detect_gaps` and `normalize_extracted` functions.
- [ ] `detect_gaps(state)` returns `{"gaps": sorted_list, "has_gaps": bool}` where `sorted_list` contains the `id` of every field with `required: true` whose value is absent from `state["extracted"]`.
- [ ] `detect_gaps` returns `{"gaps": [], "has_gaps": False}` when `state["extracted"]` is `None` or `{}`.
- [ ] `detect_gaps` returns `{"gaps": [], "has_gaps": False}` when all required fields are present.
- [ ] `detect_gaps` returns gaps in sorted order.
- [ ] `normalize_extracted` returns `{}` (no state change) when `state["extracted"]` is already a dict.
- [ ] `normalize_extracted` returns `{"extracted": {}}` when `state["extracted"]` is `None`, a string, a list, or any non-dict type.
- [ ] Both functions are importable via `from yamlgraph.tools.questionnaire import detect_gaps, normalize_extracted`.
- [ ] A YAML graph that wires `check_gaps` and `normalize` as `type: python` tools resolves and executes correctly.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-XXX")` (see amendment note below) cover all ACs above.
- [ ] Changelog fragment added to `changelog/unreleased/`.

## Context

- Companion to FR-414 (schema-as-state loader) — `detect_gaps` reads `state["schema"]`; see amendment note on dependency.
- ninchat_voice has 6+ identical copies of this logic.
- Zero domain coupling — works for any schema with `fields[].id` + `fields[].required`.
- The questionnaire pattern (extract → detect_gaps → probe → loop) is emerging as a reusable graph topology.

---

## Amendment Notes (Judge — 2026-05-19)

The core proposal is valid: 6+ identical 15-20 line duplications with zero domain coupling qualify as a **framework primitive**. The `type: python` tool mechanism is confirmed supported (see `yamlgraph/tools/python_tool.py`). However, the FR cannot enter enforcement as-is because:

### 1. No acceptance criteria (blocker)
The original proposal had no `## Acceptance Criteria` section. Without measurable ACs, tests cannot be written before implementation — violating TDD. ACs have been added above; verify they cover all intended behaviour before implementing.

### 2. No REQ-YG-XXX requirement ID (blocker)
Every new capability must be registered in `ARCHITECTURE.md` and `scripts/req_coverage.py` per ADR-001. The next available IDs after REQ-YG-408 must be assigned. Add one requirement row per distinct testable contract (expect 1–2 rows). Update `ALL_REQS` range in `scripts/req_coverage.py` and tag all tests with the new IDs. Replace `REQ-YG-XXX` in the ACs above with the actual assigned IDs.

### 3. Implementation discrepancy: `detect_gaps` must sort its output (bug in original)
The problem description says "return sorted gap list" but the original implementation returned an unsorted list comprehension. The corrected implementation above uses `sorted()`. Enforce this in tests.

### 4. FR-414 dependency must be declared or removed
`detect_gaps` reads `state.get("schema")` which assumes a schema object is already in state. FR-414 ("schema-as-state loader") is cited as the companion that would provide this, but FR-414 does not exist in `feature-requests/`. Before implementing FR-415, clarify:
- If FR-414 is a prerequisite: create FR-414 first and add it as a declared dependency here.
- If FR-415 is independent (any caller can load schema into state any way they choose): remove the FR-414 companion reference and document the expected `state["schema"]` contract inline.

### 5. No changelog fragment referenced
A `feat` PR requires a changelog fragment in `changelog/unreleased/`. Add this step to the implementation checklist.
