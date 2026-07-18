# 2026-07-18 — The enforcement where the tool judged its own judge

**Context:** the three-FR enforce arc (746 → 745 → 747), all judged by
a parallel session while this one drafted them. FR-746 was a template
slot (Ideal Result above Proposed Solution). FR-745 built the triage
graph the questioner arc designed. FR-747 gave the two FR-744 boundary
errors their actionable messages. Mechanically boring — the judgements
were good, so enforcement was boring (`boring_enforcement` held three
for three). The interesting events were all at the seams.

**Trap encountered: the tool's invariant blocked its own acceptance
test.** AC-02 required a raw triage read on a live Proposed FR — but
by the time the graph ran, the parallel Judge session had judged every
candidate, and `append_triage`'s Proposed-only guard (written hours
earlier, in code, at the boundary) refused its own smoke test twice.
First reflex was to find another Proposed FR; the correct move was
cheaper: run against a *copy* at Proposed status. The guard was never
the obstacle — it was the first field evidence the guard works. Both
invariants (Azure-404 run appended nothing; Judged-status run refused)
fired correctly before any successful append. A tool whose first
production act is to refuse two invalid requests has passed a test no
fixture provides.

**The recursion that pays for the FR:** the triage run on FR-747's
text found a real spec/judgement drift — Proposed Solution §1 still
said "raise at LOAD time" while F1 had re-pinned the raise to lazy
`load_prompt`. One haiku call, ~$0.006, caught the exact
`intent_drift` class the Scripture warns about, in the very FR being
enforced next. The calibration ledger opens 1-for-8 (one judge-grade
claim, seven confirmatory restatements) — which is a sane base rate
for a checklist instrument, and the kill criterion (F2: <3
outcome-changing claims by the 10th judged FR removes gate + hook)
now has its first data point on the survival side.

**Parallel-session economics, resolved by decree:** the shared index
carried a foreign staged FR (748) at commit time. Doctrine says
staged-check + explicit file lists; the human said "no git dance."
The reconciliation was one `git reset -- <file>` — the minimal
gesture that honors `one_session_one_repo` without ceremony. The
ritual's value is the *check*, not the choreography; when the check
finds one foreign file, the cure is one command, not a stash cycle.

**Distilled:** `guard_refusing_its_author_is_green` — when a
boundary invariant you just wrote blocks your own acceptance path,
that is the acceptance path. Record the refusal as the witness and
route around it with a copy/fixture; weakening the guard to let the
test through inverts the proof. (First strike; watch for recurrence
before graduation.)

**Seed:** the triage graph's first field catch was against an FR
already judged — the drift it found lived between judgement and
enforcement, not before judgement. Is the higher-value firing moment
actually *enforcement-start* (attack the frozen scope + record
against the code about to be written), with judgement-start kept only
for the canon pass? The 10-FR calibration review can answer this from
the ledger: count where each outcome-changing claim would have fired.
