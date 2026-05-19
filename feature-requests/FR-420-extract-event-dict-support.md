# Feature Request: FR-420 extract_event must handle plain dicts

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-19

## Summary

`extract_event()` in `yamlgraph/utils/fsm/helpers.py` handles `str` and Pydantic models but **not plain `dict`**. When LangGraph's `ainvoke` returns the final state, a `CopilotResult` Pydantic model stored under a TypedDict field annotated as `dict` arrives as a plain Python dict. `extract_event` returns `None`, the event_map never matches, and the FSM falls through to `success_event = "error"`. This silently kills every watcher pipeline judge step.

## Value Statement

Watcher2 pipeline judge steps reach APPROVE/AMEND/REJECT verdicts instead of dying with `event=error`. GH-420, GH-421, and any future graph that stores `CopilotResult` under a `dict`-typed state key all benefit.

## Problem

### Root cause

`extract_event(raw, event_map)` handles two branches:
1. `isinstance(raw, str)` — direct + first-line match
2. `hasattr(raw, "model_dump")` — iterates Pydantic field values

It has no branch for `isinstance(raw, dict)`. When LangGraph's state machinery processes a node returning `{state_key: CopilotResult(...)}` for a TypedDict field declared as `dict`, the Pydantic wrapper is stripped and `ainvoke` returns the value as a plain Python dict (confirmed by proof test).

```
extract_event(CopilotResult instance, event_map) → "approve"   ✓
extract_event({"output": "APPROVE\n...", ...},  event_map) → None  ✗
```

### Evidence from logs

`logs/fsm-pipeline-gh-420-20260519-174713.log` (and gh-421 equivalent):
```
[judge] Copilot CLI completed with exit code 0
✅ yamlgraph_async completed: event=error elapsed_ms=59902
judge --error--> failed
```
— copilot returned APPROVE, `judge_result` was a plain dict, `extract_event` returned None,
  fell through to `success_event = "error"`.

The `🗺️ event_map: ... → ...` log line is absent — `extract_event` never found a match.

### Proof

`feature-requests/FR-420/proof_extract_event_dict_bug.py` — run standalone, no chaplain needed:
```
python feature-requests/FR-420/proof_extract_event_dict_bug.py
```

Case 1 (Pydantic instance): all 4 verdicts extracted ✓
Case 2 (plain dict):         all 4 return None        ✗ ← confirmed bug
Case 3 (state simulation):   Pydantic ✓  plain dict ✗

## Proposed Solution

**Normalize at the boundary** (the one law). The boundary is `extract_event`. Add a `dict` branch that mirrors the `model_dump()` branch — iterate string values, apply the same first-line match logic.

### Change: `yamlgraph/utils/fsm/helpers.py`

```python
def extract_event(raw: Any, event_map: dict[str, str]) -> str | None:
    if isinstance(raw, str):
        candidate = raw.strip().lower()
        mapped = event_map.get(candidate)
        if mapped:
            return mapped
        first_line = candidate.split("\n", 1)[0].strip()
        return event_map.get(first_line)

    # NEW: plain dict (e.g. CopilotResult serialized by LangGraph state machinery)
    if isinstance(raw, dict):
        for field_value in raw.values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
                if mapped:
                    return mapped
                first_line = candidate.split("\n", 1)[0].strip()
                mapped = event_map.get(first_line)
                if mapped:
                    return mapped

    if hasattr(raw, "model_dump"):
        for field_value in raw.model_dump().values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
                if mapped:
                    return mapped
                first_line = candidate.split("\n", 1)[0].strip()
                mapped = event_map.get(first_line)
                if mapped:
                    return mapped

    return None
```

**Why dict before model_dump**: A Pydantic model with `model_dump()` iterates the same dict values anyway; putting dict first handles the serialized case without code duplication. The Pydantic branch remains for direct-model callers.

## Scope

- `yamlgraph/utils/fsm/helpers.py` — add dict branch to `extract_event`
- `tests/unit/test_fr416_extract_event_first_line.py` — extend with dict-input cases
- Proof test already exists at `feature-requests/FR-420/proof_extract_event_dict_bug.py`

## Out of Scope

- Changing judge graph state annotation from `dict` to `str` — that would work around the bug but violate "normalize at boundary"; the boundary is `extract_event`
- Changing `copilot_runtime.py` to store a plain string — loses structured metadata (exit_code, session_id, backend)

## Acceptance Criteria

- [ ] `extract_event({"output": "APPROVE\nreasoning"}, event_map)` → `"approve"`
- [ ] `extract_event({"output": "AMEND\nreasoning"}, event_map)` → `"revise"`
- [ ] Existing string and Pydantic-model cases unchanged
- [ ] `proof_extract_event_dict_bug.py` exits 0 after fix (currently exits 1)
- [ ] Full unit suite clean
- [ ] REQ-YG-319 tests still pass

## REQ Traceability

