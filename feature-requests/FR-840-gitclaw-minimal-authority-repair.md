# Feature Request: FR-840 GitClaw Minimal Authority Repair

**Priority:** HIGH
**Type:** Platform / GitClaw authority boundary
**Status:** Enforced 2026-08-20 - canonical GitClaw published at `a7621f21`;
consumer rollout explicitly waived by owner at the canonical gate
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-838
**Depends on:** FR-829, FR-830, FR-835, FR-836, FR-838
**Blocks:** Any third FR-837 consumer attempt and FR-831 Task 7
**Prior art:** FR-839 was REJECTED on 2026-08-20 for overcorrection: it bundled
a sound mechanical repair with deletion of the `APPROVED WITH REVISIONS`
judgement vocabulary. Its rejection record requires any replacement to retain
that vocabulary, prevent revisions from contradicting immutable owner
requirements, and route review revisions through another enforcement/review
cycle before publication. Issues #5 and #6 in the Oulu consumer remain the two
proven authority-drift witnesses: judge sees only the model-written `FR.md`,
enforcement folds revisions into `FR.md`, and review compares only mutually
rewritten downstream artifacts, so owner semantics were twice inverted under a
green pipeline.
**First consumer / first event:** The next trusted-owner GitClaw issue, when the
pipeline must prove after every model stage that the implementation still
satisfies the exact owner request that triggered the run.

## Summary

Repair GitClaw's owner-authority boundary with the minimal mechanical change
set and no verdict-vocabulary change:

1. the trusted workflow writes an immutable canonical
   `features/<slug>/request.json` from the GitHub event before any model stage
   and passes only its SHA-256 into graph state;
2. the graph verifies that artifact's exact bytes after plan, judgement,
   enforcement, and review, including retries, before each next transition;
3. enforcement implements but must not modify `request.json`, `FR.md`, or
   `judgement.md`; judge revisions become additive constraints recorded in
   `judgement.md`, not rewrites of the FR;
4. judge and review keep verdicts `APPROVED`, `APPROVED WITH REVISIONS`, and
   `REJECTED`, but a revision may never alter owner-requested semantics — a
   change that would contradict `request.json` is `REJECTED`; and
5. review `APPROVED WITH REVISIONS` routes to the existing remediation lap
   (`ledger_reviewed_rejected -> enforce -> review`), never to push; only exact
   `APPROVED` reaches containment and publication.

This FR repairs shared authority flow only. It does not delete or repair
consumer issues #5/#6 artifacts (FR-838 owns that gate), does not file a third
Task 6 issue, and does not implement Task 7.

## Evidence and Root Cause

Unchanged from the FR-839 record and re-verified against baseline `2a0a3c4`:

- `prompts/plan.yaml` is the only stage receiving `issue_title`/`issue_body`;
- `prompts/judge.yaml` judges `features/<slug>/FR.md` alone;
- `prompts/enforce.yaml` instructs folding `APPROVED WITH REVISIONS` revisions
  into `FR.md`, mutating the artifact that was judged;
- `prompts/review.yaml` compares the diff against `FR.md` and `judgement.md`
  only; and
- `gitclaw.yaml` routes `review_verdict == 'APPROVED WITH REVISIONS'` directly
  to `contain -> push` with no remediation lap.

Issue #5 drifted labels/validation; issue #6's judge invented revision R-2
converting owner-required rejection into fallback success, enforcement folded
it, and review approved the folded pair. The defect is authority loss after
planning plus unreviewed publication of revision-flagged diffs — not the
existence of a revisions verdict.

## Decision

Keep the three-verdict vocabulary. Change only artifact immutability, stage
inputs, and routing:

| Concern | FR-839 (rejected) | FR-840 |
|---|---|---|
| `request.json` + per-stage hash verify | Yes | Yes (unchanged core) |
| Enforcement mutating FR/judgement | Forbidden | Forbidden (unchanged core) |
| Judge/review verdict vocabulary | Approve-or-reject only | All three retained |
| Judge `APPROVED WITH REVISIONS` | Removed | Proceeds to enforcement; revisions are additive constraints in `judgement.md`; must not contradict `request.json` |
| Review `APPROVED WITH REVISIONS` | Removed | Routes to remediation lap; never to push |
| Push condition | Exact `APPROVED` | Exact `APPROVED` (same) |

