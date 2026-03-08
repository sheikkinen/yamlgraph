# Feature Request: FR-155 Fix Stale Reference Doc Count in README

**Priority:** LOW
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

`README.md` line 175 claims "all 18 reference docs" but `reference/` contains 24 documents (excluding `reference/README.md`). Fix the prose and add a guard test to prevent future drift.

## Value Statement

Users navigating the README get an accurate reference doc count, enforced by CI so it never silently drifts when new reference documents are added.

## Problem

`README.md` line 175 states:

> 📚 **Start here:** [reference/README.md](reference/README.md) - Complete index of all 18 reference docs

Actual count of `reference/*.md` excluding `README.md`: **24 documents**.

The sentence was accurate at some earlier point but was never updated as new reference documents were added (expressions.md, intent-questionnaire-pattern.md, scheduling-agents.md, mcp-server.md, tool-call-nodes.md, passthrough-nodes.md, etc.).

This is the same drift class as:
- FR-121: ARCHITECTURE.md provider count went stale
- FR-154: ARCHITECTURE.md capability/requirement count went stale

All three share the root cause: a hardcoded number in prose that drifts when the underlying collection grows.

## Proposed Solution

### Step 1: Fix the prose (GREEN)

Update `README.md` line 175 to reflect the actual count:

```diff
-📚 **Start here:** [reference/README.md](reference/README.md) - Complete index of all 18 reference docs
+📚 **Start here:** [reference/README.md](reference/README.md) - Complete index of all 24 reference docs
```

> **Note:** Implementer must recount at implementation time — the number 24 reflects the count as of this FR's writing.

### Step 2: Add guard test (RED → GREEN)

Create `tests/unit/test_readme_reference_doc_count.py` following the pattern established by `tests/unit/test_architecture_provider_count.py` (REQ-YG-121):

```python
"""Tests for README.md reference doc count consistency.

FR-155: Ensures the reference doc count in README.md matches the actual
number of .md files in reference/ (excluding README.md itself).
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-147")
class TestReadmeReferenceDocCount:
    """README.md must reflect the actual number of reference documents."""

    def test_reference_doc_count_matches_directory(self) -> None:
        """Reference doc count in README must equal files in reference/."""
        ref_dir = REPO_ROOT / "reference"
        actual_count = len([
            f for f in ref_dir.glob("*.md") if f.name != "README.md"
        ])

        readme_path = REPO_ROOT / "README.md"
        text = readme_path.read_text()

        match = re.search(
            r"all (\d+) reference docs", text
        )
        assert match, "Could not find reference doc count in README.md"
        documented_count = int(match.group(1))

        assert documented_count == actual_count, (
            f"README.md says {documented_count} reference docs "
            f"but reference/ contains {actual_count}"
        )
```

### Step 3: Register requirement

- Add REQ-YG-147 to ARCHITECTURE.md requirements section under a new capability (e.g., CAP-49 "README Reference Doc Count Guard").
- Add REQ-YG-147 to `scripts/req_coverage.py` `_ALL_FRAMEWORK_REQS` and `CAPABILITIES`.
- Tag the test with `@pytest.mark.req("REQ-YG-147")`.

> **Note:** The REQ-YG and CAP numbers must be verified at implementation time — use the next available numbers.

## Acceptance Criteria

- [ ] `README.md` reference doc count updated to match actual `reference/*.md` file count
- [ ] Guard test `tests/unit/test_readme_reference_doc_count.py` exists and passes
- [ ] Guard test fails if a new `.md` file is added to `reference/` without updating the count
- [ ] Guard test fails if the count is manually changed to an incorrect number
- [ ] REQ-YG-147 registered in ARCHITECTURE.md, `req_coverage.py`, and tagged on test
- [ ] `python scripts/req_coverage.py --strict` passes
- [ ] `pytest tests/unit/test_readme_reference_doc_count.py -v` passes

## Alternatives Considered

### Option A: Remove the count entirely

Replace "all 18 reference docs" with "all reference docs" so it never goes stale.

**Rejected because:**
- A concrete number helps users gauge documentation scope at a glance
- The guard test pattern is proven (FR-121, FR-154) and prevents drift at near-zero maintenance cost

### Option B: Generate the count dynamically at build time

Use a script to inject the count into README.md during release.

**Rejected because:**
- Adds build complexity for a single number
- The CI guard test achieves the same safety with simpler tooling
- README.md should be human-readable and editable without a build step

## Implementation

| Step | File | Change |
|------|------|--------|
| RED | `tests/unit/test_readme_reference_doc_count.py` | Create guard test (fails on 18 ≠ 24) |
| GREEN | `README.md` L175 | Update count to 24 |
| REGISTER | `ARCHITECTURE.md` | Add REQ-YG-147 under new CAP-49 |
| REGISTER | `scripts/req_coverage.py` | Add 147 to `_ALL_FRAMEWORK_REQS` and `CAPABILITIES` |

### Estimated touch points

- 3 files, ~40 lines added/changed

## Related

- **Pattern precedent:** `feature-requests/FR-121-architecture-provider-count.md` (same drift class)
- **Pattern precedent:** `feature-requests/FR-154-architecture-capability-count-guard.md` (same drift class)
- **Guard test model:** `tests/unit/test_architecture_provider_count.py` (REQ-YG-121)
- **Staleness monitoring:** `feature-requests/FR-095-doc-staleness-monitor.md` (automated drift detection)
- **Orphan docs fix:** `feature-requests/FR-092-ref-readme-orphan-docs.md` (earlier manual fix)
