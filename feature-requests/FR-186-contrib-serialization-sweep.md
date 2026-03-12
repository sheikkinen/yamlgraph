# Feature Request: Contrib Serialization Sweep

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-11
**Depends on:** FR-044 (complete), FR-044b (complete)

## Summary

Replace remaining inline `hasattr(obj, "model_dump")` patterns in `examples/` and `questionnaire-api/` with `to_serializable()` from `yamlgraph.contrib`. Completes the migration started in FR-044b.

## Value Statement

Contributors see one canonical serialization pattern instead of ad-hoc inline checks, reducing copy-paste drift and making Pydantic v3 migration a single-function change.

## Problem

FR-044b migrated 10 files but left ~10 inline `hasattr(obj, "model_dump")` checks across 8 files. These are duplication hotspots that `jscpd` may flag and that diverge over time.

**Remaining inline patterns (verified by grep):**

| File | Line(s) | Semantic |
|------|---------|----------|
| `examples/philosopher/tools.py` | 122, 138 | L122: `model_dump().get("proposals", [])` — extract-after-dump. L138: simple dump. |
| `examples/storyboard/nodes/image_node.py` | 44 | Simple dump with dict/str fallback |
| `examples/npc/demo.py` | 251 | Converts to `str()`, not dict — display-only |
| `examples/questionnaire/tools/handlers.py` | 147 | `_to_dict()` returns `{}` for non-dicts — **different semantics** |
| `questionnaire-api/src/api/routes/v2/sessions.py` | 363 | `model_dump().get("values", dumped)` — extract-after-dump |
| `questionnaire-api/src/api/routes/questionnaire.py` | 267 | Same extract-after-dump pattern as sessions.py |
| `questionnaire-api/src/questionnaire/handlers/gaps.py` | 22, 28, 86 | Complex multi-branch: `.values` attr check, dump+get, Pydantic v1 fallback |
| `questionnaire-api/src/questionnaire/handlers/scoring.py` | 26 | `model_dump().get("values", {})` — extract-after-dump |

### Semantic Categories

**Category A — Direct replacement** (pattern identical to `to_serializable`):
- `philosopher/tools.py:138` — simple item dump

**Category B — Compose with `to_serializable`** (dump then extract key or add fallback):
- `storyboard/nodes/image_node.py:44` — dump with non-dict fallback (must preserve `else` branch)
- `philosopher/tools.py:122` — `to_serializable(x).get("proposals", [])`
- `questionnaire-api` sessions.py, questionnaire.py, scoring.py — `to_serializable(x).get("values", ...)`