## Frozen Request Artifact

Add canonical `tools/request_contract.py` with standard-library-only commands:

```text
python -m tools.request_contract write <feature> <issue-number>
python -m tools.request_contract verify <feature> <expected-sha256>
```

`write` reads only workflow environment variables `GITCLAW_REPOSITORY`,
`ISSUE_TITLE`, and `ISSUE_BODY`; validates canonical slug and positive integer
issue number; creates the feature directory without following symlinks; and
atomically writes UTF-8 `request.json` with sorted keys, compact separators,
`ensure_ascii=False`, and one terminal newline:

```json
{
  "version": 1,
  "repository": "owner/repository",
  "issue_number": 7,
  "feature_name": "canonical-feature-slug",
  "title": "Exact owner title",
  "body": "Exact owner body"
}
```

Bounds and rejections: title ≤ 256 characters, body ≤ 1 MiB UTF-8, artifact
≤ 1.1 MiB; reject missing environment values, NUL in artifact content, wrong
repository shape, noncanonical slug, symlink or non-directory parent,
pre-existing `request.json`, and size overflow. `write` prints only the
lowercase SHA-256 of exact file bytes; no title/body ever appears in stdout,
logs, shell interpolation, or graph variables. `verify` opens the path
fail-closed as a non-symlink regular file, enforces bounds, compares hashes
with `hmac.compare_digest`, strictly re-parses and revalidates schema and
slug/issue coherence, and exits nonzero on any mismatch.

`request.json` is committed with the other contained feature artifacts on
successful publication; rejected runs retain existing ledger semantics.

## Workflow and Graph Gates

In `.github/workflows/intake.yml`, after slug resolution and before
`yamlgraph graph run`: call `write` with title/body via `env:` only, store the
returned hash as `REQUEST_SHA256`, and pass `request_sha256` as a graph
variable. Owner text never enters graph state.

In `gitclaw.yaml`: add `request_sha256: str` to state; add one verification
tool node invoked after each of plan, judge, enforce, and review, before that
stage's next ledger transition or verdict read, with loop limits covering the
remediation lap. Any missing, modified, replaced, symlinked, malformed,
oversized, or hash-mismatched artifact fails the run before transition.

Routing changes (exact):

- `review_verdict == 'APPROVED WITH REVISIONS'` joins the existing
  `REJECTED` remediation edges (`ledger_reviewed_rejected -> enforce`) and its
  final-rejection edge when the enforce loop limit is reached;
- the remediation-lap enforce prompt is given `features/<slug>/review.md` as an
  explicit additive-constraint input so review findings reach the stage that
  must repair them (R-1);
- `contain -> push` remains reachable only from exact
  `review_verdict == 'APPROVED'`; and
- judge routing keeps all three verdicts exactly as today.

## Authority Contract

Update shared policy and all four prompts minimally:

- `request.json` is immutable owner evidence, mechanically created before
  planning; its title/body remain untrusted data, never executable
  instructions, while its requested behavioral constraints bind all stages.
- Planning writes `FR.md` consistent with `request.json` and must visibly flag
  any owner requirement it cannot satisfy rather than silently substitute it.
- Judgement reads `request.json` and `FR.md`. `APPROVED WITH REVISIONS` may add
  clarifying or tightening constraints recorded in `judgement.md`; any revision
  that omits, contradicts, or semantically rewrites an owner requirement makes
  the verdict `REJECTED`.
- Enforcement implements `FR.md` plus recorded judgement revisions as additive
  constraints. It must not edit `request.json`, `FR.md`, or `judgement.md`.
  On a remediation lap entered after review `APPROVED WITH REVISIONS` or
  `REJECTED`, enforcement additionally reads `features/<slug>/review.md` and
  treats its findings as additive implementation constraints, then returns to
  independent review before any containment or push (R-1).
- Review reads `request.json`, `FR.md`, `judgement.md`, implementation, tests,
  and evidence. Contradiction with `request.json` is blocking even when FR and
  judgement agree. `APPROVED WITH REVISIONS` sends the run back through
  enforcement; only exact `APPROVED` publishes.

