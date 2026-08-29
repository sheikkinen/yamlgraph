# Judgement: FR-918 CI Python Matrix Refresh (Floor + Ceiling Honesty)

**Verdict:** APPROVED WITH REVISIONS — the matrix/support-contract direction is sound, but implementation authority activates only after the FR reconciles its bracket policy wording, names the release build job update, preserves strict branch-protection verification, and updates stale dependency-governance documentation.

**Reviewed against:** `feature-requests/FR-918-ci-python-matrix-refresh.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/workflows/workflow.yml`; `.github/workflows/security.yml`; `pyproject.toml`; `CLAUDE.md`.

## What is sound

The FR correctly re-enters the pipeline as the matrix/support-claim half of the FR-917 split: FR-917 is marked split into FR-918 and FR-919 (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:5`), and the prior judgement required a matrix/support-claim FR with Python-version CI coverage and branch-protection migration (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:71-82`).

The problem is real. Current CI pins `core-test` to Python 3.12, tests only `['3.11', '3.12']`, and builds releases on 3.12 (`.github/workflows/workflow.yml:19-27`, `:44-46`, `:86-89`); the security workflow also pins 3.12 (`.github/workflows/security.yml:23-25`). Meanwhile `pyproject.toml` permits `>=3.11,<3.15` and advertises classifiers through 3.13 (`pyproject.toml:10-20`). The FR's 3.14 decision is also the honest R-2 option: narrow `requires-python` so untested 3.14 is not install-allowed (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:25-33`; `feature-requests/FR-918-ci-python-matrix-refresh.md:52-58`).

The branch-protection coupling and human-review gate are properly recognized. Repo doctrine records required contexts as `commitlint`, `test (3.11)`, and `test (3.12)`, with strict up-to-date enabled and admin pushes bypassing protection (`CLAUDE.md:387-403`); FR-918 names the operator/admin sequence and the need to record API verification (`feature-requests/FR-918-ci-python-matrix-refresh.md:84-104`). This is the right class of caution because judge doctrine treats CI and branch-protection changes as adversarial enforcement-infrastructure input requiring human review (`.github/skills/judge-fr/doctrine.md:97-100`; `.github/copilot-instructions.md:81-84`, `:233-236`).

Strategic classification: **pattern documentation / CI policy**, not a framework primitive. The implementation surface is repository enforcement infrastructure and packaging metadata; the right shape is a small policy refresh with explicit operator gates, not a new YAMLGraph abstraction.

## Required revisions

### R-1: Replace exact-set support language with the chosen floor-plus-ceiling bracket policy

Revise the Summary, Value Statement, Ideal Result, and acceptance criteria so they do not claim that every supported interpreter is directly exercised by CI. The current text says "Every interpreter version the package claims to support is exercised by CI" and "the declared support contract and the tested set are the same set" (`feature-requests/FR-918-ci-python-matrix-refresh.md:18-27`, `:44-49`), but the same FR intentionally keeps Python 3.12 classified and supported while removing its dedicated CI leg (`feature-requests/FR-918-ci-python-matrix-refresh.md:70-72`) and rejects a three-leg matrix (`feature-requests/FR-918-ci-python-matrix-refresh.md:141`).

The foldable revision is: state that CI directly tests the floor and ceiling of the declared supported range, that classified intermediate versions are supported by bracket policy rather than by per-minor CI legs, and that no install-allowed interpreter may sit outside the tested bracket. Do not add a 3.12 leg under this FR unless the FR is returned for re-judgement with the cost/scope rationale changed.

### R-2: Add the release `build` Python update to the explicit implementation plan

Add `.github/workflows/workflow.yml` release `build` job Python `3.12` -> `3.13` to the Proposed Solution and acceptance criteria. FR-918's own version-to-job mapping requires `build` on 3.13 (`feature-requests/FR-918-ci-python-matrix-refresh.md:60-68`), and the workflow currently sets the tag-release build job to 3.12 (`.github/workflows/workflow.yml:70-89`), but the Proposed Solution lists only `test`, `core-test`, `security.yml`, `pyproject.toml`, `CLAUDE.md`, changelog, and diary (`feature-requests/FR-918-ci-python-matrix-refresh.md:74-82`). The acceptance criteria repeat the same omission (`feature-requests/FR-918-ci-python-matrix-refresh.md:113-132`).

### R-3: Preserve and verify strict branch protection, not only required contexts

Revise the branch-protection migration to preserve the strict up-to-date setting and record it alongside contexts. The FR relies on the strict up-to-date rule to force stale automation PRs to update with `main` (`feature-requests/FR-918-ci-python-matrix-refresh.md:100-104`), and repo doctrine records that rule as enabled (`CLAUDE.md:401-403`), but the proposed verification command records only `.contexts` (`feature-requests/FR-918-ci-python-matrix-refresh.md:92-97`).

The foldable revision is: either include strict preservation explicitly in the PATCH procedure or perform a read-modify-write that preserves the existing strict value, then record verification output containing both `strict` and `contexts` in the FR implementation status.

### R-4: Update dependency-governance documentation for the unchanged py312 constraints artifact

