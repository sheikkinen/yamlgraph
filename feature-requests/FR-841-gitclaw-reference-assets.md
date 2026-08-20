# Feature Request: FR-841 GitClaw Owner Reference Assets

**Priority:** HIGH
**Type:** Platform / GitClaw input channel
**Status:** Judged - APPROVED WITH REVISIONS; R-1 through R-3 folded
2026-08-20; human publication gate pending
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-838, FR-840
**Blocks:** Any third FR-837 consumer attempt that adapts existing probe code
**Prior art:** FR-831 dispositioned the working control-plane probes as
"Reuse contract; port implementation later" while its transfer packet ruled
"evidence input, not executable code" — porting was promised with no vehicle.
Every Oulu issue therefore carried a prose-only reimplementation contract;
issues #5 and #6 drifted at exactly the clauses the existing scripts already
encoded, and from-scratch retrieval design occasionally triggered LLM consent
refusals. FR-840 supplies the immutable `request.json` and per-stage hash
verification this FR extends. FR-829's untrusted-issue-prose rule is preserved:
trust here derives from owner-committed repository files, not from issue text.
**First consumer / first event:** The next Oulu source or composer issue, when
the pipeline must adapt an owner-committed working script instead of
reimplementing its behavior from prose.

## Summary

Add a trusted channel for owner-supplied reference implementations. The
operator commits reference files under top-level `references/<set>/` on the
default branch before filing an issue. The issue body names one reference set.
Before any model stage, the trusted workflow validates and copies that set into
`features/<slug>/reference/`, writes a hash manifest, and passes the manifest
SHA-256 into graph state. The FR-840 per-stage verification points additionally
verify the reference manifest, so no model stage can add, remove, or edit
reference bytes.

Prompts and policy then let planning and enforcement treat reference files as
authoritative prior implementation: derive, adapt, and port from them, and
preserve their observable behavior except where the FR explicitly narrows it.
Issue prose remains untrusted and non-executable; the reference set is trusted
because the owner committed it to the repository, and the issue merely selects
it by name.

This FR adds the input channel only. It does not file any consumer issue, does
not modify source adapters or composition, and does not alter FR-840 semantics.

Hard prerequisite (R-1): implementation may not start until FR-840 is judged,
enforced in canonical GitClaw, and rolled out to the consumer with exact
reviewed parity, so its per-stage `request_contract verify` points exist.
FR-841 attaches reference-manifest verification to those concrete points; it
must not implement a parallel or replacement verification lifecycle.

## Value Statement

The issue contract shrinks from a multi-level prose reimplementation
specification to "adapt this reference; here are the deltas". Review becomes
mechanical (compare behavior against the reference) instead of interpretive
(compare prose against prose). The model's retrieval-design deliberation
surface — where consent refusals occur — is minimized because retrieval is
presented as settled, owner-reviewed fact.

## Frozen Reference Contract

Operator side:

- Reference sets live only under top-level `references/<set-name>/` on the
  default branch, committed by the operator through normal review. `<set-name>`
  uses the canonical slug charset.
- Files are UTF-8 text (scripts, configs, docs). Binaries are rejected.
- Bounds: at most 8 files per set, 256 KiB per file, 1 MiB per set.

Issue side (exact parsing semantics, R-2):

- Selection lines are matched full-line as exactly `Reference-set: <set-name>`
  against the issue body delivered via `env:`. Comments, labels, front matter,
  quoted prose, and substrings never select a set.
- Zero matching lines: no reference is staged and `reference_sha256` is the
  empty string; the pipeline behaves exactly as FR-840 alone.
- Exactly one matching line with a canonical `<set-name>`: that set is staged.
- Two or more matching lines, or any matching line with a malformed name, or
  an unknown or empty set: the run fails before staging and before any model
  stage. The line grants nothing beyond selection: only owner-committed
  tracked files under `references/<set-name>/` can be staged. Bound
  violations, symlinks, traversal, and non-regular files also fail the run
  before any model stage.

Workflow side (new `tools/reference_assets.py`, standard library only):

```text
python -m tools.reference_assets stage <feature> <set-name>
python -m tools.reference_assets verify <feature> <expected-sha256>
```

