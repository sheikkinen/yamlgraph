# Feature Request: FR-185 Philosopher Copilot Node Migration

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-11
**Judged:** 2026-03-11

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

### Evaluation

| Criterion | Assessment |
|---|---|
| Scope clear and minimal? | ✅ Exactly 2 nodes migrated, with tightly-coupled prompt/tool/model changes. No feature creep. |
| Contradictions or ambiguities? | ⚠️ Minor — see notes below. None block implementation. |
| Acceptance criteria measurable? | ✅ All 14 ACs are concrete and verifiable. Test counts verified (19 tests, 5 classes). |
| Implementation approach feasible? | ✅ Infrastructure exists: `CopilotResult` model, `copilot_node.py` factory, established patterns in enforcer and watcher graphs. |
| Aligns with architecture? | ✅ Follows three-layer pattern (copilot = logic, tools = side effects). Honors Commandments 5 (Pydantic) and 6 (no silent fallbacks). |
| Single responsibility? | ✅ All changes serve one goal: migrate philosopher reasoning nodes to copilot type. |

### Notes for implementer

1. **`extract_json()` location unspecified.** The FR shows the utility code but doesn't declare its file path. Recommended: place in `examples/philosopher/models.py` alongside the Pydantic models, since it imports `PipelineError` from core but is philosopher-specific logic. If a second consumer appears later, promote to `yamlgraph/utils/`.

2. **Prompt paths are relative.** The FR references `prompts/analyze.yaml` — the actual paths are `examples/philosopher/prompts/analyze.yaml` and `examples/philosopher/prompts/reflect.yaml`. The implementer should follow actual filesystem paths.

3. **Watcher graph is not fully copilot.** The FR states the watcher "uses `type: copilot` nodes" — accurate for `plan` and `judge`, but the watcher's `summarize` node uses `type: llm`. This doesn't affect the solution but the problem statement slightly overstates the inconsistency.

4. **`write_proposals()` fallback branch.** The proposed code retains `elif hasattr(proposals_raw, "proposals")` for testability with mock data. Acceptable — this is a conscious test-support branch, not a speculative cascade.

### Scope boundary (frozen)

**In scope:** Node type migration, Pydantic models, prompt changes, tool refactoring, test updates, `extract_json()` utility, README table update.

**Out of scope:** Session continuations (FR-105), retry logic, migrating the watcher's `summarize` node, promoting `extract_json()` to core.

## Summary

Migrate the philosopher daemon's `analyze` and `reflect` nodes from `type: llm` to `type: copilot`, aligning with the established chaplaincy pattern used by the watcher and enforcer. Validate copilot output through Pydantic models, preserving type safety.

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

### New Pydantic models (`examples/philosopher/models.py`)

Create explicit Pydantic models for copilot output validation:

```python
from pydantic import BaseModel, Field


class Proposal(BaseModel):
    """A single graduation proposal."""
    type: str = Field(description="Category: trap, heuristic, or seed")
    name: str = Field(description="Pattern name (snake_case)")
    count: int = Field(description="Occurrence count across diary entries")
    files: list[str] = Field(description="Diary files where pattern appears")


class ProposalList(BaseModel):
    """Validated list of graduation proposals from analyze node."""
    proposals: list[Proposal] = Field(
        default_factory=list,
        description="List of graduation proposals",
    )


class DiaryEntry(BaseModel):
    """Validated diary entry from reflect node."""
    theme: str = Field(description="Short title for the diary entry (2-4 words)")
    body: str = Field(description="Main reflection content in markdown format")
    seed: str = Field(description="A forward-looking question for future exploration")
```

### JSON extraction utility

Copilot may wrap JSON in markdown fences or preamble text. A small extraction helper handles this:

