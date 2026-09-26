# Feature Request: Unit tests never write into FR-889 governed roots — the suite is green on the locked main checkout

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1094-tests-never-write-into-repo-tree.judgement.md)); R-1–R-6 folded 2026-09-25. **Authority active (2026-09-25):** C-1 (fold) and C-2 (CI placement, see [Human decisions](#human-decisions)) satisfied. Merge gated on C-3–C-6. **Implemented (2026-09-26)** — see [Implementation record](#implementation-record).
**Effort:** 0.5 day
**Requested:** 2026-09-25
**First consumer / first event:** the next
`pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on the main checkout.
On 2026-09-25 it reported `1 failed, 6903 passed, 73 skipped, 1 xfailed`
([tmp/pytest-unit.log](../tmp/pytest-unit.log), not committed). The single
failure was
`tests/unit/test_fr_numbering.py::TestFeatureRequestNumbering::test_untracked_files_are_not_collisions`,
which raised `PermissionError` writing
`feature-requests/FR-000-untracked-probe.md` into the FR-889-locked tree. The
same file passes 7/7 in a fresh worktree.
**Research:** FR-890 research route **skipped by operator decision for this
batch (2026-09-25)**. Substitute: the in-body Alternatives Considered below
(six solution classes, one chosen, one preserved dissent, each
dispositioned, plus an `is_this_a_graph` answer), in the form FR-1084 uses;
plus the census of repository-tree writes in Problem §3, run 2026-09-25
against this worktree (HEAD `82733de3`).
**Prior art:**
[FR-889](FR-889-os-enforced-main-write-lock.md) (Enforced 2026-08-30). The
lock that exposed this defect: `scripts/worktree.sh lock-main` runs
`chmod -R u-w` over `yamlgraph tests scripts capabilities .github/hooks docs
feature-requests` ([worktree.sh#L506](../scripts/worktree.sh#L506),
[#L525-L538](../scripts/worktree.sh#L525-L538)). This FR does not change the
lock; it removes a test that cannot run under it, and reuses the lock in CI.
FR-907 (FR-number guard; no FR file — the number is shared with
[FR-907-smtp-email-tool.md](FR-907-smtp-email-tool.md), see Problem §5).
Commit `e7efd2e0` (PR #490, 2026-08-29) introduced
`test_untracked_files_are_not_collisions` one day before FR-889 locked main.
Its purpose — the guard reads `git ls-files`, not a glob — is kept; only
where the probe is planted changes.
[FR-756](FR-756-core-test-isolation.md) (Enforced). Isolation across the
package/process boundary (`examples/`, `scripts/`, `.chaplain/`); it
separates which tests run, not where they write.
[FR-140](FR-140-clean-git-env-test-fixture.md) (Approved) and
[FR-982](FR-982-unit-suite-runs-with-tracer-live.md) (Approved). Autouse
session fixtures in [tests/conftest.py](../tests/conftest.py#L51-L87) that
normalize env pollution at the test-process boundary. Same boundary, env
not filesystem; precedent for fixing the boundary once for every test.
[FR-861](FR-861-shared-repo-write-discipline.md) (Proposed). Agent write
discipline on the shared repo; covers sessions, not the test suite.
[FR-469](FR-469-fr-number-allocation-gate.md) (Proposed). FR-number
allocation; shares the module under test, not the defect.
REJECTED sweep: `Status: REJECTED` FRs matching
`isolation|pollution|tmp_path|repo tree|read-only|hermetic` returned five
(judgement R-6):
[FR-117](FR-117-enforce-worktree-watch-integration.md) spawned
`enforce_worktree.sh` from `watch.sh`; it is pipeline orchestration and
never touches where tests write.
[FR-277](FR-277-watcher2-baseline-checkpointing.md) cached watcher2
doctrine inputs by hash; it is a run-time cache, not a filesystem boundary.
[FR-643](FR-643-novel-fandom-worldgen-loop.md) was a worldgen graph for
novel_fandom; its only overlap is the word "isolation" in its prompts.
[FR-839](FR-839-gitclaw-immutable-owner-contract.md) added an immutable
owner artifact to GitClaw's CI; it protects a model's input, not the
repository from tests.
[FR-874](FR-874-cross-device-agent-memory-sync.md) synced agent memory
through git; it moves notes between machines and has no test-suite surface.
None shares this FR's problem or solution.

## Summary

Make `test_untracked_files_are_not_collisions` plant its untracked probe in a
`tmp_path` git repository instead of the real `feature-requests/`, and run
the CI unit suite with the FR-889 governed roots locked, so a test that writes
into a governed root fails in the PR instead of on the next locked-main run.

## Value Statement

Any agent or operator running the fast unit suite on the main checkout gets a
green result that means no test wrote into an FR-889 governed root, instead
of one known red test that hides the next real one.

## Problem

1. **The test writes into the real tree.**
   [test_fr_numbering.py#L123-L130](../tests/unit/test_fr_numbering.py#L123-L130)
   writes `FR_DIR / "FR-000-untracked-probe.md"` where
   `FR_DIR = REPO_ROOT / "feature-requests"`
   ([#L23-L24](../tests/unit/test_fr_numbering.py#L23-L24)), then asserts the
   name is absent from `_tracked_fr_names()`, which runs
   `git ls-files feature-requests/FR-*.md` with `cwd=REPO_ROOT`
   ([#L61-L78](../tests/unit/test_fr_numbering.py#L61-L78)). On the locked
   main checkout `feature-requests/` is `u-w`, so `write_text` raises
   `PermissionError` before the assertion runs.
2. **Composition, not a flaw in either part.** The probe test (2026-08-29)
   and the lock (2026-08-30) were each correct and each green in the
   environment they were verified in. FR-889's record cites a green unit
   suite (6181 passed) run outside the locked tree. Nothing ran the suite
   on the locked checkout until 2026-09-25 (`composition_bug`).
3. **Census of repository-tree writes under `tests/`** (2026-09-25, HEAD
   `82733de3`):
   - Direct single-line writes on repo-root constants — `(REPO_ROOT|REPO|ROOT|PROJECT_ROOT|FR_DIR|…) / … .(write_text|write_bytes|mkdir|touch|unlink|rmdir)(`:
     **0 hits.** `open(<repo const>…, "w|a|x")`: **0**.
     `shutil.(rmtree|copy|copytree|move)(<repo const>…)`: **0**.
     `REPO_ROOT / "tmp|outputs|logs|data|vectorstore"`: **0**.
   - Two-step writes (AST scan: a name assigned from a repo-root constant or
     `Path(__file__)` and not from `tmp_path`/`tempfile`, later receiving a
     write-class call or `open` for write): **24 flagged, 2 true lines in
     1 test** — `test_fr_numbering.py:126` (`probe.write_text`) and `:130`
     (`probe.unlink`). The other 22 are false positives: `tmp_path`-derived
     directories whose variable names collide with tainted names elsewhere
     in the module (`test_check_changelog_req.py` ×7,
     `test_fr643v2_novel_fandom_worldgen.py` ×4,
     `test_fr794_python_tool_manifest_root_fix.py` ×2) and `str.replace`
     calls on text (`test_fr788…` ×1, `test_fr890…` ×2, `test_fr951…` ×2,
     `test_fr995…` ×4).
   - **Empirical bound.** The locked-main run failed exactly one of 6904
     executed fast tests. No other executed fast test writes into a locked
     root *and* lets the `PermissionError` escape.
   - **Honest bounds — not covered by either method:** writes made by
     subprocesses (28 files under `tests/unit/` run commands with
     `cwd=REPO_ROOT`); writes made by production code under test that
     resolves its own repo-relative paths; tests marked `slow`, the 73
     skipped, and `tests/integration/`; tests that catch and swallow
     `PermissionError`; root constants named outside the scan's list.
   - **Writes into unlocked directories** (`tmp/`, `outputs/`, `logs/`,
     `examples/`, `graphs/`, `prompts/`, root files): the static scan found
     **none** direct. Subprocess and production-code writes there are
     **unmeasured**; such tests pass on locked main because FR-889 does not
     govern those paths. They are not failures and are out of scope.
4. **No enforcement exists.** [tests/conftest.py](../tests/conftest.py)
   has autouse session fixtures for tracing env (`_tracing_off`) and
   `GIT_*` env (`_clean_git_env`) and a collection hook for `req` markers;
   [tests/unit/conftest.py](../tests/unit/conftest.py) holds OTEL fixtures.
   Neither audits filesystem writes. CI runs `tests/unit` on a writable
   checkout ([workflow.yml#L63](../.github/workflows/workflow.yml#L63),
   [#L95](../.github/workflows/workflow.yml#L95)), so this class of defect
   reaches `main` green and turns red only on the locked checkout.
5. **Traceability finding (outside the fix).** The module is tagged
   `REQ-YG-627` ([#L90](../tests/unit/test_fr_numbering.py#L90)) and its
   docstring cites `CAP-252`. In [ARCHITECTURE.md](../ARCHITECTURE.md) and
   [CAP-252](../capabilities/CAP-252-shared-smtp-email-tool.yaml),
   REQ-YG-627 is the shared SMTP email tool. The FR-number guard reused
   FR-907's number and REQ when PR #489 and the SMTP tool both landed as
   FR-907 (changelog `0.5.23/fr-907-fr-number-uniqueness-guard.md` and
   `0.5.23/fr-907-shared-smtp-email-tool.md`). See Human decision needed.
6. **Doctrine.** A red suite belongs to the current change author; the
   repository forbids dismissing it as older than the change. Its named root
   class is test pollution — hidden state or incomplete isolation. This is
   that class: a test depends on the writability of the real tree.

## Ideal Result

The fast unit suite is green on the FR-889-locked main checkout, and it
stays green because CI runs the suite with the same roots locked, so any test
that writes into an FR-889 governed root (`FR889_GOVERNED_ROOTS`) fails in
its own PR. Paths outside those roots are not covered.

## Proposed Solution

1. **Hermetic probe.** Give `_tracked_fr_names` a `root: Path = REPO_ROOT`
   parameter used as the `git ls-files` `cwd`. Rewrite
   `test_untracked_files_are_not_collisions(tmp_path)` to `git init` a repo
   under `tmp_path` (with `_clean_git_env` already active), commit
   `feature-requests/FR-001-tracked.md`, write an untracked
   `feature-requests/FR-000-untracked-probe.md`, and assert
   `_tracked_fr_names(tmp)` contains the tracked name **and** does not
   contain the probe. The positive assertion stops an empty listing from
   passing (`plausible_wrong_answer`). The other six tests keep reading the
   real repository read-only.
2. **Census hits.** The census found one true hit, so class (b) and class
   (a) coincide at this HEAD. If a locked run exposes any further test,
   implementation stops and this FR is amended with the exact file and fix
   before that file is edited (judgement R-5).
3. **CI mirrors the lock.** In the `test` job of
   [workflow.yml](../.github/workflows/workflow.yml#L69-L99), after
   dependency install and before `Run tests`, add a step that runs
   `scripts/worktree.sh lock-main`. `main_checkout_dir` resolves to the CI
   checkout ([worktree.sh#L509-L513](../scripts/worktree.sh#L509-L513)), so
   the root list has one source. `ubuntu-latest` runs as a non-root user, so
   `chmod u-w` is effective. Side effects accepted: `pip install -e`
   metadata, `.coverage` and `.pytest_cache` live at the repo root (not
   governed); `__pycache__` under `yamlgraph/` and `tests/` becomes
   unwritable and Python skips writing bytecode there.

## Acceptance Criteria

The judgement's revised AC-01 to AC-08 are adopted (R-2 to R-5).

- [ ] AC-01 (RED, committed alone with `SKIP=pytest`):
  `test_untracked_files_are_not_collisions(tmp_path)` creates a temporary
  git repository with repository-local identity, one committed FR, and one
  untracked probe; it calls `_tracked_fr_names(tmp_path)`, asserts the
  tracked name is present and the probe absent, and fails against current
  code because the helper accepts no root argument.
- [ ] AC-02 (GREEN): `_tracked_fr_names(root: Path = REPO_ROOT)` uses `root`
  as the `git ls-files` working directory; AC-01 passes and the witness
  creates, modifies, and deletes nothing under the real repository's
  governed roots.
- [ ] AC-03: `pytest tests/unit/test_fr_numbering.py -q --no-cov` passes in
  the implementation worktree.
- [ ] AC-04: in a disposable standalone clone checked out at the
  implementation commit, `scripts/worktree.sh lock-main` followed by
  `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` reports zero
  failures; the implementation record states the commit SHA, exact
  commands, and summary.
- [ ] AC-05: the required CI `test` job runs `scripts/worktree.sh lock-main`
  after dependency installation and before `pytest tests/unit/`; both
  Python 3.11 and 3.13 matrix entries complete successfully.
- [ ] AC-06: if any locked run exposes a test other than the named
  FR-numbering witness, implementation stops and FR-1094 is amended with the
  exact file and intended correction before that file is edited; no failure
  is skipped or excluded.
- [ ] AC-07: the changed witness has a function-level
  `@pytest.mark.req("REQ-YG-631")`; CAP-255 and the `REQ-YG-631`
  architecture entry name the CI lock and witness;
  `python scripts/req_coverage.py --strict` passes. No new artifact claims
  `REQ-YG-627`.
- [ ] AC-08: a `changelog/unreleased/` fix fragment uses `scope: tests` and
  `req: REQ-YG-631`; the FR contains the implementation record; the diary
  entry contains a **Seed:**.

## Alternatives Considered

Solution classes (chosen: 4):

1. **(a) Fix only this test with `tmp_path`.** Makes the suite green today.
   Rejected alone: nothing keeps it green; the next test that writes into a
   governed root lands through a writable CI checkout and is found on the
   next locked-main run, as this one was.
2. **(b) Fix every census hit.** At this HEAD the census has one true hit,
   so (b) equals (a) and has the same weakness.
3. **(c) Autouse guard via `sys.addaudithook`** that fails a test on any
   `open` for write, `mkdir`, `unlink` or `rename` under a governed root.
   **Preserved dissent.** It fires locally on any checkout, including
   worktrees, with a precise traceback. It loses here on cost: the hook is
   process-global and cannot be removed, runs on every `open` event in every
   test on every xdist worker, needs an allowlist for legitimate writers
   (FR-889 carve-outs, bytecode caches), duplicates the governed-root list
   that FR-889 owns, and is blind to subprocess writes — 28 unit test files
   run commands with `cwd=REPO_ROOT`. If a hit ever lands that CI's lock
   cannot see, this class is the next step.
4. **(b) plus the OS lock in CI.** Chosen. The enforcement is the FR-889
   mechanism itself, so it cannot drift from the lock, covers in-process and
   subprocess writes alike, costs one workflow step, and blocks at the
   merge boundary (`enforcement_at_merge_boundary`). Cost stated honestly:
   it edits CI, which is enforcement infrastructure, so the diff needs human
   review (`instruction_boundary_uncrossed`); it detects in CI, not in a
   local worktree run; and CI runs slow-marked tests the local census did
   not execute under the lock, so the first CI run may expose further hits
   (AC-06 stops and amends this FR before fixing them).
5. **(d) Run the unit suite only in worktrees.** Rejected: it hides the
   defect. The suite would still write into the repository tree; the result
   would depend on where it is run.
6. **(e) Unlock main for test runs.** Rejected: it bypasses FR-889 and
   reopens the write surface the lock exists to close.

`is_this_a_graph`: no. The fix is a test fixture change and one CI step. The
census is a deterministic grep and AST scan over about 600 files; no item
needs a model judgement.

## Human decisions

Operator standing rule (2026-09-25): suggested defaults count as accepted.

- **Where the CI lock step runs:** the existing required `test` matrix job,
  after dependency installation and before pytest (judgement R-6, C-2). It
  is already a required context (`test (3.11)`, `test (3.13)`), so the check
  blocks merge without a branch-protection change.
- **Diff review of the workflow edit:** the operator reviews the CI step
  before merge (judgement C-3, `instruction_boundary_uncrossed`).
  **Approved by the operator, 2026-09-26** (step `Lock governed roots
  (FR-1094)` in `.github/workflows/workflow.yml`). The paired step
  `Unlock governed roots (FR-1094)` was approved separately the same day
  (see [Unlock step](#unlock-step-2026-09-26)).

## Scope (frozen by judgement)

D-1 `tests/unit/test_fr_numbering.py` (root parameter plus the hermetic
witness only); D-2 the `workflow.yml` lock step; D-3 CAP-255 and the
`REQ-YG-631` entry in `ARCHITECTURE.md`; D-4 one changelog fragment; D-5
this implementation record and one diary entry. Not authorized: changes to
`scripts/worktree.sh` or FR-889's roots, other tests, Windows CI, an audit
hook, skips or exclusions, CAP-252 or SMTP, FR renumbering, or retagging
the rest of the FR-numbering module.

## Implementation record

**Status:** implemented on branch `fix/fr-1094-governed-roots-lock`;
AC-05 (CI matrix) and C-3 (operator review of the workflow step) are
checked on the PR.

| AC | Evidence |
|---|---|
| AC-01 | RED commit `test(tests): FR-1094 RED hermetic untracked-probe witness` (`SKIP=pytest`): `TypeError: _tracked_fr_names() takes 0 positional arguments but 1 was given`; `1 failed, 6 passed`. |
| AC-02 | GREEN commit `fix(tests): FR-1094 hermetic FR-numbering witness; CI runs under the lock`: `_tracked_fr_names(root: Path = REPO_ROOT)` with `cwd=root`. The probe is written under `tmp_path` only. |
| AC-03 | `pytest tests/unit/test_fr_numbering.py -q --no-cov` → exit 0 in the worktree. |
| AC-04 | Standalone clone `/private/tmp/fr1094-clone` at `f5c115f07560897812a7c70ce7db7fb2a5484aaa`: `scripts/worktree.sh lock-main` (then `touch feature-requests/x` → `Permission denied`), then `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` → `6904 passed, 73 skipped, 1 xfailed`, exit 0. The branch was then rebased onto `main` after #701; the rebase changed only `feature-requests/` files, so the tested code is the code in this PR. |
| AC-05 | `workflow.yml` `test` job: step `Lock governed roots (FR-1094)` runs `scripts/worktree.sh lock-main` after `Install dependencies` and before `Run tests`. Matrix result: on the PR. |
| AC-06 | The locked CI run exposed one other failure; see [AC-06 amendment](#ac-06-amendment-2026-09-26). |
| AC-07 | Function-level `@pytest.mark.req("REQ-YG-631")` on the witness; CAP-255 and `REQ-YG-631` name `.github/workflows/workflow.yml` and `tests/unit/test_fr_numbering.py`; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` → exit 0. |
| AC-08 | `changelog/unreleased/fr-1094-tests-never-write-into-repo-tree.md` (`type: fix`, `scope: tests`, `req: REQ-YG-631`); diary `docs/diary/2026-09-26-reflection-fr-1094.md` with a **Seed:**. |

**Deviations:** none. A first locked run also passed
`PYTHONPATH=$PWD -p no:cacheprovider`; it was rerun with the exact AC-04
command, and that run is the one recorded.

### AC-06 amendment (2026-09-26)

**File:** `tests/unit/test_fr1065_resumable_map_probes.py`,
`test_batch_loop_bounds_peak_memory` (added by FR-1065, PR #696, merged
2026-09-25).

**Observed:** the CI `test (3.11)` job failed twice at the same head:
`assert 8129307 < (14843517 / 2)` and `assert 7659483 < (14850243 / 2)`,
so the batched run peaked at 55% and 52% of the one-step run. Locally
(Python 3.13, locked clone, with and without coverage) the ratio is
28–37% and the test passes. The probe runs in memory and writes no files,
so no mechanism ties it to the lock; the 50% margin was asserted after
one CI run.

**Correction:** assert the FR-1065 claim itself (a bounded batch loop
lowers peak memory): `batched < one_step`, without the fixed 50% margin.
The count assertion is unchanged. Operator ruling 2026-09-26; this adds
the file to the frozen scope (D-1).

### Unlock step (2026-09-26)

**Observed:** CI run 36194184888, `test (3.13)`: `Run tests` passed, then
`Run encoding-boundary linter` (`ruff check --select PLW1514 --preview .`)
failed with `Failed to initialize cache at
.../tests/fixtures/ramp_target/.ruff_cache: Permission denied`. The nested
fixture project has its own ruff config, so ruff writes a cache inside the
locked `tests/` root. `test (3.11)` was cancelled by fail-fast.

**Correction:** step `Unlock governed roots (FR-1094)` runs
`scripts/worktree.sh unlock-main` right after `Run tests`, so the lock
covers pytest only. Part of D-2; operator approved 2026-09-26 (C-3).

## Out of scope

Tests writing into ungoverned directories (`tmp/`, `outputs/`, `logs/`,
`examples/`, root files); the guarantee covers `FR889_GOVERNED_ROOTS` only. The Windows CI job. Local-run detection (class 3).
The REQ-YG-627 misattribution (Problem §5; operator, 2026-09-25: not fixed here). Changes to the FR-889
lock or its governed-root list.

## Related

- Lock: [FR-889](FR-889-os-enforced-main-write-lock.md), [scripts/worktree.sh](../scripts/worktree.sh#L506-L538)
- Test: [tests/unit/test_fr_numbering.py](../tests/unit/test_fr_numbering.py#L123-L130)
- Boundary fixtures precedent: [FR-140](FR-140-clean-git-env-test-fixture.md), [FR-982](FR-982-unit-suite-runs-with-tracer-live.md)
- Isolation precedent: [FR-756](FR-756-core-test-isolation.md)
- CI: [.github/workflows/workflow.yml](../.github/workflows/workflow.yml#L69-L99)
