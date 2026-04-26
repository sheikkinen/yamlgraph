# Feature Request: Exclude Slow Tests from Pre-commit Pytest Hook

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 days
**Requested:** 2026-04-26

## Summary

Update the root pre-commit `pytest` hook to run only fast unit tests by adding `-m "not slow"` to the command.

## Value Statement

Contributors get predictable, fast commit feedback and avoid long-running commits caused by intentionally slow test scenarios.

## Problem

The current pre-commit `pytest` hook runs all unit tests, including tests marked `@pytest.mark.slow`:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov'
```

This conflicts with the existing test-speed pattern already established in the repository (`pytest -m "not slow"` for fast iteration) and can cause commit-time hangs or excessive wait times.

## Objectives

1. Keep commit-time quality gates fast and reliable.
2. Align pre-commit behavior with the documented fast-test workflow in `CLAUDE.md`.
3. Preserve full slow-test coverage outside pre-commit (manual runs and CI).

## Constraints

1. Scope is limited to the root `.pre-commit-config.yaml` `pytest` hook entry.
2. Do not alter test semantics, marker definitions, or CI workflow scope.
3. Keep current hook messaging that directs users to run integration tests separately.

## Proposed Solution

Change the pre-commit hook entry from:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov && echo "" && echo "✓ Unit tests passed. Run integration tests separately:" && echo "  pytest tests/integration/ -v"'
```

to:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov -m "not slow" && echo "" && echo "✓ Unit tests passed. Run integration tests separately:" && echo "  pytest tests/integration/ -v"'
```

### Implementation Approach

1. Edit `.pre-commit-config.yaml` and append `-m "not slow"` to the root `pytest` hook command.
2. Run the pre-commit `pytest` hook to confirm fast-test selection behavior remains functional.
3. Update FR status and related trace notes after implementation.

## Acceptance Criteria

- [x] Root `.pre-commit-config.yaml` `pytest` hook includes `-m "not slow"` in the command.
- [x] `pre-commit run pytest --all-files` executes unit tests without selecting `@pytest.mark.slow` tests.
- [x] Hook still fails on non-slow unit test failures.
- [x] Slow tests remain runnable via `pytest tests/unit/ -q --no-cov -m "slow"`.
- [x] Tests added (or existing test coverage extended) for hook command behavior if repository patterns require configuration assertions.
- [x] Documentation updated if any pre-commit command examples are affected.

## Alternatives Considered

1. Keep running all unit tests in pre-commit and optimize individual slow tests further.
   - Rejected: does not guarantee fast commit feedback and duplicates FR-275’s marker strategy.
2. Remove `pytest` from pre-commit entirely.
   - Rejected: weakens local quality gates.
3. Introduce a separate fast test script wrapper.
   - Rejected: unnecessary indirection; direct hook command change is simpler and consistent with existing patterns.

## Related

- `.pre-commit-config.yaml` (current root pytest hook entry)
- `CLAUDE.md` (documents fast command `pytest tests/unit/ -q --no-cov -m "not slow"`)
- `ARCHITECTURE.md` REQ-YG-275 (slow marker infrastructure and fast/slow execution split)
- `feature-requests/FR-275-test-speed-optimization.md`

## Research Brief

### Competitive Landscape

- **LangGraph** runs tests via make targets (`test`, `test_parallel`, `test_watch`) rather than putting pytest in pre-commit; optimization is done through parallel execution and workflow commands, not a commit-hook slow marker split.  
  Link: https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/Makefile
- **CrewAI** keeps pre-commit focused on lint/type/security hooks (ruff/mypy/pip-audit) and does not run pytest in pre-commit. Test performance is tuned in pytest addopts (`-n auto`, timeout, dist strategy).  
  Links:  
  https://github.com/crewAIInc/crewAI/blob/main/.pre-commit-config.yaml  
  https://github.com/crewAIInc/crewAI/blob/main/pyproject.toml
- **Google ADK** similarly uses pre-commit for formatting/static checks and documents unit tests as a separate explicit step (`pytest ./tests/unittests`).  
  Links:  
  https://github.com/google/adk-python/blob/main/.pre-commit-config.yaml  
  https://github.com/google/adk-python/blob/main/CONTRIBUTING.md
- **OpenAI Agents SDK** separates test execution into make targets (`tests-parallel` with marker `not serial`, plus `tests-serial`) instead of pre-commit pytest gating.  
  Links:  
  https://github.com/openai/openai-agents-python/blob/main/Makefile  
  https://github.com/openai/openai-agents-python/blob/main/pyproject.toml
- **AutoGen** centralizes checks in task runners (`poe test`/`poe check`) and defines targeted markers (e.g., `grpc`), not commit-hook slow-test filtering.  
  Links:  
  https://github.com/microsoft/autogen/blob/main/python/README.md  
  https://github.com/microsoft/autogen/blob/main/python/pyproject.toml

**Cheaper-than-build assessment:** Documentation alone is **not** sufficient here because YAMLGraph already documents `-m "not slow"` while the root hook currently contradicts that behavior. A one-line config fix is cheaper and removes the inconsistency at the enforcement boundary.

### Existing Abstractions

- Root pre-commit pytest hook exists and currently runs all unit tests without marker filtering:  
  `.pre-commit-config.yaml:226-229`
- Slow marker infrastructure already exists (REQ-YG-275):  
  `pyproject.toml:168-176`  
  `ARCHITECTURE.md` (REQ-YG-275 table entry)  
  `capabilities/CAP-126-test-speed-optimization.yaml`
- Fast/slow command pattern is already documented:  
  `CLAUDE.md:61` and `CLAUDE.md:67`
- Existing tests already validate slow-marker behavior and command patterns:  
  `tests/unit/test_fr275_test_speed_optimization.py`
- Another local pre-commit pytest pattern exists in an example project (shows this is tooling-level, not graph-node-level):  
  `examples/rtm-hello/.pre-commit-config.yaml`

### Diary Precedents

- `docs/diary/2026-04-24-reflection-fr-275-test-speed-optimization.md`  
  - Trap: **quick_confidence/symptom_patch**  
  - Heuristic: **Measure before optimizing** (`time pytest tests/unit/ -m "not slow"`).
- `docs/diary/2026-04-21-reflection-fr-261-inquisitor-into-watch-loop.md`  
  - Trap: **infrastructure_self_exempt**  
  - Heuristic: keep pre-commit gates fast; move expensive audits off commit critical path.
- `docs/diary/2026-04-24-reflection-fr-263-hellograph-speed-azure.md`  
  - Evidence that full-suite pre-commit behavior can block unrelated commits; seed suggests narrower commit-time test selection.

### Usage Evidence

- Existing graphs using related abstractions: **0** (this proposal modifies dev tooling, not graph runtime/node abstractions).
- Real-world use cases beyond the proposal:
  - Root contributor workflow (`.pre-commit-config.yaml` pytest hook).
  - Existing example-level pre-commit pytest workflow (`examples/rtm-hello/.pre-commit-config.yaml`).
  - Repository already contains **5** actual `@pytest.mark.slow` annotations in test code, indicating current selective-test infrastructure in active use.

### Classification Signal

- Abstraction level: **pattern**
- Recommended approach: **build**
- Key risk: Excluding slow tests in pre-commit can hide regressions in slow paths unless CI/manual slow-test runs remain explicit and routinely enforced.

## Judgment

**VERDICT:** APPROVE

**Scope:** FROZEN — this FR remains limited to the root `.pre-commit-config.yaml` `pytest` hook command and matching test assertions/documentation consistency checks. No new test abstraction, node type, or CI workflow change is in scope.

**Classification:** **Pattern documentation** (existing abstractions already exist; this change enforces documented fast-test pattern at the pre-commit boundary).

**Acceptance test assessment:** The RED acceptance tests in `tests/unit/test_fr286_precommit_pytest_exclude_slow.py` compile and fail for the correct reason (missing `-m "not slow"` in root pre-commit pytest entry), not for import/fixture/setup errors.

**Authority:** GRANTED — proceed to implementation.
