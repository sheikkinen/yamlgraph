# Judgement: FR-839 GitClaw Immutable Owner Contract

**Verdict:** APPROVED - FR-839 identifies a repeated authority-boundary failure
and freezes a minimal, mechanically testable immutable-owner contract. Human
review approved publication and tests-first local canonical implementation on
2026-08-20; canonical and consumer pushes remain separately gated.

**Prior art:** FR-829 established generated-feature security policy; FR-830
established repository-scoped ledger identity; FR-835 and FR-836 established
composition and output contracts; FR-837 issue #5 and FR-838 issue #6 are two
concrete authority-drift witnesses. Human FR judgement doctrine remains
unchanged.

**Reviewed against:** `feature-requests/FR-839-gitclaw-immutable-owner-contract.md`;
FR-829, FR-830, FR-835 through FR-838 and their judgements;
`docs/analysis/gitclaw-evaluation.md`; repository judge doctrine, judgement
template, and Copilot instructions.

## What is sound

The problem is repeated and platform-owned. Issue #5 changed exact owner output
and validation requirements. Issue #6 then changed invalid-input rejection into
a successful fallback. Both reviews approved because downstream stages saw only
mutually rewritten local FR/judgement artifacts.

The proposed boundary is correctly placed where external input enters. A
platform-written canonical `request.json` is hashed before model execution and
verified after every model stage and retry. Title/body remain untrusted data,
but their behavioral constraints cannot be silently superseded.

The repair is mechanically testable: exact bytes and hash, schema/path/size and
symlink failures, workflow ordering, graph verification points, approve-or-reject
routing, tamper witnesses, and an issue-#6 authority-inversion fixture.

Strategic classification: **GitClaw framework primitive**, not YAMLGraph core.
It applies to every future autonomous generated-feature intake while preserving
cron, composition, candidate extraction, containment, ledger implementation,
sources, and human FR judgement doctrine.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Standard-library `tools/request_contract.py` writer/verifier and focused tests |
| D-2 | Intake workflow request creation and safe hash propagation |
| D-3 | `gitclaw.yaml` state and verification after plan/judge/enforce/review, including retries |
| D-4 | Shared policy and four prompt authority/verdict alignment |
| D-5 | Generated-policy and graph/workflow contract tests plus README documentation |
| D-6 | Human-reviewed canonical publication and separately approved exact consumer parity rollout |

Not authorized: issue #5/#6 deletion or repair; third Task 6 issue; Task 7;
source access/change; cron, composition, candidate extraction, containment,
ledger implementation, dependency, secret, cadence, notification, publication,
YAMLGraph core, or human FR judgement doctrine changes.

## Acceptance criteria

- [ ] AC-01: Red tests prove missing immutable evidence and unsafe revision routing.
- [ ] AC-02: Writer creates exact bounded canonical JSON and outputs only SHA-256.
- [ ] AC-03: Verifier fails closed on every integrity/schema/path/boundary violation.
- [ ] AC-04: Workflow creates request before graph and passes only safe hash.
- [ ] AC-05: Graph verifies after every model stage/retry before transition/push.
- [ ] AC-06: Policy/prompts preserve untrusted-data safety and immutable authority.
- [ ] AC-07: Generated judge/review accept only APPROVED or REJECTED.
- [ ] AC-08: Enforcement cannot mutate request/FR/judgement; review checks all evidence.
- [ ] AC-09: Tamper and issue-#6 authority-inversion witnesses fail before publication.
- [ ] AC-10: Focused/full canonical suites and quality gates pass.
- [ ] AC-11: Human approves exact canonical diff before commit/push.
- [ ] AC-12: Exact consumer parity, hashes, full suite, audit, and separate approval pass.
- [ ] AC-13: No forbidden platform/consumer behavior changes.
- [ ] AC-14: Closure records commits, tests, hashes, audits, gates, and failures.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Publish this human-reviewed judgement before implementation. | GATE |
| C-2 | Implement red tests before runtime/workflow/prompt changes. | GATE |
| C-3 | Missing or invalid request evidence must fail before transition; no fallback. | GATE |
| C-4 | Never pass/log owner text through shell arguments or graph variables. | GATE |
| C-5 | Restrict approve-or-reject to autonomous GitClaw intake. | GATE |
| C-6 | Human reviews exact canonical enforcement-infrastructure diff before push. | GATE |
| C-7 | Consumer rollout is exact parity only with separate human approval. | GATE |

Authority granted: implement locally only the immutable request artifact,
per-stage verification, autonomous approve-or-reject routing, aligned
policy/prompts/docs, tests, and later separately gated parity rollout.
