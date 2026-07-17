# FR-745: FR Triage Graph — the checklist tier, mechanized; the signature, reserved

**Status:** Proposed
**Type:** Feature (chaplain graph + FR-lifecycle hook)
**Effort:** 1 day
**Requested:** 2026-07-17
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
