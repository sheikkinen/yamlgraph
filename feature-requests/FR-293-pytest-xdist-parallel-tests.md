# Feature Request: FR-293 pytest-xdist parallel test execution

## Status: Judged — Approved with amendments

## Problem

Unit test suite takes ~42s with `-m "not slow"` (64s before slow markers). With 3800+ tests across 238 files, the bottleneck is sequential execution on a 12-core machine. Collection alone takes 3.2s. Subprocess-heavy tests (git init, bash scripts) dominate the top 20 files.

## Objective

Add `pytest-xdist` for parallel test execution. Target: fast-run (`-m "not slow"`) under 20s on 12 cores.

## Constraints

- Must not break existing test isolation (tmp_path, autouse fixtures)
- Must not interfere with pre-commit hook pytest invocation
- Must preserve `--no-cov` fast path (coverage + xdist has known overhead)
- Session-scoped fixtures must be compatible with worker forking

## Acceptance Criteria

- AC-01: `pytest-xdist` listed in `pyproject.toml` `[project.optional-dependencies]` under `dev`
- AC-02: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` completes under 20s
- AC-03: All existing tests pass with `-n auto` (no isolation failures)
- AC-04: Pre-commit pytest hook updated with both `-n auto` AND `-m "not slow"`
- AC-05: CLAUDE.md updated with parallel test commands
- AC-06: `dependency-rationale.md` entry added for pytest-xdist
- AC-07: CI pytest invocation updated or explicitly excluded from xdist scope
- AC-08: Coverage + xdist produces correct report (no missing lines)

## Implementation Approach

0. Benchmark xdist startup overhead on small test subset to validate <20s target
1. Add `pytest-xdist` to dev dependencies
2. Add dependency rationale entry
3. Run full test suite with `-n auto` to identify isolation failures
4. Fix any session-scoped fixture incompatibilities (e.g., shared temp dirs)
5. Update pre-commit pytest hook with `-n auto -m "not slow"`
6. Update CI workflow or document exclusion rationale
7. Verify coverage + xdist correctness (`--dist loadscope` or `--cov-append`)
8. Update CLAUDE.md with parallel commands

## Risk

- Some tests may share state via module-level variables or singletons (e.g., LLM factory cache)
- ~~`conftest.py` session-scoped `_clean_git_env` fixture may not propagate to workers~~ **Cleared**: each worker forks and runs session fixtures independently; `os.environ` mutation is idempotent
- Coverage collection with xdist requires `pytest-cov` `--dist loadscope` or `--cov-append` flag
- xdist spawns 12 workers (~2-3s init overhead); may negate gains on small subsets — benchmark first
- CI runners have different core counts than local (2-4 cores typical) — `-n auto` adapts but speedup varies

## Evidence

Current timing profile (from `tmp/durations.txt`):
- Total: 42s (fast run), 104s (full run)
- Collection: 3.2s
- Top 20 files: ~35s cumulative (subprocess-heavy)
- 12 CPU cores available
- Expected parallel speedup: 3-5x on subprocess-heavy tests (I/O bound, not CPU bound)
