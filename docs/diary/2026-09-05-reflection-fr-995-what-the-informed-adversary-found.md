# What the Informed Adversary Found That the Ignorant One Could Not

**Date:** 2026-09-05
**FR:** FR-995 — review round (`scripts/review.sh 592`)
**Trigger:** operator: "review, reflect, commit reflections, merge."

## The result

Six blocking findings on a PR that had just passed the outsider, the author's
own re-read, 29 green tests, lint, requirement coverage and the CI policy
checks. Every finding was real:

1. The cleanup trap was installed before the lock was acquired. A losing
   invocation exited through the trap and **deleted the winner's lock**. The
   reviewer proved it with a contention probe; my "lock" test had asserted
   the trap line existed.
2. The ledger row was written before the optional comment; a failed comment
   left a measurement behind. The judge had written R-3 precisely to prevent
   rows from unvalidated runs; I had read it and still ordered the steps
   wrong.
3. The parser accepted an opinion with no reason, an item with no question,
   an empty checklist line, and matched headings as prefixes. Each is a
   fail-closed rule I had written into the FR myself, in R-2's words.
4. The fetched PR text was written under the repo and never removed.
5. The doctrine was 61 lines against a 60-line criterion my own PR body
   claimed to meet.
6. AC-09 was recorded as "not done, by scope" while the judgement froze it
   as required; the implementation record said the ledger was empty while
   the head contained a row.

## Why my tests missed all six

Every wrapper test I wrote asserted **the text of the script** — that a line
existed, that one line came before another. The reviewer's probes asserted
**behaviour** — run it with a lock present, run it with a failing comment,
feed the parser an empty reason. `gate_checks_shape_not_substance`, turned on
my own tests: a test that greps the source for `trap cleanup` is a test that
the author typed the words. Replaced with fakes on PATH (`yamlgraph`, `gh`)
and a redirected ledger; 36 behavioural tests now, ten of them exercising
failure paths the source-text tests could not reach.

The order-of-operations bugs (1, 2) are `intent_drift` at its plainest: the
FR said one thing, the script did another, and I read the script as if it
said what the FR did. The reviewer read the script as a stranger to my
intent — which is the informed adversary's version of the outsider's trick.

## The two adversaries, observed on one PR

| | outsider (06:44Z) | reviewer (09:55Z) |
|---|---|---|
| given | title + body | head, diff, FR, judgement, files, tests |
| found | six phrases only an insider could follow; the FR's "dogfood comment below" pointing at nothing | a lock deletion, a ledger ordering bug, three parser holes, a temp-file leak, a line count, a status contradiction |
| could not have found | any of the reviewer's six | any of the outsider's six |
| overlap | none | none |

Same PR, same hour, zero overlap. That is the pattern the morning's diary
predicted and this afternoon measured. Neither reader is the other's
substitute; both are cheaper than the human who would otherwise be the only
adversary.

## Heuristics

`assert_behaviour_not_source`: a test that reads the script's text proves
the author typed it. Run the script with the failure induced — a lock
present, a subprocess that exits 1, a malformed input — and assert what it
did. Fakes on PATH cost twenty lines and reach every branch.

`the_informed_adversary_reads_as_a_stranger_to_intent`: the reviewer's
value is not knowing more than the author; it is reading the code without
the author's belief about what it does. Order-of-operations bugs are
invisible to the person who knows the intended order.

## Seed

**Seed:** The outsider and the reviewer found disjoint sets. The judge, an
hour earlier, found a fourth set (the calibration contradiction, the untyped
boundary, the unattributable ledger). Three adversaries, three disjoint
yields, one PR. Is there a fourth position on some other axis — time, maybe:
a reader who sees only the diff between this PR and the one that will
supersede it in a month — or is the space of cheap adversaries now covered
for this repo?
