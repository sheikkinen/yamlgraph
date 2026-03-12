# Feature Request: Philosopher Copilot Node Migration

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Effort:** 0.5 days
**Requested:** 2026-03-12

> **Note:** This proposal duplicates **FR-185** (`feature-requests/FR-185-philosopher-copilot-nodes.md`), which is already **Approved** and scope-frozen as of 2026-03-11. This draft was generated from a stale inbox item. Recommend consuming this draft without creating a new FR number — proceed directly to enforcing FR-185.

## Judgement

**Verdict: REJECT** — Duplicate of FR-185.

**Reason:** This draft covers the identical scope as **FR-185** (`feature-requests/FR-185-philosopher-copilot-nodes.md`), which was already **Approved** and scope-frozen on 2026-03-11. The draft itself acknowledges the duplication (line 9). No new information, constraints, or acceptance criteria are introduced beyond what FR-185 already specifies.

**Action:** Proceed directly to enforcing FR-185. This draft is consumed without generating a new FR number.

## Summary

Migrate the philosopher daemon's `analyze` and `reflect` nodes from `type: llm` to `type: copilot`, aligning with the established chaplaincy pattern used by the watcher and enforcer daemons.

## Value Statement

Chaplaincy maintainers get a consistent node architecture across all chaplain daemons, eliminating Pydantic serialization friction and simplifying the philosopher graph while retaining full type safety via explicit Pydantic validation of parsed output.

## Problem

The philosopher daemon (`examples/philosopher/graph.yaml`) uses `type: llm` nodes for its `analyze` and `reflect` stages, while the watcher (`examples/copilot/graph.yaml`) and enforcer (`examples/enforce/graph.yaml`) use `type: copilot` nodes. This creates three friction points:

1. **Pydantic serialization issues** — `ProposalList is not JSON serializable` errors when the LLM node returns structured output that downstream tools struggle to unwrap. The `write_proposals()` tool already has a 4-way unwrap cascade (`.proposals`, `.model_dump()`, `dict.get()`, raw list) as a symptom.

2. **State type warnings** — `Unknown type 'dict[str, Any]'` warnings from the state builder when using complex inline schemas.

3. **Jinja2 template escaping complexity** — Prompts use `{{ scan_result | tojson(indent=2) }}` which requires careful escaping. Copilot nodes receive the full rendered prompt as a single CLI argument, sidestepping template engine interactions.

The enforcer graph (FR-183) demonstrates the target pattern: all LLM-heavy phases use `type: copilot`, Python tools handle scanning and file I/O.

## Proposed Solution

Replace the two `type: llm` nodes with `type: copilot` nodes. Prompts instruct copilot to emit parseable JSON. Downstream tools parse `CopilotResult.output` through Pydantic models — replacing the 4-way unwrap cascade with a single validated parse path.

### Graph changes (`examples/philosopher/graph.yaml`)

```yaml
# Before
  analyze:
    type: llm
    prompt: analyze
    ...
    state_key: proposals

# After
  analyze:
    type: copilot
    prompt: analyze
    variables:
      scan_result: "{state.scan_result}"
      graduation_threshold: "{state.graduation_threshold}"
    state_key: proposals
    timeout: 300
```

```yaml
# Before
  reflect:
    type: llm
    prompt: reflect
    ...
    state_key: diary_entry

# After
  reflect:
    type: copilot
    prompt: reflect
    variables:
      scan_result: "{state.scan_result}"
      proposals: "{state.proposals}"
    state_key: diary_entry
    timeout: 300
```

No `cli_flags: allow_all_paths` — these nodes perform pure reasoning (no filesystem access). All file I/O is handled by Python tool nodes.

### New Pydantic models (`examples/philosopher/models.py`)

```python
from pydantic import BaseModel, Field

class Proposal(BaseModel):
    type: str = Field(description="Category: trap, heuristic, or seed")
    name: str = Field(description="Pattern name (snake_case)")
    count: int = Field(description="Occurrence count across diary entries")
    files: list[str] = Field(description="Diary files where pattern appears")

class ProposalList(BaseModel):
    proposals: list[Proposal] = Field(default_factory=list)

class DiaryEntry(BaseModel):
    theme: str = Field(description="Short title (2-4 words)")
    body: str = Field(description="Main reflection in markdown")
    seed: str = Field(description="Forward-looking question")
```

### JSON extraction utility (`examples/philosopher/models.py`)

`extract_json(text, node_name)` strips markdown fences and preamble, finds JSON boundaries, raises `PipelineError` on failure (no silent fallbacks per Commandment 6).

### Tool changes (`examples/philosopher/tools.py`)

Replace the 4-way unwrap cascade in `write_proposals()` with: `CopilotResult → extract_json() → ProposalList.model_validate_json()`.

### Prompt changes

Remove `schema:` blocks from both prompts. Add explicit "output ONLY valid JSON" guards with format examples.

### State type changes

```yaml
# Before
  proposals: Any
  diary_entry: Any

# After
  proposals: dict     # CopilotResult envelope
  diary_entry: dict   # CopilotResult envelope
```

## Acceptance Criteria

- [ ] AC-1: `analyze` node uses `type: copilot` in `examples/philosopher/graph.yaml`
- [ ] AC-2: `reflect` node uses `type: copilot` in `examples/philosopher/graph.yaml`
- [ ] AC-3: `prompts/analyze.yaml` has no `schema:` block; includes "output ONLY valid JSON" guard
- [ ] AC-4: `prompts/reflect.yaml` has no `schema:` block; includes "output ONLY valid JSON" guard
- [ ] AC-5: `write_proposals()` parses `CopilotResult.output` through `ProposalList` — no multi-way unwrap cascade
- [ ] AC-6: All 19 existing philosopher tests pass (updated for new data shapes)
- [ ] AC-7: `yamlgraph graph lint examples/philosopher/graph.yaml` passes
- [ ] AC-8: No `ProposalList is not JSON serializable` errors at runtime
- [ ] AC-9: README.md table updated: `analyze` and `reflect` rows show `copilot` type
- [ ] AC-10: `ProposalList` and `DiaryEntry` Pydantic models in `examples/philosopher/models.py` with typed fields
- [ ] AC-11: `extract_json()` handles markdown fences, preamble, raises `PipelineError` on failure
- [ ] AC-12: No `cli_flags: allow_all_paths` on philosopher copilot nodes
- [ ] AC-13: Unit tests for `extract_json()` (clean JSON, fenced, preamble, malformed)
- [ ] AC-14: Unit tests for Pydantic model validation

## Alternatives Considered

1. **Keep `type: llm` and fix serialization** — Treats symptom but leaves architectural inconsistency and the 4-way unwrap cascade.
2. **Hybrid migration (one node only)** — Half-migrating increases inconsistency rather than reducing it.
3. **Raw `json.loads()` without Pydantic** — Violates Commandment 5; untyped dicts would wander downstream.

## Related

- **FR-185** — This exact scope (already approved)
- **FR-184** — Philosopher Daemon (original implementation)
- **FR-081** — Copilot Node Type
- **FR-183** — Simplified Enforce Pipeline (reference pattern)
- `examples/enforce/graph.yaml` — Reference copilot node usage
- `yamlgraph/node_factory/copilot_node.py` — Copilot node implementation
- `tests/unit/test_philosopher.py` — 19 existing tests across 5 classes
