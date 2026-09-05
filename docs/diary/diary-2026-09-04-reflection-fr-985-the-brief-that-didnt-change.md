# The brief that didn't change

**Date:** 2026-09-04
**FR:** FR-985 (shelved), closing the census arc of FR-983 → FR-984 → FR-985.

## What happened

After FR-984 landed, the operator ran the corp person-profile census
three times in an hour, narrowing the fan-out each time: 12 lanes, 4, 2.
Coverage went 57% → 85% → 92%. Rate-limit responses went 1249 → 727 →
349. And the brief — the hundred-line profile a human reads — said the
same thing all three times. Same themes, same surface concentration,
same cadence, same "kind of engineer."

I had spent the afternoon building the case that a brief over 57% of the
population was a `plausible_wrong_answer`: fluent, structurally valid,
semantically false. The operator read three of them side by side and
said: *on summary level it's not a wrong answer — it's diminishing
returns.* They were right. The ledger's coverage number was a true fact
about the ledger. It was not a true fact about the brief.

FR-985 was shelved on that evidence. Its fail-closed floor, default
`1.0`, would have refused all three runs to protect a summary that had
already proved it didn't need protecting.

## The deployment finding

The operator's summary: `gpt-5.4-mini` in `swedencentral` does not
provide the capability this census requires. Not the model's judgement
— the classifications were fine — but the quota. At two concurrent
lanes the 429 rate still ran flat at ~90/min for the whole run; at four,
~200/min. That is a per-minute ceiling, not a burst, and no retry ladder
turns a ceiling into headroom. FR-984 gave the operator the knob to stay
under it; the knob cannot raise it. The graph's `max_concurrency: 4`
should become `2` for this consumer, and a census of 268 rows at two
lanes takes seven minutes. That is the cost of this deployment, now
measured rather than suffered.

The runs also surfaced a second failure class the 429s had been hiding:
sixteen or seventeen rows per run marked `problem_class 'docs' not in
vocabulary`. The model, asked to classify documentation PRs against a
`problem_labels` list with no documentation entry, answered with a
`change_kind` value instead. The FR-940 canonicalisation gate refused
it. That is the guard working; the defect is in the invocation — add
`"docs"` to `problem_labels`. Three runs of 429 noise had to clear
before a twenty-row signal became legible. `read_raw_output_first`, once
more.

## Traps

**`ledger_truth_as_brief_truth`.** I measured a defect in the ledger
(coverage 56.8%) and asserted it as a defect in the brief. The brief is
a lossy summary; a lossy summary of 57% of a corpus and of 92% of it can
be the same summary, and today it was. Whether a coverage gap matters
depends on what the downstream artifact *is*. A histogram of
`change_kind` over 147 vs 246 rows differs; a paragraph saying
"tooling-heavy engineer" does not. I had the histogram's sensitivity in
mind and the paragraph's in hand. Cure: before calling a downstream
artifact wrong, produce two of them from different inputs and diff. The
operator did this in an hour; I had theorised for three.

**`guardrail_default_before_witness`.** FR-985's `min_coverage = 1.0`
default was written, judged, and folded before anyone had seen what a
partial-coverage brief actually looked like next to a full one. The
judge accepted it because it matched Commandment 6's letter. It matched
the letter and missed the case: Commandment 6 forbids substituting the
survivors *when the substitution changes the answer*. Three runs showed
it didn't. Cure: a fail-closed default needs one witnessed case where
failing open produced a materially different result. If the case
cannot be shown, the default is disclosure, not refusal.

**`arc_momentum`.** FR-983 → SPLIT → FR-984 enforced → FR-985 judged and
folded, in one day, with every gate green. By 15:00 the arc had its own
gravity: FR-985 was "next" because the sequence said so, not because
the evidence still did. The operator's three runs were the first
evidence-gathering step in five hours that was not about the process
itself. The Scripture names `growth_as_default`; this is its temporal
form — the next step exists because the last one did.

## What went right

- Shelving cost nothing but the afternoon's judgement. Nothing was
  enforced under FR-985; no code to unwind. The plan-judge-enforce
  sequence held the decision point exactly where it should be: after
  judgement, before enforcement, with authority granted but unspent.
- The judgement's revisions were good and remain on file: the truthful
  `{selected} of {judged} … (cap N)` header, the local containment
  witness, the non-gating observation. If the demo is reopened, the
  starting point is one afternoon further along than it was.
- FR-984 did what it claimed and no more: 1249 → 349 429s by turning one
  knob three times. The observation is recorded on the FR with the
  numbers, including the one it does not fix.

## Heuristics

- `diff_two_artifacts_before_calling_one_wrong`: a downstream summary is
  only "wrong" if a summary from better input differs. Produce both.
- `fail_closed_needs_a_witnessed_divergence`: a refusing default earns
  its place only with one recorded case where not refusing changed the
  answer; otherwise disclose and proceed.
- `next_because_last`: when the next FR exists because the previous one
  did, stop and run the thing once before judging it.

**Seed:** The census framework already computes coverage and already
writes a brief. Could it compute the brief *twice* — once from all judged
rows, once from a random half — and report the divergence as a
sensitivity number beside the coverage? A brief that survives a 50%
ablation unchanged is one whose coverage gap the reader can ignore; one
that flips is one where the floor should have fired. That number, not a
default, would have settled FR-985 in one run.