- `stage` proves every staged byte comes from committed repository content
  (R-3): it enumerates the selected set from Git-tracked regular files under
  `references/<set-name>/` at the checked-out HEAD and rejects untracked,
  locally modified, deleted, and ignored files alongside symlinks,
  non-regular files, and any path escaping the set or feature directory. It
  copies the files to `features/<slug>/reference/`, writes
  `features/<slug>/reference/manifest.json` (version, set name, checked-out
  commit SHA, ordered relative paths, per-file SHA-256), and prints only the
  manifest file's SHA-256. It refuses pre-existing `reference/` and symlinked
  parents.
- `verify` fail-closes on missing/modified/replaced manifest, per-file hash
  mismatch, wrong or missing commit SHA, extra or missing files, symlinks, and
  bounds, mirroring FR-840 `request_contract verify` semantics.

Graph side:

- New state `reference_sha256: str` (empty string when the issue names no set).
- The FR-840 per-stage verification points also verify the reference manifest
  when a set is staged. Tampering fails before the next transition.
- `reference/` and its manifest are committed with the feature on publication;
  containment already allows `features/<slug>/**`.

## Authority Contract

Policy and prompt deltas, minimal:

- Reference files are owner-committed prior implementation: models may read,
  quote, derive, and port from them. They are still data — never executed
  during the pipeline run, never granted new capabilities beyond
  `policy/generated-features.md` (a reference script using a forbidden
  capability must be flagged and its capability rejected, not ported).
- Planning: when a reference set is staged, the FR must state which observable
  behaviors are preserved from the reference and which the owner request
  narrows or changes. Silent behavioral divergence from the reference is a
  planning defect.
- Judgement: verify FR-versus-reference consistency alongside the FR-840
  request-versus-FR check.
- Enforcement: adapt the reference rather than reimplementing from prose where
  a reference exists; must not modify `reference/`.
- Review: compare implementation behavior against the reference and the FR's
  declared deltas; undeclared divergence is blocking.

## Consent-Restriction Fallback

Adapting an owner-committed script narrows the model's design latitude and the
refusal surface, but does not eliminate refusals. A stage refusal fails the run
through existing fail-closed paths; the recorded fallback is operator-authored
code filed as a normal owner commit with GitClaw used only for review. This FR
documents that fallback in the README; it adds no automation for it.

## Exact Canonical Change Surface

1. `tools/reference_assets.py` (new);
2. `tests/test_reference_assets.py` (new);
3. `tests/test_intake_tools.py` (graph/workflow contract assertions);
4. `tests/test_generated_feature_policy.py` (policy/prompt markers);
5. `.github/workflows/intake.yml`;
6. `gitclaw.yaml`;
7. `policy/generated-features.md`;
8. `prompts/plan.yaml`;
9. `prompts/judge.yaml`;
10. `prompts/enforce.yaml`;
11. `prompts/review.yaml`; and
12. `README.md` reference-channel documentation.

No cron, composition, candidate extraction, containment, ledger, source
adapter, consumer feature, dependency, secret, or cadence change. Consumer
rollout is exact reviewed-file parity after separate human approval.

## Validation

Tests-first canonical validation must prove:

- `stage`: exact copy and manifest bytes/hash, Unicode round-trip, only the
  manifest hash on stdout; rejection of unknown/empty sets, slug violations,
  traversal, symlinks (file and parent), binaries/non-UTF-8, every count/size
  bound, pre-existing `reference/`, and untracked, locally modified, deleted,
  or ignored files (R-3); manifest records the checked-out commit SHA;
  atomic failure leaves no partial `reference/`;
- `verify`: rejection of manifest edit/replacement, per-file tamper, added and
  removed files, wrong hash, malformed JSON, and bounds;
- workflow: staging occurs after slug resolution and before graph run; the
  `Reference-set:` line is parsed exactly per the R-2 semantics and only from
  the issue body via `env:`; zero lines stage nothing and pass empty
  `reference_sha256`; two or more exact lines, or malformed names, fail before
  staging;
- graph: reference verification joins every FR-840 per-stage point, including
  the remediation lap; tamper between stages fails before transition;
