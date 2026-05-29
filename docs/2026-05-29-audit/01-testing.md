# Audit Report — Testing & Coverage

**Date**: 2026-05-29 | **Version**: 0.5.4

## Test Execution

```
Command: pytest tests/unit/ -q --no-cov -m "not slow" -n auto
Result:  4032 passed, 139 skipped, 1 xfailed in 48.56s
```

### Breakdown
- **Passed**: 4,032 tests
- **Skipped**: 139 (marked `slow` or conditional on API keys/optional deps)
- **xfailed**: 1 (expected failure, tracked)
- **Failed**: 0

## Code Coverage

```
Command: pytest tests/unit/ --cov=yamlgraph --cov-report=term-missing -q -m "not slow" -n auto
Result:  89.39% coverage (threshold: 70%)
```

| Metric | Value |
|--------|-------|
| Total statements | 7,674 |
| Missed statements | 814 |
| Coverage | 89.39% |
| Required threshold | 70% |
| Margin above threshold | +19.39% |

## Requirement Traceability (ADR-001)

```
Command: python scripts/req_coverage.py
Result:  280/280 requirements covered
```

- **Requirements defined**: 280
- **Tagged tests**: 4,536 unique tests across 4,899 test-req pairs
- **Uncovered requirements**: 0
- **Capabilities**: All 146 capabilities have full test coverage

### Capability Coverage Highlights
| Capability | Reqs | Tests |
|-----------|------|-------|
| CAP-01 Config Loading & Validation | 4 | 322 |
| CAP-02 Graph Compilation | 6 | 133 |
| CAP-03 Node Execution | 5 | 172 |
| CAP-04 Prompt Execution | 6 | 312 |
| CAP-131 Prompt Caching | 12 | 48 |
| CAP-138 Watcher Pipeline FSM | 1 | 68 |
| CAP-15 Expression Language | 2 | 154 |

## Verdict

**PASS** — Testing infrastructure is comprehensive. Coverage well above threshold. Full requirement traceability maintained.
