# FR-154: Architecture Capability Count Guard

**Priority:** LOW
**Type:** Bug
**Status:** Superseded by FR-177
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

The ARCHITECTURE.md summary sentence (L273) claims "19 capabilities covering 68 requirements" but the actual capability table contains 46 rows and 108 unique REQ-YG-IDs. The sentence was correct circa CAP-19 and was never updated. Fix the prose and add a guard test to prevent future drift.

## Value Statement

Documentation readers and auditors get an accurate capability/requirement count at the top of the traceability section, enforced by CI so it never silently drifts again.

## Problem

ARCHITECTURE.md L273 states:

> YAMLGraph implements **19 capabilities** covering **68 requirements**.

Actual counts from the capability summary table:
- **46 capability rows** (numbered 1–47, no #29 — retired per FR-089)
- **109 unique REQ-YG-IDs** referenced across the document (FR draft said 108; verified 109 at judgement time)

The sentence was accurate when CAP-19 (MCP Server Interface) was the latest capability. Capabilities 20–47 were added over subsequent releases without updating the introductory sentence. This is the "audit as ritual" trap — the Inquisitor flagged it (D-001) but no automated guard existed.

This follows the same drift pattern that FR-121 solved for provider counts: a hardcoded prose number that goes stale when the underlying table grows.

> **Judge's note — scope freeze:** The test extracts counts dynamically, so the exact number at implementation time will be authoritative. The implementer must verify the live count rather than hardcoding the numbers from this FR.

## Proposed Solution

### Step 1: Fix the prose (GREEN)

Update ARCHITECTURE.md L273 to reflect the actual counts:

```diff
-YAMLGraph implements **19 capabilities** covering **68 requirements**. Each capability maps to specific modules.
+YAMLGraph implements **46 capabilities** covering **109 requirements**. Each capability maps to specific modules.
```

> **Judge's note:** FR draft said 108 requirements; actual count at judgement is 109. Implementer must re-count at implementation time.

### Step 2: Add guard test (RED → GREEN)

Create `tests/unit/test_architecture_capability_count.py` following the pattern established by `tests/unit/test_architecture_provider_count.py` (REQ-YG-121):

```python
"""Tests for ARCHITECTURE.md capability/requirement count consistency.

FR-154: Ensures the capability and requirement counts in the ARCHITECTURE.md
summary sentence match the actual capability table.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-146")
class TestArchitectureCapabilityCount:
    """ARCHITECTURE.md summary must reflect actual capability table counts."""

    def test_capability_count_matches_table(self) -> None:
        """Capability count in summary sentence must equal table row count."""
        arch_path = REPO_ROOT / "ARCHITECTURE.md"
        text = arch_path.read_text()

        # Count data rows in capability summary table (lines starting with "| <digit>")
        table_rows = re.findall(r"^\| \d+", text, re.MULTILINE)
        actual_cap_count = len(table_rows)

        # Extract count from summary sentence
        match = re.search(
            r"implements \*\*(\d+) capabilities\*\*", text
        )
        assert match, "Could not find capability count in ARCHITECTURE.md"
        documented_count = int(match.group(1))

        assert documented_count == actual_cap_count, (
            f"ARCHITECTURE.md says {documented_count} capabilities "
            f"but table has {actual_cap_count} rows"
        )

    def test_requirement_count_matches_table(self) -> None:
        """Requirement count in summary sentence must equal unique REQ-YG-IDs in table."""
        arch_path = REPO_ROOT / "ARCHITECTURE.md"
        text = arch_path.read_text()

        # Extract all unique REQ-YG-IDs from the entire document
        all_reqs = set(re.findall(r"REQ-YG-\d+", text))
        actual_req_count = len(all_reqs)

        # Extract count from summary sentence
        match = re.search(
            r"covering \*\*(\d+) requirements\*\*", text
        )
        assert match, "Could not find requirement count in ARCHITECTURE.md"
        documented_count = int(match.group(1))

        assert documented_count == actual_req_count, (
            f"ARCHITECTURE.md says {documented_count} requirements "
            f"but document contains {actual_req_count} unique REQ-YG-IDs"
        )
```

### Step 3: Register requirement

- Add REQ-YG-146 to the ARCHITECTURE.md requirements section under a new CAP-48 "Architecture Capability Count Guard" (do **not** broaden CAP-37 — single responsibility per capability).
- Add REQ-YG-146 to `scripts/req_coverage.py` `_ALL_FRAMEWORK_REQS` and `CAPABILITIES`.
- Tag the test with `@pytest.mark.req("REQ-YG-146")`.

## Acceptance Criteria

- [x] ARCHITECTURE.md L273 sentence updated to match actual table counts
- [x] Guard test `tests/unit/test_architecture_capability_count.py` exists and passes
- [x] Guard test fails if a new capability row is added without updating the sentence
- [x] Guard test fails if a new REQ-YG-ID is added without updating the sentence
- [x] REQ-YG-146 registered in ARCHITECTURE.md, `req_coverage.py`, and tagged on test
- [x] `python scripts/req_coverage.py --strict` passes
- [x] `pytest tests/unit/test_architecture_capability_count.py -v` passes

## Alternatives Considered

### Option A: Make the count fully dynamic (no hardcoded number)

Replace the sentence with a script-generated value or remove the counts entirely ("YAMLGraph implements capabilities covering requirements as listed below").

**Rejected because:**
- The sentence serves as a quick orientation for readers — removing concrete numbers reduces scanability
- A CI-enforced guard test achieves the same goal (preventing drift) while preserving the human-friendly prose
- Follows the established pattern from FR-121 (provider count guard)

### Option B: Remove the sentence entirely

Delete the summary sentence since the table is right below it.

**Rejected because:**
- The sentence provides context before the reader hits a large table
- Removing documentation to avoid maintaining it violates Commandment 10

## Implementation

| Step | File | Change |
|------|------|--------|
| RED | `tests/unit/test_architecture_capability_count.py` | Create guard test (fails on 19 ≠ 46, 68 ≠ 108) |
| GREEN | `ARCHITECTURE.md` L273 | Update counts to 46 capabilities, 108 requirements |
| REGISTER | `ARCHITECTURE.md` | Add REQ-YG-146 row |
| REGISTER | `scripts/req_coverage.py` | Add 146 to `_ALL_FRAMEWORK_REQS` and `CAPABILITIES` |

### Estimated touch points

- 3 files, ~60 lines added/changed

## Related

- **Pattern precedent:** `feature-requests/FR-121-architecture-provider-count.md` (same drift class)
- **Guard test model:** `tests/unit/test_architecture_provider_count.py` (REQ-YG-121)
- **Numbering gap fix:** `feature-requests/FR-089-docs-capability-numbering.md` (removed strikethrough CAP-29)
- **Origin:** `.chaplain/inbox/fix-architecture-capability-count.md` (Inquisitor D-001)
- **Stale range fix:** `feature-requests/FR-087-stale-req-range.md` (similar doc-drift pattern)

## Judgement

**Verdict: APPROVE — Scope frozen, authority granted.**

**Date:** 2026-03-08

### Evaluation

| Criterion | Assessment |
|-----------|------------|
| Scope clear & minimal? | ✅ Fix one stale sentence + add one guard test. 3 files, ~60 lines. |
| Contradictions? | ⚠️ Minor: FR claimed 108 requirements, actual count is 109. Corrected in this judgement. |
| Acceptance criteria measurable? | ✅ All 7 criteria are concrete and CI-verifiable. |
| Implementation feasible? | ✅ Follows proven FR-121 pattern verbatim. 0.5 day estimate is realistic. |
| Architectural alignment? | ✅ Replicates established guard test pattern. |
| Single responsibility? | ✅ One concern: capability/requirement count drift. |

### Observations

1. **Requirement count off-by-one corrected.** FR draft said 108; `grep -o 'REQ-YG-[0-9]*' ARCHITECTURE.md | sort -u | wc -l` yields 109. The test extracts counts dynamically, so the exact number at implementation time is authoritative — the implementer must verify rather than blindly copy from this FR.

2. **CAP assignment resolved.** FR left an open question about broadening CAP-37 vs creating CAP-48. Judgement: create CAP-48 "Architecture Capability Count Guard" to preserve single responsibility per capability.

3. **Regex scope is safe.** The `^\| \d+` regex matches only lines 279–324 in ARCHITECTURE.md (the capability summary table). No other numbered tables exist in the document. If one is added in the future, the test would over-count and fail visibly — a safe failure mode.

4. **The `test_requirement_count_matches_table` searches the entire document** for REQ-YG-IDs rather than scoping to the capability table. This is acceptable because all REQ-YG-IDs in ARCHITECTURE.md appear in the requirements/capability sections. If a REQ-YG-ID were added to prose outside these sections, the test would catch the discrepancy — again, a safe failure mode.

### Binding Constraints

- Implementer **must re-count** capability rows and unique REQ-YG-IDs at implementation time; do not hardcode 46/109 without verification.
- Use CAP-48 for the new capability (not CAP-37).
- Follow TDD: commit RED (failing test, SKIP=pytest) then GREEN (fix) separately.
