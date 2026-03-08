# Feature Request: No-Silent-Fallback Lint Rule (W017)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add lint rule W017 that flags `on_error: skip` nodes in YAML graphs as silent fallback patterns that hide failures from traces and logs.

## Value Statement

Graph authors get immediate feedback when error-swallowing patterns creep into pipelines, preventing silent data loss that is harder to diagnose than an explicit crash.

## Problem

`on_error: skip` silently drops node failures — the pipeline continues as if nothing happened, producing incomplete or wrong results without any trace of the failure. This violates Commandment 6 ("Thou shalt bear witness of thy errors") and the Scripture trap `plausible_wrong_answer`: "Silent fallback harder to catch than crash."

Current codebase search finds 8 files with `on_error: skip` usage (~9 active instances across examples, projects, and test fixtures):

```
examples/daily_digest/graph.yaml
examples/ocr_cleanup/graph.yaml
examples/book_translator/graph.yaml (×2)
examples/diary_digest/graph.yaml
examples/demos/system-status/graph.yaml
projects/opinto_ohjaus/ (×4 across sub-projects)
projects/innovators_toolkit/toolkit.yaml (×9)
tests/fixtures/linter/retry_tool_pass.yaml
```

None of the example/project graphs have downstream verification that the skipped node's absence was handled. The `pipeline_audit` example already identifies this as an anti-pattern worth detecting — this FR makes that detection a first-class lint rule.

## Proposed Solution

Add a **W017** warning rule in `checks_contracts.py` that fires when a node uses `on_error: skip`.

### Detection Logic

```python
def check_silent_fallback(graph_path: Path) -> list[LintIssue]:
    """W017: on_error: skip silently drops failures."""
    issues = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("on_error") == "skip":
            issues.append(LintIssue(
                severity="warning",
                code="W017",
                message=(
                    f"Node '{node_name}' uses on_error: skip — "
                    f"failures are silently dropped"
                ),
                fix=(
                    f"Use on_error: fail (crash loudly), "
                    f"on_error: fallback (with explicit config), "
                    f"or add error state accumulation in a downstream node"
                ),
            ))
    return issues
```

### Examples

```yaml
# ❌ W017: Silent fallback hides failure
nodes:
  summarize:
    type: llm
    prompt: summarize
    on_error: skip

# ✅ Explicit failure
nodes:
  summarize:
    type: llm
    prompt: summarize
    on_error: fail

# ✅ Fallback with config
nodes:
  summarize:
    type: llm
    prompt: summarize
    on_error: fallback
    fallback:
      provider: openai
```

### Integration

1. Add `check_silent_fallback` to `checks_contracts.py` (alongside W016, W020, W021)
2. Register in `graph_linter.py` with `# FR-165` comment
3. Add test class `TestW017SilentFallback` in `test_linter_contracts.py` using inline `_create_temp_graph()` helper (consistent with existing contract tests — no external fixture files needed)
4. Add requirement `REQ-YG-114` to `ARCHITECTURE.md` Capability 16 table and register in `scripts/req_coverage.py`

### Existing Graph Impact

W017 is a **warning**, not an error. Existing graphs with `on_error: skip` will trigger informational warnings but will not block linting or CI. Graph authors can:
- Switch to explicit error handling (`on_error: fail` or `on_error: fallback`) where appropriate
- Accept the warning as informational until a generic noqa suppression mechanism lands (see follow-up FR below)

## Acceptance Criteria

- [ ] W017 rule added to `yamlgraph/linter/checks_contracts.py` as `check_silent_fallback()`
- [ ] Rule fires on every `on_error: skip` node
- [ ] Rule registered in `graph_linter.py` lint pipeline with `# FR-165` comment
- [ ] Test class `TestW017SilentFallback` with inline graph dicts (pass and fail cases)
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-114")`
- [ ] `REQ-YG-114` added to `ARCHITECTURE.md` Capability 16 requirements table
- [ ] `REQ-YG-114` registered in `scripts/req_coverage.py` (`_ALL_FRAMEWORK_REQS` and `CAPABILITIES["CAP-16"]`)
- [ ] Tests pass: `pytest tests/unit/test_linter_contracts.py -v`

## Out of Scope

- **YAML `# noqa` suppression mechanism**: No generic noqa mechanism exists in the linter. Implementing it is a cross-cutting capability benefiting all rules — file as a separate FR (e.g., FR-166: YAML noqa suppression).
- **Python AST check for `x = x or default` patterns**: Would require a separate rule (W018) with AST parsing of Python tool files. Follow-up FR.
- **Graph-level dataflow analysis** to determine if a downstream node checks for missing state: Too complex for the value. Simpler to flag all `on_error: skip` and let authors address explicitly.

## Alternatives Considered

1. **Flag only when no downstream verification exists**: Would require graph-level dataflow analysis. Too complex for the value — simpler to flag all `on_error: skip`.

2. **Promote to error (E-code)**: Rejected — `on_error: skip` is sometimes intentional for optional enrichment (e.g., `system-status/graph.yaml` memory_pressure node). A warning is the right severity.

3. **Tie to `verification_question` field (FR-164)**: FR-164's verification gate pattern could suppress W017 when a downstream verification node exists. This is a natural evolution but should not block the base rule.

## Related

- **Commandment 6**: "Thou shalt bear witness of thy errors"
- **Scripture trap**: `plausible_wrong_answer` — "Silent fallback harder to catch than crash"
- **Scripture cure**: `callsite_fix` — "Fix at the specific caller, not the shared utility"
- **FR-061**: Contract violation lint rules (W020, E012, W021) — same `checks_contracts.py` module
- **FR-119**: Top-level provider/model lint (W016) — prior rule in same module
- **FR-164**: Verification gate pattern — future suppression mechanism
- **E010/E011**: Existing `on_error` checks in `checks_semantic.py` — complementary rules
- `examples/demos/pipeline_audit/` — Example that already detects `on_error: skip` as anti-pattern
