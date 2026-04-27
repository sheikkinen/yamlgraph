# Reflection: FR-294 Pre-commit venv PATH isolation

**Date:** 2026-04-27
**FR:** FR-294
**Trap encountered:** downstream_fix — test failures from missing CLI tools were diagnosed at the test level, but the root cause was the pre-commit hook's missing PATH

## What happened

During FR-293 enforcement, `test_dispatcher_lints_clean` failed with `FileNotFoundError: statemachine-lint`. The tool existed in `.venv/bin/` but pre-commit doesn't activate the venv — it only calls `.venv/bin/python`. Subprocess calls from within tests couldn't find venv-installed CLI tools.

## Insight

**The One Law:** The boundary is the pre-commit hook entry point. PATH must be normalized there, not worked around in individual tests with `shutil.which()` guards. One `export PATH=".venv/bin:$PATH"` at the entry fixes all downstream subprocess calls.

## Seed

Should all pre-commit hooks that invoke `.venv/bin/python` also prepend the PATH? Are there other hooks (ruff, vulture, radon) that might benefit from consistent venv PATH exposure?
