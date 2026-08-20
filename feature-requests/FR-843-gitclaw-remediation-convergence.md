# Feature Request: FR-843 GitClaw Remediation Convergence

**Priority:** HIGH
**Type:** Platform / GitClaw pipeline semantics
**Status:** Enforced 2026-08-20 - canonical `a983bf1`, smoke parity `ada0c83`;
live witness issue #2 published `yle-news-haiku-digest` at `dc71bde` with
first-pass exact APPROVED and all four stages on `claude-sonnet-5`
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-840
**Depends on:** FR-829, FR-830, FR-840, FR-842
**Blocks:** Reliable unattended intake for any consumer, including the FR-841
restart and the Oulu fresh start
**Prior art:** FR-840 (canonical `a7621f21` + flat-condition hotfix `846ddfe`)
made authority artifacts immutable and routed review `APPROVED WITH REVISIONS`
to the remediation lap. The first live smoke (`sheikkinen/gitclaw-yle-haiku`
issue #1, run `32362016430`) proved the authority contract end to end — plan
quoted `request.json` with a traceability table, enforcement twice refused to
edit `FR.md`, revisions never published — and exposed two convergence defects
documented below. FR-842 fixed the lint/compile parity gap found by the same
smoke. The README already promises "one remediation lap, then final reject";
current routing does not deliver it.
**First consumer / first event:** The next owner issue in any GitClaw
repository, when a parseable `REJECTED` or `APPROVED WITH REVISIONS` review
verdict must end in a visible terminal state instead of a silent loop-limit
stop. Unknown/unparseable verdicts remain the existing separate fail-closed
surface (bare `END`), outside this FR (R-2).

## Ideal Result

After exactly one remediation lap, every parseable non-approved review verdict
produces a posted review comment and a closed issue via `reject_final`, while
judgement revisions remain enforceable without rewriting frozen authority
artifacts — no parseable verdict/loop-count combination can end at a bare
loop-limit stop, and exact `APPROVED` remains the only publication path (R-4).

## Evidence and Root Cause

Smoke ledger and run log (`32362016430`, 35 minutes):

```
seen → planned → judged_approved (WITH REVISIONS)
     → enforced → review: APPROVED WITH REVISIONS
     → reviewed_rejected → enforced (lap 1)
     → review: APPROVED WITH REVISIONS
     → [ledger_reviewed_rejected loop limit 1 blocked]
     → [read_review_verdict loop limit 2] → silent END
```

Result: run concluded "success", issue #1 open, ledger non-terminal at
`enforced`, no review comment posted, and the reviewed 16/16-test generated
feature discarded with the ephemeral runner. Re-triggering now exits 65
(interrupted, human recovery).

**F-1 — Revision deadlock (prompt defect).** The judge issued a revision whose
satisfaction requires editing `FR.md` prose, and review then flagged
"`FR.md` still contains pre-revision text" as its sole blocking finding, lap
after lap. Under FR-840 nobody may edit `FR.md`, so this class of finding can
never converge. The prompts never state the corollary of immutability: the
judgement's recorded revisions are the controlling contract *layered over*
frozen `FR.md` prose, and unfolded prose is expected, not a defect.

**F-2 — Silent exhaustion (routing defect).** Remediation edges allow a second
lap while `_loop_counts.enforce < 2`, but `ledger_reviewed_rejected` has loop
limit 1, so the second non-`APPROVED` verdict can neither remediate nor reach
`reject_final` (guarded by `enforce >= 2`); the graph stops at a loop-limit
warning. The README-promised terminal handling (`reject_final`: post review,
record `reviewed_rejected_final`, close issue) is unreachable in exactly the
case it exists for.

**F-3 — Verdict-behavior nondeterminism (observed, owner question).** All four
model stages ran with `model=None` (Copilot CLI default). Verdict strictness —
the behavior F-1/F-2 depend on — silently tracks whatever the CLI default is
that day. `cli_flags.model` is already supported (FR-266 prior art).

## Decision

1. **Convergence contract (F-1):**
   - `prompts/judge.yaml`: a revision must be implementable without editing
     `request.json`, `FR.md`, or `judgement.md`. A finding that would require
     rewriting FR prose is grounds for `REJECTED`, never a revision.
   - `prompts/review.yaml`: evaluate the implementation against `request.json`
     plus `FR.md` *as amended by* the judgement's recorded revisions. Frozen
     pre-revision `FR.md` prose is expected under the immutability rule and
     must not be reported as a defect or blocking finding.
2. **One lap, then visible terminal (F-2):** remediation is entered only from
   the first review (`_loop_counts.enforce == null`); any later
   non-`APPROVED` verdict routes to `reject_final`, which posts `review.md`
   to the issue, records `reviewed_rejected` + `reviewed_rejected_final`, and
   closes the issue. All conditions stay flat (FR-842 grammar). Losing the
   unpublished implementation on final rejection remains by design
   (fail-closed); no quarantine ref is added.
3. **Model pin (F-3, frozen):** pin `claude-sonnet-5` on all four copilot
   nodes via `cli_flags.model`, one identical value. The identifier was
   verified against the installed Copilot CLI on 2026-08-20: a probe run with
   `--model claude-sonnet-5` executed successfully, and a negative probe with
   an invented identifier was rejected with `Model ... is not available`,
   proving real validation (R-3). Adopters change one value per node; the
   README documents the pin and the portability trade-off.

## Exact Canonical Change Surface

1. `gitclaw.yaml` (routing conditions, loop limits, four `cli_flags.model`
   entries);
2. `prompts/judge.yaml`;
3. `prompts/review.yaml`;
4. `tests/test_intake_tools.py` (routing evaluator + model-pin assertions);
5. `tests/test_generated_feature_policy.py` (prompt convergence markers);
6. `README.md` (pipeline diagram note + model pin).

No workflow, tools, policy-file, ledger-implementation, cron, containment, or
dependency change. Ledger legality of `enforced -> reviewed_rejected ->
reviewed_rejected_final` is already proven by existing reject paths and tests.

## Frozen Routing

From `read_review_verdict` (flat conditions only; `_loop_counts.enforce` is
`null` before any remediation lap and `1` after the single allowed lap, per
the live smoke evidence and the existing evaluator contract) (R-1):

- `review_verdict == 'APPROVED'` -> `ledger_reviewed_approved` (unchanged);
- `review_verdict == 'REJECTED' and _loop_counts.enforce == null` ->
  `ledger_reviewed_rejected` -> `enforce`;
- `review_verdict == 'APPROVED WITH REVISIONS' and _loop_counts.enforce == null`
  -> `ledger_reviewed_rejected` -> `enforce`;
- `review_verdict == 'REJECTED' and _loop_counts.enforce >= 1` ->
  `reject_final`;
- `review_verdict == 'APPROVED WITH REVISIONS' and _loop_counts.enforce >= 1`
  -> `reject_final`;
- unknown verdicts -> `END` (unchanged fail-closed; explicitly outside this
  FR's visible-terminal promise per R-2).

Loop limits stay consistent with exactly one remediation lap; the
`_review_targets` evaluator test must prove (R-1):

- both non-approved verdicts at `_loop_counts.enforce == null` route only to
  `ledger_reviewed_rejected`;
- both non-approved verdicts at `_loop_counts.enforce >= 1` (evaluated at 1
  and at a defensive 2) route only to `reject_final`;
- `APPROVED` routes only to `ledger_reviewed_approved`;
- unknown verdicts route only to `END`; and
- no verdict/loop-count combination can reach `ledger_reviewed_rejected`
  after the one allowed remediation lap.

## Validation

- Red: current graph routes `(REVISIONS, enforce==1)` to
  `ledger_reviewed_rejected` (blocked) and never `reject_final`; prompt files
  lack the convergence clauses; nodes carry no model.
- Green: evaluator matrix per the Frozen Routing section (both non-approved
  verdicts × `enforce` in `null`/`1`/`2`, plus `APPROVED` and unknown) proves
  remediation exactly once, then `reject_final`; scratch-dir compile
  (`yamlgraph graph run`, FR-842 method) passes; prompt marker tests for the
  judge implementability clause and the review frozen-prose clause; model-pin
  test asserts all four copilot nodes carry exactly `claude-sonnet-5`;
  full canonical suite green.
- Live witness: after canonical push, propagate to
  `sheikkinen/gitclaw-yle-haiku`, file one fresh owner issue (same Yle-haiku
  contract), and require a terminal outcome: either published feature with
  closed issue, or `reject_final` with posted review and closed issue — no
  silent END. Interrupted issue #1 stays untouched as evidence.

## Human Gates

1. Human approves the FR-843 judgement before implementation.
2. Human reviews the exact canonical diff and red/green evidence before push.
3. Human approves filing the fresh smoke issue (spend/side-effect gate).

## Acceptance Criteria

- [x] AC-01: Red evidence captures the unreachable `reject_final`, missing
      prompt clauses, and unpinned models on the current baseline
- [x] AC-02: Judge prompt forbids revisions that require editing authority
      artifacts; such needs are `REJECTED`
- [x] AC-03: Review prompt treats judgement revisions as controlling over
      frozen `FR.md` prose and never blocks on unfolded prose
- [x] AC-04: Routing gives exactly one remediation lap; both parseable
      non-approved verdicts at `enforce == null` reach only
      `ledger_reviewed_rejected`, at `enforce >= 1` (evaluated at 1 and 2)
      only `reject_final`; unknown verdicts only `END`
- [x] AC-05: `reject_final` posts the review, records the terminal ledger
      states, and closes the issue; no parseable verdict/loop-count
      combination ends at a bare loop-limit stop
- [x] AC-06: All conditions remain flat and the graph passes real compile
      (scratch-dir run) and lint (now parity-checked per FR-842)
- [x] AC-07: All four copilot nodes pin exactly `claude-sonnet-5` via
      `cli_flags.model`, and README documents the pin and portability
      trade-off
- [x] AC-08: Focused and full canonical suites plus quality gates pass
- [x] AC-09: Human approves the exact canonical diff before commit/push
- [x] AC-10: Fresh smoke issue reaches a visible terminal outcome with no
      silent END; issue #1 remains untouched evidence
- [x] AC-11: FR records commits, tests, logs, gates, deviations, and failed
      attempts

## Enforcement Record (2026-08-20)

- Canonical GitClaw commit `a983bf10773a2ca0c95f31e9696ee14d5783370b`; smoke
  consumer parity at `ada0c83` (byte-verified; one stray root test file from
  an earlier shell mishap was swept in by `git add -A` and removed in the
  next commit — recorded deviation).
- Red: 5 targeted failures (`tmp/fr843-canonical-red.log`, local). Green:
  144/144 full suite (`tmp/fr843-canonical-full.log`), lint 0 errors and
  0 warnings, scratch-dir compile 20 nodes.
- Deviation (defensive, semantics-identical for integer counters): the FR-842
  lint gap checker (W803) explores non-integer and negative counter states,
  so the frozen `== null | >= 1` matrix ships as the total partition
  `== null | < 1 | >= 1`; the evaluator test pins verdicts at
  `null/0/1/2`.
- Live witness (AC-10/AC-13): fresh issue #2 `Yle news haiku digest` → run
  `32366594247` (13m57s) → first-pass exact `APPROVED` → feature
  `yle-news-haiku-digest` published at
  `dc71bdea46bc814ddac3531e57391ec4ad2f98c9`, issue closed with the
  implementation comment; ledger seen→planned→judged_approved→enforced→
  reviewed_approved→pushed→closed. All four stages logged
  `model='claude-sonnet-5'` (4/4). No silent END. Interrupted issue #1
  untouched.
- Note: the remediation path itself was not exercised live (the witness
  approved first-pass); its behavior is proven by the evaluator matrix and
  the real verdict-extraction fixture.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-840 | Preserve immutability, three verdicts, and exact-`APPROVED` publication; add the convergence corollary those rules imply |
| FR-842 | Reuse the flat-condition grammar and scratch-dir compile validation method |
| FR-266 | Use existing `cli_flags.model` support; no yamlgraph change |
| Smoke issue #1 / run `32362016430` | Immutable interrupted evidence; not recovered, relabelled, or rerun |
| README pipeline contract | Make the promised "one remediation lap, then final reject" true |

## Alternatives Rejected

- **Let enforcement fold review findings into FR.md:** reopens the exact
  FR-839/issue-#6 mutation channel.
- **Unlimited remediation laps:** unbounded spend on a non-converging
  disagreement; one lap then terminal matches the documented contract.
- **Quarantine branch for rejected work:** preserves unreviewed-quality code
  paths in the repo; the posted review comment is the recoverable record.
- **Hardcode a guessed model id:** avoided — `claude-sonnet-5` was verified
  against the installed CLI with positive and negative probes before freezing.

## Scope Fence

FR-843 authorizes the routing, prompt, model-pin, test, and README changes in
canonical GitClaw plus one propagated fresh smoke witness. It authorizes no
workflow/tool/policy/ledger/cron/containment change, no issue #1 recovery, no
FR-841 implementation, and no Oulu restart work.
