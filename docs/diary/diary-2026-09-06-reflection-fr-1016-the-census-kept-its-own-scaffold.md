# The Census Kept Its Own Scaffold

**Date:** 2026-09-06
**FR:** FR-1016 retire the FR-1012 one-shot tooling
**Session:** Claude Code on the Windows host; the session that wrote the tooling this morning and deleted it this evening, on the operator's verbs

## What happened

Twelve hours after writing three scripts to execute the Chaplain removal
— a census driver, a journaled archive script, a post-merge witness — I
deleted them, together with their adapters and 626 lines of tests. The
operator asked one question after the weekend inventory: "are the
chaplain scripts keepers?" The answer took a table of five columns and
came out no on every row: every event they served had passed, nothing
outside their own tests called them, and their only requirement had been
written so that their tests would have something to point at.

Two details from the enforcement are worth keeping.

**The census had voted to keep its own test file.** Row
`tests/unit/test_fr1012_chaplain_census.py`, verdict keep, confirmed by
me this afternoon. It was the right verdict *at census time* — the file
witnessed live code. This evening the same file was in the deletion set,
and the end-state witness that guards "every census keep row is still
there" failed GREEN. The census record is immutable by the judgement's
own condition, so the witness now excludes the FR-1016 set with a
comment saying why. A verdict has a timestamp; a witness that replays
verdicts has to know which later decisions supersede which rows, or it
becomes the thing that blocks the next correct deletion.

**Another session had already paid a debt on the dead code.** While
FR-1016 was being judged, PR #628 documented four `noqa` confessions for
lines in the census script — a gate had started flagging them
repo-wide. Twenty minutes later the lines were gone and the confessions
point at files that do not exist. The `noqa` gate does not check that a
confession's file still exists, so nothing fails; the entries simply
dangle. The judgement froze the FR's surfaces before #628 landed, so
they stay untouched here and are recorded as a deviation for the human.
Two sessions, one repository, one evening: one wrote documentation for
code the other was deleting. `one_session_one_repo` was written about
the shared index; this is the same trap one level up, in the shared
*intent*.

## The trap

**Scaffold survives the building.** Machinery built for a one-time
transformation inherits the legitimacy of the transformation: it is
tested, it has a capability record, it is in `scripts/`, so it reads as
infrastructure. The census asked 115 items "has your event passed?" and
exempted the 1,600 lines that asked the question. `scripts/` already
held five such survivors from earlier migrations. Nothing in the process
fires when a tool's last event passes, because the process only fires on
additions and failures — a tool that will never run again produces
neither.

## Heuristic

At the moment a one-shot's event completes — the census run, the
archive push, the witness pass — the same commit that records the
result should either delete the tool or name the FR that will. "Keep it
for the next time" is a forecast, and the next time has its own
constants, canaries and ceilings that this copy hard-codes wrong. Git
history is the archive; `docs/archive/` names the commit. If the tool
was worth writing, the record of what it did is what the successor
needs, not the tool.

**Seed:** the census pattern knows how to ask "has your event passed?"
of a corpus of tests and capabilities. `scripts/` is a corpus too. Should
every script carry the FR that is its trigger in a header, so that a
sweep — the same census graph with a scripts adapter — can list the
one-shots whose FR is DONE and propose their retirement, instead of
waiting for an operator to notice a name in `ls`?

## Postscript: how the merge came to hinge on ten cache files

The operator asked, on giving the merge word: how did the human gate on
this PR end up being a decision about `untracked_files_left_in_chaplain`
being 10 rather than 0?

The chain, backwards. The round-2 judge made the human's acceptance of
"10" a named condition (C-7) because the round-1 judge had frozen the
value 0 into AC-01 *before the witness had run*; a second frozen
condition (C-4) made the record immutable once it existed; the observed
run said 10; so the two frozen conditions could only be reconciled by a
party outside both — the human. The value itself was never in doubt:
ten `.pyc` files compiled from the deleted modules, gitignored, removed
by hand a minute later, with `.chaplain/` gone. No one believed the
runtime was still there. The supervision function was spent on a
question that had no content.

Two mechanisms produced this.

**The judge predicted evidence instead of binding it.** AC-01 pinned a
*value* for a field of a record that did not exist yet. That is
`threshold_encodes_forecast` in a new costume: an acceptance criterion
that forecasts what the observation will say, so that the observation
can only agree or fail. A criterion may fix the *shape* and *provenance*
of evidence not yet observed — which file, which fields, who ran it,
that it is preserved unchanged — never its value. "The record shows the
count the witness observed, and the FR explains it" was always the
right criterion; "== 0" was a guess dressed as a gate.

**The witness counted what its own spec said to ignore.** The
post-merge witness was specified as "`.chaplain` is untracked-empty";
`__pycache__` is gitignored, so by the spec those ten files were not
what the check was for. The script counted every regular file under the
directory. A one-line `find` exclusion at authoring time — or reading
the raw record once before the judge froze on it — would have produced
0 honestly and the whole C-7 exchange would not have existed. The
number 10 is an artifact of the ruler, not a fact about the tree.

And one thing that went right: when the frozen 0 met the observed 10, I
did not decide. Returning the FR to the judge, and the judge handing the
final word to the human, is the separation the morning's diary entry
asked for. The cost was that the separation fired on the wrong question.
Separation of authority is necessary; it is not sufficient. The
supervisor's attention is the scarcest resource in the loop, and a
process that spends it on a `.pyc` count has a defect upstream of the
gate, in whoever wrote the number down before it was observed.

**Heuristic:** never freeze a value for evidence that has not been
observed; freeze its shape, its source, and its immutability, and let
the observation speak. When a human gate turns out to be about a value
nobody disputes, do not congratulate the process for stopping — find
the criterion that predicted the observation and fix that.

**Seed:** could the judge graph refuse, mechanically, any acceptance
criterion that compares a not-yet-existing artifact's field to a
literal? The pattern is detectable: `== <literal>` on a path that
`git ls-files` does not yet know. A lint on the judgement, before the
human ever sees it.

