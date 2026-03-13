# Feature Request: Philosopher Challenge Node (Devil's Advocate Gate)

**FR-195**
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-03-13

## Summary

Add `distill` + `challenge` copilot nodes with unwrap gates to the philosopher graph, creating an adversarial quality gate that prevents weak or coincidental patterns from reaching `.chaplain/inbox/`.

## Value Statement

Graph authors get a devil's advocate gate that filters false-positive graduations, ensuring only genuinely recurring and actionable patterns survive to the chaplain inbox.

## Problem

The philosopher graph (`examples/philosopher/graph.yaml`) writes **every** proposal meeting the occurrence threshold directly to `.chaplain/inbox/`. There is no adversarial validation — `analyze` proposes and `propose` writes, without challenge.

Two failure modes:

1. **False positives**: Diary entries may use similar language without describing the same underlying pattern (Scripture trap: `false_duplicate` — "syntactic similarity ≠ semantic equivalence").
2. **Unchallenged premises**: The analyze node validates pattern occurrence but not pattern *value* — it never asks "Is the pain real?" (Scripture trap: `unchallenged_premise` — "Judge validates execution, not intent → need Red Hat").

The Scripture itself calls for this: `seeds.inquisitor_auto_escalation` envisions automatic quality gates, and `unchallenged_premise` explicitly names the missing Red Hat thinking.

## Proposed Solution

Insert four new nodes between `analyze` and `propose`:

```
scan → analyze → distill → unwrap_distill → challenge → unwrap_challenge → [propose | reflect] → ... → END
```

**Correction from initial design:** Copilot nodes store `CopilotResult` in state (fields: `output`, `exit_code`, `model`, `backend`, `session_id`). Conditional edges cannot navigate into parsed JSON within `.output`. Therefore, dedicated Python unwrap nodes sit between each copilot node and its downstream consumer, following the established pattern in `write_proposals()` and `write_diary()`.

### 1. `distill` copilot node

Selects the single strongest graduation candidate from the full proposal list.

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

Prompt evaluates candidates on:
- Occurrence count (frequency signal)
- Evidence spread (distinct diary entries, not repeated mentions in one file)
- Specificity (actionable as a Scripture entry)
- Novelty (not already partially captured)

Output: single JSON object matching `Proposal` schema, or `{"selected": null}` when no candidate is strong enough.

### 2. `unwrap_distill` Python node

Parses `CopilotResult.output` through Pydantic and stores a plain dict (or `None`) in state.

```yaml
unwrap_distill:
  type: python
  tool: unwrap_distill_tool
  state_key: top_candidate
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

    # Handle {"selected": null} signal — check key presence, not just value,
    # to avoid discarding valid Proposal JSON that lacks a "selected" key.
    if parsed is None or ("selected" in parsed and parsed["selected"] is None):
        return {"top_candidate": None}

    # If wrapped in {"selected": {...}}, unwrap; otherwise parse directly
    payload = parsed["selected"] if "selected" in parsed else parsed
    proposal = Proposal.model_validate(payload)
    return {"top_candidate": proposal.model_dump()}
```

### 3. Null short-circuit edge

When `top_candidate` is `None` (distill found no worthy candidate), skip `challenge` and go directly to `reflect`. This avoids wasting an LLM call challenging nothing.

```yaml
edges:
  - from: unwrap_distill
    to: challenge
    condition: "top_candidate != None"
  - from: unwrap_distill
    to: reflect
    condition: "top_candidate == None"
```

### 4. `challenge` copilot node

Plays devil's advocate on the top candidate.

```yaml
challenge:
  type: copilot
  prompt: challenge
  variables:
    top_candidate: "{state.top_candidate}"
    scan_result: "{state.scan_result}"
  state_key: challenge_result
  timeout: 300
```

Prompt challenges along these axes:
- **Recurrence vs. repetition**: Is this genuinely recurring, or is the diary author using similar phrasing?
- **Actionability**: Would adding this to Scripture actually prevent future mistakes?
- **Specificity**: Is the pattern specific enough to be a distinct trap/heuristic/seed?
- **False duplicate**: Could this be a rewording of an existing Scripture entry?
- **Evidence quality**: Are the diary files truly independent occurrences?

Output: structured `ChallengeVerdict` JSON.

### 5. `unwrap_challenge` Python node

Parses `CopilotResult.output` into a validated `ChallengeVerdict` dict.

```yaml
unwrap_challenge:
  type: python
  tool: unwrap_challenge_tool
  state_key: challenge_parsed
```

Implementation in `examples/philosopher/tools.py`:

