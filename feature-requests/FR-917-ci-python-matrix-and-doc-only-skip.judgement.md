# Judgement: FR-917 CI Python Matrix Refresh + Doc-Only PR Test Skip

**Prior art:** the hits (FR-918, FR-919 and their judgements) are this judgement's own split children per D-1/D-2 — lineage, not competing precedent.

**Verdict:** SPLIT — the stale Python matrix and doc-only PR skip are both real CI problems, but the FR explicitly bundles separate concerns and the skip design needs its own release/protection edge-case proof before implementation authority exists.

**Reviewed against:** `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/workflows/workflow.yml`; `.github/workflows/security.yml`; `pyproject.toml`; `constraints/dev-py312.txt`; `CLAUDE.md`; `.github/copilot-instructions.md`.

## What is sound

The FR identifies a real enforcement gap: the current `test` matrix is `['3.11', '3.12']` while `pyproject.toml` declares Python `>=3.11,<3.15` and classifiers through Python 3.13 (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:31-34`; `.github/workflows/workflow.yml:42-53`; `pyproject.toml:10-20`). Keeping 3.11 as the floor is also sound because raising the floor would be a separate support-contract change (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:63-65`).

The doc-only cost problem is likewise real: the workflow runs on every PR and currently has no path-aware gate before `core-test` or the matrix job (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:36-39`; `.github/workflows/workflow.yml:3-67`). The FR correctly rejects workflow-level `paths-ignore` for required checks and prefers job-level skips that produce check conclusions branch protection can accept (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:74-78`, `:144`).

The branch-protection coupling is correctly named. Repo doctrine records required contexts as `commitlint`, `test (3.11)`, and `test (3.12)` (`CLAUDE.md:397-407`), and the FR recognizes that changing the matrix without updating required contexts can leave PRs waiting on orphaned checks (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:40-43`).

Strategic classification: **pattern documentation / CI policy**, not a framework primitive. The implementation surface is repository enforcement infrastructure, so it must remain small, explicit, and human-reviewed; judge doctrine requires adversarial treatment for CI/hook/doctrine changes (`.github/skills/judge-fr/doctrine.md:98-100`).

## Required revisions

### R-1: Split the bundle into two judged FRs

Create one FR for **Python matrix/support-claim refresh** and one FR for **doc-only expensive-job skipping**. The current FR states the problems are separate (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:16-21`) and names two first events (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:8-11`). Judge doctrine requires SPLIT when orthogonal concerns are bundled (`.github/skills/judge-fr/doctrine.md:49-50`, `:75-77`).

The matrix FR may include only interpreter-version changes, support-metadata honesty, CI/docs updates needed to keep branch protection coherent, changelog, diary, and the required human/admin protection update. The doc-only skip FR may include only path classification, job-level skip wiring, required-check behavior proof, changelog, and diary.

### R-2: Resolve the Python 3.14 support-claim contradiction in the matrix FR

The FR says 3.13 is the newest interpreter the package claims to support while also citing `requires-python = ">=3.11,<3.15"` and noting that Python 3.14 is stable (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:16-18`, `:31-33`, `:66-68`; `pyproject.toml:10`). The revised matrix FR must choose one honest contract:

1. test and classify the highest allowed interpreter, or
2. narrow `requires-python` so untested 3.14 is not install-allowed, or
3. explicitly define the CI policy as "floor plus newest classified interpreter" and justify why `requires-python <3.15` remains an allowed but non-classified compatibility envelope.

This must be an explicit acceptance criterion, not rationale hidden in prose.

### R-3: Make branch-protection migration mechanically safe in the matrix FR

The proposed post-merge command updates required contexts from `test (3.12)` to `test (3.13)` (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:117-123`), but a PR whose workflow no longer emits `test (3.12)` can be blocked before merge by the existing required context (`CLAUDE.md:397-407`). The revised matrix FR must specify the actual sequence: pre-merge protection update, admin direct push, temporary overlap of old/new contexts, or another explicit human/admin procedure. The procedure must say which actor performs it, when, and how the API result is recorded.

### R-4: Specify skip behavior separately for `workflow.yml`, `security.yml`, and tag releases

The doc-only skip proposal adds a `changes` job only to `workflow.yml` but also says `security.yml` gets the same gate (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:80-108`, `:114-115`; `.github/workflows/security.yml:1-42`). The revised doc-only FR must define the independent `security.yml` gate, because jobs cannot depend on a job from another workflow.

