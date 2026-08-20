# Judgement: FR-840 GitClaw Minimal Authority Repair

**Verdict:** APPROVED WITH REVISIONS - authority activates only after FR-840 explicitly wires review `APPROVED WITH REVISIONS` findings into the next enforcement pass; the immutable owner-request repair is otherwise scoped, evidenced, and mechanically testable. R-1 was folded into the FR on 2026-08-20; human publication gate pending.

**Prior art:** FR-839 (rejected) is the direct predecessor; FR-840 carries its mechanical core and discards the verdict-vocabulary removal per its rejection record. FR-829/830/835/836/838 boundaries are preserved unchanged. Name-match hits FR-795 (schema-dialect repair) and FR-825 (KTweb encoding repair) share only the word "repair" and are unrelated surfaces; no disposition beyond noting the non-overlap.

**Reviewed against:** `feature-requests/FR-840-gitclaw-minimal-authority-repair.md`; `feature-requests/FR-839-gitclaw-immutable-owner-contract.md`; `feature-requests/FR-839-gitclaw-immutable-owner-contract.judgement.md`; `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`; `feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`; `feature-requests/FR-835-gitclaw-composition-boundary.md`; `feature-requests/FR-836-gitclaw-candidate-output-contract.md`; `feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md`; `/Users/sami.j.p.heikkinen/src/gitclaw/.github/workflows/intake.yml`; `/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/policy/generated-features.md`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/plan.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/judge.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/review.yaml`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The problem is real, repeated, and correctly classified as a GitClaw framework primitive rather than YAMLGraph core. FR-840 cites two authority-drift witnesses where the judge and review compared only generated downstream artifacts after the owner request had been rewritten (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:11-20`, `:62-66`). FR-839's rejection record confirms the same root cause while explicitly forbidding the overcorrection that removed `APPROVED WITH REVISIONS` (`feature-requests/FR-839-gitclaw-immutable-owner-contract.judgement.md:3-7`, `:90-93`). This satisfies the doctrine's strategic-classification and prior-art-disposition requirements.

The repair is placed at the correct boundary. Repository doctrine says to normalize at external-input boundaries (`.github/copilot-instructions.md:50-64`), and FR-840 creates a workflow-written `request.json` before any model stage, passes only its SHA-256 through graph state, and verifies exact bytes after plan, judgement, enforcement, and review (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:30-43`, `:121-132`). This is a smaller and stronger repair than adding another model pass to police model drift.

The FR is consistent with current baseline evidence. Current intake still passes `issue_title` and `issue_body` as graph variables (`/Users/sami.j.p.heikkinen/src/gitclaw/.github/workflows/intake.yml:80-95`); the graph state still includes those fields (`/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml:8-13`); plan is the only stage that receives them (`/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml:166-179`); judge reads only `features/{feature_name}/FR.md` (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/judge.yaml:8-13`); enforcement currently folds `APPROVED WITH REVISIONS` into `FR.md` (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml:7-13`); review compares only `FR.md` and `judgement.md` (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/review.yaml:8-14`); and review `APPROVED WITH REVISIONS` currently routes to containment and push (`/Users/sami.j.p.heikkinen/src/gitclaw/gitclaw.yaml:340-347`). The proposed tests target those exact seams (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:183-209`, `:223-246`).

Scope is mostly minimal. FR-840 keeps the three-verdict vocabulary (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:38-43`, `:73-80`), forbids consumer issue repair and Task 7 work (`:45-47`, `:273-279`), preserves FR-829/830/835/836 contracts (`:248-257`), and names a finite canonical change surface (`:163-181`). Its acceptance criteria are largely mechanically checkable through file content, graph routing assertions, request-contract unit tests, workflow inspection, tamper witnesses, and full-suite validation.

## Required revisions

### R-1: Specify how review revisions are consumed on the remediation lap

Amend FR-840's Authority Contract, Workflow and Graph Gates, Validation, and Acceptance Criteria so a review verdict of `APPROVED WITH REVISIONS` is not merely routed away from push but is also actionable by the next enforcement pass. The folded FR must require the remediation-lap enforcement prompt to read `features/<slug>/review.md` when the prior review verdict was `APPROVED WITH REVISIONS` or `REJECTED`, treat review findings as additive implementation constraints, preserve the ban on editing `request.json`, `FR.md`, and `judgement.md`, and return to independent review before any containment or push.

