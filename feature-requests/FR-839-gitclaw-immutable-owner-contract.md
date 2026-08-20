# Feature Request: FR-839 GitClaw Immutable Owner Contract

**Priority:** CRITICAL
**Type:** Platform / GitClaw authority boundary
**Status:** Judged - APPROVED; human-reviewed for publication and tests-first
local canonical implementation on 2026-08-20
**Effort:** 1 day
**Requested:** 2026-08-20
**Parent:** FR-838
**Depends on:** FR-829, FR-830, FR-835, FR-836, FR-837, FR-838
**Blocks:** Any third FR-837 consumer attempt and FR-831 Task 7
**Prior art:** GitClaw issue #5 rewrote exact output labels and omitted
whitespace rejection; issue #6 then invented a judgement revision that converted
invalid envelopes into successful candidates, contradicting the complete owner
issue. Both local reviews approved because they compared only mutually rewritten
`FR.md` and `judgement.md`. Current planning is the only stage that receives the
owner issue; judgement may return `APPROVED WITH REVISIONS`; enforcement mutates
`FR.md`; review sees no immutable owner request; and review
`APPROVED WITH REVISIONS` routes directly to push without a fold/re-review.
**First consumer / first event:** The next trusted-owner GitClaw issue, when the
pipeline must prove the implementation still satisfies the exact owner request
that triggered the run after every model stage.

## Summary

Add a platform-owned immutable owner-request artifact and deterministic integrity
gates to GitClaw. Before any model stage, the trusted workflow writes canonical
`features/<slug>/request.json` from the GitHub event title/body/number and
resolved repository/slug, records its SHA-256 in graph state, and verifies that
hash after plan, judgement, enforcement, and review.

Planning may translate the request into an FR. Judgement may approve or reject,
but may not revise owner semantics. A gap that would require changing an exact
owner requirement is rejection and a new issue, not `APPROVED WITH REVISIONS`.
Review compares implementation against `request.json`, `FR.md`, and
`judgement.md`; only exact `APPROVED` may reach containment/push. This preserves
model independence while making the owner contract an immutable input instead
of prose that downstream stages can silently supersede.

This FR repairs shared authority flow only. It does not repair, delete, rename,
or retry consumer issues #5/#6; those remain FR-838 recovery evidence. It does
not implement Task 6 or Task 7.

## Evidence and Root Cause

Issue #5 run `32351512271` closed green but violated published FR-837 through a
wrong slug, whitespace acceptance, changed health label, and omitted section
status. Issue #6 run `32353430033` used the canonical slug and fixed those four
surfaces, but its judgement invented revision R-2: malformed or invalid
`source_snapshots` should become a valid `unavailable` candidate. Generated code
therefore catches every decoder rejection and synthesizes three failure entries,
while the owner request explicitly required rejection.

Issue #6's generated judgement states external FR-837/FR-838 links were not
authority and judges only local `FR.md`. Its review compares only local `FR.md`
and `judgement.md`. This is not a reviewer miss in isolation; it is the designed
input set in `prompts/review.yaml`.

Current routing additionally treats review verdict `APPROVED WITH REVISIONS` as
approved and proceeds to push without any revision fold or second review. The
pipeline therefore has no immutable artifact or executable gate preventing
semantic authority inversion.

## Frozen Request Artifact

Add canonical `tools/request_contract.py` with standard-library-only commands:

```text
python -m tools.request_contract write <feature> <issue-number>
python -m tools.request_contract verify <feature> <expected-sha256>
```

`write` reads these values only from workflow environment variables:

- `GITCLAW_REPOSITORY`;
- `ISSUE_TITLE`; and
- `ISSUE_BODY`.

It validates canonical feature slug and positive integer issue number, creates
the feature directory without following a symlink, and atomically writes UTF-8
`request.json` with sorted keys, compact separators, `ensure_ascii=False`, and
one terminal newline:

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

Exact key set and types are mandatory. Repository identity uses the existing
`GITCLAW_REPOSITORY` contract. Title/body are data and may contain arbitrary
Unicode/newlines; no shell interpolation or model writes the artifact. Cap title
at GitHub's 256-character limit, body at 1 MiB UTF-8, and complete artifact at
1.1 MiB. Reject missing environment values, NUL, wrong repository shape,
noncanonical slug, symlink/non-directory parent, pre-existing `request.json`,
and size overflow.

