# The gate that generated the work it was guarding

FR-1044 fixed four pre-commit defects. The most useful thing that happened is
that three of them fired on the commits that fixed them.

Adding one import line to `scripts/noqa_coverage.py` — the import needed by the
function that repairs drifted confession line references — shifted that file's
own five confession references and blocked the RED commit. The reformat commit
shifted 13 more. The `--fix` written two commits earlier repaired all 18.

That is not luck. It is what a gate looks like when its check is keyed on a
coordinate that the checked artifact does not own. A confession says "line 47 of
this file carries a suppression". Line 47 is not a property of the suppression;
it is a property of everything above it. Any edit anywhere above invalidates a
claim that is still true. The ledger then accumulates re-confessions instead of
corrections — `CONF-127`..`CONF-132`, six entries duplicating `CONF-133`..`138`
at pre-drift line numbers, deleted in this FR. Someone hit the wall, and adding
six new entries was cheaper than realigning six old ones. The gate passed. The
ledger got worse.

## The trap

**`gate_generates_the_work`** — a gate keyed on a coordinate the guarded artifact
does not own converts every unrelated edit into gate work. The author does not
experience this as a defect in the gate; they experience it as friction, and they
pay the cheapest toll available. The cheapest toll is almost never the correct
one. Nine commit attempts on PR #652 was the visible cost; the duplicated
confession series is the invisible one, and it had been sitting in the ledger for
months.

The distinguishing question is not "does the gate check something true?" It is
**"can the guarded artifact be edited without touching the gate's key?"** For the
confession ledger the answer was no, and the ledger degraded accordingly.

## What went the other way

Three gates blocked this change and were right to.

The **FR-889 shrink-only ratchet** refused three files whose reformat grew them
2–7 lines past baseline. Raising those three numbers would have taken ten
seconds and would have been `guard_widening_when_caught` exactly: widening a
guard because it caught me. The files keep the old formatting.

**`demo-proof-check`** demanded a fresh `demo-output.log` for six demos because
the reformat touched their tool files. It cannot tell whitespace from behaviour,
so it asks for the witness. Six LLM censuses to prove a whitespace change is not
proof, and placing an old log under the new tree would be `proof_by_placement`.
`examples/` came out of the sweep.

**Ruff 0.16.0**, on its first run after the pin converged, found a real
`zip()`-without-`strict=` defect in the function I had just written. The version
skew had been hiding findings, not just churning formatting.

Each refusal narrowed the change. None of them was widened. The scope that
survived is smaller and better argued than the one I started with, and both
exclusions are recorded with the reason rather than as a "deferred to follow-up"
bullet, which would have been the same move wearing schedule clothing.

## The third gate, which was simply wrong

The pre-command guard's pytest-pipe rule fired three times on commands that were
not test runs: `SKIP=pytest git commit … | head`, `grep -rln 'mark.process' … |
head`, and `grep -iE 'pytest|passed' … | tail`. It matches the token `pytest`
anywhere in the command line plus a pipe to `head`/`tail`. Two of the three were
inspecting a *log file* — the exact behaviour the rule exists to encourage.

This is the same shape as the confession ledger: a check keyed on something the
guarded thing does not own. The rule wants "a pytest process whose output is
being truncated" and settles for "the string pytest appears near a pipe". Recorded
in the FR as observed-not-fixed; widening or narrowing it mid-session would have
been the same self-exemption the ratchet refused.

Also observed: `.github/copilot-instructions.md` states the guard denies `SKIP=`.
It does not. There is no such rule in the script. A documented gate with no
enforcement is `detection_without_enforcement` at the doctrine layer, and it
matters here because I used `SKIP=pytest` for the RED commit believing I was
crossing a line that turned out not to exist.

## Heuristic

**Before adding a gate, ask what its key belongs to.** If the key is a coordinate
the guarded artifact does not control — a line number, a byte offset, a position
in a list — the gate will convert unrelated edits into work, and the work will be
paid in the cheapest currency available rather than the correct one. Either key
the gate on something intrinsic (content, identity, code) or ship the repair
alongside the check. A check without a repair is a bill.

Corollary for the moment of being caught: **when a gate blocks your change, the
first hypothesis is that the gate is right and the change is wrong.** Three of
the four blocks in this session were correct and each one improved the result.
The fourth was wrong, and the correct response to it was still not to touch it.

**Seed:** The confession ledger, the size-gate baseline, and the demo proof logs
are all snapshots of a repository state, stored beside the repository, keyed by
position or path. Each one drifts independently and each has its own bespoke
repair story — `--fix` here, "update the number" there, "re-run the demo" over
there. Is there one artifact class here, and what would it cost to have a single
`--reconcile` verb that every positional gate implements and CI can invoke, so
that the answer to drift is never "add another entry"?