Add a mechanical test requirement proving that a synthetic review `APPROVED WITH REVISIONS` finding changes the next enforcement inputs and cannot publish until a subsequent exact `APPROVED` review. Current FR-840 routes review revisions to the existing rejected remediation edge (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:41-43`, `:136-141`, `:235-236`), but the current enforce prompt only names `FR.md` and `judgement.md` (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml:7-13`). Without this revision, review revisions can be withheld from the very stage expected to repair them.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tools/request_contract.py` writer/verifier and `tests/test_request_contract.py` |
| D-2 | `.github/workflows/intake.yml` request creation after slug resolution and safe hash-only graph invocation |
| D-3 | `gitclaw.yaml` state, request verification nodes after plan/judge/enforce/review, retry/remediation routing, and exact push gate |
| D-4 | `policy/generated-features.md` and `prompts/plan.yaml`, `prompts/judge.yaml`, `prompts/enforce.yaml`, `prompts/review.yaml` authority-boundary updates |
| D-5 | `tests/test_intake_tools.py` and `tests/test_generated_feature_policy.py` graph/workflow/prompt/policy assertions |
| D-6 | `README.md` pipeline/authority documentation |
| D-7 | Human-reviewed exact canonical diff and separately approved exact consumer parity rollout |

Not authorized: removing or renaming the `APPROVED WITH REVISIONS` verdict; changing human FR judgement doctrine; repairing, deleting, renaming, or retrying issue #5 or issue #6 artifacts; filing a third Task 6 issue; implementing Task 7; changing cron, composition, candidate extraction, containment behavior, ledger implementation, source adapters, dependencies, secrets, cadence, notifications, publication semantics, YAMLGraph core, or any consumer behavior except exact reviewed canonical parity after separate human approval.

## Revised acceptance criteria

- [ ] AC-01: Red tests reproduce the current missing immutable request evidence, enforce fold-into-FR instruction, and review-with-revisions publishing on the canonical baseline.
- [ ] AC-02: `tools/request_contract.py write` creates exact bounded canonical UTF-8 JSON from `GITCLAW_REPOSITORY`, `ISSUE_TITLE`, and `ISSUE_BODY`; rejects invalid env/schema/slug/size/symlink/pre-existing/NUL cases; writes atomically; and prints only the lowercase SHA-256 of exact file bytes.
- [ ] AC-03: `tools.request_contract verify` fail-closes on every integrity, schema, path, type, duplicate/unknown/missing key, symlink, nonregular-file, size, malformed JSON, wrong hash, byte modification, replacement, and feature/path incoherence violation.
- [ ] AC-04: Intake writes `request.json` after slug resolution and before `yamlgraph graph run`; passes only `request_sha256` as a graph variable; and never shell-interpolates or logs owner title/body.
- [ ] AC-05: `gitclaw.yaml` removes owner title/body from graph state, carries `request_sha256`, and verifies the request after every model stage and every retry before the next ledger transition, verdict read, containment, or push.
- [ ] AC-06: Judge and review retain `APPROVED`, `APPROVED WITH REVISIONS`, and `REJECTED`; prompts and policy define any owner-semantics contradiction as `REJECTED`.
- [ ] AC-07: Enforcement implements `FR.md` plus judgement revisions as additive constraints without editing `request.json`, `FR.md`, or `judgement.md`.
- [ ] AC-08: Remediation-lap enforcement reads `review.md` after review `APPROVED WITH REVISIONS` or `REJECTED`, treats review findings as additive implementation constraints, and returns to review before containment.
- [ ] AC-09: Review `APPROVED WITH REVISIONS` reaches `ledger_reviewed_rejected -> enforce -> review`, never `contain`; exact review `APPROVED` remains the only route to containment and push; final rejection still closes after the existing enforce loop limit.
- [ ] AC-10: Prompt/policy marker tests prove enforce contains no fold-into-FR instruction, all stages name `request.json` as binding owner evidence at their appropriate input boundary, and no prompt test claims semantic certainty beyond mechanically checkable markers.
- [ ] AC-11: An issue-#6-shaped fixture where owner input requires rejection but FR/judgement/review attempts fallback success is rejected before publication.
- [ ] AC-12: A synthetic tamper witness modifying `request.json` between stages fails verification before the next transition.
- [ ] AC-13: Existing ledger, containment, composition, candidate-output, focused canonical, full canonical, and quality-gate suites pass.
- [ ] AC-14: Human approves the folded FR-840 judgement before implementation and separately approves the exact canonical diff, red/green evidence, consumer parity diff, hashes, full suite, and audit before any canonical or consumer push.
- [ ] AC-15: FR-840 records commits, test counts, logs, hashes, gates, deviations, failed attempts, and confirms no forbidden platform or consumer behavior changes before any third Task 6 issue.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 into FR-840 before implementation authority activates. | GATE |
| C-2 | Commit or otherwise preserve RED evidence before runtime, workflow, graph, or prompt changes. | GATE |
| C-3 | Missing, malformed, tampered, oversized, symlinked, replaced, or hash-mismatched `request.json` must fail before transition; no fallback may substitute owner evidence. | GATE |
| C-4 | Owner title/body may appear only in canonical `request.json` and model-readable file content; they must not be passed as graph variables, shell arguments, stdout, or logs. | GATE |
| C-5 | Enforcement must never edit `request.json`, `FR.md`, or `judgement.md`; review remediation must be conveyed through `review.md` and another enforcement/review cycle. | GATE |
| C-6 | Enforcement-infrastructure diffs touching workflow, graph routing, prompts, policy, and request-contract tooling require human review before push. | GATE |
| C-7 | Consumer rollout is exact parity only, with SHA-256 equality and separate human approval. | GATE |

Authority granted: after R-1 is folded into the FR, implement only the minimal GitClaw authority-boundary repair that creates immutable owner-request evidence, verifies it after each model stage and remediation pass, preserves the three-verdict vocabulary, routes review revisions through enforce/review instead of push, and forbids mutation of the authority artifacts.
