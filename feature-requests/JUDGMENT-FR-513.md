# Judgment: FR-513 - DM v2 Emotional State in World Ledger

**Date:** 2026-06-17
**Status:** GRANT with refinements
**Verdict:** Problem is clearly evidenced; solution is well-scoped and architecturally sound. Two moderate risks require prompt refinement before enforcement.

## Problem Validation: ✓ SOLID

**Evidence base:**
- Book review run 10019 identified 4 continuity breaks
- All 4 are emotional-state failures, not mechanical failures
- Mechanical continuity checks all pass (lifecycle gating, inventory, faction)
- Root cause is clear: emotional state is implicit (derived from proximity), not explicit (carried in seam)

**Diagnosis is correct:**
- When turn-1 of Ch3 runs, the LLM receives mechanical facts but not emotional facts
- The LLM re-derives relationships from character proximity alone
- Result: lovers become strangers, alliances become random groupings

This is not speculation; it's observed in the generated text and confirmed by the reviewer.

## Solution Scope: ✓ WELL-BOUNDED

**What's in scope:**
- Relationships (between, type, status, tensions, last_interaction)
- Optional array extension to world_state (doesn't break existing code)
- Deterministic extraction from recaps (grounded, not invented)
- Carry forward at chapter boundaries

**What's out of scope (correctly):**
- Power dynamics, desire vectors, trust levels (too fine-grained for v1)
- Conversation transcripts or detailed interaction logs (too heavy)
- Predictive relationship evolution (what might happen next)
- Character motivations beyond relationship facts

**Effort estimate is realistic:**
- 0.25 day: prompt design ✓
- 0.2 day: code changes (mostly carry-forward logic) ✓
- 0.05 day: tests ✓
- Total: 0.5 day ✓

## Architecture Alignment: ✓ STRONG

**Adheres to existing principles:**

1. **One Law: "Normalize at boundary, not downstream"**
   - ✓ Relationships go in world_state (the seam boundary)
   - ✓ Not added as turn-level inference
   - ✓ Not recovered downstream in scene generation

2. **Single source of truth**
   - ✓ Relationships live in world_state, not parallel ledgers
   - ✓ Chapter-close extracts once; all downstream code references it

3. **"Carry forward established facts, not invented"**
   - ✓ Prompt specifies: ground relationships in recaps
   - ✓ Not: invent relationships from character summary

4. **Existing pattern extension**
   - ✓ world_state already mixes mechanical + narrative-significant facts
   - ✓ Relationships are narrative-significant facts
   - ✓ Consistent with "inventory: concrete things that MATTER"

## Risk Analysis

### Risk 1: LLM Hallucination of Relationships ⚠️ MODERATE

**Scenario:** Chapter-close LLM invents a relationship not established in the recaps.
- Example: "Hilde and Reinmar are romantically involved" (not in recaps)
- This would contaminate world_state and propagate to next chapter

**Mitigation (required before enforcement):**
1. Strengthen prompt rule: "Every relationship MUST cite a specific recap line. No relationship without evidence."
2. Add validation function: scan relationships array for those without grounding
3. Add test: ensure invalid relationships are rejected or logged

**Current spec says:** "Ground in recaps; don't invent" — but no enforcement mechanism.

**Refinement needed:** Add validation rule to chapter-close.yaml:
```yaml
validation:
  - "Every relationship entry must include a recap_citations field listing which turn(s) established it"
  - "If citations field is empty or missing, reject the relationship as ungrounded"
```

### Risk 2: Relationship Accumulation Over Long Stories ⚠️ MODERATE

**Scenario:** A 12-chapter story accumulates 24+ relationships. Turn-1 context explodes.
- Turn loop receives: "Here are 24 relationship entries to consider"
- Context window grows; noise increases
- Risk: LLM loses signal in volume

**Current mitigation:** Not addressed in spec.

**Refinement needed:** Pruning rules:
1. Mark relationships as "active" (ongoing), "dormant" (paused), or "archived" (concluded)
2. Only include "active" relationships in turn-1 context
3. Guidance: "If a relationship is unmentioned for 3+ chapters, mark as dormant; if conclusively resolved, move to archived"

**Example:**
```yaml
relationships:
  - between: [Hilde, Gunnar]
    type: romantic_bond
    status: active  # Include in turn context

  - between: [Hilde, OldRival]
    type: enmity
    status: archived  # Resolved in Ch5; don't include in Ch6+ context
```

### Risk 3: Turn-1 Context Bloat ⚠️ MINOR

**Scenario:** running_scene() includes full relationship objects in turn-1 prompt.
- Each relationship has 5 fields; 5 relationships = 25 lines of context
- Context space is finite

**Current mitigation:** Not specified in the FR.

**Refinement needed:** Specify serialization format for turn-1 context:
```yaml
# Compact format for turn-1 (not full JSON):
Relationships:
- Hilde and Gunnar: active lovers (tension: public secrecy)
- Svala, Reinmar: alliance managing feud pressure
```

Instead of:
```json
{
  "relationships": [
    {"between": ["Hilde", "Gunnar"], "type": "romantic_bond", ...},
    ...
  ]
}
```

### Risk 4: Schema Collision with Other Stories ⚠️ MINOR

**Scenario:** Another story uses different relationship types (e.g., "patron/client," "spiritual_guide").
- Current spec lists: romantic_bond, alliance, enmity, hierarchy
- Is this list extensible? Closed? Validated?

**Current spec:** Open (any type is allowed).

**Risk:** Inconsistent type naming across stories. Recommend:
- Add enum validation: types should be from known set
- Or keep open but document common types
- Lean: keep open, but add note that new types should be rare

## Acceptance Criteria Review: CLEAR BUT INCOMPLETE

**A1-A6:** Clear and testable ✓
**A7:** Requires actual run 10019 re-generation ✓ (good final gate)

**Missing test criteria:**
- **A8:** Hallucinated relationships are detected/rejected
- **A9:** Long stories don't explode turn context with relationships
- **A10:** Pruning rules work (dormant/archived relationships don't leak into turn context)

## Judgment: GRANT WITH REFINEMENTS

**Approved for enforcement with these refinement commits:**

### Refinement 1: Grounding Validation
Update chapter_close.yaml prompt:
```yaml
validation:
  - "Every relationship entry must include at least one quoted recap reference."
  - "If you cannot cite a recap establishing a relationship, omit it."
```

Add test: `test_relationships_are_grounded()`
- Verify all relationships have recap citations
- Reject relationships without evidence

### Refinement 2: Relationship Status Cardinality
Update schema:
```yaml
relationships:
  - status: [active | dormant | archived]  # Not just active/dormant/...
```

Add guidance: "Active: involved in this or recent chapters. Dormant: paused >2 chapters. Archived: conclusively resolved."

Add test: `test_dormant_relationships_excluded_from_turn_context()`
- Verify Ch6 turn-1 doesn't include archived relationships from Ch3

### Refinement 3: Turn-1 Serialization Format
Update turn_ops.py running_scene():
```python
# Don't pass full relationship objects; serialize as compact strings
relationship_context = "; ".join(
    f"{r['between'][0]} and {r['between'][1]}: {r['type']} "
    f"({r['status']}, tensions: {', '.join(r['tensions'])})"
    for r in relationships
    if r['status'] == 'active'
)
```

Add test: `test_turn_context_includes_active_relationships()`
- Verify turn-1 context includes compact relationship summaries
- Verify dormant/archived relationships are omitted

### Refinement 4: False-Positive Detection
Add test: `test_detects_ungrounded_relationships()`
- Manually construct a world_state with hallucinated relationship
- Pass through to turn context
- Verify system flags it as ungrounded or omits it

## Enforcement Gate

Before moving to enforcement phase:

1. **Update FR-513** with three refinements above
2. **Add four test cases** (A8-A11) to acceptance criteria
3. **Update chapter_close.yaml** with validation rules
4. **Update turn_ops.py** with relationship serialization format

Estimated time to complete refinements: 1-2 hours (mostly documentation).

## Why This Grant is Conditional

The core insight is solid and the architecture is sound. But the spec has three implementation gaps:
1. No defense against LLM hallucination
2. No pruning strategy for long stories
3. No context serialization specification

These are not architectural flaws; they're engineering details. With these refinements, the FR is enforcement-ready.

---

**Judgment Decision:** ✓ **GRANT** (with refinements)

**Next Step:** Incorporate refinements into FR-513, then proceed to enforcement phase.

**Effort Impact:** Refinements add ~1-2 hours to planning; reduce enforcement risk significantly.

**Timeline Estimate (with refinements):**
- Planning refinements: 1-2h
- Enforcement: 0.5d (original estimate unchanged)
- Validation: 0.25d (run 10019 re-generation + book_reviewer)
- **Total: ~1 day of effort**

---

## Additional Observation: Relationship-Driven Test Strategy

Once FR-513 is enforced, consider a new test class:

```python
class TestRelationshipContinuity:
    """Validate that relationships persist and evolve correctly across chapters."""

    def test_established_lovers_remain_lovers(self):
        """Ch2 establishes romance; Ch3 maintains it."""

    def test_new_alliance_established_in_recap(self):
        """When recaps show cooperation, relationship added."""

    def test_dormant_relationship_excluded_from_context(self):
        """Paused relationships don't influence next chapter unnecessarily."""

    def test_resolved_relationship_archived(self):
        """Enemy becomes ally; old enmity moves to archived."""
```

This would become the *regression suite* for emotional continuity (analogous to lifecycle regression tests for character presence).

---

**Judgment Closed:** 2026-06-17 20:50
**Status Update:** FR-513 is GRANTED (conditional on refinements)
**Authority:** Code enforcement pending refinement incorporation
