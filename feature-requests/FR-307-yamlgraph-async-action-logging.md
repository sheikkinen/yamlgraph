# Feature Request: FR-307 yamlgraph_async Action Logging

**Priority:** HIGH
**Type:** Bug
**Status:** Draft
**Effort:** 0.5 days
**Requested:** 2026-05-02

## Summary

Add comprehensive logging to `yamlgraph_async_action.py` so that silent failures in graph execution are diagnosable from the FSM log alone.

## Value Statement

Pipeline operators can diagnose why a graph step produced no output without re-running the pipeline or inspecting LangSmith traces, reducing mean-time-to-diagnosis from hours to seconds.

## Problem

During the gh-264 pipeline run (FR-306), the judge graph completed in 8 seconds and the enforce graph in 7 seconds. Both were yamlgraph_async invocations that should have taken minutes. The log showed:

```
No event_map match in output:  🚀 Running graph: step-judge-v2.yaml
   Variables: {'topic_file': '...', 'fr_path': '...'}

🔗 Trace: https://eu.smith
```

The output was truncated to 200 characters. stderr was never logged. The exit code on success was never logged. Root cause (missing prompt file, empty LLM response, or graph compilation error) was invisible.

### Specific gaps

1. **stderr swallowed on exit 0** — `yamlgraph` prints errors/warnings to stderr but `yamlgraph_async` only logs stderr on non-zero exit codes. Graph compilation warnings, prompt-not-found errors, and provider failures are invisible when the process still exits 0.
2. **stdout truncated to 200 chars on event_map miss** — The warning log slices `stdout_text[:200]`, cutting off the actual LLM output that would reveal whether the graph ran at all.
3. **No stdout logging on success path** — When event_map matches, we see which pattern matched but not the full output. When no event_map is configured, nothing is logged.
4. **Exit code not logged on success** — Cannot distinguish "ran normally" from "crashed gracefully with exit 0".

## Proposed Solution

Edit `yamlgraph_async_action.py` to add:

1. **Always log stderr** (at WARNING level) when non-empty, regardless of exit code
2. **Log full stdout on event_map miss** (at WARNING level) — remove the `[:200]` truncation, or increase to at least 2000 chars
3. **Log exit code and stdout length on every run** (at INFO level) — e.g. `exit=0, stdout=42 chars, stderr=0 chars`
4. **Log a DEBUG-level dump of stdout** on successful event_map match for traceability

## Acceptance Criteria

- [ ] **AC-01:** When yamlgraph exits 0 with non-empty stderr, stderr content appears in the log at WARNING level
- [ ] **AC-02:** When event_map is configured and no pattern matches, full stdout (up to 2000 chars) is logged
- [ ] **AC-03:** Every yamlgraph invocation logs exit code, stdout length, and stderr length at INFO level
- [ ] **AC-04:** Existing unit tests for yamlgraph_async still pass
- [ ] **AC-05:** No changes to the event routing logic — only logging additions

## Alternatives Considered

1. **Redirect yamlgraph output to a separate log file** — Rejected. Adds file management complexity; the FSM log should be self-contained for diagnosis.
2. **Add --verbose flag to yamlgraph CLI** — Complementary but insufficient; the action must still capture and log whatever yamlgraph emits.

## Related

- Discovered during: FR-306 (gh-264 pipeline run)
- Parent: FR-305 (pipeline FSM v2)
- File: `.chaplain/actions/yamlgraph_async_action.py`