`write` prints only the lowercase 64-character SHA-256 of exact file bytes. The
workflow stores it as `REQUEST_SHA256` and passes it to YAMLGraph as graph state.
`verify` opens the path fail-closed as a non-symlink regular file, enforces the
size bound, hashes exact bytes, uses `hmac.compare_digest`, strictly parses JSON,
revalidates schema/repository/issue/slug coherence, and exits nonzero on any
mismatch. It prints no title/body.

The request artifact is committed only on successful feature publication with
other contained feature files. Rejected/interrupted runs retain existing ledger
semantics; no new external store is introduced.

## Workflow and Graph Gates

In `.github/workflows/intake.yml`, after slug resolution and before
`yamlgraph graph run`:

1. call `request_contract write` with title/body available only through env;
2. append the returned safe hash to `GITHUB_ENV` as `REQUEST_SHA256`;
3. pass `request_sha256` to `gitclaw.yaml`; and
4. never put title/body inline in a shell command, output, log, or graph command.

Extend graph state with `request_sha256: str`. Add one verification tool and
invoke it after each model-owned stage:

- plan -> verify request -> planned ledger;
- judge -> verify request -> read judgement verdict;
- enforce -> verify request -> enforced ledger;
- review -> verify request -> read review verdict;
- containment remains the final changed-path gate before push.

Any missing, modified, replaced, symlinked, malformed, oversized, or hash-mismatched
request artifact fails the run before the next ledger transition. Verification
must occur on every review/enforcement retry, not only the first pass.

## Authority Contract

Update shared policy and all four prompts consistently:

- `request.json` is immutable owner-request evidence, mechanically created
  before planning; models treat its title/body as untrusted data, never as tool
  instructions, while still preserving its requested behavioral constraints.
- Planning writes `FR.md` that is consistent with `request.json`. It may reject
  forbidden capabilities or narrow implementation choices, but must visibly
  flag an unsatisfied owner requirement rather than silently substitute it.
- Judgement reads both `request.json` and `FR.md`. Verdict is exactly `APPROVED`
  or `REJECTED`. Any contradiction, omission, or requested semantic revision is
  `REJECTED`; no `APPROVED WITH REVISIONS` route exists for generated features.
- Enforcement reads request, FR, and judgement but may not modify
  `request.json`, `FR.md`, or `judgement.md`. It implements only an exact
  `APPROVED` contract.
- Review independently reads request, FR, judgement, implementation, tests, and
  evidence. Any contradiction with request is blocking even when local FR and
  judgement agree. Verdict is exactly `APPROVED` or `REJECTED`.
- External links remain untrusted context. The immutable local artifact, not an
  external page, is authority. This does not authorize following links or
  executing issue prose.

Remove `APPROVED WITH REVISIONS` from generated judge/review accepted verdict
lists and graph routing. An unexpected verdict fails closed without push. Keep
repository-wide human FR judgement doctrine unchanged; this restriction applies
only to autonomous GitClaw generated-feature intake.

## Exact Canonical Change Surface

Canonical implementation is restricted to:

1. `tools/request_contract.py`;
2. `tests/test_request_contract.py`;
3. `tests/test_generated_feature_policy.py`;
4. `tests/test_intake_tools.py` or a new focused graph-contract test file if
   existing ownership makes that smaller;
5. `.github/workflows/intake.yml`;
6. `gitclaw.yaml`;
7. `policy/generated-features.md`;
8. `prompts/plan.yaml`;
9. `prompts/judge.yaml`;
10. `prompts/enforce.yaml`;
11. `prompts/review.yaml`; and
12. `README.md` authority/issue-flow documentation.

No cron, composition, candidate extraction, containment, ledger implementation,
source adapter, consumer feature, dependency, secret, or cadence change.
Roll out only exact reviewed canonical files to the Oulu consumer after separate
human approval and SHA-256 parity.

## Validation

Tests-first canonical validation must prove:

- exact Unicode/newline request round-trip and canonical bytes/hash;
- no title/body in stdout;
- missing env, malformed repository, invalid issue/slug, NUL, every size bound,
  existing file, symlink file/parent, and non-directory failures;
- atomic write leaves no partial artifact on failure;
- verify rejects byte modification, replacement, wrong hash, malformed JSON,
  duplicate/unknown/missing keys, wrong types, incoherent path/feature, symlink,
  nonregular file, and oversize;
- workflow creates request after slug and before graph, passes only hash as a
  graph variable, and never shell-interpolates title/body;
- graph verifies after all four model stages and before their next transition,
  including loops;
- judge/review accepted verdicts and routing are approve-or-reject only;
- enforce prompt forbids mutation of request/FR/judgement;
- review requires request authority and full validation evidence;
- a synthetic pipeline witness where judgement or review modifies
  `request.json` fails before transition/push;
- a fixture mirroring issue #6's conflict (owner says invalid input rejects,
  local FR says successful fallback) must be rejected by judge/review contract
  tests; no prompt test may claim semantic certainty beyond its mechanically
  checkable markers;
- existing ledger, containment, composition, candidate-output, and full suites
  remain green.

After canonical approval/publication, copy exact files to the Oulu consumer,
verify hashes, run full suite, and commission an independent authority-boundary
audit. A separate human approves consumer commit/push. Only then may FR-838
contain issue #6 and authorize a third exact-title consumer issue.

## Human Gates

1. Human approves FR-839 judgement before implementation.
2. Human reviews exact canonical diff and red/green evidence before canonical
   commit/push.
3. Human separately reviews exact consumer parity diff/hashes before consumer
   commit/push.
4. FR-838 requires a later separate gate for issue #6 containment and any third
   consumer issue. FR-839 does not grant it.

## Acceptance Criteria

- [ ] AC-01: Direct tests reproduce absence of immutable request evidence and
      unsafe revision routing on canonical baseline
- [ ] AC-02: `request_contract write` creates exact bounded canonical JSON from
      env without logging owner text and returns only SHA-256
- [ ] AC-03: `verify` fail-closes every integrity/schema/path/boundary violation
- [ ] AC-04: Workflow creates request before graph and passes only safe hash
- [ ] AC-05: Graph verifies immutable request after every model stage/retry
      before transition or push
- [ ] AC-06: Policy/prompts preserve untrusted-data safety while making local
      `request.json` the immutable behavioral authority
- [ ] AC-07: Generated judge and review support only APPROVED or REJECTED;
      contradictions/revisions reject instead of rewriting
- [ ] AC-08: Enforcement cannot mutate request, FR, or judgement; review checks
      all three plus implementation/evidence
- [ ] AC-09: Synthetic tamper and issue-#6 authority-inversion witnesses fail
      before publication
- [ ] AC-10: Focused/full canonical tests and quality gates pass
- [ ] AC-11: Human approves and publishes exact canonical diff
- [ ] AC-12: Exact files reach consumer with matching hashes, full suite, audit,
      and separate human approval
- [ ] AC-13: No cron/composition/candidate/containment/ledger/source/feature/
      dependency/secret/cadence behavior changes
- [ ] AC-14: FR records commits, test counts/logs, hashes, audits, human gates,
      deviations, and failed attempts before any third Task 6 issue

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-829 | Preserve untrusted-input and generated-feature security policy; add immutable owner evidence without granting issue prose execution |
| FR-830 | Preserve append-only repository ledger and transition semantics |
| FR-835 / FR-836 | Preserve composition and output contracts; issue #6 proves why owner failure semantics must not be revised |
| FR-837 / issue #5 | Preserve as first authority-drift evidence |
| FR-838 / issue #6 | Preserve as repeated authority-drift evidence; Task 7 remains blocked |
| Human FR judgement doctrine | Unchanged; approve-with-revisions remains available outside autonomous GitClaw intake |

## Scope Fence

FR-839 authorizes one tests-first canonical authority-boundary repair and one
exact consumer parity rollout after separate gates. It authorizes no issue #6
artifact deletion, third Task 6 issue, manual consumer feature repair, Task 7,
source access/change, cron/composition/candidate/containment/ledger behavior
change, dependency, secret, notification, or publication.