**Category C — Exclude** (semantics differ):
- `npc/demo.py:251` — `str(model)` uses Pydantic `__repr__` (e.g., `Summary(field='value')`); `str(to_serializable(model))` produces `str(dict)` (e.g., `{'field': 'value'}`). Display-only context but output format changes. Violates the "blind pattern replacement" principle (Alternative #3).
- `questionnaire/tools/handlers.py` — `_to_dict()` returns `{}` for non-dicts; `to_serializable` returns input unchanged. Replacing breaks callers that expect a dict. Already excluded in FR-044b.
- `questionnaire-api/src/questionnaire/handlers/gaps.py` — Three-branch logic: `.values` attribute access, dump+get, Pydantic v1 `dict()` fallback. Too complex for `to_serializable`; would need a dedicated `extract_values()` helper, which is out of scope.

## Proposed Solution

Replace Category A and B patterns. Leave Category C unchanged.

### Category A — Direct replacement

```python
# Before (philosopher/tools.py:138)
if hasattr(proposal, "model_dump"):
    proposal = proposal.model_dump()
elif hasattr(proposal, "get"):
    pass  # Already a dict
else:
    continue  # Skip unknown types

# After
from yamlgraph.contrib import to_serializable
proposal = to_serializable(proposal)
if not isinstance(proposal, dict):
    continue  # Skip unknown types
```

### Category B — Compose

**storyboard/nodes/image_node.py** — Preserves the `else` fallback for non-model/non-dict inputs (e.g., a bare string). Without the fallback, downstream `story_dict.get("panels", [])` would raise `AttributeError` on non-dict inputs:

```python
# Before (storyboard/nodes/image_node.py:44)
if hasattr(story, "model_dump"):
    story_dict = story.model_dump()
elif isinstance(story, dict):
    story_dict = story
else:
    story_dict = {"panels": [str(story)]}

# After
from yamlgraph.contrib import to_serializable
story_dict = to_serializable(story)
if not isinstance(story_dict, dict):
    story_dict = {"panels": [str(story_dict)]}
```

**philosopher/tools.py:122** — Uses a local variable to avoid double invocation. This intentionally collapses the original `hasattr(model_dump)` and `isinstance(dict)` branches into one, since `to_serializable` normalizes both Pydantic models and dicts to dicts:

```python
# Before (philosopher/tools.py:115-127)
if hasattr(proposals_raw, "proposals"):
    proposals = proposals_raw.proposals
elif hasattr(proposals_raw, "model_dump"):
    proposals = proposals_raw.model_dump().get("proposals", [])
elif isinstance(proposals_raw, dict):
    proposals = proposals_raw.get("proposals", [])
else:
    proposals = proposals_raw if isinstance(proposals_raw, list) else []

# After
from yamlgraph.contrib import to_serializable
serialized = to_serializable(proposals_raw)
if hasattr(proposals_raw, "proposals"):
    proposals = proposals_raw.proposals
elif isinstance(serialized, dict):
    proposals = serialized.get("proposals", [])
elif isinstance(serialized, list):
    proposals = serialized
else:
    proposals = []
```

**questionnaire-api sessions.py / questionnaire.py / scoring.py** — Extract key after serialization:

```python
# Before (sessions.py / questionnaire.py)
if hasattr(extracted, "model_dump"):
    dumped = extracted.model_dump()
    extracted = dumped.get("values", dumped)
elif isinstance(extracted, dict) and "values" in extracted:
    extracted = extracted["values"]

# After
from yamlgraph.contrib import to_serializable
extracted = to_serializable(extracted)
if isinstance(extracted, dict) and "values" in extracted:
    extracted = extracted["values"]
```

```python
# Before (scoring.py)
if hasattr(extracted_raw, "model_dump"):
    extracted = extracted_raw.model_dump().get("values", {})
elif isinstance(extracted_raw, dict) and "values" in extracted_raw:
    extracted = extracted_raw["values"]
elif isinstance(extracted_raw, dict):
    extracted = extracted_raw

# After
from yamlgraph.contrib import to_serializable
extracted = to_serializable(extracted_raw)
if isinstance(extracted, dict) and "values" in extracted:
    extracted = extracted["values"]
elif not isinstance(extracted, dict):
    extracted = {}
```

### Exclusions (documented, not changed)

- `yamlgraph/map_compiler.py` (3×) — Core framework; intentionally shallow `model_dump()` for map flattening (FR-052). Cannot depend on contrib.
- `examples/npc/demo.py:251` — `str(model)` uses Pydantic `__repr__`; `str(to_serializable(model))` produces `str(dict)`. Different output format.
- `examples/questionnaire/tools/handlers.py` — `_to_dict()` returns `{}` for non-dicts. Documented in FR-044b.
- `questionnaire-api/src/questionnaire/handlers/gaps.py` — Multi-branch ExtractionResult unwrapping with Pydantic v1 fallback. Needs a dedicated helper (future FR).

## Acceptance Criteria

- [ ] Category A inline check replaced with `to_serializable()` (1 file: `philosopher/tools.py:138`)
- [ ] Category B inline checks composed with `to_serializable()` (5 sites: `philosopher/tools.py:122`, `storyboard/nodes/image_node.py:44`, `sessions.py`, `questionnaire.py`, `scoring.py`)
- [ ] storyboard replacement preserves the `else` fallback for non-dict inputs
- [ ] philosopher:122 replacement uses local variable (no double `to_serializable` invocation)
- [ ] philosopher:122 branch collapse (model_dump + dict → single dict branch) documented in commit
- [ ] Category C exclusions documented in this FR (no code changes): `npc/demo.py`, `handlers.py`, `gaps.py`
- [ ] `map_compiler.py` untouched (3 inline checks remain, documented exclusion)
- [ ] Existing tests pass — no functional changes (`pytest tests/ -q`)
- [ ] `jscpd` duplication check passes
- [ ] `ruff check` passes
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-070")` (existing CAP-20 requirement)

## Alternatives Considered

1. **Create `extract_values()` in contrib** — Would handle the questionnaire-api patterns but adds a new function for 4 call sites. Not justified; compose with `to_serializable` + `.get()` is clearer.
2. **Replace gaps.py too** — The three-branch logic is too complex. A future FR could introduce `extract_values()` if the pattern recurs.
3. **Global regex replace** — Explicitly rejected. The diary entry (2026-02-17) documents the "blind pattern replacement" trap: patterns *look* identical but semantics differ (e.g., `_to_dict` returns `{}` for non-dicts, storyboard has a non-dict fallback).

## Related

- FR-044: `yamlgraph.contrib` creation (COMPLETE)
- FR-044b: First migration wave — 10 files (COMPLETE)
- FR-052: Map output flattening — owns `map_compiler.py` inline checks
- CAP-20: Contrib Utilities capability (REQ-YG-070)
- `docs/diary-2026-02-17.md`: Documents the blind replacement trap
- `reference/contrib.md`: Contrib usage guide
