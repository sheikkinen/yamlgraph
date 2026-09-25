# Judgement: FR-1094 Unit tests never write into the repository tree

**Prior art:** `FR-1094-tests-never-write-into-repo-tree.md` is the FR this judgement governs. FR-889, FR-756, FR-140, FR-982, FR-861, FR-469 and rejected FR-117, FR-277, FR-643, FR-839, FR-874 are dispositioned in the FR and reviewed below.

**Verdict:** APPROVED WITH REVISIONS — the existing FR-889 lock is the minimal enforcement mechanism, but authority activates only after R-1 through R-6 are folded into the FR and the CI placement decision is recorded.

**Reviewed against:** `feature-requests/FR-1094-tests-never-write-into-repo-tree.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `tests/unit/test_fr_numbering.py`; `tests/conftest.py`; `scripts/worktree.sh`; `.github/workflows/workflow.yml`; `ARCHITECTURE.md`; `capabilities/CAP-252-shared-smtp-email-tool.yaml`; `capabilities/CAP-255-os-enforced-main-write-lock.yaml`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-756-core-test-isolation.md`; `feature-requests/FR-140-clean-git-env-test-fixture.md`; `feature-requests/FR-982-unit-suite-runs-with-tracer-live.md`; `feature-requests/FR-861-shared-repo-write-discipline.md`; `feature-requests/FR-469-fr-number-allocation-gate.md`; rejected prior art `feature-requests/FR-117-enforce-worktree-watch-integration.md`, `feature-requests/FR-277-watcher2-baseline-checkpointing.md`, `feature-requests/FR-643-novel-fandom-worldgen-loop.md`, `feature-requests/FR-839-gitclaw-immutable-owner-contract.md`, and `feature-requests/FR-874-cross-device-agent-memory-sync.md`. The uncommitted `tmp/pytest-unit.log` named at FR-1094:10-12 was not consumed and grants no evidentiary weight.

## What is sound

The defect is real from committed evidence alone: the test constructs its probe under the repository `feature-requests/` directory and writes and unlinks it (`tests/unit/test_fr_numbering.py:23-24,123-130`), while FR-889 removes owner-write permission from that governed root (`scripts/worktree.sh:503-507,524-537`). Moving the probe into a temporary git repository preserves the actual semantic contract: `_tracked_fr_names` must list tracked FRs and ignore an untracked one (`tests/unit/test_fr_numbering.py:64-79`).

The prevention mechanism also conforms before extending. The required CI matrix already installs dependencies before invoking the full unit suite (`.github/workflows/workflow.yml:65-95`), and `lock-main` derives one governed-root list and enforces it with filesystem permissions (`scripts/worktree.sh:506-537`). Reusing that command before pytest is materially smaller and more complete than adding a process-global audit hook; it covers both in-process and subprocess writes without duplicating the root list. The alternatives section preserves the audit-hook dissent, gives six genuine solution classes, and answers `is_this_a_graph` (`FR-1094:196-233`).

