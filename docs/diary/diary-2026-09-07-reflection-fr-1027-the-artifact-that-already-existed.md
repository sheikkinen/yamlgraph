# 2026-09-07 — FR-1027: the artifact that already existed, and the premise that did not

The ask was "plan as an FR a graph summarizing last week; tools to fetch FR &
PR from git; repo as a variable," with an assumed blast radius of *a new
graph*. The first fifteen minutes of precedent search dissolved most of it:
`examples/demos/recap/` has answered "what changed in this repo since T?" for
any repository since FR-700, FR-702 gave it a disposition axis, FR-703 and
FR-704 evicted every mechanical field from the model, and FR-821 has been
publishing its output to `docs/recaps/` on a Monday cron for three weeks. The
graph existed. The FR axis existed. The repo variable existed.

What did not exist was the second noun in the request. The recap reads the
local git object store and nothing else, so it can see 92 squash-merge
subjects ending in `(#N)` and resolve none of them.

## The trap: the requester's blast radius is a hypothesis, not a specification

I could have built the new graph. It would have worked, it would have matched
the request as phrased, and it would have been a second artifact answering a
question the first one already answers — with duplicated git collection and a
Monday output split in two. `false_duplicate` warns against calling things
duplicates on syntactic similarity; this was the inverse error waiting to
happen, where the *artifact class* was identical and only the phrasing was new.

The cure was cheap and I nearly skipped it: **ask, with the evidence in
hand.** Not "what do you want?" but "here is what exists, here is the actual
gap, here are three shapes and the one I recommend." The operator picked the
smaller blast radius in one click. The whole exchange cost less than the
duplicate graph's lint pass would have.

A heuristic I want to keep, because I have now watched it work twice:

> **A stated blast radius is evidence about the requester's mental model, not
> about the code.** Search first, then report the delta between the two, then
> ask. Correcting the model is usually the deliverable.

## The premise that did not survive contact

The judgement — APPROVED WITH REVISIONS, five revisions, seven gates — wrote
one sentence I could not obey: *"Invalid `since` … remain[s] loud because the
existing git collection contract already fails those inputs."* It does not.
`git rev-parse --since="not a date"` returns the **current epoch, exit 0**, and
so does `git log --since` for the five collectors already in the graph. A
garbage window has always yielded an empty week, silently.

Two ways to respond. Make the new collector strict, satisfying the
judgement's sentence and making one of six collectors behave unlike the other
five. Or inherit the silence, contradict the sentence, and say so in writing.

I took the second, and the reason is the one law: **the boundary is
`shell.py`/git's date parser, not my node.** A guard at my node is
`downstream_fix` wearing a compliance costume — it would satisfy an
instruction while leaving the actual defect in place and the graph internally
inconsistent. The honest move was a test named for the choice
(`TestSinceGrammarIsGitsOwn`, which pins the argv rather than asserting an
outcome) and a deviation paragraph pointing at the separate FR.

> **A judgement's *reasoning* can be wrong even when its *requirement* is
> right.** R-2 wanted the boundary bounded and normalized; it was correct.
> Its premise about the existing contract was false. Fold the requirement,
> measure the premise, and record the disagreement — a fold that quietly
> repairs the judge's factual error is a private language between author and
> judge (`private_language`), and the next reader inherits neither.

## The measurement that made a red suite legible

`pytest tests/unit -m "not slow"` on this branch: **250 failed, 6275 passed**.
The forbidden phrase was right there and easy to reach for. Instead: a
detached worktree at the merge base, the identical command, and `comm` over
the two sorted 268-line `FAILED`/`ERROR` sets. Both directions empty. The
delta is +63 passes and nothing else, and the root cause of the 268 is one
boundary with a legible error message — POSIX `shlex.quote()` arriving at
cmd.exe.

That is not the same act as claiming a pre-existing failure. It cost four
minutes and it converts an excuse into an artifact: a named boundary, a
baseline SHA, a diff command anyone can rerun.

> **The cure for "pre-existing failure" is not discipline, it is a baseline
> worktree.** `git worktree add --detach <merge-base>`, same command, `comm`
> the two failure sets. Assert the number, never the adjective.

## The criterion I could not close, and did not pretend to

AC-14 wanted the bare-repo integration witness. It is written, committed, and
unrunnable here: the graph dies at its **first** node on this host, identically
on the unmodified base. Then the second measurement, the one I almost did not
take — `.github/workflows/workflow.yml` runs `pytest tests/unit` only.
`tests/integration/` is executed by nothing, on any platform.

So the criterion is not "blocked on Windows, green in CI." It is
**unwitnessed everywhere**, and a tick would have been a lie that CI would
never have caught. `[~] PARTIAL`, the unit half named, the two measurements
cited, three options costed, and the choice handed to the operator.

The uncomfortable part is the discovery, not the disposition: a whole test
directory is decorative. Every integration criterion in every FR that ever
said "and CI will run it" was `gate_checks_shape_not_substance` all along, and
FR-1027 found it by accident while trying to tick one box.

## Heuristic

> **When a criterion cannot be witnessed, find out whether it could ever have
> been.** "Blocked on my platform" and "run by no platform" look identical
> from inside the failing test and are entirely different facts. The second
> is a finding; the first is a note.

**Seed:** `tests/integration/` exists, is maintained, is referenced by
acceptance criteria across dozens of FRs, and is run by no pipeline. How many
other frozen criteria in `feature-requests/` name a witness that no lane
executes — and is that answerable as a census over the AC lines themselves,
mapping each cited command to the workflows that actually invoke it?
(`impossibly_large_sequential_task`: "how many ACs across 1000 FRs cite an
unrun witness" is exactly the corpus-map-reduce framing.)
