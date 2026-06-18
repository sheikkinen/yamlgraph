# Diary: Boundary at Admission, Not Detection

**Date:** 2026-06-17
**FR:** FR-509 (cast-filter), FR-508 (layered memory), FR-507 (lifecycle gate)
**Runs:** 10010 → 10011 → 10012 → 10013

---

## What Happened

The lifecycle gate was firing on every chapter open: chapters 2–6 tried to include
Arnulf in active cast despite the seam packet saying he was missing/absent before
chapter 7. Each violation caused the turn to fail, session swallowed it, the loop
retried, and eventually the chapter close ran anyway — so generation *completed*
but the witness check still failed because the log captured each gate fire.

My first hypothesis was throughput: not enough turns for the story to finish.
I raised the cap from 96 to 128. Pacing improved (10012 reached 7/7 completion
parity) but lifecycle_gate_violation_count went from 6 → 5 — violations persisted
because the source of the problem was not pacing.

The second hypothesis was correct: the leak was upstream of the gate. Cast was
assembled from the full reviewed roster, then the gate detected the violation, then
the session caught the exception, then the loop continued. The gate was doing its
job; I was watching symptoms downstream of the defect.

Fix: filter the roster against the N-1 seam packet *before* building cast, using
the same `validate_character_lifecycle` helper the gate uses. Characters who would
violate the gate are excluded from cast admission at source. The gate remains as
backstop. One call to `_filter_roster_for_lifecycle` wired into `invoke_turn`
before the cast list comprehension.

10013 (cap 128, with FR-509): lifecycle_gate_violation_count = 0, pass = true.

---

## Cognitive Traps Encountered

**throughput_as_proxy_for_correctness**
When the story didn't complete I assumed more turns would solve it. Turns do help
pacing, but lifecycle violations are independent of turn budget. The first cap
increase (96→128) improved one metric while leaving the real defect untouched. I
should have read the violation log *before* adjusting the operational parameter.

**detection_conflated_with_enforcement**
The gate was working correctly. The problem was that it was called *after* an
illegal cast had been assembled. Correct detection downstream does not imply
correct enforcement upstream. The Scripture calls this explicitly:
"Normalize at the boundary where external data enters, not downstream where it
manifests." The cast is assembled from roster — that assembly is a boundary where
lifecycle authority should be applied.

**symptom_patch_loop**
Each run I ran witness metrics, saw violations, and considered prompt or scoring
changes rather than tracing the cast assembly path first. Two full runs elapsed
before I looked at where cast was built versus where it was validated.

---

## What Worked

**trace_the_causal_chain**
Once I looked at `invoke_turn` line-by-line the defect was immediate: `roster =
[all reviewed]`, then `cast = [from roster]`, then `_enforce_lifecycle_gate(cast)`.
The gate was the last step, not the first. Three lines of code fixed it.

**gate_as_backstop_not_primary_enforcement**
Keeping the lifecycle gate *after* the filter is the right design: the filter
removes known violations at source, the gate catches anything the filter missed
(misconfigured seam, migration gap, logic drift). Defense-in-depth. The filter
reduces frequency; the gate retains correctness.

**witness_as_verdict_not_guide**
The witness metrics (pass/fail) correctly reported the state but didn't point to
cause. I had to *read the log* for the violation messages and *read the code* for
the cast assembly order. The witness is a binary verdict. Analysis requires going
upstream.

---

## Heuristic

**Detect at gate; admit at boundary.**
A gate that fires repeatedly is evidence that admission policy is missing upstream.
Detection gates are not admission filters. When a gate fires on every chapter open,
the question is not "how do I make the gate quieter" but "why are violating
candidates reaching the gate at all?"

---

## Seed

If the LLM generates a seam packet that erroneously sets `to_state: alive` for a
character who should be `missing_presumed_dead` (as happened in chapters 3 and 5
of the 10012 run), the cast filter will still exclude the character at chapter
open — but the incorrect state will persist in chapter_memory and live_synopsis.
Later chapters may then inherit wrong world state even if the cast filter protects
the turn.

**Forward question:** Does the chapter_memory's `character_state_deltas` need
semantic validation against the previous committed seam state before persistence,
not just shape normalization? Would an overturn rule that rejects `alive` transitions
for characters who have no `allowed_reappearance_from_chapter` at close time,
similar to what the cast filter now does at open time, close the remaining
state-drift loop at the source?
