# Feature Request: FR-294 Pre-commit pytest hook venv PATH isolation

## Status: Enforced

## Problem

The pre-commit pytest hook invokes `.venv/bin/python -m pytest` but does not activate the venv. This means tools installed in the venv (e.g. `statemachine-lint`, `statemachine-validate`, `yamlgraph`) are not on `PATH` when tests spawn subprocesses via `subprocess.run()` or `shutil.which()`.

**Symptom:** Tests that call venv-installed CLI tools fail with `FileNotFoundError` during pre-commit, but pass when the venv is manually activated.

**Example:** `test_dispatcher_lints_clean` calls `subprocess.run(["statemachine-lint", ...])`. The binary exists at `.venv/bin/statemachine-lint`, but pre-commit's PATH doesn't include `.venv/bin/`.

The `requires_fsm_cli` skipif guard uses `shutil.which("statemachine-validate")`, which also fails without venv activation — but the skip correctly fires only when the tool is genuinely absent. When the base conda environment leaks a different Python or when PATH ordering varies, the guard becomes unreliable.

## Current hook

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov'
```

## Objective

Ensure pre-commit pytest hook runs with `.venv/bin` on PATH so that subprocess calls to venv-installed tools succeed.

## Constraints

- Must not require manual venv activation before running `git commit`
- Must work with both `pre-commit run` and `git commit` invocations
- Must not break CI (GitHub Actions installs deps globally, no venv)

## Proposed Fix

```yaml
entry: bash -c 'export PATH=".venv/bin:$PATH" && .venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov -m "not slow" -n auto'
```

This prepends `.venv/bin` to PATH before invoking pytest, making all venv-installed tools available to subprocess calls.

## Acceptance Criteria

- AC-01: Pre-commit pytest hook prepends `.venv/bin` to PATH
- AC-02: Tests calling `shutil.which("statemachine-lint")` find the binary during pre-commit
- AC-03: Tests calling `subprocess.run(["statemachine-lint", ...])` succeed during pre-commit
- AC-04: CI workflow unaffected (no venv in CI)

## Risk

- Low. PATH prepend is idempotent and scoped to the bash subshell.
