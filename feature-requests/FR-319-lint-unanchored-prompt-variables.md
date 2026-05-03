# Feature Request: FR-319 Lint Unanchored Prompt Variables

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Add a `yamlgraph graph lint` warning for nodes that declare `variables:` but do not reference those variables in their prompt template.

## Value Statement

Graph authors get immediate feedback when graph-to-prompt contracts drift, preventing silent variable drops that cause LLM target improvisation.

## Problem

Issue #306 reports a concrete drift failure: `fr_path` was passed by the graph, but the prompt text did not render it, so the model selected an unintended FR from ambient context.

This is currently undetected:

1. `yamlgraph/linter/checks.py` validates missing declarations (`E001`/`E002`) but has no inverse check for **declared node variables never referenced by prompt text**.
2. Runtime validation (`yamlgraph/utils/template.py::validate_variables`) enforces only missing required variables.
3. `tests/unit/test_template.py::test_validate_extra_variables_ok` confirms extra variables are accepted and ignored.

Result: the contract mismatch is silent at runtime and invisible at lint time.

## Research: Existing Patterns, Alternatives, Prior Art

1. **Internal prior art for dead-contract warnings:** `check_tool_references()` emits `W001` for defined-but-unused tools.
2. **Existing template parsing utility:** `yamlgraph/utils/template.py::extract_variables()` already supports both simple placeholders and Jinja2 syntax.
3. **Existing lint pipeline extension point:** `yamlgraph/linter/graph_linter.py::lint_graph()` already composes independent checks; adding one warning check is architecture-aligned.
4. **Alternative considered (and rejected):** hard-fail at runtime for extra variables in `validate_variables()` would be broader and breaking for graphs intentionally passing additional context.
5. **Scope check:** no existing linter check currently detects unanchored `nodes.*.variables` keys.

## Objectives

1. Detect unanchored keys in `nodes.*.variables` for prompt-bearing nodes.
2. Report the mismatch as a warning with actionable details.
3. Keep behavior change strictly at lint time (no runtime semantic change).

## Constraints

1. Scope is limited to graph linter checks and directly coupled unit tests.
2. Severity is warning (non-blocking) in the first iteration.
3. No runtime behavior changes in executor, node factories, or prompt rendering.
4. First iteration covers explicit `nodes.*.variables` only.

## Proposed Solution

Add a new lint check (proposed code: `W023`) and wire it into `lint_graph(...)`:

1. For each node with both `prompt` and non-empty `variables`:
   1. Resolve prompt path using existing `resolve_prompts_dir()` / `get_prompt_path()` logic.
   2. Load prompt content.
   3. Determine anchored keys by combining:
      - direct template references (`{key}`, `{{ key }}`) via existing variable extraction.
      - state-qualified references in prompt text (`{{ state.key }}`) for keys passed from state.
2. Emit one warning per node if any declared variable keys are unanchored.
3. Warning message must include node name, prompt name, and missing key list.
4. Add focused unit tests for positive and negative cases.

## Acceptance Criteria

- [x] **AC-01:** Lint emits `W023` when a prompt node declares `variables` keys not referenced by its prompt template.
- [x] **AC-02:** No `W023` when declared keys are referenced directly (`{key}` / `{{ key }}`).
- [x] **AC-03:** No `W023` when declared keys are referenced via state-qualified Jinja (`{{ state.key }}`).
- [x] **AC-04:** `W023` message includes node name, prompt name, and exact unanchored key(s).
- [x] **AC-05:** Nodes without `prompt` or without `variables` are ignored.
- [x] **AC-06:** Rule is warning severity and does not flip `LintResult.valid` to false by itself.
- [x] **AC-07:** Unit tests are RED before implementation and GREEN after implementation.

## Failing Acceptance Tests (RED)

Current RED proof (executed against current code):

```bash
python - <<'PY'
import tempfile
from pathlib import Path
import yaml
from yamlgraph.linter.graph_linter import lint_graph

tmp = Path(tempfile.mkdtemp(prefix="fr319-red-"))
(tmp / "prompts").mkdir()
(tmp / "prompts" / "judge.yaml").write_text(
    "system: Judge\nuser: Examine feature request in feature-requests/\n"
)

graph = {
    "version": "1.0",
    "name": "red-unanchored-vars",
    "state": {"fr_path": "str"},
    "nodes": {
        "judge": {
            "type": "llm",
            "prompt": "judge",
            "variables": {"fr_path": "{state.fr_path}"},
            "state_key": "verdict",
        }
    },
    "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
}

graph_path = tmp / "graph.yaml"
graph_path.write_text(yaml.safe_dump(graph))
result = lint_graph(graph_path, tmp)
assert any(issue.code == "W023" for issue in result.issues), (
    "RED: expected W023 for unanchored variable fr_path; "
    f"actual issues={[i.code for i in result.issues]}"
)
PY
```

Observed failure:

```text
AssertionError: RED: expected W023 for unanchored variable fr_path; actual issues=[]
```

Planned unit test file for implementation phase:

- `tests/unit/test_fr319_lint_unanchored_prompt_variables.py`

## Alternatives Considered

1. **Runtime error on extra variables in `validate_variables`** — Rejected; breaks existing permissive runtime behavior.
2. **Watcher-only prompt guard** — Rejected; this is a framework-level graph lint concern, not watcher-specific.
3. **Manual review discipline** — Rejected; non-mechanical and regression-prone.

## Related

- GitHub issue #306: <https://github.com/sheikkinen/yamlgraph/issues/306>
- `docs/diary/2026-05-03-fr-311-hook-retry-unanchored-prompts.md`
- `yamlgraph/linter/checks.py`
- `yamlgraph/linter/graph_linter.py`
- `yamlgraph/utils/template.py`
- `tests/unit/test_template.py` (`test_validate_extra_variables_ok`)
- `tests/unit/test_graph_linter.py` (`W001` unused-tool warning precedent)
- Topic path requested by prompt: `.chaplain/processing/gh-306.md` (not present in this worktree)
- Canonical source used for planning: issue #306
