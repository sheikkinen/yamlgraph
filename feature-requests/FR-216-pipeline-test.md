# Feature Request: Pipeline Test — No Action Needed

**Priority:** LOW
**Type:** Enhancement
**Status:** Rejected
**Effort:** 0 days
**Requested:** 2026-04-07

## Summary

Pipeline test submission to verify the Chaplain inbox → draft → judge → enforce workflow operates correctly end-to-end.

## Value Statement

Infrastructure maintainers confirm the Chaplain pipeline processes inbox items without manual intervention, catching routing or formatting regressions before real feature requests enter the queue.

## Problem

The Chaplain pipeline (inbox → plan → judge → enforce) has no lightweight smoke-test mechanism. Without a dry-run submission, regressions in file pickup, template rendering, or draft routing go undetected until a real feature request fails.

## Proposed Solution

No code changes required. This FR serves as a no-op test payload. The pipeline should:

1. Pick up `.chaplain/inbox/pipeline-tst.md`
2. Generate this draft in `.chaplain/drafts/`
3. Judge should reject (no actionable work)
4. Enforce should skip (rejected FR)

## Acceptance Criteria

- [x] Inbox file consumed and deleted
- [x] Draft FR generated in `.chaplain/drafts/`
- [x] Judge marks as Rejected (no actionable scope)
- [ ] Enforce pipeline skips rejected FR

## Judgement

**Verdict: REJECT**

No actionable scope. This FR is a pipeline smoke test, not a feature request.
The pipeline operated correctly: inbox → draft → judge (reject). All criteria
except the final enforce-skip are now satisfied. Moving to `feature-requests/`
with Rejected status for the enforce stage to skip.

## Alternatives Considered

- **Manual verification**: Inspect each pipeline stage by hand — doesn't scale, misses timing issues.
- **Integration test**: A pytest-based pipeline test would be more robust but is out of scope for this submission.

## Related

- `.chaplain/watch.sh` — daemon that processes inbox items
- `feature-requests/TEMPLATE.md` — template this FR follows
