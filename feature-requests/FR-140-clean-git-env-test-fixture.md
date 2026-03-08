# Feature Request: Clean GIT_* env vars in test fixtures

**Priority:** HIGH
**Type:** Bug
**Status:** ✅ Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Create a `clean_git_env` pytest fixture that strips leaked `GIT_*` environment variables so tests creating temporary git repos pass cleanly under pre-commit.

## Value Statement

All developers get reliable pre-commit enforcement without `--no-verify` escapes, closing the CHANGELOG-bypass loophole and restoring trust in the commit pipeline.

## Problem

When tests run under pre-commit, the harness injects `GIT_DIR`, `GIT_WORK_TREE`, and other `GIT_*` environment variables into the process. These leak into subprocess git calls made by test fixtures that create temporary repos in `tmp_path`, causing git to operate on the pre-commit context instead of the test's temporary repo. Result: 23 tests fail.

The current workaround is `--no-verify`, which bypasses the entire pre-commit pipeline — including CHANGELOG enforcement (FR-125), conventional commit checks (FR-127), and requirement traceability (req-coverage-strict). This turns enforcement into a suggestion. Flagged as ⚠ OBSERVATION in Audit XXIV and ⚠ NOTE in Audit XXV (consecutive).

**Affected test files:**
- `tests/unit/test_finalize_merge.py` — `_make_repo()`, `_write_fr()`, `_run_finalize()` all call `subprocess.run(["git", ...])`.
- `tests/integration/test_worktree_integration.py` — `clean_git_repo` fixture creates repos via subprocess.
- `tests/unit/test_inquisitor_gate.py` — bash scripts with embedded git commands via subprocess.

**Root cause:** Boundary normalization violation. External data (`GIT_*` vars from pre-commit) enters the test process unsanitized. Per Scripture: *"Normalize at the boundary where external data enters, not downstream where it manifests."*

## Proposed Solution

Add a session-scoped autouse fixture in `tests/conftest.py` that strips all `GIT_*` environment variables at the start of the test session.

```python
@pytest.fixture(autouse=True, scope="session")
def _clean_git_env():
    """Strip GIT_* env vars injected by pre-commit to prevent subprocess bleed.

    When pre-commit runs tests, it sets GIT_DIR, GIT_WORK_TREE, etc.
    These override tmp_path-based repos in test fixtures. Stripping them
    at session start follows boundary normalization: sanitize external
    data where it enters the test process.
    """
    git_vars = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
    for k in git_vars:
        del os.environ[k]
    yield
    os.environ.update(git_vars)
```

**Why session-scoped autouse:**
- No test needs to opt in — zero migration effort.
- Session scope avoids per-test overhead (the vars don't change during the run).
- Restore-after-yield preserves the pre-commit contract for any post-test hooks.

**Existing pattern followed:** `tests/conftest.py` already has `_prevent_env_pollution()` (autouse, function-scoped) that strips `LANGCHAIN_TRACING`. This fixture extends the same boundary-sanitization pattern to `GIT_*` variables at session scope.

## Acceptance Criteria

- [x] `_clean_git_env` fixture exists in `tests/conftest.py`, session-scoped and autouse
- [x] All unit tests pass when invoked via `pre-commit run --all-files` (specifically the pytest hook)
- [x] No `--no-verify` flag needed for commits that trigger the test hook
- [x] Fixture is a no-op when `GIT_*` vars are absent (running outside pre-commit)
- [x] Existing tests remain unaffected when run via `pytest` directly
- [x] Fixture restores stripped variables after the session (yield-based cleanup)
- [x] Tests added: a unit test that verifies `GIT_DIR` is stripped when set, and is a no-op when absent
- [x] `@pytest.mark.req` traceability tag added to new test(s)

## Alternatives Considered

1. **Per-test fixture (function-scoped):** Unnecessary overhead — the `GIT_*` vars are static for the entire pre-commit invocation. Session scope is sufficient and cheaper.
2. **Modifying individual test helpers** (e.g., adding `env=` cleanup to every `subprocess.run` call): Downstream fix — violates boundary normalization. Every new test file that calls `subprocess.run(["git", ...])` would need to remember to clean the env. The fixture solves it once at the boundary.
3. **Pre-commit hook `args: [--no-git-env]`:** No such flag exists. Pre-commit does not offer a way to suppress `GIT_*` injection.
4. **Running tests outside pre-commit (CI-only):** Defeats the purpose of local enforcement. The Scripture is clear: *"Never --no-verify."*

## Related

- Audit XXIV (2026-03-08): ⚠ OBSERVATION — 23 tests fail under pre-commit
- Audit XXV (2026-03-08): ⚠ NOTE — `--no-verify` used as workaround
- `tests/conftest.py`: Existing `_prevent_env_pollution()` pattern (lines 18-33)
- FR-125: Enforce pipeline finalize (documents CHANGELOG bypass via `--no-verify`)
- FR-077: CHANGELOG commit enforcement
- FR-127: CI conventional commit enforcement
- `scripts/enforce_worktree.sh:69`: Uses `--no-verify` (candidate for removal after this fix)
- Scripture trap: `partial_remediation` — "Fix all occurrences, not just cited one"
- Scripture cure: `callsite_fix` — fixture is the callsite where external env enters tests