Extends REQ-YG-319 (FSM bridge shared module: `extract_event` contract). No new REQ needed — this is a missing input-type case in an existing function.

## Judgement

**Verdict:** APPROVE WITH AMENDMENTS - Scope frozen, authority granted after incorporating the constraints below.

The defect is real and currently reproducible in the codebase:

1. `extract_event()` in `yamlgraph/utils/fsm/helpers.py` has `str` and `model_dump()` paths, but no `dict` path.
2. The FR proof script reproduces the boundary failure: Pydantic model input maps correctly, plain dict input returns `None`.
3. The failing path matches production routing behavior: unresolved event mapping falls through to `success_event = "error"`.

Required amendments before enforce:

1. Condemn with RED tests first.
Add failing unit coverage for dict inputs across all verdict tokens before changing production code.
2. Keep matching deterministic and narrow.
Use exact match first, first-line fallback second; do not add fuzzy/substring parsing.
3. Preserve extraction precedence.
Do not alter existing string or Pydantic behavior while adding dict support.
4. Add bridge-level evidence for routing behavior.
Include at least one test proving `_resolve_event`-equivalent behavior with `result[event_key]` as a plain dict routes correctly after fix.
5. Keep fix at the boundary.
Do not rewrite watcher graph state annotations or copilot output schema as part of this FR.

Scope freeze:

1. In scope:
`yamlgraph/utils/fsm/helpers.py`, targeted FSM helper/bridge tests, FR-420 proof script maintenance if needed for deterministic repro.
2. Out of scope:
Watcher graph prompt redesign, changing judge state key type contracts, generalized event parser redesign beyond dict parity.

Acceptance bar for merge:

1. RED -> GREEN evidence for dict-input extraction.
2. Existing FR-416 first-line extraction tests remain green (no regression).
3. Proof script demonstrates bug is gone (`plain dict` case maps verdict events and exits 0).
4. Requirement tags remain present on new/updated tests (`REQ-YG-319`).

**Judge:** GitHub Copilot (Claude Sonnet 4.6), 2026-05-19

---

## Judgement Review

**Reviewing judge:** GitHub Copilot (Claude Sonnet 4.6), 2026-05-19

**Original verdict upheld** with two amendments below.

### What the prior judgement got right

1. Root cause is correctly identified and proven by the proof script.
2. RED-before-GREEN constraint is correct per Scripture.
3. Scope freeze is precise and minimal.
4. "Normalize at the boundary" principle correctly applied — fix in `extract_event`, not in callers.

### Amendment A — Eliminate code duplication in the proposed implementation

The proposed solution adds a `dict` branch with a loop body identical to the `model_dump` branch. The branches are disjoint (`isinstance(Pydantic, dict)` is `False`) so there is no correctness bug, but the duplication will drift. The correct implementation unifies both non-string paths:

```python
def extract_event(raw: Any, event_map: dict[str, str]) -> str | None:
    if isinstance(raw, str):
        candidate = raw.strip().lower()
        mapped = event_map.get(candidate)
        if mapped:
            return mapped
        first_line = candidate.split("\n", 1)[0].strip()
        return event_map.get(first_line)

    # Handles both plain dict (LangGraph serialized state) and Pydantic models
    d: dict | None = raw if isinstance(raw, dict) else (
        raw.model_dump() if hasattr(raw, "model_dump") else None
    )
    if d is not None:
        for field_value in d.values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
                if mapped:
                    return mapped
                first_line = candidate.split("\n", 1)[0].strip()
                mapped = event_map.get(first_line)
                if mapped:
                    return mapped

    return None
```

This is shorter, DRY, and the type annotation `d: dict | None` documents both inputs at the boundary.

### Amendment B — New test file, not extension of FR-416

The prior judgement targets `tests/unit/test_fr416_extract_event_first_line.py` for dict-input tests. FR-416's test file is scoped to first-line extraction on strings and Pydantic models. Adding dict cases there mixes responsibilities and obscures the FR-420 change in blame/revert. Use a new `tests/unit/test_fr420_extract_event_dict_support.py` tagged `@pytest.mark.req("REQ-YG-319")`.

### Constraints carried forward unchanged

1. RED tests before implementation.
2. Exact match first, first-line fallback second — no fuzzy/substring parsing.
3. Existing string and Pydantic-model behavior must remain identical.
4. At least one test proving `_resolve_event`-equivalent routing with `result[event_key]` as plain dict.
5. Fix only in `helpers.py`; no watcher graph or schema changes.

### Revised acceptance bar

1. RED → GREEN evidence using the unified implementation (Amendment A).
2. Test file is `test_fr420_extract_event_dict_support.py` (Amendment B).
3. All FR-416 first-line tests remain green.
4. `proof_extract_event_dict_bug.py` exits 0 (Case 2 maps all verdicts, Case 3 plain dict maps correctly).
5. Full unit suite clean.

**Status after review:** APPROVE — scope frozen, authority granted.
