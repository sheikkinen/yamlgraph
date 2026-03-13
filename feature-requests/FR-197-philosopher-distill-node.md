# Feature Request: Philosopher Distill Node — Ranked Prioritization

**FR-197**
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-03-13

## Summary

Add a `distill` copilot node to the philosopher graph that selects the single most pressing graduation candidate from the analyze output, replacing flat listing with weighted ranked prioritization.

## Value Statement

The philosopher daemon produces higher-quality graduation proposals by selecting the strongest candidate instead of flooding the chaplain inbox with every pattern above the threshold.

## Problem

The philosopher graph (`examples/philosopher/graph.yaml`) treats all proposals equally. The `analyze` copilot node produces a flat JSON array of every pattern meeting the occurrence threshold, and `propose` writes all of them to `.chaplain/inbox/`. This creates two issues:

1. **No prioritization**: A pattern with 3 occurrences in old diary entries is treated the same as one with 8 occurrences in the last week. Count alone is a poor proxy for urgency.
2. **Inbox flooding**: Every qualifying pattern generates an inbox file, producing batches of graduation proposals that compete for the chaplain's attention. The most pressing candidate gets no priority.

The Scripture's `graduation` process says "Heuristic appears twice → create FR; confirmed recurrence → graduate." But confirmed recurrence requires weighing *quality* of evidence, not just quantity.

## Proposed Solution

Insert a `distill` copilot node + `unwrap_distill` Python node between `analyze` and `propose`. The copilot node performs multi-criteria evaluation in a single pass (no additional LLM nodes needed).

### Pipeline change

```
Before: scan → analyze → propose → reflect → write_diary
After:  scan → analyze → distill → unwrap_distill → propose → reflect → write_diary
```

### 1. `distill` copilot node

```yaml
distill:
  type: copilot
  prompt: distill
  variables:
    proposals: "{state.proposals}"
    scan_result: "{state.scan_result}"
  state_key: distill_result
  timeout: 300
```

The prompt instructs the copilot to evaluate candidates on weighted criteria:

- **Recency** (high weight): Patterns appearing in recent diary entries signal active pain, not historical noise
- **Severity** (medium weight): Traps that caused bugs or rework outweigh informational heuristics
- **Evidence spread** (medium weight): Appearances across distinct diary entries > repeated mentions in one file
- **Specificity** (low weight): Actionable as a concrete Scripture entry, not a vague observation

Output: single JSON object matching the `Proposal` schema (the winning candidate), or `{"selected": null}` when no candidate is strong enough after weighting.

**CopilotResult envelope handling:** `{state.proposals}` resolves to a `CopilotResult` object. The Jinja2 prompt must access the inner JSON via `proposals.output`:

```jinja2
{% if proposals and proposals.output %}
{{ proposals.output }}
{% else %}
[]
{% endif %}
```

### 2. `unwrap_distill` Python node

Parses `CopilotResult.output` into a validated `Proposal` dict or `None`, following the established unwrap pattern from `write_proposals()` and `write_diary()`.

```yaml
unwrap_distill:
  type: python
  tool: unwrap_distill_tool
  state_key: top_candidate
```

Tool declaration:

```yaml
tools:
  unwrap_distill_tool:
    type: python
    module: examples.philosopher.tools
    function: unwrap_distill
```

Implementation in `examples/philosopher/tools.py`:

```python
def unwrap_distill(state: dict) -> dict:
    """Parse distill CopilotResult into a validated Proposal dict or None."""
    from examples.philosopher.models import Proposal, extract_json

    raw = state.get("distill_result")
    if not isinstance(raw, CopilotResult):
        return {"top_candidate": None}

    json_str = extract_json(raw.output, "distill")
    parsed = json.loads(json_str)

    if parsed is None or ("selected" in parsed and parsed["selected"] is None):
        return {"top_candidate": None}

    payload = parsed["selected"] if "selected" in parsed else parsed
    proposal = Proposal.model_validate(payload)
    return {"top_candidate": proposal.model_dump()}
```

### 3. Conditional short-circuit

