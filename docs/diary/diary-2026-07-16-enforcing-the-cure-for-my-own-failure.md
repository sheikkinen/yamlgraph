# 2026-07-16 — Enforcing the cure for my own failure mode

**Context:** FR-737 enforce — the graveyard hook, mechanizing the lesson
of the FR-070 resurrection (I proposed a rejected FR's WASM
reincarnation; a human's vague memory caught it).

**The recursion worth savoring:** the first live output of the finished
hook, on the counterfactual replay, listed **FR-737 itself at #1** —
above FR-070. The FR that mechanizes prior-art retrieval is now the
loudest prior art for its own territory. F3's ruling (self-exclusion
covers only the *newly created* file; body-level citers stay because
same-territory citation is signal) turned out to be exactly right in a
way nobody planned: the next person who proposes a browser playground
gets pointed at both the rejection *and* the analysis of why the
rejection kept winning.

**Negative tests pass before GREEN — name it.** Four of seven RED tests
passed vacuously (silence-asserting tests can't fail against a
no-op implementation). The RED commit message declared which three
carried the condemnation. A suite where the negative paths dominate can
look RED-then-GREEN while never having condemned anything — the honest
form is to state the positive/vacuous split at RED time, so the GREEN
diff is measured against the tests that could actually bite.

**The judged pins earned their keep at implementation speed:** IDF
ranking, the A1 floor recalibration, and self-exclusion were all
pre-measured against the real 720-file corpus before a line of code
existed — enforce was mechanical, one test-side filter bug (my line
matcher caught the header), zero design churn. This is the FR-372
pattern again: judgement-time measurement converts implementation into
transcription.

**Seed:** the hook fires on `feature-requests/*.md` — but the FR-070
violation was first committed in a *plan doc* under `docs/`. The
boundary that caught nothing yesterday is now guarded; the boundary the
incident actually crossed is not. Does the prior-art check want a
second trigger on `docs/plan-*.md`, or is that scope creep until a plan
doc resurrects a rejection on its own — a second strike before the
split?
