# Feature Request: W016 — Lint Warning for Top-Level provider/model

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

Add linter warning W016 that fires when `provider:` or `model:` appear at the graph top level (outside the `defaults:` block), where they are silently ignored by the framework.

## Value Statement

Graph authors get immediate feedback when provider/model configuration is misplaced, preventing silent configuration drift where graphs appear to use a specific provider but actually fall back to environment defaults.

## Problem

When `provider:` or `model:` are placed at the YAML top level (same indentation as `nodes:`, `edges:`, `version:`), the framework ignores them. The `GraphConfigSchema` uses `extra="allow"`, so no validation error is raised — the keys are silently accepted but never read by the compilation pipeline, which only inspects `defaults:` and per-node config.

**Real incident:** Commit `b14960e` added `provider: anthropic` and `model: claude-haiku-4-5` at top level in `examples/copilot/graph.yaml`. The graph appeared configured but actually used the `PROVIDER` env var fallback. This was later manually fixed by moving them into `defaults:`.

Without a lint rule, this class of silent misconfiguration will recur.

## Proposed Solution

Add a check function `check_top_level_provider_model()` in `yamlgraph/linter/checks_contracts.py` that loads the raw YAML dict and detects `provider` or `model` keys at the top level.

### Warning format

```
W016: 'provider' at top level has no effect; move to 'defaults:' block
W016: 'model' at top level has no effect; move to 'defaults:' block
```

### Implementation pattern

Follows the existing FR-061 contract-violation pattern (W020, W021):

```python
def check_top_level_provider_model(graph_path: Path) -> list[LintIssue]:
    """W016: provider/model at top level is silently ignored.

    These keys only take effect inside the defaults: block or per-node.
    Placing them at top level creates silent configuration drift.
    """
    issues = []
    graph = load_graph(graph_path)

    for key in ("provider", "model"):
        if key in graph and key not in graph.get("defaults", {}):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W016",
                    message=(
                        f"'{key}' at top level has no effect; "
                        f"move to 'defaults:' block"
                    ),
                    fix=f"defaults:\n  {key}: {graph[key]}",
                )
            )
        elif key in graph and key in graph.get("defaults", {}):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W016",
                    message=(
                        f"'{key}' at top level has no effect "
                        f"(defaults.{key} already set); remove top-level '{key}'"
                    ),
                    fix=f"Remove top-level '{key}:' line",
                )
            )

    return issues
```

### Wiring

In `graph_linter.py`, add to the contract-violation section (~line 108):

```python
all_issues.extend(check_top_level_provider_model(graph_path))
```

## Acceptance Criteria

- [x] `check_top_level_provider_model()` in `checks_contracts.py` detects `provider`/`model` at YAML top level
- [x] Warning code is W016 with severity `warning`
- [x] Message includes the key name and instructs to move to `defaults:`
- [x] When key exists at top level only → suggests move to `defaults:`
- [x] When key exists at both top level and `defaults:` → suggests removing top-level duplicate
- [x] When keys are only in `defaults:` → no warning
- [x] When keys are only at node level → no warning
- [x] When neither key is present at top level → no warning
- [x] Wired into `lint_graph()` in `graph_linter.py`
- [x] Tests added in `test_linter_contracts.py` with `@pytest.mark.req` marker
- [ ] No existing graphs in `examples/` trigger the warning (verify with `yamlgraph graph lint examples/**/graph.yaml`)
- [ ] Documentation updated: add W016 to lint rule reference if one exists

## Alternatives Considered

1. **Make `provider`/`model` work at top level** — Rejected. The `defaults:` block exists for this purpose. Adding a second path creates ambiguity about precedence and violates the single-source principle.

2. **Schema-level rejection (Pydantic `extra="forbid"`)** — Rejected. Changing `GraphConfigSchema` to `extra="forbid"` would break other legitimate extra fields and is too broad a change. A lint warning is the right granularity.

3. **E-code (error) instead of W-code (warning)** — Considered. While misplaced config is arguably an error, it doesn't break graph execution — it just silently uses fallback values. A warning is consistent with W020 (variables on python node) which is the same class of "silent no-op" issue.

## Related

- **FR-061** (`061-contract-violation-lint-rules.md`): Established the contract-violation lint pattern (W020, W021, E012) that this rule follows
- **Commit `b14960e`**: Real-world instance of this bug in `examples/copilot/graph.yaml`
- `yamlgraph/linter/checks_contracts.py`: Implementation target
- `yamlgraph/linter/graph_linter.py`: Wiring target
- `tests/unit/test_linter_contracts.py`: Test target

## Judgement

**Verdict: APPROVED** — Scope frozen. Authority granted.

**Reviewed:** 2026-03-07

### Findings

All factual claims verified:
- ✅ Commit `b14960e` exists and matches the described incident
- ✅ `GraphConfigSchema` uses `extra="allow"` (line 178 of `graph_schema.py`) — confirms silent acceptance
- ✅ W016 code is unused (highest W-codes: W015 semantic, W020–W021 contracts, W071 providers)
- ✅ No existing example graphs have top-level `provider`/`model` — clean baseline
- ✅ Implementation pattern matches W020/W021 precedent in `checks_contracts.py`
- ✅ Wiring point at `graph_linter.py` line ~108 (FR-061 contract section) is correct
- ✅ Alternatives considered are well-reasoned — warning (not error, not schema change) is the right granularity

### Notes for implementer

1. **REQ marker:** AC line 98 says `@pytest.mark.req` but omits the ID. Use `REQ-YG-003` (linting & pattern validation) — no new requirement needed.
2. **`__all__` export:** `checks_contracts.py` has an explicit `__all__`. Add `check_top_level_provider_model` to it.
3. **Import in `graph_linter.py`:** Add the new function to the `from yamlgraph.linter.checks_contracts import (...)` block.
