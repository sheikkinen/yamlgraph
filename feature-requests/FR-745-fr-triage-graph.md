# FR-745: FR Triage Graph — the checklist tier, mechanized; the signature, reserved

**Status:** Completed
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

- [x] AC-01 RED: triage output schema + FR-append format + no-Status-
      change invariant, fixture-pinned.
- [x] AC-02: real run on one live Proposed FR; raw read recorded here
      (does the pre-mortem find anything a human judge would keep?).
- [x] AC-03: disposition gate blocks an undispositioned triage section
      at pre-commit (witnessed).
- [x] AC-04: economics from run output (small-model cost per triage).
- [x] AC-05: calibration-ledger line format used by the next real
      judgement (witnessed by citation — pending the next judgement).

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

## Enforcement Record (2026-07-18)

**Delivered** (F3 ordering honored: raw read BEFORE gate/hook armed):

- `.chaplain/graphs/fr_triage/` — `tools.py` (read_fr, append_triage,
  gate_check), `graph.yaml` (read→triage→append; haiku pinned via
  `defaults: {provider: anthropic, model: claude-haiku-4-5}`),
  `prompts/triage_fr.yaml` (inline schema: `canon_answers` ≤3,
  `pre_mortem_witnesses` ≤5, `value_prop_check`; single-line pins).
  Caps enforced in CODE at the append boundary, not just the prompt
  (two_strike_split applied preemptively). Empty triage raises
  (zero-yield, FR-744 precedent). `append_triage` refuses non-Proposed
  FRs, Status-line changes, and double-append.
- 5 unit witnesses: [tests/unit/test_fr_triage.py](../tests/unit/test_fr_triage.py)
  (REQ-YG-564, CAP-206).
- Gate: [.github/hooks/scripts/checks/triage_gate.py](../.github/hooks/scripts/checks/triage_gate.py)
  wired as `triage-gate` in `.pre-commit-config.yaml`; reads STAGED
  blobs only (FR-738 F2 discipline). Hook: one reminder-only line in
  `fr-checks.sh` on FR creation — no LLM, no latency (F1).

**AC-02 raw read** (2026-07-18, target: FR-747 text at Proposed
status): the pre-mortem found a claim a judge would keep — it caught
that FR-747's Proposed Solution §1 still says "raise at LOAD time"
while the judgement's F1 re-pinned the raise to lazy `load_prompt` at
node execution: a real spec/judgement drift, exactly the intent_drift
class. Two further witnesses (hint flooding on legitimate import
errors; `messages` false-positive on non-role-list usage) restate F2/F3
mitigations — confirmatory, not novel. Canon answers were accurate and
grounded (cited FR-744 incidents, skills patch 2e8b6293). No novel
output, no verdict language, caps held. Verdict: the checklist tier is
real; 1 of 8 claims is judge-grade, which is the expected base rate for
a triage instrument. Field bonus: both `append_triage` invariants fired
correctly before any successful append (Azure-404 misconfig run
appended nothing; Judged-status run refused — Proposed-only held).

**AC-03 witness**: staged a Judged-status FR carrying `- [pending]`
claims → gate exited 1 with the disposition message; unstaged edits do
not count (blob read from index). Proposed drafts and Triage-free FRs
pass (unit witnesses).

**AC-04 economics**: one triage run = single haiku call, ~9s wall
(08:22:37→08:22:46), input ≈ FR text (~6 KB ≈ 2.5K tokens) + prompt,
output ≈ 700 tokens → ≈ $0.006/triage at haiku pricing ($1/$5 per M).
Negligible against the judgement attention it pre-spends.

**AC-05 calibration-ledger format** (to be written by each judgement
that consumes a triage section, one line under its verdict):
`**Triage calibration:** upheld N / overturned M / deferred K — <what changed, if anything>`
First real citation: FR-747's enforcement record (upheld 1/8 — the
"raise at LOAD time" drift; §1 and AC-02 reworded before enforcement).
The F2 kill-criterion review counts these lines (review at 10th judged
FR; <3 outcome-changing claims → gate + hook REMOVED, FR re-closed
designed-and-disproven).
