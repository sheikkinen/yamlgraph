# Diary: Pre-commit Gate Cascade as Requirements Discovery

**Date**: 2026-06-02
**FR**: FR-466 CAP Retirement Support
**Duration**: ~45 min enforcement

## Observation

The RED commit for FR-466 was blocked three times by pre-commit hooks before succeeding:
1. `ruff` auto-fix (re-stage)
2. `ruff-format` auto-fix (re-stage)
3. `req_coverage --strict` phantom REQ-YG-428 (needed CAP-163 YAML file)
4. `cap-architecture-sync` auto-updated ARCHITECTURE.md (re-stage)

Each failure revealed a real constraint: the phantom REQ gate forced creation of the CAP file *before* the implementation existed, which is actually correct — the capability registry is the contract, not the code.

## Trap: Boundary Inventory Before First Commit

The cognitive trap was assuming the RED tests + test file were self-contained. They weren't — `@pytest.mark.req("REQ-YG-428")` created a dependency on the capability registry that `req_coverage --strict` enforces. The test *is* the boundary where the new REQ ID enters the system.

A second trap: using `_import_script` instead of `_load_module` — the helper function name was assumed from the test's intent rather than read from the file. Three reads, not one.

## Heuristic

**Gate cascade as requirements discovery**: When a pre-commit hook fails on a RED commit, the failure is not friction — it's the system telling you your change has undeclared dependencies. Each gate failure reveals a boundary you hadn't inventoried. Count gate failures as discovered requirements, not as obstacles.

## Seed:

Could pre-commit failures be automatically logged as "boundary discoveries" in a structured format, creating a feedback loop where the number of gate failures per commit becomes a metric of change complexity? A commit that triggers 4 gate cascades is objectively more complex than one that triggers 0 — could this inform effort estimation?
