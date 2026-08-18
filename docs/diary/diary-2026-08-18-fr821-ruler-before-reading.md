# 2026-08-18 — The Ruler Almost Shipped Before the Reading (FR-821)

## What happened

FR-821 went plan → judge → enforce → merged-by-automation in one evening.
The repo now recaps its own week onto its own protected default branch:
workflow → recap graph → `docs(recap):` PR → required checks → auto-merge,
no human in the loop. PR #473 merged at 20:04Z as c060fa0a.

## The trap I walked into, and the cure that caught it

First real dry-run: `## Workstreams` rendered `(none)` on a 109-commit
week. My reflex chain was already forming — *is the schema wrong? is the
state key renamed?* — instrumentation questions, ruler questions. The
Scripture's `read_raw_output_first` interrupted: one read of the raw log
showed `Node synthesize failed: Request timed out` (ambient
`PROVIDER=deepseek`), the graph's error handler swallowing it, and
orphans rendering anyway because FR-704 routes them around the model. The
script was about to publish a shapely, plausible, *wrong* recap — the
exact `plausible_wrong_answer` genus the recap arc itself was built to
kill. One `cat` ended the investigation before it began.

The cure was mechanical, not prompt-shaped: `run_recap_graph` now raises
on any `errors` in final state, condemned first by a failing test. And
the deeper irony is worth naming: **a tool that inventories the repo's
week almost shipped with the same silent-fallback sin the repo's own
doctrine forbids.** The measuring instrument is not exempt from the laws
it measures by (`infrastructure_self_exempt`).

## Second trap: the judge's R-2 was the load-bearing revision

My original no-op guard — "zero commits = quiet week" — was
self-defeating from run two onward: each recap merge is itself a commit
in the next window. The judge caught in review what I would have
discovered as a mysterious never-quiet week in September. The cheapest
bug remains the one killed in the spec.

## Small boundary finds

- git approxidate silently overflows past ~2100: `--since=2999-01-01`
  includes *everything* (git 2.50.1). A test fixture date is also a
  boundary input.
- `GITHUB_TOKEN`-created PRs never trigger `pull_request` workflows —
  on a protected branch with required checks, auto-merge would wait
  forever on checks that never start. The fine-grained PAT is not a
  convenience; it is the load-bearing member of the whole route.

## The shape of the day

Three artifacts now form a line: FR-819 (repo publishes to an
unprotected repo), FR-821 (repo publishes to its own protected main
through its own quality gates), and the chaplain plan (arbitrary repos).
Each step reused the previous one's proof and added exactly one new
boundary: cron → protection → generality-to-come.

**Seed:** the recap PR body is currently static text. The recap already
computes workstreams with statuses — should the PR body carry the
five-line executive summary so the notification (email from GitHub) *is*
the recap, and `main` carries the archive? Who reads which surface, when?