```python
def unwrap_challenge(state: dict) -> dict:
    """Parse challenge CopilotResult into a validated ChallengeVerdict dict."""
    from examples.philosopher.models import ChallengeVerdict, extract_json

    raw = state.get("challenge_result")
    if not isinstance(raw, CopilotResult):
        return {"challenge_parsed": {"verdict": "reject", "confidence": 0.0,
                                      "objections": ["No challenge result"], "surviving_arguments": []}}

    json_str = extract_json(raw.output, "challenge")
    verdict = ChallengeVerdict.model_validate_json(json_str)
    return {"challenge_parsed": verdict.model_dump()}
```

### 6. Conditional routing on parsed verdict

Gate `propose` on the unwrapped verdict dict:

```yaml
edges:
  - from: unwrap_challenge
    to: propose
    condition: "challenge_parsed.verdict == 'approve'"
  - from: unwrap_challenge
    to: reflect
    condition: "challenge_parsed.verdict != 'approve'"
```

This works because `challenge_parsed` is a plain dict — `resolve_state_path()` uses `.get()` for dict access.

### 7. `ChallengeVerdict` model

Add to `examples/philosopher/models.py`:

```python
class ChallengeVerdict(BaseModel):
    """Devil's advocate verdict on a graduation candidate."""

    verdict: str = Field(description="'approve' or 'reject'")
    confidence: float = Field(
        description="Confidence in verdict (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    objections: list[str] = Field(
        description="Devil's advocate concerns raised",
    )
    surviving_arguments: list[str] = Field(
        description="Arguments that withstood challenge",
    )
```

### 8. Adapt `propose` to read `top_candidate`

`write_proposals()` checks for `top_candidate` in state. When present (a plain dict, already unwrapped), wraps it in a `ProposalList` and writes that single proposal. When absent, falls back to reading `proposals` (preserving existing behavior).

```python
# In write_proposals(), before the existing CopilotResult branch:
top = state.get("top_candidate")
if isinstance(top, dict) and top:
    proposals = [Proposal.model_validate(top)]
elif isinstance(proposals_raw, CopilotResult):
    # ... existing unwrap logic
```

### 9. Enrich `reflect` prompt

Pass challenge verdict to `reflect` so diary captures the adversarial reasoning:

```yaml
reflect:
  type: copilot
  prompt: reflect
  variables:
    scan_result: "{state.scan_result}"
    proposals: "{state.proposals}"
    challenge_verdict: "{state.challenge_parsed}"
  state_key: diary_entry
  timeout: 300
```

### 10. Complete edge topology (FR-194 coordination)

FR-194 (World Context, APPROVED) adds `load_context` between `propose` and `reflect`. The full edge list accounts for both FRs:

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
    to: challenge
    condition: "top_candidate != None"
  - from: unwrap_distill
    to: load_context        # FR-194: short-circuit path still gets context
    condition: "top_candidate == None"
  - from: challenge
    to: unwrap_challenge
  - from: unwrap_challenge
    to: propose
    condition: "challenge_parsed.verdict == 'approve'"
  - from: unwrap_challenge
    to: load_context        # FR-194: rejected path gets context for reflect
    condition: "challenge_parsed.verdict != 'approve'"
  - from: propose
    to: load_context        # FR-194: approved path gets context for reflect
  - from: load_context
    to: reflect             # FR-194
  - from: reflect
    to: write_diary
  - from: write_diary
    to: END
```

If FR-194 is not yet implemented when FR-195 is enforced, replace `load_context` with `reflect` in the edge targets above. The topology remains correct either way.

### 11. State additions

```yaml
state:
  distill_result: dict       # CopilotResult envelope from distill copilot node
  top_candidate: dict        # Unwrapped single strongest candidate (or null)
  challenge_result: dict     # CopilotResult envelope from challenge copilot node
  challenge_parsed: dict     # Unwrapped ChallengeVerdict dict
