# Feature Request: FR-308 Judge Fallback Must Fail, Not Approve

**Priority:** CRITICAL
**Type:** Bug
**Status:** Superseded by FR-309
**Effort:** 0.25 days
**Requested:** 2026-05-02

## Summary

Change the judge step's default event from `success: approve` to `success: error` so that unrecognized or missing LLM output fails the pipeline instead of auto-approving.

## Value Statement

Pipeline operators get a judge gate that actually blocks — a missing verdict means "I couldn't judge" (fail), not "looks good" (approve). This prevents broken, no-op, or errored judge invocations from silently greenlighting enforcement.

## Problem

In `watcher-pipeline-v2.yaml`, the judge action is configured as:

```yaml
judge:
  - type: yamlgraph_async
    event_map:
      APPROVE: approve
      REVISE: revise
      REJECT: reject
    success: approve    # ← THIS IS THE BUG
```

The `success` key is the fallback event emitted when no `event_map` pattern matches. During the gh-264 run, the judge graph's output contained only the startup banner (no LLM verdict). The action logged `No event_map match in output` and fell through to `success: approve`, auto-approving a feature request that was never reviewed.

This violates Commandment 6 ("bear witness of thy errors — hide nothing") and the Knowledge Graph cure `plausible_wrong_answer` ("output passes shape check but is semantically wrong").

### Failure modes that currently auto-approve

| Scenario | What happens | Should happen |
|---|---|---|
| Judge prompt file missing | Graph prints banner, exits 0, no verdict | Pipeline fails |
| LLM returns empty response | No event_map match, falls through | Pipeline fails |
| LLM returns gibberish | No APPROVE/REVISE/REJECT substring | Pipeline fails |
| Graph compilation error (exit 0) | Banner only in stdout | Pipeline fails |
| Provider auth failure (exit 0) | Error in stderr, empty stdout | Pipeline fails |

## Proposed Solution

Two changes:

### 1. Change fallback in pipeline config

```yaml
judge:
  - type: yamlgraph_async
    event_map:
      APPROVE: approve
      REVISE: revise
      REJECT: reject
    success: error      # ← No match = pipeline fails
    error: error
```

### 2. Add the missing judge prompt file

The judge graph (`step-judge-v2.yaml`) references `prompts_dir: ../copilot/prompts` with `prompt: judge`, but `.chaplain/copilot/prompts/judge.yaml` does not exist. This is why the judge produced no verdict.

Create `.chaplain/graphs/watcher-plan/prompts/judge.yaml` (co-located with the graph's actual prompts_dir) with a prompt that:
- Reads the FR at `{fr_path}`
- Evaluates against acceptance criteria quality, scope, and feasibility
- Outputs exactly one of: `APPROVE`, `REVISE: <reason>`, `REJECT: <reason>`

## Acceptance Criteria

- [ ] **AC-01:** `watcher-pipeline-v2.yaml` judge action has `success: error` (not `approve`)
- [ ] **AC-02:** Judge prompt file exists at the path referenced by `step-judge-v2.yaml`
- [ ] **AC-03:** When judge graph produces no APPROVE/REVISE/REJECT output, the pipeline transitions to `failed` state
- [ ] **AC-04:** When judge graph produces APPROVE, pipeline proceeds to enforce_session (unchanged)
- [ ] **AC-05:** When judge graph produces REVISE, pipeline loops back to plan (unchanged)

## Alternatives Considered

1. **Add a "no-match" event to event_map** — Rejected. The `success` key already serves this purpose; changing its value is sufficient.
2. **Validate prompt existence in yamlgraph_async before running** — Complementary (belongs in FR-307 logging) but doesn't fix the fallback semantics.
3. **Remove the success fallback entirely** — Not possible; yamlgraph_async requires a success event for the non-event_map code path.

## Related

- Discovered during: FR-306 (gh-264 pipeline run)
- Logging improvements: FR-307
- Parent: FR-305 (pipeline FSM v2)
- Config: `.chaplain/config/watcher-pipeline-v2.yaml`
- Graph: `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`
- Scripture: Commandment 6, `plausible_wrong_answer` trap
