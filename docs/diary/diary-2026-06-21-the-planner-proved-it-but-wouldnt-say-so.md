# The Planner Proved It But Wouldn't Say So

*2026-06-21 — FR-559, DM v3 M0 floodmark plot-model spike*

## What happened

FR-559 was judged before I returned: APPROVE WITH CONDITIONS, and J1 was the blocking one. The
whole epistemic value of the spike is a *proven negative* — "Arnulf onstage at Ch3 is unspellable"
— and the Judge pinned the assertion to `result.status == UNSOLVABLE_PROVEN`, with
`TIMEOUT`/`MEMOUT`/no-engine excluded, precisely because a bare `not solvable` bool would let a
1-second timeout pass for the wrong reason. The `plausible_wrong_answer` trap, named in advance.

Then the toolchain refused to cooperate. I installed `unified-planning` plus every pip engine —
`fast-downward`, `fast-downward-opt`, `symk`, `symk-opt`, `aries` — and *none* of them returned
`UNSOLVABLE_PROVEN`. On a genuinely, finitely unsolvable problem, Fast Downward's own log says
`Completely explored state space -- no solution!` — a complete proof — and then exits **12**
(`SEARCH_UNSOLVED_INCOMPLETE`), never 11 (`SEARCH_UNSOLVABLE`) or 10 (`TRANSLATE_UNSOLVABLE`). I
verified it wasn't a wrapper artifact by invoking the bundled FD directly on a hand-written
unsolvable PDDL: same exit 12. symk did the same. aries simply *hung* — it iterates makespan
unboundedly on untimed classical problems and never proves unsolvability without a horizon.

So the literal J1 condition was empirically unsatisfiable. The enum the Judge named is, in
practice, never produced by the engines we have.

## The trap

**`instruction_boundary_uncrossed` meets a tempting silent reinterpretation.** The fast path was
obvious and wrong: just accept `UNSOLVABLE_INCOMPLETELY` as "the negative" and move on. But that
re-opens the exact conflation the Judge blocked — a timeout *also* yields a non-positive,
non-proven status. Quietly widening a blocking judged condition to make my own work pass is the
`quick_confidence` trap dressed as pragmatism. The condition was blocking *because* this is the
deliverable; reinterpreting it unilaterally is precisely the move the doctrine forbids ("When I
feel certain, let that be the sign to Judge").

The other trap was subtler: treating the engine as a trusted oracle. `UNSOLVABLE_INCOMPLETELY` is
the wrapper's *conservative* label — it means "I did not prove completeness," which is true for a
heuristic search but a *lie* for blind A* that exhausted a finite state space in milliseconds. The
enum is a boundary mistranslation, not an actual incompleteness.

## The cure

I stopped and escalated — presented the evidence and a recommended amendment, and got an explicit
decision before writing spike code. The amendment preserves J1's *intent* while correcting the
enum it names: for a **complete** engine+config (`fast-downward` `astar(blind())`) on a **finite**
problem, the proven-negative predicate is `status in (UNSOLVABLE_PROVEN, UNSOLVABLE_INCOMPLETELY)`;
`TIMEOUT`/`MEMOUT`/`INTERNAL_ERROR` remain a *distinct* set that fails the test (exhaustion never
produces them), and no-engine still skips. The proof-vs-give-up distinction the Judge guarded is
fully intact; only the enum value moved. The completeness of the search is what carries the proof,
not the label the wrapper chose to print.

The boundary here was **schema/provider**: an external library's status enum is a type lie the
same way a provider's `content: str vs list` is. Normalize at the boundary — define
`PROVEN_UNSOLVABLE` and `GAVE_UP` sets in `validate.py` where the engine result enters — not
downstream in the test, and certainly not by weakening the assertion.

## Seed

The Judge wrote J1 against a presumed engine capability that turned out not to exist. The condition
was *right in spirit, wrong in mechanism* — and only enforcement-time empiricism surfaced the gap.
Should a judged FR carry an explicit "capability assumptions" section listing the external
behaviours its conditions presume (here: "an installed engine emits `UNSOLVABLE_PROVEN`"), so the
enforcer de-risks those *first* — before the RED test — and an unmet assumption auto-routes back to
the Judge instead of tempting a silent reinterpretation?