Add a CLAUDE.md documentation update for the `constraints/dev-py312.txt` section, or explicitly list that section as a scoped documentation surface. FR-918 says the py312 constraints artifact remains unchanged and py313 regeneration is a follow-up (`feature-requests/FR-918-ci-python-matrix-refresh.md:64-68`), but CLAUDE.md currently says `constraints/dev-py312.txt` pins the environment CI tests against and that Python 3.12 matches CI (`CLAUDE.md:60-72`). After FR-918, CI's single-version jobs move to 3.13 and the matrix moves to 3.11/3.13, so that text would become a stale support/documentation claim unless corrected.

The foldable revision is: keep `constraints/dev-py312.txt` unchanged, but update the surrounding prose to say it remains the FR-761 Python 3.12 reproducibility artifact and that regenerating an equivalent Python 3.13 constraints artifact is out of scope/follow-up.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revisions to `feature-requests/FR-918-ci-python-matrix-refresh.md` satisfying R-1 through R-4 |
| D-2 | `.github/workflows/workflow.yml`: `test` matrix, `core-test`, and tag-release `build` Python version only |
| D-3 | `.github/workflows/security.yml`: setup-python version only |
| D-4 | `pyproject.toml`: `requires-python` bound only; classifiers remain 3.11/3.12/3.13 |
| D-5 | `CLAUDE.md`: Branch Protection table and dependency-governance prose directly affected by the matrix refresh |
| D-6 | Operator branch-protection migration: required contexts and strict verification only |
| D-7 | Changelog fragment and diary reflection |
| D-8 | FR implementation-status evidence: branch-protection GET output and first post-merge PR witness link |

Not authorized: Python 3.14 support, `<3.15` restoration, adding a 3.14 CI leg, adding a 3.12 matrix leg, raising or dropping the 3.11 floor, regenerating or renaming `constraints/dev-py312.txt`, doc-only skip logic, workflow path filters, release/publish/create-release behavior changes beyond the build Python version, or any branch-protection mutation outside preserving strict and replacing `test (3.12)` with `test (3.13)`.

## Revised acceptance criteria

- [ ] AC-01: FR-918 text states a floor-plus-ceiling CI bracket policy, not "every supported interpreter is directly exercised"; Python 3.12 remains classified/supportable only as an intermediate version inside the tested bracket.
- [ ] AC-02: `.github/workflows/workflow.yml` `test` matrix is exactly `['3.11', '3.13']`.
- [ ] AC-03: `.github/workflows/workflow.yml` `core-test` setup-python version is `3.13`.
- [ ] AC-04: `.github/workflows/workflow.yml` tag-release `build` setup-python version is `3.13`.
- [ ] AC-05: `.github/workflows/security.yml` setup-python version is `3.13`.
- [ ] AC-06: `pyproject.toml` has `requires-python = ">=3.11,<3.14"` and unchanged classifiers for 3.11, 3.12, and 3.13.
- [ ] AC-07: Python 3.14 is explicitly unsupported until a follow-up FR adds a green 3.14 CI leg and verifies dependency wheels; no `<3.15` install claim remains.
- [ ] AC-08: The version-to-job mapping table in FR-918 matches the workflow files byte-for-byte, including the release `build` job.
- [ ] AC-09: `CLAUDE.md` Branch Protection table lists required contexts as `commitlint`, `test (3.11)`, and `test (3.13)`.
- [ ] AC-10: `CLAUDE.md` dependency-governance prose no longer says the py312 constraints artifact matches the current CI Python version; it records the artifact as unchanged and py313 constraints regeneration as out of scope/follow-up.
- [ ] AC-11: Required status checks are migrated by the operator to `commitlint`, `test (3.11)`, and `test (3.13)` while preserving strict up-to-date behavior; FR implementation status records verification output containing both `strict` and `contexts`.
- [ ] AC-12: First post-merge PR witness shows green `test (3.11)` and `test (3.13)` checks; run link is cited in FR implementation status.
- [ ] AC-13: Operator explicitly reviews the workflow diff and executes the branch-protection PATCH; the FR records that human review gate.
- [ ] AC-14: Changelog fragment and diary reflection are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement beyond FR edits until R-1 through R-4 are folded into FR-918. | GATE |
| C-2 | Treat all workflow and branch-protection edits as enforcement-infrastructure changes requiring explicit operator review. | GATE |
| C-3 | Do not allow or claim Python 3.14 support in this FR; a `<3.15` restoration or 3.14 CI leg requires a follow-up judged FR. | GATE |
| C-4 | Do not change branch protection beyond preserving strict and replacing required `test (3.12)` with `test (3.13)`; verification must record both strict and contexts. | GATE |
| C-5 | Do not regenerate, rename, or replace `constraints/dev-py312.txt`; only documentation around its status is authorized here. | GATE |
| C-6 | Do not implement doc-only skip behavior, workflow path filters, or release-job gating changes under FR-918. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-918, enforcement may implement the Python matrix/support-contract refresh across the frozen surfaces above and the operator may perform the recorded branch-protection migration.
