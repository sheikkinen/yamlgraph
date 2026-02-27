# Requirement Cross-Check — Architecture Traceability Audit

**FR-107 Demo** | Phantom Requirement Detection

This example demonstrates the architecture cross-check feature from FR-107.
A YAMLGraph pipeline runs `req_coverage.py` and produces a human-readable
traceability report.

## What FR-107 Does

`req_coverage.py` already verified that every requirement has tagged tests.
FR-107 adds a second check: every requirement ID in `ALL_REQS` must also
have a corresponding row in `ARCHITECTURE.md`. Requirements that exist in
code but lack architecture documentation are **phantom requirements**.

```
Architecture → Requirement → Test
     ↑              ↑           ↑
  ARCHITECTURE.md  ALL_REQS   @pytest.mark.req()
     ↑
  FR-107 closes this gap
```

## Usage

```bash
# Normal mode — warnings only, always exits 0
yamlgraph graph run examples/demos/req-cross-check/graph.yaml --var mode="normal" --full

# Strict mode — exits non-zero if phantom requirements found
yamlgraph graph run examples/demos/req-cross-check/graph.yaml --var mode="strict" --full
```

## Graph Structure

```
START → check → report → END
          │        │
          │        └─ LLM analyzes output → traceability report
          │
          └─ Agent runs req_coverage.py
```

## Sample Output (all clean)

```
REQUIREMENT TRACEABILITY REPORT
======================================================================
Requirements: 84/84 covered
Tagged tests: 1987 unique, 2326 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 222 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 109 tests
  ...
  ✅ CAP-32 eBook Authoring Pipeline: 2/2 reqs, 15 tests
```

LLM report:

```
## Traceability Summary
- Total requirements tracked: 84
- Test coverage status: 84 covered / 0 uncovered

## Architecture Cross-Check (FR-107)
- No phantom requirements detected — all IDs documented in ARCHITECTURE.md

## Verdict
- PASS
```

## Sample Output (phantom requirement detected)

When a requirement is in `ALL_REQS` but missing from `ARCHITECTURE.md`:

```
⚠ 1 requirement(s) missing from ARCHITECTURE.md:
    REQ-YG-999
```

## Direct CLI Usage (no graph needed)

```bash
# Summary
python scripts/req_coverage.py

# Detailed per-test mapping
python scripts/req_coverage.py --detail

# Strict — fail on any gap
python scripts/req_coverage.py --strict
```

## Related

- [FR-107](../../../feature-requests/FR-107-req-architecture-cross-check.md) — Feature request
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) — ADR-001 Requirement Traceability
- [scripts/req_coverage.py](../../../scripts/req_coverage.py) — The cross-check script
