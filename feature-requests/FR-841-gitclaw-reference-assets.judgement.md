# Judgement: FR-841 GitClaw Owner Reference Assets

**Verdict:** APPROVED WITH REVISIONS — the reference-channel direction is sound, but authority activates only after R-1 through R-3 are folded into the FR and FR-840 is enforced as the prerequisite verification substrate. R-1 through R-3 were folded into the FR on 2026-08-20; human publication gate pending.

**Reviewed against:** `feature-requests/FR-841-gitclaw-reference-assets.md`; cited precedents `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`, `feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`, `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`, `feature-requests/FR-835-gitclaw-composition-boundary.md`, `feature-requests/FR-836-gitclaw-candidate-output-contract.md`, `feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md`, `feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md`, and `feature-requests/FR-840-gitclaw-minimal-authority-repair.md`; judge doctrine `.github/skills/judge-fr/doctrine.md`; judgement template `.github/skills/judge-fr/judgement.template.md`; repo doctrine `reference/getting-started.md` and `ARCHITECTURE.md`.

## What is sound

FR-841 identifies a real failure mode: FR-831 left working probes as "Reuse contract; port implementation later" evidence, and FR-841 records that issues #5 and #6 drifted at clauses existing scripts had already encoded (`feature-requests/FR-841-gitclaw-reference-assets.md:11-19`). The proposed channel is narrower than embedding scripts in issue bodies because trust derives from owner-committed files while issue prose only selects a set (`feature-requests/FR-841-gitclaw-reference-assets.md:26-40`, `:216-220`).

The stage/verify split is architecturally aligned with FR-840's immutable request artifact: it copies bounded text into the contained feature directory, records per-file hashes, and verifies before model-stage transitions (`feature-requests/FR-841-gitclaw-reference-assets.md:72-95`). The policy contract preserves FR-829's no-execution and capability non-escalation boundary by treating references as data, not runtime authority (`feature-requests/FR-841-gitclaw-reference-assets.md:96-114`; `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md:122-140`).

The proposal is a single platform concern, not a consumer feature: it explicitly excludes source adapters, composition, candidate extraction, ledger behavior, private control-plane transfer, and downstream issue filing (`feature-requests/FR-841-gitclaw-reference-assets.md:42-43`, `:139-141`, `:228-234`). Strategic classification: **framework primitive for GitClaw**, because the same reference channel would serve the next Oulu source/composer issue and any later owner-committed prior implementation, while existing prose transfer has already failed twice.

## Required revisions

### R-1: Make FR-840 enforcement a hard prerequisite

