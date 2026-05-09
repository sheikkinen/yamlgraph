# Reflection: FR-358 Watcher2 Primary PR Title Selection

**Date:** 2026-05-09
**FR:** FR-358 — watcher2 done PR title should use primary feat/fix commit
**Reviewer:** watcher2 post-implement reflection

## Trap

`downstream_fix`: the PR title was read from `git log -1 --format=%s` — the
latest commit. When branches naturally accumulate diary and format commits after
the main implementation commit, the tail commit (docs/chore) overwrote the
meaningful feat/fix subject on squash-merge. Fixing this at the point of use
(the `done` path) rather than enforcing commit ordering discipline is the
boundary-normalisation cure: normalize the title at the selection boundary, not
at every downstream consumer.

`intent_drift`: the validate_gate diary-parity trigger was also using the latest
commit title for feat/fix detection. Failing to update that path in lockstep
would have created a semantic split — the PR title selector says "primary feat",
but the gate still checks "latest commit". Both paths now share the same
`select_primary_pr_title.sh` policy.

## What Happened

FR-358 introduced a shared selector script
(`.chaplain/lib/watcher/select_primary_pr_title.sh`) implementing three-tier
priority:

1. First `feat`/`fix` subject in `origin/main..HEAD` (oldest-first).
2. First subject whose CC type is not `chore` or `docs`.
3. First subject unconditionally (docs/chore-only branch fallback).

The `done` path in `watcher-pipeline-v2.yaml` was updated to call the script
instead of `git log -1`, and `validate_gate_action.py` was updated to call the
same script for diary-parity trigger detection. `REQ-YG-318` and CAP-140 were
reworded accordingly, the old `test_ac09` (which asserted the superseded
`git log -1` behavior) was deleted, and six new acceptance tests confirm the
new policy.

## What Worked

- Single shared script with no additional dependencies: one `bash` file, one
  place to change when the policy evolves.
- Acceptance tests drive the spec rather than only documenting it: each AC has
  an explicit test that would fail if the selector regressed.
- Retiring the old test before adding new ones avoids the
  `partial_remediation` trap — there is no path left that asserts the wrong
  behavior.

## Seed

The primary-title selector currently handles only the title surface. Should
the same policy be extended to PR body derivation — e.g., sourcing the body
from the primary commit's long-form message rather than only the last commit's
description? Or does coupling body generation to title selection risk the
`framework_costume` trap by encoding too much editorial judgment into a
deterministic script?
