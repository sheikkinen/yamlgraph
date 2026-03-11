# FR-178: Eliminate `execute_prompt()` from probe_recap Python Tool Node

**Priority:** MEDIUM
**Type:** Refactor
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-03-10

## Summary

`projects/outcaller/nodes/probe_recap.py::extract_answers()` calls `execute_prompt()`
directly from a Python tool node. Replace it with a declarative `llm` node in
`outcaller.yaml` so that all LLM invocations are expressed in YAML — eliminating
the root cause of OC-013 (stray Mistral invocations) and restoring alignment with
the three-layer architecture.

## Value Statement

Graph authors and operators benefit from all LLM calls being visible in YAML, making
provider selection, prompt resolution, and tracing deterministic and auditable without
reading Python implementation files.

## Problem

`extract_answers()` in `probe_recap.py` (lines 61–114) calls `execute_prompt()`
directly:

```python
# probe_recap.py ~line 90
result = execute_prompt(
    "shared/extract_answers",
    {...},
    output_model=output_model,
    prompts_dir=str(prompts_path),
)
```

This violates Architecture Commandment 3 (LLM orchestration belongs in YAML graphs,
not Python tools). The consequences are:

1. **Provider silently misresolves.** `execute_prompt()` resolves provider via:
   function arg → prompt YAML `metadata` → `PROVIDER` env var. When called from a
   Python tool, the YAML `metadata` block must be explicit; any miss falls through to
   `PROVIDER=mistral` (OC-013). A `metadata: provider: google` guard was added as a
   stopgap (OC-012) but it is a patch on a structural defect.

2. **Tracing gap.** LangSmith traces the Python tool invocation, not the LLM call
   inside it, obscuring the actual LLM span.

3. **Test coupling.** Tests must mock `execute_prompt` at the Python import level,
   not at the YAML-node level where the rest of the graph is tested.

**Why the hack exists (historical).** The original motivation was that the output
schema needed to be built dynamically from `target_fields` (user-supplied at call
start). In practice the prompt now uses a static generic schema:

```yaml
# prompts/shared/extract_answers.yaml
schema:
  name: Extraction
  fields:
    updates:
      type: "dict[str, Any]"
      description: "Map of field_id to extracted value, null if not found in transcript"
    user_refused:
      type: bool
      description: "True if caller refused to participate"
```

This schema is fully static. `load_schema_from_yaml()` is called at runtime in
`extract_answers()` but it reads the same YAML every time. There is no runtime
schema construction from `target_fields`. The hack is therefore no longer justified
by technical necessity.

**Dynamic `prompts_dir` from state.** The Python code also reads
`prompts_dir = state.get("prompts_dir", "projects/outcaller/graphs/prompts")` to
support project-specific prompt overrides. This is the only non-trivial coupling to
state that must be addressed in the YAML graph or by using the
`prompts_relative: true` node option.

## Proposed Solution

### Step 1 — Remove the Python LLM call

Convert the `extract_answers` node in `outcaller.yaml` from `type: python` to
`type: llm` with the existing `shared/extract_answers` prompt. The schema is already
embedded in the prompt YAML and is loaded at compile time by
`get_output_model_for_node()`.

```yaml
# outcaller.yaml
nodes:
  extract_answers:
    type: llm
    prompt: shared/extract_answers
    # schema is inline in prompts/shared/extract_answers.yaml — no output_model needed
    state_key: extraction_result
    loop_limit: 6
    input:
      call_context: "{{ call_context }}"
      target_fields: "{{ target_fields }}"
      extracted: "{{ extracted }}"
      transcript: "{{ transcript }}"
      answers: "{{ answers }}"
```

### Step 2 — Move post-processing into a follow-on tool node

The merge logic (overwrite only non-null fields, increment `probe_count`, propagate
`user_refused`) cannot be expressed in a bare `llm` node. A small, pure Python
function node handles it without any LLM call:

```python
# probe_recap.py — replaces extract_answers()
def merge_extraction(state: dict[str, Any]) -> dict[str, Any]:
    """Merge non-null LLM extraction results into accumulated extracted dict."""
    result = state["extraction_result"]
    merged = dict(state["extracted"])
    for field_id, value in result.updates.items():
        if value is not None:
            merged[field_id] = value
    return {
        "extracted": merged,
        "probe_count": state.get("probe_count", 0) + 1,
        "user_refused": result.user_refused,
    }
```

Wire as: `extract_answers (llm) → merge_extraction (python) → check_missing`.

### Step 3 — Resolve `prompts_dir` at the graph level

The `prompts_dir` override is currently passed via state by callers. For the
outcaller graph this is always `"projects/outcaller/graphs/prompts"`. Use
`prompts_relative: true` on the node or pin the graph-level `prompts_dir` in the
YAML header. If incaller also needs the shared node, it should declare its own
`extract_answers` llm node pointing to its own `prompts_dir` — not share Python code
that injects state variables.

### Out of scope

- `schema_from_state` framework extension (not needed; schema is already static in
  prompt YAML). If a future use case genuinely requires per-run schema construction,
  open a separate FR.

## Acceptance Criteria

- [x] `extract_answers()` in `probe_recap.py` contains zero `execute_prompt()` or
      `load_schema_from_yaml()` calls.
- [x] `outcaller.yaml` declares an `llm` node (or equivalent) for extraction — no
      `type: python` node calls an LLM for this step.
- [x] Provider for the extraction call is resolved entirely from the `metadata` block
      in `extract_answers.yaml`; changing `PROVIDER` env var does not affect it.
- [x] All existing `tests/unit/test_probe_recap.py` tests pass (mocks updated to
      target the YAML-node boundary if needed).
- [x] A new unit test exercises `merge_extraction` with a stubbed `extraction_result`
      in state (no LLM call), tagged `@pytest.mark.req("REQ-YG-083")`.
- [x] `pytest tests/unit/ -q --no-cov` passes.
- [x] `ruff check yamlgraph/ projects/outcaller/` passes.

## Alternatives Considered

1. **Keep the Python call, add a stricter provider guard** — The OC-012 `metadata`
   guard is already in place. This keeps the structural defect and the tracing gap.
   Rejected: treats symptom, not root cause.

2. **`schema_from_state` framework extension** — Build the Pydantic model at runtime
   from `target_fields` values in state, making each field a typed attribute. Provides
   richer LLM constraints per call. Rejected for this FR: the current generic dict
   schema works correctly and the extension is non-trivial. Viable as a follow-on FR
   if field-level typing proves useful.

3. **Inline the LLM call into a map node** — Over-engineered for a single extraction
   step. Rejected.

## Related

- `projects/outcaller/nodes/probe_recap.py` — contains the sin (lines 61–114)
- `projects/outcaller/graphs/outcaller.yaml` — graph to be updated
- `projects/outcaller/graphs/prompts/shared/extract_answers.yaml` — static schema source
- `yamlgraph/node_factory/base.py::get_output_model_for_node()` — compile-time schema resolution
- OC-012 / OC-013 — incident records for the Mistral provider misresolution
- `feature-requests/FR-079-*` — introduced `shared/extract_answers` prompt
