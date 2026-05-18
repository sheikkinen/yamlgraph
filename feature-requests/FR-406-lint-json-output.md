# Feature Request: Machine-Readable Lint Output (--json)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-05-18
**Judged:** 2026-05-18

## Summary

Add `--json` flag to `yamlgraph graph lint` so agents and CI scripts can consume lint results as structured JSON instead of parsing emoji-decorated text.

## Value Statement

Agent nodes and CI pipelines get stable, parseable lint output — eliminating regex parsing of human-formatted diagnostics.

## Problem

`graph lint` currently emits:
```
❌ graph.yaml
   ❌ [E501] Subgraph node 'analyze' missing 'graph' field
      Fix: Add 'graph' field: graph: subgraphs/analyze.yaml
```

This is human-readable but machine-hostile. A copilot node or Chaplain FSM step that calls `graph lint` must regex-parse the output to extract code, message, and fix. The `LintResult` Pydantic model already exists — it just isn't serialized to stdout.

## Proposed Solution

Add `--json` flag to the lint subcommand. When set, emit `LintResult.model_dump_json()` to stdout, errors to stderr:

```bash
yamlgraph graph lint --json graph.yaml
```

```json
{
  "file": "graph.yaml",
  "valid": false,
  "issues": [
    {
      "severity": "error",
      "code": "E501",
      "message": "Subgraph node 'analyze' missing 'graph' field",
      "line": 14,
      "fix": "Add 'graph' field: graph: subgraphs/analyze.yaml"
    }
  ]
}
```

For multiple files, emit newline-delimited JSON (one `LintResult` per line).

Implementation is trivial — `LintResult` is already a Pydantic model. The change is ~10 lines in `cmd_graph_lint`:

```python
if getattr(args, "json", False):
    print(result.model_dump_json())
else:
    # existing emoji output
```

## Acceptance Criteria

- [ ] `yamlgraph graph lint --json <path>` emits valid JSON to stdout
- [ ] Multiple files emit newline-delimited JSON
- [ ] Exit code semantics unchanged (1 on errors, 0 otherwise)
- [ ] Human output unchanged when `--json` not passed
- [ ] Tests added for JSON output parsing
- [ ] `graph validate --json` follows same pattern

## Alternatives Considered

- **SARIF format**: Standard for static analysis tools. Heavier than needed; could be a follow-up if IDEs need integration.
- **`--format=json`**: More extensible but YAGNI — only JSON and human matter now.

## Related

- `yamlgraph/cli/graph_validate.py` — lint CLI implementation
- `yamlgraph/linter/graph_linter.py` — `LintResult` model
- `yamlgraph/linter/checks.py` — `LintIssue` model with `code` and `fix` fields
- Inspired by Zero language's `zero check --json` (https://zerolang.ai)

## Judgement

**Verdict: APPROVED (low priority)**

Pain is anticipated rather than felt — no agent or CI script currently parses lint output. However, effort is negligible (~30 minutes including tests) because `LintResult` is already Pydantic. The change is purely additive with zero risk to existing behavior. Approve as low-priority; tackle opportunistically.
