# Diary: FR-786 API Discovery Page-Analysis Step

**Date:** 2026-08-14
**FR:** FR-786
**Duration:** ~50 min

## What happened

FR-786 arrived judged **APPROVED WITH REVISIONS** (as did 6 siblings:
FR-784, FR-787..FR-792) — the FR body had never been amended after
judgement, git showed identical commit timestamps for FR and
`.judgement.md`. Folded the four required revisions (explicit `fetch_page`
dependency, named platform catalog + exact schema, fixture-backed ACs,
frozen scope boundary) directly into the FR text, re-ran the sole-route
judge adapter (`scripts/judge.sh`), got **APPROVED** with zero further
revisions, then authored via `scripts/author.sh` against a closed task
brief mirroring the FR-785 endpoint-probe precedent.

## Trap encountered (recurrence): author.sh wrapper reports failure while the artifact is genuinely valid

Second time in two days (see `diary-2026-08-13-endpoint-probe-step.md`)
that the authoring wrapper's exit-code path diverged from ground truth.
This time the copilot CLI child hit the graph's 900s node timeout
*after* it had already written a complete `tmp/draft-authoring-report.md`
(all 5 required headings, every listed artifact real) and finished
building its own validation venv with the `verify`/`azure` extras. The
wrapper's `[ -s "$ARTIFACT" ]` check ran moments too early relative to
an async/orphaned write. Manually re-running the exact same contract
checks (headings present, artifact paths exist) the wrapper uses proved
the report substantively valid — and independently re-running lint +
both fixture smokes reproduced the *exact same* values recorded in the
agent's own report (down to the specific extracted API URLs). Cure
applied: `substance_over_presence` — checked the artifact honestly
instead of trusting the wrapper's rc=1, but also independently
reproduced the evidence rather than taking the report's word for it.

## Insight: judge-then-fold-then-rejudge is a fast, honest loop

Folding revisions and re-invoking the sole judge route took under 3
minutes end-to-end (draft judgement → `APPROVED`, zero more revisions).
The judge doctrine's input closure (FR text + cited evidence, no chat
narrative) meant the re-judgement was a clean, fresh read — it explicitly
confirmed "the prior judgement's required revisions have been folded"
by citing the exact line ranges I'd added. This is cheap enough that
"APPROVED WITH REVISIONS" should be treated as a normal mid-pipeline
state, not a stall.

## Heuristic

Seven sibling FRs in one batch carried the same unfolded-revision status
(same commit timestamp as their judgements) — a batch-authored set is
prone to batch-skipping the fold step. Before enforcing ANY FR, check
`git log -1 --format=%ai -- <fr>.md <fr>.judgement.md`; identical
timestamps mean the loop was never closed.

## Seed

Two recurrences of the same wrapper/reality divergence (endpoint-probe,
page-analysis) in the authoring adapter — is it time to graduate a
mechanical fix: have the graph's own final tool call `sync`/`fsync` the
report file and emit a completion marker *before* any subsequent
tool-call attempt, so the timeout race can't land between "report
written" and "wrapper's exit-code check"? Or should `author.sh` poll for
the artifact for a short grace window after a timeout instead of failing
immediately on `rc != 0`?