```

## Acceptance Criteria

- [x] `distill` copilot node added to philosopher graph between `analyze` and `unwrap_distill`
- [x] `distill` prompt YAML selects single strongest candidate; outputs `{"selected": null}` when none qualifies
- [x] `unwrap_distill` Python node parses `CopilotResult.output` into validated `Proposal` dict or `None`
- [x] Null short-circuit: when `top_candidate` is `None`, graph routes directly to `reflect` (or `load_context` if FR-194 present), skipping `challenge` and `propose`
- [x] `challenge` copilot node plays devil's advocate on `top_candidate`
- [x] `challenge` prompt YAML challenges along 5 axes (recurrence, actionability, specificity, false duplicate, evidence quality)
- [x] `unwrap_challenge` Python node parses `CopilotResult.output` into validated `ChallengeVerdict` dict
- [x] Conditional edge routes approved verdicts to `propose`, rejected to `reflect`
- [x] `ChallengeVerdict` Pydantic model added to `examples/philosopher/models.py` with `verdict`, `confidence`, `objections`, `surviving_arguments`
- [x] `write_proposals()` reads `top_candidate` dict when present (single proposal path), falls back to `proposals` key
- [x] `reflect` prompt includes `challenge_parsed` context via Jinja2 conditional rendering
- [x] `distill_result`, `top_candidate`, `challenge_result`, `challenge_parsed` declared in graph state
- [x] Edge topology accounts for FR-194 `load_context` node (or documents the without-FR-194 fallback)
- [x] Tool declarations added for `unwrap_distill_tool` and `unwrap_challenge_tool` in graph YAML
- [x] Unit test: `ChallengeVerdict` model validates approve/reject verdicts with confidence bounds
- [x] Unit test: `unwrap_distill` with null signal returns `{"top_candidate": None}`
- [x] Unit test: `unwrap_distill` with valid proposal returns validated dict
- [x] Unit test: `unwrap_challenge` parses approve/reject verdicts correctly
- [x] Unit test: `write_proposals` with `top_candidate` dict writes single proposal
- [x] Unit test: conditional routing with approve verdict reaches `propose`
- [x] Unit test: conditional routing with reject verdict skips to `reflect`
- [x] Unit test: null `top_candidate` short-circuits past `challenge` to `reflect`
- [x] Tests added with `@pytest.mark.req` traceability
- [x] `distill.yaml` and `challenge.yaml` prompt files created in `examples/philosopher/prompts/`

## Alternatives Considered

1. **Challenge all proposals individually** — Requires N LLM calls per run. The distill-then-challenge pattern is more efficient: evaluate the strongest candidate; if it doesn't survive, weaker ones certainly won't.

2. **Confidence threshold on `analyze` output** — Self-evaluation is unreliable (Scripture: `plausible_wrong_answer`). An independent adversarial node provides genuine challenge.

3. **Python-based heuristic filter** — Simple rules (min count, min file spread) cannot detect false duplicates or unchallenged premises. Semantic reasoning is required.

4. **Router node instead of conditional edges** — A router bundles LLM + routing. Here, the challenge node's purpose is adversarial reasoning, not classification. Separating challenge (copilot) from routing (conditional edge) is cleaner and more testable.

5. **Direct condition on CopilotResult fields** — `resolve_state_path()` can access `.output` on the CopilotResult object, but the verdict lives *inside* the output string as JSON. Parsing JSON within a condition expression is not supported. Dedicated unwrap nodes are the established pattern (see `write_proposals()`, `write_diary()`).

## Related

- **FR-184** (`feature-requests/FR-184-philosopher-daemon.md`): Philosopher daemon — the pipeline being extended
- **FR-185** (`feature-requests/FR-185-philosopher-copilot-nodes.md`): Copilot node migration — established the copilot node pattern
- **FR-194** (`feature-requests/FR-194-philosopher-world-context.md`): World context — adds `load_context` node (coordinate insertion points)
- **Scripture traps**: `unchallenged_premise`, `false_duplicate`, `plausible_wrong_answer`
- **Scripture seeds**: `inquisitor_auto_escalation`
- `examples/philosopher/graph.yaml`: The philosopher graph being modified
- `examples/philosopher/models.py`: Pydantic models for philosopher output
- `examples/philosopher/tools.py`: Python tools including `write_proposals()`
- `yamlgraph/models/schemas.py`: `CopilotResult` class definition
- `yamlgraph/utils/conditions.py`: `resolve_state_path()` and `evaluate_condition()`

## Judgement

**Verdict:** APPROVE (2026-03-13)

**Corrections applied during judgement (2 issues fixed in-place):**

1. **Flow diagram reversed node order** (line 34): Showed `unwrap_distill → distill`
   but copilot nodes must execute before their unwrap nodes. Fixed to
   `distill → unwrap_distill → challenge → unwrap_challenge`.

2. **`unwrap_distill` null-signal bug** (section 2 pseudocode): `parsed.get("selected")`
   returns `None` when the key is absent — meaning valid Proposal JSON (which lacks
   a `"selected"` key) would be discarded as null. Fixed to check key presence:
   `"selected" in parsed and parsed["selected"] is None`.

**Assessment:**
- Scope is clear and cohesive — single responsibility (adversarial quality gate)
- Acceptance criteria are measurable (24 items, each testable)
- Follows established copilot + unwrap pattern (FR-185)
- `resolve_state_path()` confirmed to support dotted dict access (`challenge_parsed.verdict`)
- FR-194 coordination is well-handled with explicit fallback path
- Alternatives considered are thorough and well-reasoned
- Scripture traps cited (`false_duplicate`, `unchallenged_premise`, `plausible_wrong_answer`)
  correctly motivate the feature

**Scope frozen. Authority granted to implement.**
