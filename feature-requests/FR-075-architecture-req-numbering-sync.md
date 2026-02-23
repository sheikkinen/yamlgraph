# FR-075: Architecture Requirement Numbering Sync

**Priority:** LOW
**Type:** Documentation
**Status:** Implemented
**Effort:** 0.25 day
**Requested:** 2026-02-23
**Judged:** 2026-02-23
**Implemented:** 2026-02-23

---

## Summary

Synchronize the ARCHITECTURE.md capability summary table with the detailed requirements tables and `scripts/req_coverage.py`. Fix documentation drift that makes requirements untraceable.

---

## Problem

The capability summary table (ARCHITECTURE.md lines 260-288) is out of sync with the actual requirements. A reader cannot find where several requirements belong.

### Missing from Capability Summary Table

| Row | Current Value | Should Include |
|-----|---------------|----------------|
| 3 (Node Execution) | REQ-YG-009 – 011 | + REQ-YG-050 |
| 14 (Graph-Level Streaming) | REQ-YG-048 – 049 | + REQ-YG-065 |
| 17 (Execution Safety Guards) | REQ-YG-055 – 058 | + REQ-YG-059, 060, 061, 062, 064 |
| 28 (Thinking Budget) | *Row doesn't exist* | REQ-YG-083 |

### Evidence

`scripts/req_coverage.py` correctly has:
```python
"CAP-03": ("Node Execution", [..., "REQ-YG-050"]),
"CAP-14": ("Graph-Level Streaming", ["REQ-YG-048", "REQ-YG-049", "REQ-YG-065"]),
"CAP-17": ("Execution Safety Guards", ["REQ-YG-055"..."REQ-YG-062", "REQ-YG-064"]),
"CAP-28": ("Graph-Level Thinking Budget", ["REQ-YG-083"]),
```

But ARCHITECTURE.md capability table does not match.

---

## Note: Outcaller Numbering (OC-XXX vs REQ-YG-XXX)

The `projects/outcaller/` subproject uses `OC-XXX` numbering (OC-000 through OC-007) for project-local tracking. REQ-YG-078–082 (CAP-27) covers the framework-level telco integration requirements, tested in `tests/unit/test_telco_nodes.py` and `tests/integration/test_telco_twilio.py` (34 tests). These requirements and tests are retained.

---

## Proposed Solution

Update ARCHITECTURE.md capability summary table:

```markdown
| 3 | Node Execution | ... | REQ-YG-009 – 011, 050 |
| 14 | Graph-Level Streaming | ... | REQ-YG-048 – 049, 065 |
| 17 | Execution Safety Guards | ... | REQ-YG-055 – 062, 064 |
| 28 | Graph-Level Thinking Budget | `models/graph_schema`, `utils/llm_factory` | REQ-YG-083 |
```

---

## Acceptance Criteria

- [x] ARCHITECTURE.md row 3 includes REQ-YG-050
- [x] ARCHITECTURE.md row 14 includes REQ-YG-065
- [x] ARCHITECTURE.md row 17 includes REQ-YG-059, 060, 061, 062, 064
- [x] ARCHITECTURE.md row 28 exists with REQ-YG-083
- [x] `python scripts/req_coverage.py --strict` passes
- [x] No test tag changes required

---

## Constraints

- No test file modifications
- No code changes
- Documentation-only FR

---

## Related

- `ARCHITECTURE.md` — capability summary table
- `scripts/req_coverage.py` — requirement coverage script