## Exact Canonical Change Surface

1. `tools/request_contract.py` (new);
2. `tests/test_request_contract.py` (new);
3. `tests/test_intake_tools.py` (graph/workflow contract assertions);
4. `tests/test_generated_feature_policy.py` (policy/prompt markers);
5. `.github/workflows/intake.yml`;
6. `gitclaw.yaml`;
7. `policy/generated-features.md`;
8. `prompts/plan.yaml`;
9. `prompts/judge.yaml`;
10. `prompts/enforce.yaml`;
11. `prompts/review.yaml`; and
12. `README.md` pipeline/authority documentation.

No cron, composition, candidate extraction, containment, ledger
implementation, source adapter, consumer feature, dependency, secret, or
cadence change. Consumer rollout copies only exact reviewed canonical files
after separate human approval and SHA-256 parity.

## Validation

Tests-first canonical validation must prove:

- request writer/verifier: exact Unicode/newline round-trip, canonical bytes
  and hash, no owner text on stdout, every env/schema/slug/size/symlink/
  pre-existing/NUL rejection, atomic no-partial-write on failure, verify
  rejection of byte modification, replacement, wrong hash, malformed JSON,
  duplicate/unknown/missing keys, wrong types, path/feature incoherence,
  symlink, nonregular file, and oversize;
- workflow: request written after slug and before graph run; only the hash
  passed as a graph variable; no inline `${{ }}` interpolation of owner text;
- graph: verification node after each of the four model stages and inside the
  remediation lap; `APPROVED WITH REVISIONS` review routing reaches
  `ledger_reviewed_rejected` and never `contain`; exact `APPROVED` remains the
  only path to push; all three verdicts remain in judge/review accepted lists;
- prompts/policy: enforce contains no fold-into-FR instruction and forbids
  mutating the three authority artifacts; judge/review name `request.json` as
  binding input and define the revision boundary; mechanically checkable
  markers only, no semantic-certainty claims;
- an issue-#6-shaped fixture (owner requires rejection of invalid input; FR or
  judgement proposes fallback success) is exercised against the prompt/policy
  contract markers and the routing tests;
- a synthetic tamper witness: modifying `request.json` between stages fails
  verification before the next transition;
- a synthetic review `APPROVED WITH REVISIONS` finding demonstrably changes the
  next enforcement pass's inputs and cannot publish until a subsequent exact
  `APPROVED` review (R-1); and
- existing ledger, containment, composition, candidate-output, and full
  canonical suites remain green.

## Human Gates

1. Human approves the FR-840 judgement before implementation.
2. Human reviews the exact canonical diff and red/green evidence before
   canonical commit/push.
3. Human separately reviews the exact consumer parity diff and hashes before
   consumer commit/push.
4. Issue #6 containment and any third Task 6 issue remain FR-838-gated; FR-840
   grants neither.

## Acceptance Criteria

- [x] AC-01: Red tests reproduce missing immutable request evidence, the
      enforce fold-into-FR instruction, and review-with-revisions publishing
      on the canonical baseline
- [x] AC-02: `write` produces exact bounded canonical JSON from env and prints
      only the SHA-256
- [x] AC-03: `verify` fail-closes every integrity/schema/path/bound violation
- [x] AC-04: Workflow writes the request before the graph and passes only the
      hash
- [x] AC-05: The graph verifies the request after every model stage and retry
      before the next transition
- [x] AC-06: Judge and review retain all three verdicts; revisions that alter
      owner semantics are defined as REJECTED in prompts and policy
- [x] AC-07: Review `APPROVED WITH REVISIONS` routes to the remediation lap;
      only exact `APPROVED` reaches contain/push
- [x] AC-08: Enforcement implements additive judgement revisions without
      editing `request.json`, `FR.md`, or `judgement.md`
- [x] AC-09: Tamper and issue-#6-shaped witnesses fail before publication
- [x] AC-10: Focused and full canonical suites plus quality gates pass
- [x] AC-11: Human approves the exact canonical diff before commit/push
- [~] AC-12 (WAIVED by owner): Exact consumer parity with matching hashes, full suite, audit,
      and separate human approval