It must also preserve tag-release behavior. `workflow.yml` runs on version tags and the release `build` job depends on `test` (`.github/workflows/workflow.yml:3-7`, `:69-96`); `security.yml` also runs on version tags (`.github/workflows/security.yml:1-7`). A doc-only PR optimization must not cause tag-push `test`, `build`, `publish`, `create-release`, or `security` to skip because no PR file diff is present.

### R-5: Make the path classifier testable without relying on prose

The revised doc-only FR must include a concrete changed-file fixture table covering at least:

| Changed files | Expected expensive jobs |
|---|---|
| `docs/diary/example.md` only | skipped |
| `feature-requests/FR-XXX-example.md` only | skipped |
| `changelog/unreleased/example.md` only | skipped |
| `README.md` only | skipped if root Markdown is intentionally doc-only; otherwise runs |
| `.github/workflows/workflow.yml` | runs |
| `prompts/example.yaml` | runs |
| `graphs/example.yaml` | runs |
| `capabilities/CAP-XXX-example.yaml` | runs |
| `docs/diary/example.md` + `yamlgraph/example.py` | runs |

The current prose says "only `*.md`, `docs/`, `changelog/`, `feature-requests/` count as docs" (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md:111-115`), but a gate needs named fixtures so enforcers can test the actual glob semantics.

### R-6: Add an explicit human-review gate for CI and branch-protection changes

Both split FRs must carry a GATE condition that CI workflow changes and repository branch-protection mutations require explicit human/operator review before merge or direct push. Judge doctrine treats enforcement-infrastructure changes as adversarial input (`.github/skills/judge-fr/doctrine.md:98-100`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New matrix/support-claim FR derived from FR-917 |
| D-2 | New doc-only skip FR derived from FR-917 |
| D-3 | Optional update to `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md` marking it split/superseded |

No implementation is authorized under the combined FR-917. Not authorized: editing `.github/workflows/workflow.yml`, `.github/workflows/security.yml`, `pyproject.toml`, `constraints/dev-py312.txt`, `CLAUDE.md`, branch-protection settings, changelog fragments, or diary entries as enforcement of FR-917 before the split FRs are individually revised and judged.

## Revised acceptance criteria

- [ ] AC-01: FR-917 is marked `Status: Split` or otherwise superseded without changing CI behavior.
- [ ] AC-02: A matrix/support-claim FR exists with a single responsibility: Python-version CI coverage and the exact branch-protection migration procedure.
- [ ] AC-03: The matrix/support-claim FR states whether Python 3.14 is supported, unsupported, or allowed-but-unclassified, and aligns `requires-python`, classifiers, CI, and documentation accordingly.
- [ ] AC-04: The matrix/support-claim FR defines how `core-test`, `test`, `security`, and release build Python versions relate to the support policy.
- [ ] AC-05: A doc-only skip FR exists with a single responsibility: path-aware skipping of expensive PR jobs.
- [ ] AC-06: The doc-only skip FR defines independent gates for `.github/workflows/workflow.yml` and `.github/workflows/security.yml`.
- [ ] AC-07: The doc-only skip FR proves tag pushes still run release-required jobs and the dependency security scan.
- [ ] AC-08: The doc-only skip FR includes a changed-file fixture table with expected run/skip results for Markdown-only, FR-only, changelog-only, workflow, graph, prompt, capability, Python, and mixed diffs.
- [ ] AC-09: Both split FRs include a human/operator review gate for CI workflow and branch-protection changes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement CI, security workflow, branch-protection, support-metadata, changelog, or diary changes under FR-917; authority requires the split FRs to re-enter judgement. | GATE |
| C-2 | Do not change required status-check contexts without an explicit human/admin migration sequence and recorded API verification. | GATE |
| C-3 | Do not introduce doc-only skip logic that can skip tag-release `test`, `build`, `publish`, `create-release`, or `security` execution. | GATE |
| C-4 | Treat all workflow and branch-protection edits as enforcement-infrastructure changes requiring explicit human/operator review. | GATE |

Authority granted: no implementation authority is granted for FR-917 as written; authority is limited to splitting and revising the proposal into the two scoped FRs above.
