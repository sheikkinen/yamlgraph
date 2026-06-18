# Diary: FR-513 Refinements Incorporated

**Date:** 2026-06-17
**Phase:** Planning → Refinement Incorporation → Ready for Enforcement
**Status:** ✓ Complete

## Summary

FR-513 (Emotional State in World Ledger) passed judgment with four specific refinements required before enforcement. All four have been incorporated into the FR specification.

## What Changed

### Refinement 1: Grounding Validation ✓
**What:** Prevent hallucinated relationships from contaminating world_state

**Incorporated:**
- Schema now includes `recap_citations: [...]` array
- Prompt guidance: "Never invent relationships without recap evidence"
- Example shows citations: `["Ch2-Turn-7-recap: 'the shape of it was already love'"]`
- Acceptance criterion A8 with test `test_relationships_are_grounded()`

**Why this matters:**
The LLM could invent relationships like "Hilde and Reinmar have romantic tension" when they never interacted. Grounding citations prove each relationship is established in the actual text, not hallucinated.

---

### Refinement 2: Relationship Status Cardinality ✓
**What:** Prevent long stories from bloating turn context with stale relationships

**Incorporated:**
- Status field updated from 4 values to 3 clear values:
  - `active`: actively engaged in this/recent chapters → include in turn context
  - `dormant`: paused/unmentioned >2 chapters → exclude from turn context
  - `archived`: conclusively resolved/dead → exclude from turn context
- Examples updated showing all three states
- Acceptance criterion A9 with test `test_dormant_relationships_excluded_from_turn_context()`

**Why this matters:**
A 12-chapter story could accumulate 24+ relationships. If all of them get passed to turn-1 context, it becomes noise. Archiving old relationships keeps turn context focused on *current* emotional tensions.

---

### Refinement 3: Turn-1 Serialization Format ✓
**What:** Prevent context bloat by serializing relationships compactly

**Incorporated:**
- New section "3. Update turn_ops.py (Refinement 3: serialization)" with code example
- Python snippet shows filtering for `status == 'active'` and compact string format:
  ```python
  relationship_context = "; ".join(
      f"{r['between'][0]} and {r['between'][1]}: {r['type']} "
      f"({r['status']}, tensions: {', '.join(r['tensions'])})"
      for r in relationships
      if r['status'] == 'active'
  )
  ```
- Acceptance criterion A10 with test `test_turn_context_includes_active_relationships()`

**Why this matters:**
Full JSON objects for each relationship consume tokens. Compact strings like "Hilde and Gunnar: romantic_bond (active, tensions: clan_feud, public_secrecy)" are human-readable and token-efficient.

---

### Refinement 4: False-Positive Detection ✓
**What:** Verify system detects/omits ungrounded relationships

**Incorporated:**
- Acceptance criterion A11 with test `test_detects_ungrounded_relationships()`
- Test methodology: construct world_state with hallucinated relationship; verify system omits it or flags as invalid
- Validates boundary normalization is working

**Why this matters:**
If the system can't detect a hallucinated relationship, refinement 1 fails. This test verifies the guard is actually working.

---

## Acceptance Criteria Status

**Original (A1-A7):** Already well-defined, now reinforced by refinements

**New (A8-A11):** Added from judgment refinements
- A8: Grounding validation
- A9: Pruning for long stories
- A10: Compact serialization
- A11: False-positive detection

**Total:** 11 acceptance criteria → enforcement ready

---

## Files Changed

- `feature-requests/FR-513-dm-v2-emotional-state-in-world-ledger.md`:
  - Schema updated with `recap_citations` field
  - Status values narrowed to active|dormant|archived
  - Turn serialization format added
  - Acceptance criteria A8-A11 added
  - Status header updated to show refinements incorporated

- `feature-requests/JUDGMENT-FR-513.md`: Created (judgment document)

---

## Ready for Enforcement

✓ Problem validated (book review evidence)
✓ Solution well-scoped (no architectural changes)
✓ Risks identified and mitigated (4 refinements)
✓ Acceptance criteria clear and testable (11 total)
✓ Implementation plan documented (~0.5 day effort)

**Next action:** Begin enforcement phase (Phase 1 - Design)

---

## Lessons (for Scripture graduation)

**Trap → Cure Pairing:**

**Trap:** *Boundary validation under-specified*
When designing a state boundary (like world_state), it's tempting to say "LLM extracts this." But without validation rules, the LLM can hallucinate. The gap between "seems right" and "is provably correct" is exactly where bugs hide.

**Cure:** *Validation rules are first-class design artifacts*
- Every field that comes from the LLM needs an acceptance rule
- Grounding citations (recap_citations) are as important as the data they validate
- Pruning rules (active|dormant|archived) are infrastructure, not error handling
- Tests for hallucination detection are regression suite, not edge cases

**Seed:** Should we add a linter rule that flags world_state fields without acceptance criteria in the YAML graph? E.g., if chapter_close.yaml extracts a new field, the linter should require acceptance criterion in graph.yaml before deployment.
