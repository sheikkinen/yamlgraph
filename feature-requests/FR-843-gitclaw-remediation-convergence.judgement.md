# Judgement: FR-843 GitClaw Remediation Convergence

**Verdict:** APPROVED WITH REVISIONS — the convergence repair is real, narrow, and testable, but authority activates only after the FR resolves three foldable ambiguities around routing-state values, visible terminal claims, and model pin ownership. R-1 through R-4 were folded on 2026-08-20: exact loop-count states frozen; scope narrowed to parseable verdicts (unknown verdicts stay bare-END fail-closed outside this FR); model pin frozen to `claude-sonnet-5` after positive and negative CLI probes; Ideal Result added. Human publication gate pending.

**Prior art:** FR-840 (`a7621f21`, hotfix `846ddfe`) supplies the immutable authority artifacts and revisions-to-remediation routing this FR completes; FR-842 supplies the flat-condition grammar and compile-validation method; FR-266 supplies `cli_flags.model`; smoke issue #1 / run `32362016430` is the immutable convergence-failure witness.

**Reviewed against:** `feature-requests/FR-843-gitclaw-remediation-convergence.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.judgement.md`; `feature-requests/FR-842-lint-compile-validation-parity.md`; `feature-requests/FR-842-lint-compile-validation-parity.judgement.md`; `feature-requests/FR-266-copilot-node-model-selection.md`; `/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/judge.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/review.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_intake_tools.py`; `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_generated_feature_policy.py`; `/Users/sami.j.p.heikkinen/src/gitclaw/.github/workflows/intake.yml`; `/Users/sami.j.p.heikkinen/src/gitclaw/README.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The problem is real and evidenced at the exact boundary where the current graph can stop silently. FR-843 records the live sequence ending after a second `APPROVED WITH REVISIONS` review with `ledger_reviewed_rejected` loop-limit blockage and no visible terminal issue result (`feature-requests/FR-843-gitclaw-remediation-convergence.md:27-41`). The current graph supports that root cause: the second non-approved review can still target `ledger_reviewed_rejected` while `ledger_reviewed_rejected` has loop limit 1, and `reject_final` is delayed until `_loop_counts.enforce >= 2` (`/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml:400-430`).

The prompt-side convergence diagnosis is also sound. FR-840 froze `request.json`, `FR.md`, and `judgement.md` as authority artifacts and required enforcement not to edit them (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:156-165`), and the current enforcement prompt implements that no-mutation rule while consuming review findings only as additive implementation constraints (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml:7-19`). FR-843 correctly identifies the missing corollary: review must not treat frozen pre-revision FR prose as a defect when the judgement revisions are the controlling layer over it (`feature-requests/FR-843-gitclaw-remediation-convergence.md:43-49`, `:66-73`).

The proposed implementation surface is appropriately small for a GitClaw framework primitive: one routing graph, two prompts, two existing test files, and README documentation (`feature-requests/FR-843-gitclaw-remediation-convergence.md:87-99`). It preserves FR-840's exact-`APPROVED` publication gate and immutable authority artifacts, preserves FR-842's flat-condition grammar, and reuses FR-266's existing `cli_flags.model` support instead of changing YAMLGraph core (`feature-requests/FR-843-gitclaw-remediation-convergence.md:171-179`; `feature-requests/FR-266-copilot-node-model-selection.md:54-58`). Strategic classification: **Framework primitive for GitClaw**, not YAMLGraph core, because the defect is in GitClaw's autonomous intake state machine and prompt contract.

Most acceptance criteria are mechanically checkable: prompt marker tests can prove the two convergence clauses, a routing evaluator can prove both parseable non-approved verdicts across loop-count states, the existing lint/compile parity method can validate flat conditions, and a fresh smoke issue can prove live terminal behavior (`feature-requests/FR-843-gitclaw-remediation-convergence.md:121-136`, `:146-169`).

## Required revisions

### R-1: Align the routing matrix with actual `_loop_counts.enforce` values

Revise the Frozen Routing and Acceptance Criteria so they name the exact states the tests must evaluate: first-review value `null`, remediation-lap value `1`, and any higher value used as a defensive final-reject case. Remove or define the ambiguous "laps 0/1/2" wording. The folded FR must require an evaluator test proving:

- `REJECTED` and `APPROVED WITH REVISIONS` at `_loop_counts.enforce == null` route only to `ledger_reviewed_rejected`;
- the same verdicts at `_loop_counts.enforce >= 1` route only to `reject_final`;
- `APPROVED` routes only to `ledger_reviewed_approved`;
- unknown verdicts follow the explicitly frozen behavior from R-2; and
- no matching verdict state can reach `ledger_reviewed_rejected` after the one allowed remediation lap.

This is required because FR-843's decision says remediation is entered only when `_loop_counts.enforce == null` (`feature-requests/FR-843-gitclaw-remediation-convergence.md:74-78`), while its validation text asks for laps `0/1/2` (`feature-requests/FR-843-gitclaw-remediation-convergence.md:126-128`, `:154-156`). The current canonical test helper already treats `None` as a meaningful state (`/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_intake_tools.py:268-324`), so the FR must freeze that contract rather than leave enforcers to infer it.

### R-2: Narrow or implement the "visible terminal" claim for unknown review verdicts

Choose one exact contract and fold it through the First consumer, Frozen Routing, Validation, Acceptance Criteria, and README change:

1. If FR-843 covers only parseable non-approved verdicts, replace broad phrases such as "a review that cannot reach exact `APPROVED`" with "a parseable `REJECTED` or `APPROVED WITH REVISIONS` review verdict", and explicitly state that unknown verdict behavior remains a separate fail-closed surface outside this FR.
2. If FR-843 covers all non-approved review outcomes, route unknown review verdicts to a visible terminal failure path that posts the review or an explicit parse-failure comment, records a terminal ledger state, and closes the issue.

The current FR contradicts itself: it promises a visible terminal state for "a review that cannot reach exact `APPROVED`" (`feature-requests/FR-843-gitclaw-remediation-convergence.md:21-23`) but freezes unknown verdicts to bare `END` unchanged (`feature-requests/FR-843-gitclaw-remediation-convergence.md:114`). The current README says unparseable verdicts fail closed (`/Users/sami.j.p.heikkinen/src/gitclaw/README.md:83-84`), so the FR must not leave whether "fail closed" means silent END or visible issue terminal state ambiguous.

### R-3: Freeze the model-pin decision before enforcement authority activates

Replace the current owner-deferred model-pin wording with one enforceable contract before implementation starts: either name the exact accepted Copilot CLI model identifier to put on all four copilot nodes, or strike F-3 from FR-843 with a one-line deviation that makes model pinning a separate FR. Do not authorize enforcers to discover, choose, or negotiate the model identifier mid-implementation.

This is required because the FR makes model determinism part of the decision and canonical change surface (`feature-requests/FR-843-gitclaw-remediation-convergence.md:81-85`, `:89-95`) but also says "do not guess the id in this FR" and defers confirmation to a human gate (`feature-requests/FR-843-gitclaw-remediation-convergence.md:141-142`). Human approval is appropriate for spend and portability, but the implementation contract must be frozen before authority; otherwise an orthogonal owner decision is bundled into the enforcement step. If retained, the test must assert the exact same non-empty model string on `plan`, `judge`, `enforce`, and `review`; if struck, remove the model-pin deliverable, README promise, and AC-07.

### R-4: Add the required Ideal Result section

Insert an `## Ideal Result` section before the implementation decision that states the desired end state in one or two mechanically checkable sentences: after one remediation lap, every parseable non-approved review result produces a posted review and closed issue via `reject_final`, while judgement revisions remain enforceable without rewriting frozen authority artifacts. This is required by repo doctrine for FR planning (`.github/copilot-instructions.md:228-233`) and will make the solution read as the minimal path back from the intended state.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `gitclaw.yaml` routing conditions, loop limits, and retained flat-condition grammar |
| D-2 | `gitclaw.yaml` model pin entries only if R-3 retains F-3 |
| D-3 | `prompts/judge.yaml` implementability clause forbidding revisions that require authority-artifact edits |
| D-4 | `prompts/review.yaml` frozen-FR/prose-as-amended-by-judgement convergence clause |
| D-5 | `tests/test_intake_tools.py` routing evaluator and optional model-pin assertions |
| D-6 | `tests/test_generated_feature_policy.py` prompt convergence marker tests |
| D-7 | `README.md` pipeline diagram/note and optional model-pin portability note |
| D-8 | FR-843 enforcement record with red/green evidence, commits, logs, deviations, failed attempts, human gates, and live-smoke result |

Not authorized: YAMLGraph core changes; condition parser/evaluator changes; workflow changes; ledger implementation changes; containment, cron, source adapter, dependency, secret, or policy-file changes; recovering or relabelling interrupted issue #1; implementing FR-841; Oulu restart work; quarantine branches for rejected generated work; changing publication semantics so anything other than exact review `APPROVED` can publish; editing generated `request.json`, `FR.md`, or `judgement.md` during enforcement; adding any second remediation lap.

## Revised acceptance criteria

- [ ] AC-01: FR-843 contains an Ideal Result section and the required revisions R-1 through R-4 are folded before enforcement starts.
- [ ] AC-02: Red evidence captures the current unreachable `reject_final` for the second parseable non-approved review, missing judge/review convergence clauses, and either unpinned copilot-node models or the recorded R-3 deviation.
- [ ] AC-03: `prompts/judge.yaml` states that a revision must be implementable without editing `request.json`, `FR.md`, or `judgement.md`; a required FR-prose rewrite is `REJECTED`, not `APPROVED WITH REVISIONS`.
- [ ] AC-04: `prompts/review.yaml` states that judgement revisions are controlling additive constraints over frozen `FR.md` prose; unfolded pre-revision FR prose alone is not a blocking finding.
- [ ] AC-05: From `read_review_verdict`, `REJECTED` and `APPROVED WITH REVISIONS` at `_loop_counts.enforce == null` route only to `ledger_reviewed_rejected`; the same verdicts at `_loop_counts.enforce >= 1` route only to `reject_final`.
- [ ] AC-06: No parseable review verdict and loop-count combination ends at a bare loop-limit stop; `APPROVED` remains the only route to `ledger_reviewed_approved`, `contain`, and `push`.
- [ ] AC-07: Unknown review verdict handling matches the R-2 contract exactly and is covered by a routing evaluator assertion.
- [ ] AC-08: `reject_final` posts `features/<feature_name>/review.md` to the issue, records `reviewed_rejected` and `reviewed_rejected_final`, commits/pushes the terminal ledger state, and closes the issue.
- [ ] AC-09: All routing conditions remain flat; `gitclaw.yaml` passes real lint and scratch-dir compile/run validation by the FR-842 method.
- [ ] AC-10: If F-3 is retained, all four copilot nodes (`plan`, `judge`, `enforce`, `review`) carry the exact same R-3-frozen `cli_flags.model` value and README documents the pin and portability trade-off. If F-3 is struck, no model-pin code or README change is made under FR-843.
- [ ] AC-11: Focused tests covering routing, prompt markers, and optional model pin pass, and the full canonical GitClaw suite plus quality gates pass.
- [ ] AC-12: Human approves the exact canonical diff and red/green evidence before commit/push.
- [ ] AC-13: After canonical push and separate human approval to spend a live run, a fresh smoke issue reaches a visible terminal outcome: either exact-approved publication with closed issue, or `reject_final` with posted review and closed issue. Interrupted issue #1 remains untouched evidence.
- [ ] AC-14: FR-843 records commits, tests, logs, gates, deviations, failed attempts, the model-pin decision, and the live-smoke result.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-843 before implementation authority activates. | GATE |
| C-2 | Preserve FR-840 authority immutability: enforcement must not edit `request.json`, `FR.md`, or `judgement.md`; review findings are conveyed through `review.md` and another enforcement/review cycle. | GATE |
| C-3 | Preserve exact review `APPROVED` as the only publication path; `APPROVED WITH REVISIONS`, `REJECTED`, and any R-2-covered unknown verdict must never reach containment or push. | GATE |
| C-4 | Do not change YAMLGraph condition grammar or use parenthesized/grouped conditions; all new routing conditions must stay flat and lint/compile clean. | GATE |
| C-5 | Do not add a second remediation lap; after the first remediation enforcement/review pass, parseable non-approved review verdicts must route to `reject_final`. | GATE |
| C-6 | Do not implement model pinning unless R-3 freezes the exact accepted CLI model identifier before code changes. | GATE |
| C-7 | GitClaw graph, prompt, and README changes are enforcement-infrastructure changes and require human review before canonical push. | GATE |
| C-8 | Live smoke issue filing is a separate human spend/side-effect gate after canonical tests and diff approval. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-843, implement only the GitClaw convergence repair that makes one remediation lap converge to exact-approved publication or visible final rejection, while preserving immutable authority artifacts, flat routing conditions, and the exact-`APPROVED` publication gate.
