# Reflection: FR-358 Watcher2 Sanity Check Review

**Date:** 2026-05-09
**FR:** FR-358 — watcher2 done PR title should use primary feat/fix commit
**Reviewer:** watcher2 post-validate sanity check

## Trap

`downstream_fix` was the root pattern here: `git log -1 --format=%s` read the
*latest* commit, not the *primary* one. Any diary or format commit appended
after the real feat/fix would silently hijack the squash-merge subject on
`main`. This is a classic downstream manifestation — the symptom shows up in
`main`'s commit history, but the root cause is at the boundary where
`PR_TITLE` is assigned in the `done` action.

`intent_drift` was the secondary risk: the `validate_gate` diary-parity trigger
also used latest-commit semantics independently. Without updating it in lockstep,
the two paths would have diverged — the PR title would reflect the primary
commit while the gate still tested feat/fix detection against the latest commit.

## What Happened

Sanity review finds the implementation clean and proportional:

1. **Scope proportionality**: 10 files changed, 444 insertions / 12 deletions.
   All changes are in watcher2 orchestration (`watcher-pipeline-v2.yaml`,
   `validate_gate_action.py`), the new shared script
   (`select_primary_pr_title.sh`), watcher2 acceptance tests, and contract
   documents (`ARCHITECTURE.md`, `CAP-140`). No YAMLGraph runtime code touched.

2. **Test quality**: Six acceptance tests, all passing, each exercising a
   distinct branch-commit scenario via a `git`-mock technique. Assertions are
   behavioral (output string equality, key substring presence in config) — no
   implementation trivia. The superseded `test_ac09` was replaced with a new
   test asserting the correct new policy, closing the gap without orphaning a
   false-positive.

3. **FR/code alignment**: All eight ACs checked. AC-01 through AC-06 have
   dedicated tests. AC-07 (RED tests present) and AC-08 (old test replaced) are
   both satisfied.

4. **Normalization at boundary**: The selector runs entirely at the point of
   `PR_TITLE` assignment. No downstream consumer needs to know which commit
   was "primary"; they all receive the already-resolved title.

## Root Cause

`git log -1 --format=%s` is a position-dependent selector: it returns whatever
commit happens to be at HEAD. Branch workflow naturally appends diary and format
commits *after* the implementation commit, making HEAD the wrong place to look
for representative intent. The fix — reading all branch commits oldest-first and
applying a priority rule — treats the title boundary correctly.

## What Worked

- Single shared shell script (`select_primary_pr_title.sh`) with no new
  dependencies: one file, one policy, two consumers (`done` + `validate_gate`).
- Acceptance tests use a `git` mock injected via `PATH` override — isolated,
  fast, and portable without requiring a real git repository in tests.
- Retiring the old test before adding new ones avoids `partial_remediation`:
  no path remains that asserts the wrong behavior.
- ARCHITECTURE.md REQ-YG-318 and CAP-140 updated together, preventing contract
  drift between documentation and behavior.

## Seed

The current primary-title selector operates on the subject line only. Should
the same `origin/main..HEAD` traversal be extended to extract structured
metadata (FR number, scope) from the primary commit for use in PR body
templating — or would encoding that editorial logic in a deterministic selector
risk the `framework_costume` trap by making the script carry too much
orchestration responsibility that belongs in the LLM-driven `done` narrative?
