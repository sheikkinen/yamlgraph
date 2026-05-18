# Feature Request: Structured Repair Actions in Lint Diagnostics

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Effort:** 1 day
**Requested:** 2026-05-18
**Judged:** 2026-05-18

## Summary

Promote `LintIssue.fix` from a prose string to a structured `RepairAction` model with a stable machine-actionable `id`, parameters, and human description — enabling deterministic auto-fix without LLM involvement.

## Value Statement

Agent nodes can apply named repairs from a dispatch table instead of re-prompting the LLM, reducing fix cost from ~1000 tokens to zero.

## Problem

Current `LintIssue.fix` is prose:
```python
fix="Add 'graph' field: graph: subgraphs/analyze.yaml"
```

An agent reading this must either:
1. Parse the prose with an LLM (expensive, unreliable)
2. Regex-match known patterns (brittle, incomplete)

Zero language solves this with `"repair": { "id": "declare-missing-symbol" }` — a stable identifier that maps to a deterministic fix function. YAMLGraph's linter already knows *what* to fix; it just encodes that knowledge as prose rather than structured data.

## Proposed Solution

### New model in `yamlgraph/linter/checks.py`:

```python
class RepairAction(BaseModel):
    """Machine-actionable fix for a lint issue."""

    id: str  # Stable key: "add-field", "rename-node", "fix-edge-reference"
    params: dict[str, Any] = Field(default_factory=dict)
    description: str  # Human-readable (current prose)
```

### Updated `LintIssue`:

```python
class LintIssue(BaseModel):
    severity: str
    code: str
    message: str
    line: int | None = None
    fix: str | None = None           # Deprecated, kept for backward compat
    repair: RepairAction | None = None  # NEW: structured repair
```

### Repair ID registry (initial set):

| Code | repair.id | params |
|------|-----------|--------|
| E501 | `add-field` | `{"node": "x", "field": "graph", "suggested": "subgraphs/x.yaml"}` |
| E001 | `declare-state-key` | `{"key": "summary", "node": "generate"}` |
| E002 | `add-prompt-file` | `{"prompt": "analyze", "path": "prompts/analyze.yaml"}` |
| W501 | `add-mapping` | `{"node": "x", "mapping_type": "input"}` |
| E601 | `fix-edge-target` | `{"edge_from": "a", "invalid_target": "b", "valid_targets": [...]}` |

### Auto-fix dispatcher (follow-up):

```python
# yamlgraph/linter/repairs.py
REPAIR_REGISTRY: dict[str, Callable[[Path, RepairAction], bool]] = {
    "add-field": _repair_add_field,
    "declare-state-key": _repair_declare_state_key,
    ...
}
```

A `yamlgraph graph lint --fix` command could apply all deterministic repairs automatically.

## Acceptance Criteria

- [ ] `RepairAction` model added to linter
- [ ] `LintIssue.repair` field populated for all issues that currently have `fix` prose
- [ ] `repair.id` values are documented in a registry (linter docs or code constant)
- [ ] JSON output (FR-406) includes `repair` object
- [ ] Existing `fix` field still populated (deprecation, not removal)
- [ ] Tests verify repair IDs are stable across code changes
- [ ] No auto-fix implementation yet (deferred to follow-up FR)

## Alternatives Considered

- **Keep prose `fix` only**: Works for humans, useless for agents. Fails the "machine-readable at boundaries" doctrine.
- **Embed YAML patches**: Too specific; breaks when graph structure changes. Named IDs are stable across schema evolution.
- **LLM-based auto-fix**: Expensive and unreliable for issues where the fix is deterministic.

## Related

- FR-406: Machine-readable lint output (prerequisite for useful consumption)
- `yamlgraph/linter/checks.py` — `LintIssue` model
- `yamlgraph/linter/patterns/` — pattern-specific checks that emit `fix` prose
- Zero language repair metadata: https://zerolang.ai
- Scripture trap: `plausible_wrong_answer` — structured repairs avoid LLM generating "looks right" fixes

## Judgement

**Verdict: REJECTED**

Pain is imagined. No consumer exists — not a single line of code programmatically reads `LintIssue.fix` today. The repair registry would be heavier than the linter itself (~15 checks), triggering the "framework costume" trap. Adds deprecation baggage (`fix` + `repair` coexisting). The Zero language analogy is aspirational mimicry, not evidence of need. Revisit only when a concrete agent-driven auto-fix FR materializes that requires structured repairs as input.
