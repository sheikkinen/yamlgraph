# Two Brains, One Route

**Date:** 2026-09-04
**FR:** FR-960 Claude judge variant (child D-2 of the FR-958 SPLIT)
**Session:** the same Claude Code session that enforced FR-959; not the FR author's

## What happened

FR-960 was the small one: a second copilot node in the judge graph, a
`JUDGE_BACKEND` switch in the wrapper, and a filename that includes the
backend and the FR. Half a day, said the estimate. It took a working day,
and almost none of the time went to the code.

The graph edit went through `scripts/author.sh` with a committed brief. The
brief named the exact YAML; the Copilot agent produced it, ran lint, hit
`E601` because a passthrough node needs `output: {}`, repaired it, and
reported. I had written the RED routing tests before the brief so the brief
could cite them as its smoke. That ordering — tests, then brief, then
adapter — is the only order in which the brief can be honest about what
"smoke" means.

Then the wrapper. Eight new bash tests, none of which can run on this host
because `subprocess.run(["bash", …])` from Python resolves to the broken WSL
stub (FR-953). I ran the same stub script by hand under Git Bash: five
behaviours, five expected exit codes. CI carries the pytest form. The
witness says both things.

Then the runs. Copilot judged FR-961 in four minutes. The Claude judge
needed the operator's C-8 signature first — a separate spend decision from
the FR-959 Option A, because a judge session is minutes of an Opus agent,
not one word of "pong". The operator said "accepted"; I wrote the word down
and ran it twice, once with an invalid API key in the parent to prove the
strip still holds at judge scale.

## The inventory

The FR's deliverable was never the second judge. It was the table that
compares the two. Judgement R-6 forced a claim-by-claim inventory with
three dispositions and a sentinel for convergence. The sentinel was not
needed:

- **11 matched.** Same verdict class, same evidence lines for the macOS glob,
  same call for an evidence appendix, same interpreter-seam finding.
- **4 contradicted.** The most useful: Copilot's R-2 says derive runtime from
  registration provenance and forbid vocabulary inference; Claude's R-4
  keeps vocabulary inference and repairs it. Both are internally coherent.
  The FR-961 author now has to choose, which is exactly what
  `forced_opposite` is for.
- **5 backend-only Claude, 2 backend-only Copilot.** Claude's R-1 is the one
  that matters: the guard's allow path prints `{"decision":"approve"}`, and
  if Claude Code still honours that deprecated key, *registering the guard
  removes the permission prompt*. An enforcement FR that could delete a
  safety boundary by accident, and the first judge did not see it. Copilot,
  for its part, checked the research record's five retrieved prior-art
  hits against the FR's Prior art line and found them undischarged; Claude
  did not.

Two judges with different harnesses read the same file and one of them
found a safety hole. That sentence is the FR's value proposition, now with
a witness.

## Traps

**estimate_counts_code.** "0.5 day" counted the YAML and the shell. It did
not count the brief, the two witnesses, the two signatures, the inventory,
or the review cycle that made the previous FR honest. Enforcement
infrastructure is mostly evidence; the code is the cheap part.

**alias_is_not_a_pin.** FR-960 §1 promised "exact id pinned in the
witness" for `model: opus`. The JSON envelope on 2.1.255 does not report the
resolved model. I could have looked it up in the docs and written it down
as if observed. The witness says it could not be pinned. A pin you did not
observe is a guess wearing a pin's clothes.

**same_input_two_drafts.** Runs B and B' were byte-identical in input and
produced drafts with nine and eleven revisions. Non-determinism at this
scale is fine — the wrapper's rerun-overwrite rule means the second draft
replaced the first at the same path, and I had copied the first out only
because the FR-959 evening had taught me to. `cp` in the same shell command
as the wrapper is still the reflex, one layer down from the clobber it was
born to prevent.

## Heuristic

When a deliverable is a *comparison*, write the inventory of side A before
side B exists. Half the table was filled while the Claude judge was still
reading; the other half dropped into place. The comparison is easier to
write when one side is fixed and the other is arriving, and harder when
both are on the page shouting.

**Seed:** three witnesses were the trigger the FR set for filing the
comparison graph. This is witness one. The inventory columns — ID, section,
claim, evidence, disposition — are already a schema. When witness three
arrives, the question is not whether to graph it but whether the
`contradicted` rows should feed back into the judge prompt as a checklist
the *next* judge must explicitly address, turning disagreement into
doctrine one FR at a time.
