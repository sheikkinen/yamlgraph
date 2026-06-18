# 2026-06-18 — The critic that diffed what a reader forgives

FR-532 was the only feature request in the continuity arc whose deliverable was a
*conclusion*, not code — and its conclusion killed the next feature request in the
queue. The continuity program had spent a season on an "upstream march," and the map
(`continuity-issues.md` §4) ended with a confident arrow: *the next boundary to normalize
is positional/prop micro-state.* FR-529 was already written to build that lane. FR-532
asked one question before the build — *is the pain real?* — and the answer was no.

## The trap: trusting a number that had never met a human

The whole program was steered by the reviewer's continuity score. `10025-BC` scored 4/5
overall but **1/5 on continuity**, and that 1/5 had authority precisely because it was
specific: twelve numbered breaks, each quoting both sides of a contradiction. Specificity
reads as correctness. But the critic is a *small model* handed exactly two adjacent
chapters and told to report every fact that differs — a forensic differ, not a reader. A
differ flags that the food pouch changed hands and that the rope re-knotted; a reader
never tracked the pouch in the first place.

I classified 33 breaks across four books as a large-model human-proxy (the requester's
key insight: a *smaller*-model critic judged against a *larger* reference is calibration,
not the circular LLM-vs-LLM the FR's own J2 honesty flag had feared). **20 of 33 (61%)
were micro-state a reader glides past.** And the 13 that were reader-real shared a
property the build plan had missed entirely: every one was lifecycle (a dead man still
fighting, a drowned man reappearing), relationship (a bond that resets at the seam), or
plot (a resolved conflict restarting, a man thrown off a cliff who is simply gone next
chapter). **Not one reader-real break was positional.** FR-529's seam pin — the
"highest-leverage" next build — would have fixed zero of them.

Heuristic: **a metric that has never been calibrated against its target measures its own
sensitivity, not the thing it names.** Before building to satisfy a score, label a sample
by hand and ask what fraction of the score is the instrument's artifact. The cheapest way
to lose a week is to optimize a number nobody validated.

## The quieter finding: the formula was saturated

The score is `max(1, 5 - break_count)`. With the corpus averaging ten-plus breaks per
book, *every* book floored at 1/5 — the metric had no dynamic range left; it was a
constant wearing a scale. Recomputing it over only the reader-real breaks didn't just
lower the count, it *de-saturated* the score: a flat 1/5 wall spread to 4/3/2/1, and
`10024-BC` (seven reader-real breaks — Arnulf dead, alive, vanished, plus an erased
cliff-fall) emerged as the genuine worst, which the saturated metric could never have
told you. A blunt aggregation can hide a real signal as effectively as a wrong one.

## What the calibration vindicated

The march was right about the destination and wrong about the next step. The reader-real
residual lives exactly in the lanes the program already hardened — FR-507 (lifecycle and
bond), FR-526 (confirmed-dead), FR-528 (the no-progress tail that *is* a plot
contradiction in disguise). The physical lane was never the frontier; it was the
instrument's blind spot pointed back at us. So FR-532 did the most useful thing an FR can
do: it removed FR-529 from existence (*if it is not required, it shall not exist*) and
recalibrated the critic that had misdirected the whole queue.

**Seed:** the recalibrated critic is itself now an un-validated instrument — I changed its
prompt and trusted a *deterministic* before/after, never re-running it live. The next time
the corpus regenerates, the recalibrated `continuity` axis should be re-sampled against a
fresh human-proxy pass: did narrowing the prompt actually suppress the micro-state breaks,
or did it also silence some reader-real ones? A calibration that is never re-checked
decays into the same unexamined authority it was built to correct. Who calibrates the
recalibrated?
