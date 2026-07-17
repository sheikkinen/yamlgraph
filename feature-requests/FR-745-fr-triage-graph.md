# FR-745: FR Triage Graph — the checklist tier, mechanized; the signature, reserved

**Status:** Judged
**Type:** Feature (chaplain graph + FR-lifecycle hook)
**Effort:** 1 day
**Requested:** 2026-07-17
**Judged:** 2026-07-17 — approved with revisions; the hook goes
reminder-only and the whole mechanism gets a binding kill criterion
**First consumer / first event:** the next judgement (interactive or
chaplain) reads triage claims already sitting in the FR; first event =
the next `docs(fr): proposed` commit after enforcement.

## Ideal Result

Every FR arrives at its judgement pre-triaged: the canon has been run
against it, the pre-mortem witnesses are drafted, the value-prop
sentence is checked — all sitting *inside the FR* in the testimony
register, each item awaiting disposition. The judge (model or human)
spends attention exclusively on measurement and taste. No FR reaches
enforce with an undispositioned triage claim.

## Problem

Six for six judgements this week changed designs by measurement — but
each also spent expensive attention on enumerable checks (consumer
named? value-prop completable? which canon questions apply? what
would the pre-mortem say?). The canon (Scripture `questions:` +
`generative_methods:`) made the checklist tier enumerable; nothing
runs it. Meanwhile three post-ship catches (FR-739 phantom witness,
FR-740 F7, FR-744 F5) were pre-mortem-findable at the judge/enforce
boundary. Diary: *the-judge-that-shouldnt-be-a-hook*
(`authority_is_not_a_checklist`).

**Prior art:** FR-737/738 (prior-art hook + disposition gate — the
retrieval-aid-never-verdict pattern AND the disposition obligation
this FR reuses); FR-195 (challenge gate — LLM-as-adversary proven);
the chaplain judge stage (the auto-judgement lane this FR feeds, not
replaces); FR-743 probe (hook-lifecycle seams; UserPromptSubmit
CONFIRMED). Disposition: extends 737's pattern from one question
(prior art) to the canon; no rejected FR occupies triage territory.

## Proposed Solution

1. **`.chaplain/graphs/fr_triage/`** — small-model graph (haiku-class),
   input = the FR text: (a) canon pass — which `questions:` entries
   apply, with one-line answers where derivable from the text;
   (b) pre-mortem — "this FR shipped and failed": 3–5 concrete failure
   witnesses aimed at the ACs; (c) value-prop check — is the
   for-whom/what-pain/vs-what sentence completable from the text?
   Inline schema; zero-yield rules per FR-744 precedent.
2. **Delivery INSIDE the FR** (reception law): append
   `## Triage (generated — claims requiring disposition)`; every line
   is testimony. **Never a verdict** — the graph cannot change Status.
3. **Disposition gate** (FR-738 shape): judgement may not grant
   authority while triage claims are undispositioned (accepted → AC /
   rejected with reason). Pre-commit extension of the existing
   prior-art gate.
4. **Trigger:** PostToolUse FR-creation hook (prior-art hook's seam)
   for drafts; judge may re-run at scope-freeze for the pre-mortem
   against frozen ACs.
5. **Calibration ledger:** each judgement records which triage claims
   it upheld/overturned (one line in the FR) — the dataset for
   shape-scoped auto-judge promotion (diary seed: let the record
   decide).

## Acceptance Criteria

- [ ] AC-01 RED: triage output schema + FR-append format + no-Status-
      change invariant, fixture-pinned.
- [ ] AC-02: real run on one live Proposed FR; raw read recorded here
      (does the pre-mortem find anything a human judge would keep?).
- [ ] AC-03: disposition gate blocks an undispositioned triage section
      at pre-commit (witnessed).
- [ ] AC-04: economics from run output (small-model cost per triage).
- [ ] AC-05: calibration-ledger line format used by the next real
      judgement (witnessed by citation).

## Out of scope (purge list)

- Verdicts, Status changes, authority of any kind.
- Auto-judge promotion (needs the calibration ledger's data first).
- Triage of ninchat FRs (mirror later, NC-394 pattern).

## Questions for the human (as options, or 'none')

None — the pattern is FR-737/738 recombined with the canon; the only
novel risk (ritual triage nobody reads) is answered by the
disposition gate.

## Judgement (2026-07-17)

**Verdict: APPROVED WITH REVISIONS — 4 findings; two proposal
mechanisms corrected against sibling precedent before any code.**
Verified: FR-737/738 both Completed, `prior_art_gate.py` live at
pre-commit, `.chaplain/graphs/` convention exists.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **An LLM call inside a PostToolUse hook contradicts the sibling precedent this FR builds on**: FR-737's own judgement kept hooks fast, offline, and LLM-free — a haiku call adds seconds of latency, an API-key dependency, and an offline failure mode to EVERY FR edit; a hook that silently skips when the key is absent is a silent fallback (Commandment 6) | The hook is REMINDER-ONLY (one non-blocking line: "triage pending — run fr_triage"). The graph runs on demand (author or judge, judgement-start at latest). The delivery deadline is AUTHORITY, not the next keystroke — and the disposition gate already enforces exactly that deadline mechanically. No background-async execution (worktree/env hazards, purged) |
| F2 | **No kill criterion.** The calibration ledger records upheld/overturned but nothing binds it — an unread-but-dispositioned triage section is `audit_as_ritual` with a forced signature; the gate would make the ritual mandatory forever | Binding review after the 10th judged FR carrying triage: unless the ledger shows ≥3 triage claims that changed a judgement outcome (AC kept, scope cut, witness added), gate + hook are REMOVED and this FR is re-closed CONDEMNED-analog (designed-and-disproven). Default is removal; survival must be earned in the ledger |
| F3 | **Small-model output-shape risk is precedented** (FR-596/597: haiku returned a 658-token novel as analysis) | Schema pins: canon-pass answers and pre-mortem witnesses are single lines, hard cap 5 witnesses / 3 canon answers; zero-yield rules per FR-744. ORDERING pin: AC-02's raw read happens BEFORE the gate or hook is armed — run on a live FR, read, THEN wire (read_raw_output_first as an enforcement-sequence constraint, not just an AC) |
| F4 | Disposition-gate scope was underspecified (a draft commit right after creation must not be blocked) | Gate fires only when the FR's Status line transitions to Judged (or later) with an undispositioned `## Triage` section present; drafts and Proposed-status edits pass freely |

**Purge additions:** background/async triage execution, any hook-time
LLM call, triage on FR edits (creation + explicit re-run only).
