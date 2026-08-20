# Judgement: FR-841 GitClaw Owner Reference Assets

**Verdict:** APPROVED WITH REVISIONS — the canonical-only reference channel is sound and correctly placed at the owner-input boundary, but authority activates only after the FR reserves the generated manifest path and moves `Reference-set:` selection into tested tool code rather than workflow prose. Both revisions were folded into the replanned FR on 2026-08-20; human publication gate pending.

**Prior art:** FR-840 (enforced canonically at `a7621f21`) is the verification substrate this FR extends. FR-829/830/835/836 boundaries are preserved. FR-831 supplies the unclosed "port implementation later" gap; FR-837/FR-838 preserve the #5/#6 drift evidence — the consumer repository itself was deleted by the owner on 2026-08-20, making FR-838's remaining consumer-recovery gates obsolete while its records remain evidence.

**Reviewed against:** `feature-requests/FR-841-gitclaw-reference-assets.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.judgement.md`; `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`; `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.judgement.md`; `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`; `feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`; `feature-requests/FR-835-gitclaw-composition-boundary.md`; `feature-requests/FR-836-gitclaw-candidate-output-contract.md`; `feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md`; `feature-requests/FR-837-gitclaw-oulu-source-health-assembly.judgement.md`; `feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md`; `feature-requests/FR-838-gitclaw-oulu-assembly-recovery.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The problem is real and correctly motivated by prior evidence. FR-831 promised reusable probe behavior but left later public issues with a prose-only transfer contract (`feature-requests/FR-841-gitclaw-reference-assets.md:13-18`), while FR-837/FR-838 preserve concrete drift witnesses where generated local authority diverged from the human-reviewed contract (`feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md:12-18`, `:45-60`). The proposal addresses that gap with an owner-committed input channel rather than another prompt-only instruction.

The architecture placement is right. Repository doctrine says to normalize external data at the boundary (`.github/copilot-instructions.md:49-52`), and FR-841 stages and hashes the selected reference set before any model stage (`feature-requests/FR-841-gitclaw-reference-assets.md:32-39`). It also preserves FR-829's untrusted issue-prose rule by treating the issue line as selection only and deriving trust from tracked repository files (`feature-requests/FR-841-gitclaw-reference-assets.md:41-46`, `:126-130`; `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md:21-32`).

The scope is single-responsibility and mostly minimal. The FR explicitly adds only the input channel, not a consumer issue, source adapter, composition behavior, or FR-840 semantic change (`feature-requests/FR-841-gitclaw-reference-assets.md:48-57`, `:150-168`, `:264-270`). The consumer-deletion replanning is consistent with FR-840's enforcement record: canonical FR-840 is published at `a7621f21`, while consumer parity was owner-waived (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:263-289`), so FR-841's canonical-only shape avoids relying on the deleted consumer.

The strategic classification is **framework primitive for GitClaw**, not YAMLGraph core. There are at least three durable use cases: transferring established probe behavior from owner-reviewed source, future fresh consumers inheriting the channel from the canonical template, and review comparing generated behavior against staged reference bytes instead of reinterpreted prose (`feature-requests/FR-841-gitclaw-reference-assets.md:25-28`, `:61-66`, `:131-140`). Existing abstractions cover immutable request bytes (FR-840) but not owner-supplied implementation bytes.

The validation plan is unusually strong: unit tests for staging and verification, workflow parsing and ordering, graph-stage tamper checks including remediation, prompt/policy markers, a synthetic end-to-end tamper witness, and existing suite preservation are all named mechanically (`feature-requests/FR-841-gitclaw-reference-assets.md:170-195`, `:208-237`). That satisfies measurability and testability once the two revisions below are folded.

## Required revisions

### R-1: Reserve the generated manifest path inside every reference set

Amend the Frozen Reference Contract, `tools/reference_assets.py` requirements, Validation, and Acceptance Criteria so a selected reference set containing a relative path exactly `manifest.json` is rejected before staging. FR-841 currently allows text files under `references/<set-name>/` (`feature-requests/FR-841-gitclaw-reference-assets.md:72-76`) and then writes the generated manifest to `features/<slug>/reference/manifest.json` after copying files (`feature-requests/FR-841-gitclaw-reference-assets.md:105-108`). Without a reserved-path rule, an owner-supplied reference file can collide with the generated integrity manifest, making the copy semantics ambiguous and leaving a source file either overwritten or unverifiable.

Add tests proving `references/<set>/manifest.json` fails atomically before any `features/<slug>/reference/` artifact is created, and proving `verify` rejects a staged tree where `manifest.json` is a copied reference payload rather than the generated manifest.

### R-2: Make `Reference-set:` selection a tested boundary function

Amend the Workflow side so `tools/reference_assets.py` owns the issue-body selection boundary, for example with `python -m tools.reference_assets select` reading the issue body from `ISSUE_BODY` in the environment, printing either the selected canonical set name or the empty string, and exiting nonzero for duplicate, malformed, unknown, or empty selections. The workflow may branch on that command's result, but it must not implement the full-line matching matrix as ad hoc shell parsing.

