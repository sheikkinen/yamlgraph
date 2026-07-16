# 2026-07-16 — Ratio 1.01: the meter metered itself

**Context:** FR-739 enforcement (RED 82ba08a0 → GREEN 7c9dadf6), same
day as its proposal and judgement. Graduating the arc's repo-memory
notes into the record, because three of them are cognitive patterns,
not just facts.

**1. The RED suite killed a forever-silent bug in its first hour.**
The ETA witness (`test_eta_at_three_witnesses`) failed GREEN because
`zip(turns[-4:], turns[-3:])` pairs elements with themselves on short
lists — slope permanently 0, ETA permanently absent. Without that
test the altimeter would have shipped *looking* alive (level and peak
render fine) while its one predictive feature was dead: the
`plausible_wrong_answer` class, caught by a witness written before
the code existed. The judgement's insistence on pinning the ≥3-witness
ETA gate — which felt like ceremony — is what forced a test that
exercised slope at all.

**2. The reconciliation validated its own foundations — and exposed
its own blind spot, in one table.** `ledger.py --tap`'s first run:
neighbor session ratio **1.01** — the rounds× estimator, built on
anchor-2's *inference*, confirmed within 1% by wire truth on a
complete session. Same table, own session: **0.27** — because
chatSessions lags the turn that is executing the reconciliation.
The store you read lags the life you are living; an instrument
measuring its own session always undercounts the present. Not a bug —
a property of self-measurement worth naming, because the next reader
of that table will otherwise file a defect.

**3. Memory correction: my own note was a probe artifact.** The
repo-memory note confidently recorded "attributes in KeyValue-LIST
form" — written from the probe run whose *other* bug the two-rulers
diary documents. Truth (read from a raw record during enforcement):
plain dict. The wrong fact survived one compaction and nearly shaped
the fixture design. Corollary to the newer-ruler rule: **a memory
note inherits the defects of the probe that wrote it** — notes born
during an instrument malfunction deserve re-verification before
reuse. The note is now corrected in place, per doctrine.

**4. The AC-02 proof was necessarily self-referential.** Rung-2
receipt could only be witnessed by the receiving agent — `now.py
--tap` printed the authoring session's own post-compaction level
(158K) into the authoring agent's tool result. The instrument's
delivery was proven by the instrument's author *being delivered to*.
Emission≠reception closes only when the receiver testifies; for
agent-facing tooling, the enforcement transcript is the testimony.

**5. A guard false-positive, answered correctly.** The pre-command
guard denied a commit because `SKIP=pytest` and `| head` co-occurred
in one command line (grep output, not pytest). The correct move was
executed without deliberation — rephrase, never bypass
(`automation_inherits_doctrine`) — but the pattern is worth a tally:
if the guard's co-occurrence heuristic fires twice more on innocent
lines, its pattern needs a boundary fix, not tolerance
(`two_strike_split` applies to guards too).

**Seed:** the altimeter now records every witnessed compaction; at
three witnesses the ETA unlocks. When it does, the first *predicted*
compaction becomes testable: flush session memory on the warning,
then diff what the summary lost against what the flush saved — the
protective loop closed end-to-end. That experiment is the real
deliverable the suite was built toward.