| Criterion | Finding |
|---|---|
| Scope | **Revision required.** The known change is small, but the title and outcome claim the whole repository tree while the proposal intentionally governs only FR-889 roots and excludes several repository directories (`FR-1094:1,53-64,109-113,244-249`). AC-05 also grants unbounded authority to edit any newly failing test (`FR-1094:187-190`). |
| Consistency | **Revision required.** The proposed hermetic test writes into `tmp_path` (`FR-1094:143-152`), while AC-01 first makes that temporary `feature-requests/` directory read-only and then expects the rewritten probe check to pass (`FR-1094:169-180`). The CI location is simultaneously proposed as the existing `test` job and left as an unresolved choice (`FR-1094:156-165,235-242`). |
| Measurability | **Revision required.** The named commands and assertions are mostly mechanical, but AC-03/04 do not define a realizable pre-merge checkout: from a linked worktree, `main_checkout_dir` resolves through the common git directory to the separate main checkout (`scripts/worktree.sh:509-513`), so `lock-main` does not lock the implementation worktree. |
| Feasibility | **Sound after revisions.** A normal CI checkout is its own common-dir parent, the workflow uses non-root Ubuntu runners, dependencies are installed before the proposed lock, and the existing test command follows immediately (`.github/workflows/workflow.yml:72-95`; `scripts/worktree.sh:509-537`). |
| Architecture alignment | **Revision required.** Reusing FR-889 is aligned, but the FR knowingly requires the SMTP requirement for unrelated tests and changelog metadata (`FR-1094:122-129,191-194,244-249`). `REQ-YG-627` is exclusively the shared SMTP tool (`ARCHITECTURE.md:570,3128-3134`; `capabilities/CAP-252-shared-smtp-email-tool.yaml:1-33`), while `REQ-YG-631` owns the OS-enforced main-write lock (`ARCHITECTURE.md:573,3163-3165`). |
| Single responsibility | **Pass.** The hermetic fixture correction and CI lock are two layers of one concern: eliminate the known governed-root write and prevent recurrence. Historical FR-number traceability repair beyond what this change touches remains separate. |
| Strategic classification | **Pattern documentation / repository-process enforcement.** Existing abstractions suffice: `tmp_path` provides fixture isolation and FR-889 provides the write boundary. This is not a new framework primitive or contrib example (`FR-1094:196-233`). |
| Testability | **Revision required, then direct.** The desired helper seam and locked CI run are directly testable, but AC-01's chmod/monkeypatch formulation does not specify a RED test that can also pass against the stated GREEN implementation (`FR-1094:143-180`). |

## Required revisions

### R-1: Narrow every claim to FR-889 governed roots

Rename the FR and replace "repository tree", "nothing broke", and equivalent absolute claims in the Summary, Value Statement, Ideal Result, Acceptance Criteria, and implementation record with "FR-889 governed roots." Preserve the explicit exclusion of ungoverned directories. The implemented guarantee is that the unit suite does not write to the roots listed by `FR889_GOVERNED_ROOTS`; it is not a guarantee covering every path inside the checkout.

### R-2: Replace the contradictory RED/GREEN witness

Replace AC-01 and AC-02 with this direct sequence:

1. RED commit: rewrite only `test_untracked_files_are_not_collisions` to accept `tmp_path`, initialize a git repository there, configure repository-local test identity, commit `feature-requests/FR-001-tracked.md`, create untracked `feature-requests/FR-000-untracked-probe.md`, and call `_tracked_fr_names(tmp_path)`. Assert the tracked filename is present and the probe is absent. Against current code, this fails because `_tracked_fr_names` accepts no root argument. Commit this test alone with `SKIP=pytest`.
2. GREEN commit: add the typed `root: Path = REPO_ROOT` parameter and use it as the subprocess `cwd`. No chmod, global monkeypatch, nested invocation of a pytest test method, platform skip, or permission-restoration teardown belongs in this unit witness.

The locked-suite execution remains the end-to-end witness for the original `PermissionError`.

### R-3: Use the lock requirement, not the SMTP requirement

Replace `REQ-YG-627` in AC-06 and the changelog criterion with `REQ-YG-631`. Add a function-level `@pytest.mark.req("REQ-YG-631")` to the changed hermeticity witness, and extend CAP-255 plus the `REQ-YG-631` entry in `ARCHITECTURE.md` to name the required CI `test` job lock and this witness. Do not alter CAP-252 or its SMTP requirement. Retagging the unchanged FR-numbering tests and repairing the historical FR-907 numbering collision remain unauthorized follow-up work.

### R-4: Make pre-merge locked verification executable

Replace AC-03/04 with a locked run in a disposable standalone clone checked out at the implementation commit. Record the tested commit SHA, exact command, and summary in the FR implementation record. Do not describe a linked implementation worktree as locked by `scripts/worktree.sh lock-main`; that command targets the common main checkout.

### R-5: Remove wildcard repair authority

Replace AC-05's instruction to fix every newly exposed test in the same PR with a stop condition: if the first locked run exposes any additional test, record the exact failures and amend this FR with enumerated files and fixes before editing them. The current authority covers only `tests/unit/test_fr_numbering.py` and the CI lock step.

### R-6: Fold the prior-art and human-decision records