FR-841 defines exact selection semantics (`feature-requests/FR-841-gitclaw-reference-assets.md:78-91`) but lists only `stage` and `verify` as tool commands (`feature-requests/FR-841-gitclaw-reference-assets.md:93-98`). Because this is the untrusted-issue-prose boundary and repository doctrine prefers normalizing at the boundary over downstream symptom guards (`.github/copilot-instructions.md:49-52`, `:67-76`), the parser belongs in tested standard-library code. Add focused tests for zero lines, exactly one valid line, duplicate valid lines, malformed names, unknown sets, substrings, quoted prose, comments, front matter, and line-ending variants.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tools/reference_assets.py` with tested `select`, `stage`, and `verify` behavior |
| D-2 | `tests/test_reference_assets.py` covering selection, staging, manifest hashing, provenance, bounds, reserved-path, and tamper verification |
| D-3 | `tests/test_intake_tools.py` workflow and graph contract assertions |
| D-4 | `tests/test_generated_feature_policy.py` policy and prompt marker assertions |
| D-5 | `.github/workflows/intake.yml` staging after slug resolution and before graph run, passing only `reference_sha256` |
| D-6 | `gitclaw.yaml` state and FR-840 per-stage reference verification wiring |
| D-7 | `policy/generated-features.md` and `prompts/plan.yaml`, `prompts/judge.yaml`, `prompts/enforce.yaml`, `prompts/review.yaml` reference-authority updates |
| D-8 | `README.md` reference-channel and consent-restriction fallback documentation |

Not authorized: consumer repository creation, consumer rollout, consumer issue filing, Oulu reference-set content decisions, private control-plane content copying, source adapter changes, composition changes, candidate-output changes, containment changes, ledger changes, request-contract semantic changes, cron/cadence changes, dependency or secret changes, notification/publication behavior, Task 6/7 work, or a parallel verification lifecycle outside FR-840's concrete per-stage verification points.

## Revised acceptance criteria

- [ ] AC-01: Red tests prove the baseline has no reference channel and issues cannot select owner-committed assets.
- [ ] AC-02: `select` reads only the issue body from environment input, implements the exact full-line `Reference-set: <set-name>` matrix, prints only the selected set name or empty string, and fails before staging on duplicate, malformed, unknown, or empty selections.
- [ ] AC-03: `stage` produces exact copied bytes plus a bounded generated manifest, records commit SHA, ordered relative paths, and per-file SHA-256 values, and prints only the manifest hash.
- [ ] AC-04: `stage` rejects unknown/empty sets, slug violations, traversal, symlinks, non-regular files, binaries/non-UTF-8, every count/size bound, pre-existing `reference/`, symlinked parents, untracked/modified/deleted/ignored files, and reserved `manifest.json`.
- [ ] AC-05: Every staging failure is atomic and leaves no partial `features/<slug>/reference/` tree.
- [ ] AC-06: `verify` fail-closes on missing, edited, replaced, malformed, copied-payload, wrong-hash, wrong-commit, extra-file, missing-file, symlink, path, schema, and bound violations.
- [ ] AC-07: Workflow invokes selection and staging after slug resolution and before the graph run; issue body enters via `env:` only; zero selected lines stages nothing and passes empty `reference_sha256`.
- [ ] AC-08: Workflow passes only `reference_sha256` into graph state and never logs, shells, or graph-passes reference file contents or issue prose as authority beyond selection.
- [ ] AC-09: `gitclaw.yaml` carries `reference_sha256: str`; every FR-840 per-stage verification point, including remediation laps, also verifies the reference manifest when non-empty.
- [ ] AC-10: Missing or tampered reference bytes fail before the next transition; a synthetic two-file tamper witness fails before review.
- [ ] AC-11: Policy and prompts mark reference files as owner-committed prior implementation that may be read, quoted, derived, and ported, while remaining non-executable data that cannot escalate capabilities beyond `policy/generated-features.md`.
- [ ] AC-12: Planning must declare preserved reference behaviors and owner-request deltas; judgement and review must block undeclared or inconsistent divergence from the staged reference.
- [ ] AC-13: Issues without `Reference-set:` behave exactly as FR-840 alone.
- [ ] AC-14: Focused and full canonical suites plus quality gates pass.
- [ ] AC-15: Human approves the exact canonical diff, red/green evidence, hashes, gates, deviations, and failed attempts before canonical commit/push.
- [ ] AC-16: FR records implementation status and confirms FR-840 canonical commit `a7621f21` is the only verification substrate; no parallel lifecycle or consumer rollout is introduced.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 and R-2 into FR-841 before implementation authority activates. | GATE |
| C-2 | FR-840 canonical per-stage verification at `a7621f21` remains the substrate; do not replace or fork its lifecycle. | GATE |
| C-3 | Reference selection must be computed by tested standard-library code, not by an untested shell parsing contract. | GATE |
| C-4 | A reference set containing `manifest.json` must fail before staging; the generated manifest path is reserved. | GATE |
| C-5 | Reference files are data only: never execute them during intake, planning, judgement, enforcement, review, tests, or documentation generation. | GATE |
| C-6 | Any reference script requiring forbidden credentials, authenticated access, external mutation, dependency changes, workflow changes, or out-of-feature access must be flagged and rejected, not ported. | GATE |
| C-7 | Enforcement-infrastructure diffs touching workflow, graph routing, prompts, policy, or reference-contract tooling require human review before push. | GATE |
| C-8 | No consumer repository, Oulu issue, private content transfer, or reference-set content decision is authorized by this FR. | GATE |

Authority granted: after R-1 and R-2 are folded into the FR, implement only the canonical GitClaw owner-reference input channel that selects one owner-committed reference set, stages immutable contained bytes with a reserved generated manifest, verifies that manifest at FR-840's existing per-stage gates, and binds prompts/policy to adapt references without executing them or broadening platform capabilities.
