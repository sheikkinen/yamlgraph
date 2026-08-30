# The Guard That Only Ever Arbitrated Against Itself

**Date:** 2026-08-30
**FR:** FR-927 — retire the FR-902 lane-guard hook machinery
**Arc:** FR-902 (build) → FR-889 §4c (partial subtraction) → FR-925 (fix the
delivery) → FR-927 (delete the thing)

## What happened

Enforcement was mechanical. RED test, 7 failures each naming a live surface,
delete, GREEN. The interesting part was not the deletion — it was the two
places the deletion *bled* outside the frozen scope, and what each leak said
about how enforcement infrastructure is coupled.

## Trap: the test that anchored on its successor's presence

`test_main_write_guard.py::_check7_region()` located FR-889's guard block by
slicing from `"Check 7: main-write"` to `"Check 8:"`. It read as a
region-extraction helper. It was actually a **structural dependency on the
next check existing** — FR-889's tests could not survive FR-902's removal,
even though FR-889's code was untouched.

Eight tests went red on a deletion that changed nothing they assert about.
The judgement's C-4 ("do not change FR-889's guard while enforcing FR-927")
was satisfiable in code and *not* satisfiable in the test file, because the
test had encoded a fact about a neighbour rather than about its subject.

Generalization: **a test that locates its subject by a sibling's marker is
coupled to the sibling's lifetime.** Anchor on the subject's own terminator
(here, the shared `# Only inspect run_in_terminal` boundary that belongs to
the guard's control flow, not to any one check).

## Trap: removing a clause leaves the witness homeless

CAP-254's REQ-YG-629 said "lane creation is idempotent **and** the PreToolUse
guard denies out-of-lane writes". The plan said: drop the guard clause. Doing
exactly that left the new retirement test with nothing to trace to — ADR-001
demands every test name a requirement, and "this thing does not exist" is not
a clause you get by *deleting* text.

The cure was to state the absence positively: "lane creation is manual only:
no SessionStart/Stop lane hooks, no PreToolUse lane arbitration, no escape
variable exists in the hook chain." A retirement is an invariant, not a gap.
Subtraction FRs need a *requirement to subtract into*, or the pin has no
anchor and quietly rots into an untraceable test.

## Insight: `infrastructure_self_exempt`, confirmed a third time

FR-902's guard denied the removal of its own kill switch (`sudo rm
fr902.live` was needed). FR-889 §4c deleted Check 7's grammar but left the
identical grammar alive in Check 8 — the *survivor* imported the known-bad
cwd resolution the deletion was meant to kill. Both are the same shape:
enforcement machinery is the least-audited code in the repo precisely because
it is the code that audits. The partial subtraction is more dangerous than no
subtraction, because it leaves a discredited mechanism wearing the reputation
of the one that was fixed.

Heuristic (candidate for graduation): **when a subtraction FR leaves a
sibling mechanism using the same discredited primitive, the FR is not done —
enumerate every consumer of the primitive, not every occurrence of the
symptom.** This is `partial_remediation` scoped to enforcement code, where
the blast radius is every future session.

## Insight: the honest subtraction keeps the coverage it inherited

The frozen scope authorized deleting the FR-902 hook tests. Four of them were
genuinely dead with their scripts. One — the gc/join test — exercised
`worktree.sh gc`, `now.py`, and `session_join.py`, all explicitly *retained*
by C-5. Deleting it would have satisfied the letter of the plan and shipped
retained code with zero behavioural coverage: subtraction theatre.

It was moved and re-pointed instead: the checkpoint provenance the join reads
is now built by direct trailer commits rather than by the deleted Stop hook.
The test got *simpler* by losing its hook dependency — which is the tell that
the coupling was never load-bearing.

**Heuristic:** in a removal FR, the deletion list and the retention list must
be reconciled against the *test* inventory, not just the source inventory.
Any test whose subject is on the retention list survives, whatever its
filename says.

## Seed

FR-902 was designed, judged, enforced, live-gated, and retired inside 48
hours — the fastest full lifecycle in the repo, and the doctrine handled it
cleanly. But the retirement was triggered by an operator noticing false
denials, not by any mechanism.

**Seed:** the audit log records every OVERRIDE and every DENY with a reason
string. A guard whose escape rate approaches its denial rate is a guard that
has stopped discriminating. Could `now.py` surface a per-check
override-to-deny ratio, so an enforcement mechanism that has degenerated into
noise proposes its own retirement FR before a human has to notice? The
`audit_as_ritual` entry already names 3+ audits without a fix as ritual —
this would be its mechanical counterpart for *denials* without corrections.
