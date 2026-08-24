# 2026-08-24 — Enforcing the Ramp Family Under a Shared Index

Five FRs enforced in one arc (FR-865 installer, FR-869 spike-end guard,
FR-866 tailoring graphs, FR-868 salvage, FR-867 first application), all
while a parallel session committed FR-870/FR-871 work into the same
repo. The interleave was not hypothetical this time: HEAD moved four
times mid-cascade, a stale working tree reverted `docs/confessions.md`,
and foreign diary files appeared STAGED between my `git add` and
`git commit`. The pathspec commit (`git commit -F msg -- <files>`)
turned out to be the only commit form that is safe by construction
under a shared index — it ignores the staging area's foreign content
entirely. That is a stronger ritual than "staged-check before add" and
should replace it as the default in shared-repo sessions.

**Trap witnessed twice, cure landed in code.** FR-866's incidents merge
failed on a truncated map branch; FR-868's salvage merge failed on a
model echoing its twin's path (`hooks/x.sh` vs `_templates/hooks/x.sh`
— 49 files, 8 twin pairs, one wrong echo). Same family: the model
re-stating an identity it was GIVEN. `two_strike_split` fired on
schedule: the second strike went into code at the merge boundary —
`_normalize_map_results` now repairs the echoed path from branch
identity (`_map_index` → manifest order). The model's echo is a claim;
the input is the truth. No prompt was reworded.

**The raw read overturned the artifact again.** The salvage
disposition validated perfectly — 49/49, zero errors — and was wrong:
25 lifts including the repo's own diary as "governance history",
vulture hooks this repo already runs, and `scripture.yaml` whose
`project_name: my-minesweeper` is the FR's own staleness exhibit. Shape
passed; substance failed. Four quoted entries in the FR record did what
no validator could: they let the human see the lift bar being misread
as "different" instead of "missing and still correct". The verdict
counts were also anti-correlated with usefulness — the 2-item
`obsolete` bucket contained the one asset (`render.sh`) whose verdict
was right for the wrong reason.

**Demo-gate friction has a shape.** Three separate commits stalled on
demo-proof-check: first a fatal-marker scan matching "FAILED" inside
*quoted corpus text* in a `--full` state dump (the gate cannot tell
narration from quotation — drop `--full` from demo logs whose state
embeds failure-narrative corpora); then README-only changes under
`examples/demos/<name>/` demanding a fresh run of an expensive
LLM demo. The operator's "skip the gate" (`SKIP=demo-proof-check`) was
the correct disposition for a docs-only diff — but the gate's
predicate conflates "demo changed" with "any file under the demo dir
changed". That is `gate_checks_shape_not_substance` inverted: the gate
checks substance where only shape changed.

**Draft freshness is provenance.** The fixture demo runs and the
target runs write to the SAME `tmp/ramp/` paths. FR-866's demo logs
silently replaced the deviant-daily doctrine/rtm drafts with
fixture-derived ones; only a provenance check (`target` key in the
JSON) caught it before the review table pointed at the wrong artifacts.
Draft outputs keyed by content, not by target, are a collision waiting
for the second consumer — the graphs should stamp the target into the
filename or the drafts directory.

**FR-867 stopped exactly where it should.** The target tree held 15
files of foreign WIP; AC-02 demands clean status; `workspace_is_not_
boundary` says that WIP is not mine to resolve. The FR now carries the
activation record, dry-run transcript, and hashed handoff table up to
the two human gates — which is the completed state for an agent
session, not a failure to finish.

**Seed:** the demo gate and the authoring guard both fire on *path
prefix* while their intent is *artifact class* (executable demo
changed; governed graph authored). Could gates read the diff's file
types instead of its directories — README/docs diffs pass free,
graph/prompt/node diffs demand proof — so that "skip the gate" stops
being a recurring operator override and becomes the gate's own
distinction?
