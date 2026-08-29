# Judgement: FR-919 Doc-Only PR Skip for Expensive CI Jobs

**Prior art:** the hits (FR-917 lineage and sibling FR-918) are this FR's own split family per the FR-917 judgement D-1/D-2 — lineage, not competing precedent.

**Verdict:** APPROVED WITH REVISIONS — the split FR is real, single-purpose, and mostly testable, but authority activates only after the tag-push short-circuit is made step-safe and the research record satisfies the local substance gate.

**Reviewed against:** `feature-requests/FR-919-ci-doc-only-skip.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/workflows/workflow.yml`; `.github/workflows/security.yml`; `.github/copilot-instructions.md`.

## What is sound

The problem is real and narrowly scoped. The current CI workflow runs on every pull request and has no path-aware gate before `core-test` or the matrix `test` job (`.github/workflows/workflow.yml:3-8`, `:18-68`), and the dependency security workflow likewise runs on every pull request before installing the audit environment (`.github/workflows/security.yml:3-8`, `:17-42`). FR-919 names the cost and first consumer directly (`feature-requests/FR-919-ci-doc-only-skip.md:8-23`), satisfying the repo's value-proposition discipline rather than proposing generic CI gardening.

The FR correctly preserves the split ordered by the parent judgement. FR-917 granted no implementation authority and required a separate doc-only skip FR covering independent gates for `workflow.yml` and `security.yml`, tag-release proof, fixture-based classifier semantics, and human review (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:39-65`, `:83-96`). FR-919 stays within that single responsibility: it excludes the Python matrix sibling, keeps job names unchanged, and says no branch-protection mutation is needed (`feature-requests/FR-919-ci-doc-only-skip.md:115-124`, `:157-160`).

The path classifier is appropriately conservative. The FR defines doc-only as "every changed file matches `**/*.md`" and treats workflows, graphs, prompts, capabilities YAML, Python, and images as code-like changes that run the full suite (`feature-requests/FR-919-ci-doc-only-skip.md:47-60`). Its fixture table covers the parent judgement's required cases plus `docs/img/example.png` as an accepted false negative (`feature-requests/FR-919-ci-doc-only-skip.md:62-75`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:45-61`).

The architecture classification is **pattern documentation / CI policy**, not a framework primitive. The authorized implementation surface is existing GitHub Actions YAML plus evidence artifacts; it does not touch graph runtime, prompt authoring, provider logic, package metadata, or branch-protection settings. Because this is enforcement infrastructure, the FR's human-review gate is necessary and aligned with judge doctrine (`.github/skills/judge-fr/doctrine.md:98-100`; `feature-requests/FR-919-ci-doc-only-skip.md:120-124`).

## Required revisions

### R-1: Make the non-PR short-circuit step-safe, not only output-safe

Revise the proposed workflow snippets so `dorny/paths-filter@v3` is run only for pull request events, or cite committed evidence proving the action cannot fail on tag pushes. FR-919 currently says non-PR events short-circuit because the job output expression is `github.event_name != 'pull_request' || steps.filter.outputs.code == 'true'` (`feature-requests/FR-919-ci-doc-only-skip.md:79-90`, `:110-118`), but the shown `steps.filter` action still executes unconditionally (`feature-requests/FR-919-ci-doc-only-skip.md:91-98`). Both cited workflows run on version tags (`.github/workflows/workflow.yml:3-8`; `.github/workflows/security.yml:3-8`), and the release chain depends on `test` before `build`, `publish`, and `create-release` (`.github/workflows/workflow.yml:70-128`). A tag-push filter-step failure would violate parent C-3 even if the output expression itself would evaluate to true (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:93-96`).

The mechanically foldable revision is: in both workflows, add `if: github.event_name == 'pull_request'` to the `dorny/paths-filter@v3` step and keep the job output expression as the sole non-PR "run" source, or replace it with an equivalent explicit pull-request/non-pull-request step pair. The acceptance criteria must check the shipped YAML for this guard, not merely cite the output expression.

### R-2: Complete the local research substance record

Revise the `**Research:**` field or alternatives section to include the local doctrine's required substance markers: 4-6 genuine solution classes, precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer. FR-919 points to the parent split and an in-body alternatives table (`feature-requests/FR-919-ci-doc-only-skip.md:12-15`, `:144-153`), which is directionally sound, but local judge doctrine requires more than a shape-valid table for newly created FRs (`.github/skills/judge-fr/doctrine.md:118-128`). The expected `is_this_a_graph` answer is simple and should be stated directly: "No; this is CI event/path classification in GitHub Actions, not an LLM pipeline or graph artifact."

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-919-ci-doc-only-skip.md` revisions for tag-step safety and research substance |
| D-2 | `.github/workflows/workflow.yml` job-level doc-only skip for `core-test` and `test` |
| D-3 | `.github/workflows/security.yml` job-level doc-only skip for `security` |
| D-4 | CI witness links/status notes recorded in `feature-requests/FR-919-ci-doc-only-skip.md` |
| D-5 | `changelog/unreleased/*.md` fragment with `ci` scope |
| D-6 | `docs/diary/*.md` reflection |

Not authorized: Python matrix changes; `pyproject.toml` support metadata changes; `constraints/` regeneration; branch-protection context changes; workflow-level `paths-ignore`; skipping `commitlint`, changelog, diary, or other cheap governance gates; graph or prompt artifact edits; replacing the path classifier with a directory allowlist.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-919-ci-doc-only-skip.md` includes a substance-complete research record: dispositioned alternatives, precedent lines, preserved disagreement, and the explicit `is_this_a_graph` answer.
- [ ] AC-02: `.github/workflows/workflow.yml` has its own `changes` job whose output is true for non-pull-request events and whose `dorny/paths-filter@v3` step is guarded with `if: github.event_name == 'pull_request'` or an equivalent committed proof that tag-push execution cannot fail.
- [ ] AC-03: `.github/workflows/security.yml` has its own independent `changes` job with the same tag-safe pull-request-only file-filter behavior.
- [ ] AC-04: `core-test`, the matrix `test` job, and `security` each declare `needs: changes` and `if: needs.changes.outputs.code == 'true'`; `build`, `publish`, and `create-release` keep their existing tag guards and release-chain `needs`.
- [ ] AC-05: The shipped filter implements the FR fixture table exactly: Markdown-only diffs skip expensive jobs; any workflow, graph, prompt, capability YAML, Python, image, or mixed Markdown/non-Markdown diff runs them.
- [ ] AC-06: A doc-only PR touching only a `docs/diary/*.md` file shows `core-test`, both `test` legs, and `security` skipped; the PR reports required checks satisfied; the run link is recorded in FR-919.
- [ ] AC-07: A mixed PR containing Markdown plus a non-Markdown file runs `core-test`, both `test` legs, and `security`; the run link is recorded in FR-919.
- [ ] AC-08: Tag-release safety is proven by line-citing the shipped non-PR output and pull-request-only filter guard, and the first post-merge tag push records that `test`, `build`, and `security` executed.
- [ ] AC-09: The operator explicitly reviews both workflow diffs before merge or direct push, and the review is recorded in FR-919.
- [ ] AC-10: A `ci`-scoped changelog fragment and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 and R-2 are folded into FR-919; authority activates only after those revisions are present in the FR. | GATE |
| C-2 | Do not allow a tag push to depend on a changed-file detector that may fail or return false because there is no pull-request diff. | GATE |
| C-3 | Do not rename existing required-check jobs or mutate branch-protection contexts under this FR. | GATE |
| C-4 | Treat `.github/workflows/workflow.yml` and `.github/workflows/security.yml` edits as enforcement-infrastructure changes requiring explicit operator review. | GATE |
| C-5 | If the shipped `dorny/paths-filter@v3` semantics do not match the fixture table, stop and revise the FR instead of broadening the classifier during enforcement. | GATE |

Authority granted: after R-1 and R-2 are folded into `feature-requests/FR-919-ci-doc-only-skip.md`, implement only the doc-only job-level skip in the two cited workflows plus its recorded evidence, changelog, and diary.