When `top_candidate` is `None` (no candidate survives weighting), skip `propose` and go directly to `reflect`:

```yaml
edges:
  - from: unwrap_distill
    to: propose
    condition: "top_candidate != None"
  - from: unwrap_distill
    to: reflect
    condition: "top_candidate == None"
```

### 4. Adapt `write_proposals()` to single-candidate path

When `top_candidate` is present in state, write only that single proposal instead of the full list:

```python
# At top of write_proposals(), before existing CopilotResult branch:
top = state.get("top_candidate")
if isinstance(top, dict) and top:
    proposals = [Proposal.model_validate(top)]
else:
    # ... existing CopilotResult unwrap logic
```

### 5. State additions

```yaml
state:
  distill_result: dict    # CopilotResult envelope from distill copilot node
  top_candidate: dict     # Unwrapped single strongest candidate (or null)
```

### 6. `distill.yaml` prompt

```yaml
# FR-197: Distill — select the single most pressing graduation candidate

system: |
  You are the Philosopher's distillation lens. Given a list of graduation
  candidates, select the ONE most pressing pattern for promotion to Scripture.

  Weigh these criteria:
  - Recency (high): Patterns in recent diary entries signal active pain
  - Severity (medium): Traps that caused bugs or rework outweigh informational heuristics
  - Evidence spread (medium): Distinct diary entries > repeated mentions in one file
  - Specificity (low): Concrete, actionable as a Scripture entry

user: |
  ## Proposals from Analyze

  {% if proposals and proposals.output %}
  {{ proposals.output }}
  {% else %}
  []
  {% endif %}

  ## Scan Context

  {{ scan_result | tojson(indent=2) }}

  ## Instructions

  Select the single strongest graduation candidate. If no candidate is strong
  enough after weighing all criteria, output {"selected": null}.

  IMPORTANT: Output ONLY valid JSON — no markdown fences, no preamble text,
  no explanation. Your entire response must be a single JSON object.

  If selecting a candidate, output the proposal object directly:
  {"type": "trap", "name": "pattern_name", "count": 4,
   "files": ["diary-1.md", "diary-2.md"]}

  If no candidate qualifies: {"selected": null}
```

### 7. Complete edge topology

```yaml
edges:
  - from: START
    to: scan
  - from: scan
    to: analyze
  - from: analyze
    to: distill
  - from: distill
    to: unwrap_distill
  - from: unwrap_distill
    to: propose
    condition: "top_candidate != None"
  - from: unwrap_distill
    to: reflect
    condition: "top_candidate == None"
  - from: propose
    to: reflect
  - from: reflect
    to: write_diary
  - from: write_diary
    to: END
```

## Acceptance Criteria

- [x] `distill` copilot node added to philosopher graph between `analyze` and `unwrap_distill`
- [x] `distill.yaml` prompt evaluates candidates on recency, severity, evidence spread, and specificity
- [x] `distill.yaml` prompt correctly accesses `proposals.output` to resolve the CopilotResult envelope
- [x] `distill` prompt outputs single `Proposal` JSON or `{"selected": null}` for no-candidate case
- [x] `unwrap_distill` Python tool parses `CopilotResult.output` into validated `Proposal` dict or `None`
- [x] `unwrap_distill` handles `{"selected": null}` signal without discarding valid Proposal JSON (key-presence check, not value check)
- [x] Null short-circuit: when `top_candidate` is `None`, graph skips `propose` and routes to `reflect`
- [x] `write_proposals()` reads `top_candidate` dict when present (single proposal path), falls back to `proposals` key
- [x] `distill_result` and `top_candidate` declared in graph state
- [x] Tool declaration `unwrap_distill_tool` added to graph YAML
- [x] Unit test: `unwrap_distill` with `{"selected": null}` returns `{"top_candidate": None}`
- [x] Unit test: `unwrap_distill` with valid proposal JSON returns validated dict
- [x] Unit test: `write_proposals` with `top_candidate` dict writes single proposal file
- [x] Unit test: conditional routing with `top_candidate != None` reaches `propose`
- [x] Unit test: conditional routing with `top_candidate == None` skips to `reflect`
- [x] Tests added with `@pytest.mark.req` traceability
- [x] Documentation updated (graph description in YAML header reflects distill stage)