Fold a hard prerequisite into `Depends on`, `Human Gates`, `Acceptance Criteria`, and `Conditions for enforcement`: FR-841 implementation may not start until FR-840 is judged, enforced in canonical GitClaw, rolled out to the consumer with exact reviewed parity, and its per-stage `request_contract verify` points exist. FR-841 may then extend those concrete verification points; it must not implement a parallel or replacement verification lifecycle. Cite the FR-840 evidence that request verification is the substrate (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:121-141`, `:211-219`).

### R-2: Specify exact `Reference-set:` parsing failure semantics

Amend the frozen reference contract and validation so parsing is mechanically testable: zero exact `Reference-set: <set-name>` lines means no reference and empty `reference_sha256`; exactly one valid line selects the set; two or more exact lines fail before staging; malformed names fail before staging; matches are full-line only from the issue body passed via `env:`; comments, labels, front matter, quoted prose, and substrings do not select a set. This folds the current "at most one set" rule into testable behavior (`feature-requests/FR-841-gitclaw-reference-assets.md:64-70`, `:154-157`).

### R-3: Define the owner-committed tracked-file proof

Amend `tools/reference_assets.py stage` to prove every staged byte comes from committed repository content, not an untracked or locally modified checkout file. The foldable contract is: enumerate the selected set from Git-tracked regular files under `references/<set-name>/` at the checked-out HEAD, reject untracked files, modified tracked files, deleted tracked files, ignored files, symlinks, non-regular files, and path escapes, and include the checked-out commit SHA plus ordered relative paths and per-file SHA-256 values in `manifest.json`. This makes the trust claim in the summary mechanically true (`feature-requests/FR-841-gitclaw-reference-assets.md:26-40`, `:58-63`, `:147-151`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tools/reference_assets.py` with `stage` and `verify` commands |
| D-2 | `tests/test_reference_assets.py` |
| D-3 | `tests/test_intake_tools.py` graph/workflow contract assertions |
| D-4 | `tests/test_generated_feature_policy.py` policy and prompt marker assertions |
| D-5 | `.github/workflows/intake.yml` reference staging and hash handoff |
| D-6 | `gitclaw.yaml` state and per-stage reference verification integration |
| D-7 | `policy/generated-features.md` reference authority, no-execution, and capability non-escalation policy |
| D-8 | `prompts/plan.yaml`, `prompts/judge.yaml`, `prompts/enforce.yaml`, and `prompts/review.yaml` minimal reference-channel duties |
| D-9 | `README.md` reference-channel and consent-restriction fallback documentation |
| D-10 | Exact consumer parity rollout of only the reviewed canonical platform files after separate human approval |

Not authorized: any consumer issue; any Oulu reference-set content decision; any private control-plane content transfer; source adapter, composition, candidate-output, containment, ledger, cron, dependency, secret, notification, publication, Task 6, or Task 7 behavior changes; executing reference files during the pipeline; broadening generated-feature capabilities beyond `policy/generated-features.md`; changing FR-840 request semantics, verdict vocabulary, or routing beyond adding reference-manifest verification to its concrete verification points.

## Revised acceptance criteria

- [ ] AC-01: FR-840 is judged, enforced, and parity-rolled out first; FR-841 extends its concrete per-stage verification points and does not create a parallel authority mechanism.
- [ ] AC-02: Red tests prove the baseline has no reference channel and issues cannot select owner-committed assets.
- [ ] AC-03: `stage` rejects absent, unknown, empty, malformed, multi-line, untracked, modified, deleted, ignored, symlinked, non-regular, non-UTF-8, binary, escaping, oversized, over-count, and pre-existing `reference/` cases before any model stage.
- [ ] AC-04: `stage` copies only committed tracked UTF-8 regular files from `references/<set-name>/`, writes canonical `manifest.json` containing version, set name, checked-out commit SHA, ordered relative paths, and per-file SHA-256 values, and prints only the manifest SHA-256.
- [ ] AC-05: `stage` failure is atomic and leaves no partial `features/<slug>/reference/`.
- [ ] AC-06: `verify` fail-closes on missing, edited, replaced, malformed, oversized, wrong-hash, wrong-commit, extra-file, missing-file, symlink, non-regular, path, schema, and bound violations.
- [ ] AC-07: Workflow resolves the feature slug, writes/verifies FR-840 `request.json`, parses `Reference-set:` exactly from issue body via `env:`, stages before graph run, and passes only `reference_sha256` into graph state.
- [ ] AC-08: Issues with no exact `Reference-set:` line behave exactly as the FR-840 pipeline after AC-01, with empty `reference_sha256` and no `reference/` directory.
- [ ] AC-09: Reference verification runs at every FR-840 per-stage verification point, including the remediation lap, and tamper between stages fails before the next transition.
- [ ] AC-10: Policy and prompts mechanically bind reference authority, no execution, capability non-escalation, declared-delta planning, judgement reference consistency, enforcement no-modify, and review undeclared-divergence blocking.
- [ ] AC-11: A synthetic end-to-end witness stages a two-file reference set, tampers with one staged file after enforcement, and fails before the review transition.
- [ ] AC-12: Focused reference, workflow, prompt-policy, FR-840, ledger, containment, composition, candidate-output, full canonical, and quality-gate suites pass.
- [ ] AC-13: Human approves the exact canonical diff, red/green evidence, and audit before canonical commit/push.
- [ ] AC-14: Exact consumer parity rollout records hashes, full suite, audit, and separate human approval before any consumer issue uses the channel.
- [ ] AC-15: No forbidden platform, consumer, private-content, source, composition, candidate, ledger, containment, cron, dependency, secret, notification, publication, Task 6, or Task 7 change occurs.
- [ ] AC-16: FR-841 records commits, tests, logs, hashes, human gates, deviations, and failed attempts before any third FR-837 consumer attempt.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-3 must be folded into `feature-requests/FR-841-gitclaw-reference-assets.md` before implementation authority activates. | GATE |
| C-2 | FR-840 must be enforced and parity-rolled out first; FR-841 may only attach reference verification to those existing verified transitions. | GATE |
| C-3 | All owner-request and reference text remains untrusted data: references may be read, quoted, derived from, and ported, but never executed during the pipeline or used to grant forbidden capabilities. | GATE |
| C-4 | The enforcer must write red tests for parsing, trackedness, staging, verify tamper, workflow position, graph verification, and policy/prompt markers before production changes. | GATE |
| C-5 | Human review is mandatory for enforcement-infrastructure changes and for any consumer parity rollout. | GATE |

Authority granted: after the required revisions are folded and FR-840 is available as the enforced substrate, the enforcer may build exactly one tests-first GitClaw reference-assets channel and one exact reviewed consumer parity rollout within the frozen surfaces above.