- prompts/policy: mechanically checkable markers for reference authority,
  no-execution, capability non-escalation, declared-delta planning, and
  review's undeclared-divergence block;
- a synthetic end-to-end witness: staged two-file set, one file tampered after
  enforcement, run fails before review transition; and
- existing FR-840, ledger, containment, composition, candidate-output, and
  full canonical suites remain green.

## Human Gates

1. FR-840 must be enforced in canonical GitClaw and parity-rolled out to the
   consumer before FR-841 implementation starts (R-1).
2. Human approves the FR-841 judgement before implementation.
3. Human reviews the exact canonical diff and red/green evidence before
   canonical commit/push.
4. Human separately reviews the exact consumer parity diff and hashes before
   consumer commit/push.
5. Any reference set for Oulu (probe script transfer from control-plane) is a
   separate operator commit with its own redaction review; FR-841 does not
   authorize copying private control-plane content.

## Acceptance Criteria

- [ ] AC-01: Red tests prove the baseline has no reference channel and issues
      cannot select owner-committed assets
- [ ] AC-02: `stage` produces exact bounded manifest and prints only its hash
- [ ] AC-03: `verify` fail-closes every tamper/schema/path/bound violation
- [ ] AC-04: Workflow stages before the graph and passes only the manifest hash
- [ ] AC-05: Reference verification runs at every FR-840 per-stage point and
      remediation lap
- [ ] AC-06: Policy/prompts bind reference authority with no-execution and
      capability non-escalation markers
- [ ] AC-07: Planning must declare reference deltas; review blocks undeclared
      divergence
- [ ] AC-08: Issues without `Reference-set:` behave exactly as today
- [ ] AC-09: Tamper witness fails before the next transition
- [ ] AC-10: Focused and full canonical suites plus quality gates pass
- [ ] AC-11: Human approves the exact canonical diff before commit/push
- [ ] AC-12: Exact consumer parity with hashes, full suite, audit, and separate
      human approval
- [ ] AC-13: No forbidden platform or consumer behavior changes
- [ ] AC-14: FR records commits, tests, logs, hashes, gates, deviations, and
      failed attempts
- [ ] AC-15: FR-840 is enforced and parity-rolled out before implementation;
      FR-841 extends its concrete per-stage verification points and creates no
      parallel verification lifecycle
- [ ] AC-16: The staging manifest proves tracked-at-HEAD provenance (commit
      SHA, ordered paths, per-file hashes) and the R-2 parsing matrix is
      covered by exact tests

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Close its "port implementation later" gap with an actual transfer vehicle; transfer packet prose remains valid provenance evidence |
| FR-840 | Extend its per-stage verification points; do not alter request semantics, verdicts, or routing |
| FR-829 | Preserve untrusted-issue-prose and read-only policy; trust derives from owner-committed tracked files only |
| FR-830 | Preserve ledger semantics unchanged |
| FR-835 / FR-836 | Preserve composition and candidate contracts; references do not create a cross-feature read channel (copies are contained per feature) |
| FR-837 / FR-838 | Issues #5/#6 remain immutable evidence; any third attempt may use a reference set only after FR-838's separate gate |
| Private control-plane | No private content transfers under this FR; an Oulu reference set requires its own operator redaction review |

## Alternatives Rejected

- **Embed scripts in issue bodies:** couples trust to untrusted prose, invites
  instruction-smuggling, and bloats the contract this FR exists to shrink.
- **Let generated features read `references/` directly at runtime:** creates a
  shared mutable dependency across features; copying into the contained
  feature directory keeps ownership isolation and reproducibility.
- **Owner authors all code, GitClaw reviews only:** valid fallback, recorded as
  such, but it abandons the issue-to-feature pipeline instead of repairing its
  input channel.
- **Fold into FR-840:** bundling an input channel with the authority repair
  repeats FR-839's bundling mistake; each must be judgeable and revertible
  alone.

## Scope Fence

FR-841 authorizes one tests-first canonical reference-channel implementation
and one exact consumer parity rollout after separate gates. It authorizes no
consumer issue, no reference-set content decision, no private control-plane
transfer, no Task 6/7 work, and no cron/composition/candidate/containment/
ledger behavior, dependency, secret, notification, or publication change.