## Alternatives Considered

1. **Modify `analyze` prompt to rank and select** — Combines two concerns (pattern detection + prioritization) into one LLM call. Violates single responsibility: if ranking criteria change, the analyze prompt must be re-tuned even though pattern detection hasn't changed. Separate nodes allow independent prompt evolution.

2. **Python-based scoring heuristic** — Simple weighted formula on count + file date. Cannot evaluate severity or specificity — these require semantic reasoning about what the pattern *means*, not just how often it appears.

3. **Full adversarial pipeline (FR-195)** — FR-195 proposes distill + challenge + two unwrap nodes. This FR extracts just the distill portion as an independent, immediately valuable enhancement. FR-195's challenge node can be layered on top later if needed.

4. **Filter in `write_proposals()` only** — Python filtering can enforce thresholds but cannot rank by semantic criteria. The ranking decision is inherently an LLM task.

## Related

- **FR-184** (`feature-requests/FR-184-philosopher-daemon.md`): Philosopher daemon — the pipeline being extended
- **FR-185** (`feature-requests/FR-185-philosopher-copilot-nodes.md`): Copilot node migration — established the copilot + unwrap pattern
- **FR-195** (`feature-requests/FR-195-philosopher-challenge-node.md`): Devil's advocate gate — broader pipeline that includes distill; this FR extracts the distill portion as standalone
- `examples/philosopher/graph.yaml`: The philosopher graph being modified
- `examples/philosopher/models.py`: `Proposal`, `ProposalList`, `extract_json()`
- `examples/philosopher/tools.py`: `write_proposals()` being adapted
- `yamlgraph/models/schemas.py`: `CopilotResult` envelope class

## Judgement — 2026-03-13

**Verdict: APPROVE**

### Evaluation

| Criterion | Assessment |
|-----------|------------|
| Scope clarity | ✅ Clear. Single copilot node + unwrap + prompt + conditional routing + write_proposals adaptation. |
| Minimal | ✅ Extracts exactly one concern (ranked prioritization) from the broader FR-195. |
| Internal consistency | ✅ No contradictions. Null-signal handling uses key-presence check (lesson from FR-195 corrections). |
| Acceptance criteria | ✅ 16 criteria, each measurable. Unit tests cover both happy path and null short-circuit. |
| Implementation feasibility | ✅ All pieces (copilot node, unwrap tool, conditional routing) are proven patterns in the codebase. |
| Architecture alignment | ✅ Follows copilot + unwrap pattern from FR-185. Uses CopilotResult envelope correctly. |
| Single responsibility | ✅ One concern: ranked prioritization. Challenge/adversarial review is deliberately deferred to FR-195. |

### Notes for Enforcement

1. **FR-195 coordination**: FR-197 implements the `distill` + `unwrap_distill` portion of FR-195. After FR-197 merges, FR-195's remaining scope is `challenge` + `unwrap_challenge` only. The implementer should add a note to FR-195 indicating that the distill portion was delivered by FR-197.

2. **Requirement IDs**: AC item "Tests added with `@pytest.mark.req` traceability" requires new REQ-YG-XXX entries in ARCHITECTURE.md. Assign during implementation.

3. **CopilotResult envelope access**: The prompt template accesses `proposals.output` via Jinja2. Verify during implementation that the Jinja2 context correctly resolves `CopilotResult` objects — the `reflect.yaml` prompt already demonstrates this pattern (`{% if proposals and proposals.output %}`).

4. **`write_proposals()` dual path**: The adaptation adds a `top_candidate` code path at the top of the function. Ensure the existing `proposals` (CopilotResult) path remains untouched as fallback — the function should work for both distill-enabled and distill-disabled graph configurations.

### Authority

Scope frozen. Authority granted to implement FR-197 per the Sermon of the Chaplain.
