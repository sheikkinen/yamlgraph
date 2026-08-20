# Judgement: FR-844 GitClaw Repository Instructions

**Verdict:** APPROVED — the proposal is a narrow, marker-tested repository instruction surface that restates already-governed GitClaw invariants, records the uncertain Copilot CLI injection claim as a witness instead of an assumption, and freezes a three-file implementation surface.

**Reviewed against:** `feature-requests/FR-844-gitclaw-repository-instructions.md`; `feature-requests/FR-839-gitclaw-immutable-owner-contract.md`; `feature-requests/FR-839-gitclaw-immutable-owner-contract.judgement.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.md`; `feature-requests/FR-840-gitclaw-minimal-authority-repair.judgement.md`; `feature-requests/FR-841-gitclaw-reference-assets.md`; `feature-requests/FR-842-lint-compile-validation-parity.md`; `feature-requests/FR-843-gitclaw-remediation-convergence.md`; `/Users/sami.j.p.heikkinen/src/gitclaw/policy/generated-features.md`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/plan.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/judge.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/review.yaml`; `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_generated_feature_policy.py`; `/Users/sami.j.p.heikkinen/src/gitclaw/README.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `reference/getting-started.md`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`.

## What is sound

The problem is real and correctly classified as GitClaw prompt-surface hardening, not YAMLGraph core. FR-844 identifies the first consumer and event as the next Copilot session inside a GitClaw repository (`feature-requests/FR-844-gitclaw-repository-instructions.md:25-27`), and the target file is currently absent in canonical GitClaw. The local doctrine treats instruction channels as external-input boundaries that must be governed, not trusted by default (`.github/copilot-instructions.md:63-85`).

Scope is clear and minimal. The FR authorizes exactly `.github/copilot-instructions.md`, `tests/test_generated_feature_policy.py`, and one README layout line (`feature-requests/FR-844-gitclaw-repository-instructions.md:78-87`). It explicitly forbids prompt, policy, graph, workflow, tool, dependency, and behavior changes (`feature-requests/FR-844-gitclaw-repository-instructions.md:85-87`, `:141-145`), satisfying the scope and single-responsibility criteria.

The proposed content restates existing GitClaw contracts rather than inventing new ones. The immutable request, untrusted-data, exact-APPROVED publication, and authority-artifact rules are already in policy (`/Users/sami.j.p.heikkinen/src/gitclaw/policy/generated-features.md:8-19`) and prompts (`/Users/sami.j.p.heikkinen/src/gitclaw/prompts/judge.yaml:9-32`, `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/enforce.yaml:7-19`, `/Users/sami.j.p.heikkinen/src/gitclaw/prompts/review.yaml:8-34`). The candidate-output rule is already policy and marker-tested (`/Users/sami.j.p.heikkinen/src/gitclaw/policy/generated-features.md:34-40`, `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_generated_feature_policy.py:89-97`). Reference assets, flat conditions, convergence, and model-pin conventions are likewise already documented or tested (`/Users/sami.j.p.heikkinen/src/gitclaw/README.md:75-99`, `/Users/sami.j.p.heikkinen/src/gitclaw/README.md:130-143`, `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_generated_feature_policy.py:145-162`).

Measurability is adequate. The FR requires marker tests for every invariant line (`feature-requests/FR-844-gitclaw-repository-instructions.md:91-98`, `:108-118`), a line-count and two-section limit (`:110-111`), an explicit consistency assertion that the file names no rule absent from prompts/policy (`:96-98`), full canonical validation (`:115-116`), and a witness proving or disproving non-interactive Copilot CLI injection (`:68-76`, `:113-114`). That witness design is especially important because the FR refuses to turn a platform assumption into authority without evidence.

Prior art is sufficiently dispositioned. FR-839's rejection warns against ungoverned shadow channels while preserving the immutable request core (`feature-requests/FR-839-gitclaw-immutable-owner-contract.judgement.md:90-93`); FR-840 enforced immutable authority artifacts and exact-APPROVED publication (`feature-requests/FR-840-gitclaw-minimal-authority-repair.md:263-292`); FR-842 confirms flat conditions are the supported grammar (`feature-requests/FR-842-lint-compile-validation-parity.md:30-42`, `:134-138`); and FR-843 makes one-lap remediation plus visible terminal behavior the current pipeline contract (`feature-requests/FR-843-gitclaw-remediation-convergence.md:29-35`, `:115-143`). FR-844 preserves those contracts instead of reopening them.

Strategic classification: **pattern documentation / governed prompt surface** for GitClaw. It has a named consumer and testable drift guard, but it does not create a new framework primitive or GitClaw runtime behavior.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `/Users/sami.j.p.heikkinen/src/gitclaw/.github/copilot-instructions.md` |
| D-2 | `/Users/sami.j.p.heikkinen/src/gitclaw/tests/test_generated_feature_policy.py` marker and consistency tests |
| D-3 | `/Users/sami.j.p.heikkinen/src/gitclaw/README.md` Layout-section line naming `.github/copilot-instructions.md` |
| D-4 | `feature-requests/FR-844-gitclaw-repository-instructions.md` enforcement record with commits, tests, injection witness path/result, deviations, and human gates |

Not authorized: changing GitClaw prompts, policy semantics, graph routing, workflows, tools, dependencies, model pins, cron, containment, ledger behavior, generated feature contracts, YAMLGraph core, vendored skills, or consumer repositories; adding new rules not already present in prompts/policy; moving any stage authority out of the four stage prompts; removing or weakening existing marker tests; claiming Copilot CLI non-interactive injection authority unless the witness proves it.

## Revised acceptance criteria

- [ ] AC-01: Red evidence shows the baseline lacks `.github/copilot-instructions.md` and that the new marker tests fail before the file is added.
- [ ] AC-02: `.github/copilot-instructions.md` is no more than 60 lines, has exactly the two planned sections, and is stage-neutral.
- [ ] AC-03: Every invariant line in `.github/copilot-instructions.md` has a matching marker test in `tests/test_generated_feature_policy.py`.
- [ ] AC-04: A consistency assertion proves every verdict, state key, artifact, and rule named in `.github/copilot-instructions.md` already appears in the four prompts, `policy/generated-features.md`, or README documentation governed by prior FRs.
- [ ] AC-05: The file restates only existing prompt/policy contracts: immutable `request.json`/`FR.md`/`judgement.md` ownership, exact non-empty `state_key: candidate`, issue/reference content as data with provenance, artifact-file verdict reads, exact review `APPROVED` publication, no hand-editing generated features, flat `gitclaw.yaml` conditions, local `tmp/` evidence, and human review for enforcement infrastructure.
- [ ] AC-06: The injection witness records, with an evidence path, whether Copilot CLI non-interactive runs inside canonical GitClaw apply `.github/copilot-instructions.md`; if not, the FR records the file as contributor/adopter documentation rather than pipeline authority.
- [ ] AC-07: Focused marker tests, full canonical suite, and lint pass without changing any file outside the frozen surface.
- [ ] AC-08: Human approves the exact canonical diff before push because `.github/copilot-instructions.md` is an instruction/prompt surface and enforcement infrastructure.
- [ ] AC-09: FR-844 records commits, test counts, witness result, evidence paths, human gates, deviations, and failed attempts.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Implement tests first; preserve red evidence before adding `.github/copilot-instructions.md`. | GATE |
| C-2 | Every instruction line must be traceable to an already-existing prompt, policy, or README contract; any untraceable desired rule requires a separate FR, not this file. | GATE |
| C-3 | If the Copilot CLI witness does not prove non-interactive injection, do not describe the file as a binding pipeline-stage authority in README or the FR closure record. | GATE |
| C-4 | Human review of the exact diff is mandatory before push because this changes an instruction surface loaded by agents. | GATE |
| C-5 | Do not edit prompts, policy, graph, workflow, tools, dependencies, vendored skills, or consumer repositories under this FR. | GATE |

Authority granted: implement only the three-file canonical GitClaw repository-instructions surface, its marker/consistency tests, its README layout entry, and the recorded injection witness described above.