```python
import json
import re

from yamlgraph.models import PipelineError


def extract_json(text: str, node_name: str) -> str:
    """Extract JSON from copilot output, stripping markdown fences and preamble.

    Strategy:
    1. Strip markdown code fences (```json ... ```)
    2. Find first [ or { to last ] or }
    3. Raise PipelineError on failure (no silent fallbacks per Commandment 6)
    """
    # Strip markdown fences
    stripped = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
    if stripped.endswith("```"):
        stripped = stripped[:-3].strip()

    # Find JSON boundaries
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = stripped.find(start_char)
        end = stripped.rfind(end_char)
        if start != -1 and end > start:
            candidate = stripped[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue

    raise PipelineError(
        message=f"No valid JSON found in copilot output for node '{node_name}'",
        node=node_name,
        details={"raw_output_preview": text[:200]},
    )
```

### Graph changes (`examples/philosopher/graph.yaml`)

```yaml
# Before
  analyze:
    type: llm
    prompt: analyze
    variables:
      scan_result: "{state.scan_result}"
      graduation_threshold: "{state.graduation_threshold}"
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
    variables:
      scan_result: "{state.scan_result}"
      proposals: "{state.proposals}"
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

Note: No `cli_flags: allow_all_paths` — the philosopher's copilot nodes perform pure reasoning (analyzing data passed via variables, emitting JSON). They do not access the filesystem. All file I/O is handled by Python tool nodes (`scan`, `propose`, `write_diary`). This differs from the enforce graph where copilot nodes directly read/write code files.

### State type changes (`graph.yaml` state section)

```yaml
# Before
  proposals: Any      # Pydantic model
  diary_entry: Any    # Pydantic model

# After
  proposals: dict     # CopilotResult envelope
  diary_entry: dict   # CopilotResult envelope
```

### Prompt changes

Remove `schema:` blocks from both `prompts/analyze.yaml` and `prompts/reflect.yaml`. Add explicit JSON format instructions with "output ONLY valid JSON" guards.

**`prompts/analyze.yaml`** — remove `schema:` block, add output guard:
```yaml
user: |
  ...existing instructions...

  IMPORTANT: Output ONLY valid JSON — no markdown fences, no preamble text,
  no explanation. Your entire response must be a single JSON array.

  Output format:
  [
    {"type": "trap", "name": "pattern_name", "count": 4,
     "files": ["diary-1.md", "diary-2.md"]}
  ]

  If no patterns meet the threshold, output: []
```

**`prompts/reflect.yaml`** — remove `schema:` block, add output guard:
```yaml
user: |
  ...existing instructions...

  IMPORTANT: Output ONLY valid JSON — no markdown fences, no preamble text,
  no explanation. Your entire response must be a single JSON object.

  Output format:
  {"theme": "Short Title", "body": "Reflection content...", "seed": "Forward question?"}
```

### Tool changes (`examples/philosopher/tools.py`)

Replace the 4-way unwrap cascade in `write_proposals()` with a single Pydantic-validated parse path:

```python
from examples.philosopher.models import ProposalList
from yamlgraph.models.schemas import CopilotResult

def write_proposals(state: dict) -> dict:
    proposals_raw = state.get("proposals", [])

    # Single parse path: CopilotResult → extract JSON → validate through Pydantic
    if isinstance(proposals_raw, CopilotResult):
        json_str = extract_json(proposals_raw.output, "analyze")
        proposal_list = ProposalList.model_validate_json(
            json_str if json_str.strip().startswith("{")
            else f'{{"proposals": {json_str}}}'
        )
        proposals = proposal_list.proposals
    elif hasattr(proposals_raw, "proposals"):
        proposals = proposals_raw.proposals
    else:
        proposals = []

    # ... rest of function unchanged (iterate proposals, write files)
```

The Pydantic model replaces four speculative `hasattr`/`isinstance` branches with one validated parse. The `elif hasattr` fallback preserves testability with mock data.

### Diary tool changes (`examples/shared/diary.py`)

The `write_diary()` function must handle `CopilotResult` input:

```python
from examples.philosopher.models import DiaryEntry as PhilosopherDiaryEntry
from yamlgraph.models.schemas import CopilotResult

def write_diary(state: dict) -> dict:
    entry_data = state.get("diary_entry", {})

    # Handle CopilotResult from copilot nodes
    if isinstance(entry_data, CopilotResult):
        json_str = extract_json(entry_data.output, "reflect")
        parsed = PhilosopherDiaryEntry.model_validate_json(json_str)
        theme, body, seed = parsed.theme, parsed.body, parsed.seed
    elif isinstance(entry_data, str):
        # ... existing string parsing logic
    else:
        # ... existing Pydantic/dict logic
```

### Error handling strategy

Per Commandment 6 ("thou shalt not hedge with silent fallbacks"):

| Failure mode | Handling |
|---|---|
| Copilot emits no JSON (pure prose) | `extract_json()` raises `PipelineError` with output preview |
| Copilot emits malformed JSON | `json.loads()` fails → `extract_json()` tries next bracket pair → raises `PipelineError` if all fail |
| JSON valid but wrong shape | `model_validate_json()` raises `ValidationError` with field-level details |
| Copilot CLI timeout | Existing `subprocess.TimeoutExpired` handling in `copilot_node.py` raises `RuntimeError` |

No retries — Copilot CLI sessions are not idempotent. On failure, the graph raises and the operator inspects logs.

## Acceptance Criteria

- [x] AC-1: `analyze` node uses `type: copilot` in `examples/philosopher/graph.yaml`
- [x] AC-2: `reflect` node uses `type: copilot` in `examples/philosopher/graph.yaml`
- [x] AC-3: `prompts/analyze.yaml` has no `schema:` block; user prompt includes "output ONLY valid JSON" guard
- [x] AC-4: `prompts/reflect.yaml` has no `schema:` block; user prompt includes "output ONLY valid JSON" guard
- [x] AC-5: `write_proposals()` parses `CopilotResult.output` through `ProposalList` Pydantic model — no multi-way unwrap cascade
- [x] AC-6: All 19 existing philosopher tests pass (update as needed for new data shapes)
- [x] AC-7: Integration smoke test: `yamlgraph graph lint examples/philosopher/graph.yaml` passes
- [x] AC-8: No `ProposalList is not JSON serializable` errors at runtime
- [x] AC-9: README.md table updated: `analyze` and `reflect` rows show `copilot` type
- [x] AC-10: `ProposalList` and `DiaryEntry` Pydantic models exist in `examples/philosopher/models.py` with typed fields (not `list[Any]`)
- [x] AC-11: `extract_json()` utility handles markdown fences, preamble text, and raises `PipelineError` on parse failure
- [x] AC-12: No `cli_flags: allow_all_paths` on philosopher copilot nodes (pure reasoning, no filesystem access)
- [x] AC-13: New unit tests for `extract_json()` covering: clean JSON, fenced JSON, preamble text, malformed input
- [x] AC-14: New unit tests for `ProposalList.model_validate_json()` and `DiaryEntry.model_validate_json()` validation

## Alternatives Considered

1. **Keep `type: llm` and fix serialization** — Add `.model_dump()` call in the node factory before returning to state. This treats the symptom (serialization) but leaves the architectural inconsistency. The 4-way unwrap in `write_proposals()` would remain necessary.

2. **Hybrid: copilot for analyze, LLM for reflect** — The reflect node produces a simpler schema (`DiaryEntry` with 3 string fields) that serializes cleanly. However, half-migrating increases inconsistency rather than reducing it.

3. **Use session continuations (FR-105)** — Chain analyze → reflect via `resume: "{state.proposals.session_id}"` so the reflect node has full context from analyze. This is an orthogonal enhancement that could be added later but is out of scope for this FR.

4. **Raw `json.loads()` without Pydantic validation** — Simpler but violates Commandment 5 ("All data shall pass through the fire of Pydantic"). Untyped dicts would wander downstream, making bugs harder to catch.

## Related

- `FR-184` — Philosopher Daemon (original implementation)
- `FR-081` — Copilot Node Type (the `type: copilot` capability)
- `FR-105` — Session Continuations (potential future enhancement)
- `FR-183` — Simplified Enforce Pipeline (reference pattern for copilot-only graphs)
- `examples/enforce/graph.yaml` — Reference copilot node usage
- `examples/copilot/graph.yaml` — Reference copilot node usage
- `yamlgraph/node_factory/copilot_node.py` — Copilot node implementation
- `tests/unit/test_philosopher.py` — Existing tests (19 tests across 5 classes)