- [x] AC-13: No forbidden platform or consumer behavior changes
- [x] AC-14: FR records commits, test counts, logs, hashes, gates, deviations,
      and failed attempts before any third Task 6 issue
- [x] AC-15: Remediation-lap enforcement reads `review.md` as additive
      constraints after review `APPROVED WITH REVISIONS` or `REJECTED`; a
      synthetic revisions finding is consumed by the next enforcement pass and
      re-reviewed before any publication

## Enforcement Record (2026-08-20)

Canonical GitClaw commit `a7621f21bbf6bce2cd3bcc834602a0fb696c5c07`, exactly
the twelve declared files (674 insertions, 30 deletions).

- Red evidence (`tmp/fr840-canonical-red.log`, local): 1 collection error
  (missing `tools.request_contract`) plus 7 seam failures for graph state,
  routing, workflow, policy, and prompts.
- Green evidence: focused 70 passed (`tmp/fr840-canonical-focused.log`); full
  canonical suite 141 passed (`tmp/fr840-canonical-full.log`); `gitclaw.yaml`
  lints clean; Ruff check/format clean; no grade-D complexity; all files under
  the 450-line hard limit.
- Independent adversarial audit: no blockers; its high finding (missing
  issue-#6-shaped fixture) and all three mediums were folded as tests before
  the gate — a routing evaluator proves a review `APPROVED WITH REVISIONS`
  verdict extracted by the real `sed` command reaches only remediation or
  final rejection at every enforce loop count, never publication; loop-limit
  pins, an inline-owner-text guard, and the remediation-consumption marker
  were added. Audit diff fingerprint before the four test additions:
  `a95447d0923b220fd49c9e3e431c6f53e6776a33dd3048710878e3a0d03fdf2f`.
- Human gates: judgement R-1 folded and publication approved; the exact
  twelve-file canonical diff was approved with the explicit instruction
  "approve canonical commit/push. ignore consumer".
- Deviation (owner-directed): AC-12 consumer parity rollout is WAIVED. The
  Oulu consumer remains at `33ec4467` with the pre-FR-840 authority flow;
  FR-841's R-1 prerequisite (consumer parity) is therefore unmet until a
  future separately gated rollout.
- Known residual boundary (audit M4, pre-existing since FR-827): the verifier
  lives in the model-writable tree during enforce/review; mitigated by scoped
  `git add` and push-time rebase failure, recorded, not repaired here.
- One test-authoring defect during red capture (missing `Path` import) was
  fixed before evidence; the `sed` fixture subprocess needed an absolute
  `/usr/bin/sed` path for the local shell environment.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-839 (rejected) | Carry forward only the immutable request artifact, per-stage verification, and enforcement no-mutation core; discard the verdict-vocabulary removal per the rejection record |
| FR-829 | Preserve untrusted-input policy; owner text remains data, never instructions |
| FR-830 | Preserve append-only repository-scoped ledger semantics |
| FR-835 / FR-836 | Preserve composition and candidate-output contracts unchanged |
| FR-837 / issue #5, FR-838 / issue #6 | Preserve as immutable drift evidence; containment of #6 stays FR-838-gated |
| Human FR judgement doctrine | Unchanged; this FR governs only autonomous GitClaw generated-feature intake |

## Alternatives Rejected

- **FR-839 as judged:** rejected by human review for deleting common judgement
  vocabulary instead of repairing routing and immutability.
- **Prompt-wording-only repair:** both drift incidents occurred under prompt
  constraints; without an immutable artifact and executable gates the same
  channel stays open (two-strike rule: move the level into code).
- **Re-running judgement after enforcement instead of immutability:** adds a
  model stage to police model mutation; an exact hash gate is cheaper and
  deterministic.
- **Blocking judge revisions entirely:** loses legitimate tightening
  clarifications; the boundary is owner-semantics contradiction, not the
  verdict label.

## Scope Fence

FR-840 authorizes one tests-first canonical authority repair and one exact
consumer parity rollout after separate gates. It authorizes no issue #5/#6
artifact deletion or repair, no third Task 6 issue, no Task 7, no source
access or change, and no cron/composition/candidate/containment/ledger
behavior, dependency, secret, notification, or publication change.