Replace the title-only dismissal at FR-1094:48-51 with one substantive sentence for each rejected FR-117, FR-277, FR-643, FR-839, and FR-874 explaining why its problem and solution do not overlap this proposal. Record the operator's answer to: **Should the lock step run in the existing required `test` matrix job after dependency installation and before pytest?** If the answer is no, revise the Proposed Solution and acceptance criteria before enforcement. Keep human review of the resulting workflow diff as a merge gate.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/unit/test_fr_numbering.py`: parameterize `_tracked_fr_names` and make only the untracked-probe witness hermetic |
| D-2 | `.github/workflows/workflow.yml`: invoke the unchanged `scripts/worktree.sh lock-main` in the operator-approved required job after installation and before pytest |
| D-3 | `capabilities/CAP-255-os-enforced-main-write-lock.yaml` and `ARCHITECTURE.md`: extend only `REQ-YG-631` traceability for the CI lock and changed witness |
| D-4 | One `changelog/unreleased/` fix fragment using `scope: tests` and `req: REQ-YG-631` |
| D-5 | FR-1094 implementation record and one `docs/diary/` Distill entry with a **Seed:** |

Not authorized: changes to `scripts/worktree.sh`, FR-889's root list or carve-outs, tests other than the named FR-numbering witness, Windows CI, an audit hook or local filesystem guard, skips/exclusions for lock failures, writes to or enforcement for ungoverned directories, CAP-252/SMTP changes, historical FR renumbering, or broad repair of the existing FR-numbering test module's traceability. An additional locked-suite failure requires an FR amendment before its file enters scope.

## Revised acceptance criteria

- [ ] AC-01 (RED, committed alone with `SKIP=pytest`): `test_untracked_files_are_not_collisions(tmp_path)` creates a temporary git repository with repository-local identity, one committed FR, and one untracked probe; it calls `_tracked_fr_names(tmp_path)`, asserts the tracked name is present and the probe absent, and fails against current code because the helper accepts no root argument.
- [ ] AC-02 (GREEN): `_tracked_fr_names(root: Path = REPO_ROOT)` uses `root` as the `git ls-files` working directory; AC-01 passes and the witness creates, modifies, and deletes nothing under the real repository's governed roots.
- [ ] AC-03: `pytest tests/unit/test_fr_numbering.py -q --no-cov` passes in the implementation worktree.
- [ ] AC-04: in a disposable standalone clone checked out at the implementation commit, `scripts/worktree.sh lock-main` followed by `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` reports zero failures; the FR implementation record states the commit SHA, exact commands, and summary.
- [ ] AC-05: the operator-approved required CI job runs `scripts/worktree.sh lock-main` after dependency installation and before `pytest tests/unit/`; both Python 3.11 and 3.13 matrix entries complete successfully.
- [ ] AC-06: if any locked run exposes a test other than the named FR-numbering witness, implementation stops and FR-1094 is amended with the exact file and intended correction before that file is edited; no failure is skipped or excluded.
- [ ] AC-07: the changed witness has a function-level `@pytest.mark.req("REQ-YG-631")`; CAP-255 and the `REQ-YG-631` architecture entry name the CI lock and witness; `python scripts/req_coverage.py --strict` passes. No new artifact claims `REQ-YG-627`.
- [ ] AC-08: a `changelog/unreleased/` fix fragment uses `scope: tests` and `req: REQ-YG-631`; the FR contains the implementation record; the diary entry contains a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 are folded into FR-1094 before implementation authority activates. | GATE |
| C-2 | The operator records the CI-job placement decision in the FR before the workflow is edited. | GATE |
| C-3 | A human reviews the `.github/workflows/workflow.yml` diff before merge because it changes enforcement infrastructure (`.github/skills/judge-fr/doctrine.md:98-101`). | GATE |
| C-4 | RED and GREEN remain separate commits; the RED failure is the helper's missing root seam, not an import, missing fixture, or write to the real checkout. | GATE |
| C-5 | No additional test file is edited unless an enumerated FR amendment brings it into scope. | GATE |
| C-6 | The locked-suite witness runs from a disposable standalone clone at the implementation SHA; the main checkout is not unlocked or repurposed to obtain the result. | GATE |

Authority granted: after C-1 and C-2 are satisfied, the enforcer may implement D-1 through D-5 only; merge remains blocked on C-3 through C-6 and all revised acceptance criteria.
