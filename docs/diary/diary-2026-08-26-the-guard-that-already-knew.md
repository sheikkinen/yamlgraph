# Diary — The Guard That Already Knew: Enforcing FR-891

**Date:** 2026-08-26
**Context:** FR-891 (fail-closed agent tool boundary) enforced same-day
through the full FR-890 lifecycle: closed brief → research route (first
real consumption; canary precommitted and recalled) → judge (APPROVED WITH
REVISIONS) → worktree enforcement, RED fefc875c → GREEN.

## The insight

The defect's fix was one `if` statement away the whole time: FR-660 already
computed `success=False` per failed tool call and stored it — the signal
existed, unconsumed, exactly like the model's in-text confession in the
incident run. Twice in one incident, truth was available and nothing
mechanical acted on it. The boundary pattern's real lesson: **computing a
signal is not a control; only a consumer with authority to halt makes it
one.** Same shape as `detection_without_enforcement` — a success flag
without an aggregate check is lint without a gate.

## The trap, live

`stale_code_provenance`, personally witnessed: the first D-6 evidence run
returned exit 0 WITH a summary — impossible under the fix. The console
script resolved to the main checkout's editable install, not the worktree.
The Scripture's tripwire line ("an IMPOSSIBLE result is a tripwire proving
stale-code provenance") fired verbatim; `PYTHONPATH=$PWD` was the cure.
Worktree enforcement + editable installs = every measurement run must
verify code provenance first (`python -c "import pkg; print(pkg.__file__)"`
costs 2 seconds).

Also collided with two guards mid-flight: FR-888 denied the main-checkout
test write (worktree route worked as designed — the guard built yesterday
caught its own author today), and the pytest-pipe guard misfired on a git
commit line containing "SKIP=pytest" + "| tail" (false positive; worked
around with redirect — possible guard refinement seed).

## Judge value, quantified

The fresh-context judge caught R-1: my FR said "after the iteration loop,"
but the witnessed incident finalized on the no-more-tool-calls path INSIDE
the loop. Enforcing my own wording would have shipped a fix that misses
the exact defect it cites. One reading by an uncontaminated reader was
worth more than my three.

## Seed

The two legacy FR-660 tests asserted the fail-open behavior by name
("error format preserved") — tests can enshrine a defect as a contract.
Is there a mechanical smell for this: tests asserting `startswith("Error")`
on values that flow onward as data? A census of assertion-on-error-string
patterns might find more laundered failures.
