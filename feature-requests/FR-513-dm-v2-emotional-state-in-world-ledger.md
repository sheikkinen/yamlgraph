# Feature Request: FR-513 - DM v2 Emotional State in World Ledger

**Priority:** HIGH
**Type:** Design / Enhancement
**Status:** ✓ Enforced 2026-06-17 | ✓ Judgment Approved | ✓ Refinements Incorporated
**Effort:** ~0.5 day (prompt update + tests) + ~1-2h refinements
**Discovered:** 2026-06-17 (book_reviewer run 10019 validation)
**Judgment:** [JUDGMENT-FR-513.md](JUDGMENT-FR-513.md) — GRANT with four specific refinements

## Implementation Status (✓ Enforced 2026-06-17)

Boundary-normalized in `examples/dungeon_master/`:

- **`api/world_state.py`** — added `Relationship` model (`between`, `type`,
  `status`, `tensions`, `last_interaction`, `recap_citations`) and a
  `relationships` field on `WorldState`. `parse_world_state` enforces grounding
  at the boundary: bonds without `recap_citations` or with fewer than two named
  parties are dropped (refinements 1 + 4). `format_world_state(ws, *, relationships=...)`
  renders `"active"` (compact, dormant/archived excluded — turn context) or
  `"all"` (status-labelled — close carry-forward) per refinements 2 + 3.
- **`api/turn_ops.py`** — `running_scene` threads inherited **active**
  relationships into turn context (`relationships="active"`).
- **`prompts/chapter_close.yaml`** — system schema + user instruction now extract
  relationships grounded in recap citations; JSON contract lists `relationships`.
- **`tests/test_world_state.py`** — A8 `test_relationships_are_grounded`, A11
  `test_detects_ungrounded_relationships`, A9 `test_format_active_excludes_dormant_and_archived`,
  A10 `test_format_renders_active_relationships_compactly`, plus persistence
  (`test_running_scene_includes_active_relationships_only`) and carry-forward
  (`test_format_all_preserves_dormant_for_carry_forward`). 21/21 world_state +
  167/167 dungeon_master tests green.

A7 (re-run 10019 book review) is a behavioural validation deferred to the next
generation run — the code-path acceptance criteria (A1–A6, A8–A11) are met.

## Summary

Extend the `world_state` ledger carried at chapter boundaries to include `relationships` — emotional and alliance facts that persist across chapter boundaries. Currently, relationships (intimacy, alliance, enmity, hierarchy) evaporate at chapter breaks because they are implicit in proximity, not explicit in state. This causes character connections to reset and emotional arcs to flatten across chapters.

## Problem

**Observation from run 10019 book review:**

The book_reviewer pipeline identified 4 major continuity breaks. All were *emotional state failures*, not mechanical failures:

1. **Hilde & Gunnar's intimacy vanishes** (Ch2→Ch3)
   - Ch2 recaps: "the shape of it was already love"
   - Ch3 opening: they appear as separate functional units

2. **Svala's active tension-management disappears** (Ch2→Ch3)
   - Ch2: "Svala drove the butt of her staff between them"
   - Ch3: no reference to the tension she was maintaining

3. **Arnulf's resurrection has no bridge** (Ch5→Ch6)
   - Ch5 ends: "no longer able to reach her"
   - Ch6 begins: "standing with the group" (no transition)

4. **Character positioning resets**
   - Character relationships don't carry forward across boundaries

**Root cause analysis:**

The seam_packet and world_state are correct for *mechanical* continuity:
- ✓ Dead characters properly gated
- ✓ Inventory/location/faction consistent
- ✓ Hard facts don't contradict
- ✗ Relationships are *implicit* (derived from character proximity)
- ✗ Emotional arcs are *local* (start fresh each chapter)

When turn-1 of Ch3 runs, it receives:
- "Hilde and Gunnar are both alive at location X" (mechanical facts)
- "Hilde and Gunnar are lovers who established intimacy in Ch2" (MISSING — inferred from context window)

The turn loop has no inheritance of emotional state, so it re-derives from scratch based on character proximity. The LLM produces strangers instead of lovers.

## Current Architecture

**world_state (chapter_close.yaml):**
```yaml
world_state:
  - characters: [name, faction, status, location, inventory]
  - objects: [name, holder, location]
  - facts: [discrete state changes]
```

**seam_packet (chapter_close.yaml):**
```yaml
seam_packet:
  - resolved_events
  - open_threads
  - must_carry_facts
  - opening_constraints
  - character_lifecycle
```

Both are extracted deterministically by the chapter-close LLM.

**Design principle:** world_state = "important state of the world" (already mixes mechanical + narrative-significant facts).

Note: world_state already carries narrative-significant data:
- "inventory: concrete things that MATTER to the story"
- Relationships also matter; they should also be in world_state.

## Proposed Solution

### 1. Extend world_state with relationships array

Add `relationships` alongside characters, objects, facts:

```yaml
world_state:
  characters: [name, faction, status, location, inventory]
  objects: [name, holder, location]
  facts: [discrete state changes]
  relationships:  # NEW
    - between: [name1, name2]
      type: [romantic_bond | alliance | enmity | hierarchy]
      status: [active | dormant | archived]  # See refinement 2 below
      tensions: [list of unresolved pressures]
      last_interaction: "brief context from recaps"
      recap_citations: ["Ch2-Turn-3-recap", "Ch3-Turn-1-recap"]  # See refinement 1: grounding validation
```

Example for run 10019:
```yaml
relationships:
  - between: [Hilde, Gunnar]
    type: romantic_bond
     status: active  # active: involved in this/recent chapters
     tensions: [clan_feud, public_secrecy]
     last_interaction: "Ch2: intimate moment; Svala managed proximity"
     recap_citations: ["Ch2-Turn-7-recap: 'the shape of it was already love'"]

  - between: [Hilde, Svala, Reinmar]
    type: alliance
     status: active  # active: ongoing cooperation
    tensions: [survivor resentment, feud pressure]
    last_interaction: "Ch4: defended survivors from violence"
     recap_citations: ["Ch4-Turn-5-recap: 'Svala, Reinmar, and Hilde coordinated defense'"]

  - between: [Hilde, Arnulf]
    type: enmity
     status: archived  # archived: Arnulf returns alive Ch6; relationship conclusively resolved
    tensions: [honor dispute, return fear]
    last_interaction: "Ch5: Arnulf held at truce line"
     recap_citations: ["Ch5-Turn-8-recap: 'no longer able to reach her'", "Ch6-Turn-1-recap: 'standing with the group'"]
```

  **Status Cardinality (Refinement 2):**
  - **active:** Relationship is actively engaged or involved in this chapter or recent chapters. Include in turn context.
  - **dormant:** Relationship is paused or unmentioned for 2+ chapters. *Exclude* from turn context (don't reinvoke stale tensions).
  - **archived:** Relationship is conclusively resolved or dead (they became enemies, alliance broke, character died, etc.). *Exclude* from turn context.
### 2. Update chapter_close.yaml prompt

Add section to extract relationships deterministically:

```yaml
# In system message, after describing facts section:
- relationships: emotional and alliance facts that shape what characters will do.
  Each relationship has:
  - between: the two (or more) characters involved.
  - type: romantic_bond (lovers), alliance (cooperators), enmity (opposed),
    hierarchy (leader/follower), rivalry (competitors).
  - status: active (actively engaged), dormant (separated/paused),
    archived (conclusively concluded).
    - recap_citations: ONE OR MORE recap references proving this relationship exists. If you cannot cite a recap, omit the relationship (refinement 1: grounding validation). Example: ["Ch2-Turn-7-recap: specific quote"].
  - tensions: unresolved pressures (what would rekindle this relationship?
    list of one-line strings).
  - last_interaction: brief reference to when/how this relationship manifested
    in the chapter recaps (cite the recap, don't invent).

# In user message, after recaps:
For relationships: Carry forward from the previous world state every relationship
still true. Add new relationships formed in this chapter's recaps. Update statuses
if this chapter changed a relationship (e.g., intimate moment established lovers;
separation made alliance dormant). Remove relationships conclusively resolved.
Ground every relationship in a specific recap quote, not in the chapter summary.
Never invent relationships without recap evidence. If a relationship cannot be grounded in a turn recap, do not include it.
```

### 3. Update turn_ops.py (Refinement 3: serialization)

In `inherited_world_state()` and `running_scene()`:
- Carry *active* relationships only (exclude dormant/archived)
- Serialize relationships as *compact* strings for turn-1 context, not full JSON objects

**Serialization format:**
```python
# Example: turn-1 context includes this string, not full relationship objects
relationship_context = "; ".join(
  f"{r['between'][0]} and {r['between'][1]}: {r['type']} "
  f"({r['status']}, tensions: {', '.join(r['tensions'])})"
  for r in relationships
  if r['status'] == 'active'  # Exclude dormant/archived
)
# Result: "Hilde and Gunnar: romantic_bond (active, tensions: clan_feud, public_secrecy); Svala and Reinmar: alliance (active, tensions: survivor resentment)"
```

**Why:**
- Prevents context bloat: 24+ relationships as full JSON could exceed token budget
- Excludes stale relationships: dormant/archived don't influence turn-1 scene generation
- Human-readable: turn-1 prompt gets semantic relationships, not serialized dicts
### 3. Update turn_ops.py

In `inherited_world_state()` and `running_scene()`:
- Carry relationships forward from previous chapter
- Include relationship descriptions in turn-1 scene context
- Example: "Hilde and Gunnar are active lovers (established Ch2). Tension: public secrecy."

### 4. Add tests

**Test 1:** Relationships persist across chapters
- Generate Ch2 world_state with Hilde-Gunnar romantic_bond
- Verify Ch3 opening context includes: "Hilde and Gunnar are lovers"
- Verify they act as lovers in Ch3 (not strangers)

**Test 2:** Relationship changes are grounded
- Ch5: Arnulf returns alive; relationship status changes to dormant_separated
- Ch6: verify opening context correctly reflects new status
- Verify Arnulf's reintegration has narrative support (not magical)

**Test 3:** Tensions surface correctly
- If seam carries tension: "clan_feud, public_secrecy"
- Verify turn context includes these as potential drivers
- Verify they influence scene generation (not just ignored)

## Acceptance Criteria

- [x] **A1 - Relationships extend world_state.**
  world_state has optional `relationships` array with between/type/status/tensions/last_interaction fields.

- [x] **A2 - Chapter-close extracts relationships deterministically.**
  chapter_close.yaml prompt updated to extract relationships grounded in recaps.

- [x] **A3 - Relationships persist across chapters.**
  Turn-1 of chapter N+1 receives inherited relationships from chapter N world_state.

- [x] **A4 - Emotional state influences scene generation.**
  Turn context includes relationship descriptions (e.g., "lovers," "alliance," "dormant enmity").

- [x] **A5 - Relationship changes are bounded.**
  New relationships are only added if established in recaps; changes cite specific turns.

- [x] **A6 - Tests validate persistence and grounding.**
  New tests prove relationships persist Ch2→Ch3 and changes are grounded in play, not invented.

- [ ] **A7 - Run 10019 re-run with emotional state fixes continuity breaks.**
  Re-generate run 10019 with updated world_state; book_reviewer shows improved continuity score. *(Deferred: behavioural validation for next generation run.)*

- [x] **A8 - Relationships must be grounded in recaps (refinement 1).**
  Every relationship entry includes recap_citations; ungrounded relationships are rejected.
  Test: `test_relationships_are_grounded()` verifies all relationships have recap evidence.

- [x] **A9 - Dormant/archived relationships excluded from turn context (refinement 2).**
  Long stories don't bloat turn-1 context with stale relationships.
  Test: `test_format_active_excludes_dormant_and_archived()` verifies turn context excludes dormant/archived relationships.

- [x] **A10 - Turn context serializes relationships compactly (refinement 3).**
  Turn-1 context includes compact relationship summaries, not full JSON objects.
  Test: `test_format_renders_active_relationships_compactly()` verifies serialization format and omission of dormant/archived.

- [x] **A11 - Ungrounded relationships are detected or omitted (refinement 4).**
  Hallucinated relationships (not in recaps) are flagged or excluded from turn context.
  Test: `test_detects_ungrounded_relationships()` constructs world_state with hallucinated relationship; verifies system omits it or flags as invalid.

## Value Statement

Stories with complex relationships (romance, alliances, feuds) will maintain emotional coherence across chapter boundaries. Characters will remember their relationships instead of resetting based on context-window proximity. Emotional arcs will build toward climax rather than flatten.

## Alternatives Considered

1. **Keep world_state as-is; add relationship inference to turn loop**
   - Rejected: puts complicated logic downstream instead of at the boundary
   - Makes turn loop responsible for deriving what the seam should have carried
   - Violates "normalize at boundary" principle

2. **Create parallel narrative_state layer**
   - Rejected: introduces dual-ledger complexity
   - world_state is already "important state," relationships are important
   - Single source of truth is simpler than parallel boundaries

3. **Store relationships in character sheets**
   - Rejected: mutates identity to express temporal state (Commandment 5 violation)
   - Character sheets should be stable baselines, not temporal snapshots

4. **Move relationship tracking to seam_packet only**
   - Rejected: seam_packet carries "chapter handoff constraints"; relationships are state, not constraints
   - Mechanically belongs in world_state alongside other important state

## Related

- `feature-requests/FR-507-dm-v2-character-lifecycle-seam-gate.md` (lifecycle boundaries)
- `feature-requests/FR-510-dm-v2-confirmed-dead-prose-exclusion.md` (dead character constraints)
- `feature-requests/FR-512-dm-v2-chapter-open-context-slimming.md` (context slimming)
- `docs/diary/diary-2026-06-17-what-the-book-review-revealed.md` (emotional continuity gap analysis)
- `docs/diary/diary-2026-06-17-emotional-ledger-vs-world-state.md` (design analysis)
- `examples/dungeon_master/prompts/chapter_close.yaml`
- `examples/dungeon_master/api/turn_ops.py`

## Research Notes

**Book Review Run 10019 Findings:**
- Overall score: 3/5 (good premise/character, continuity gaps)
- Continuity score: 2/5 (4 major breaks, all emotional-state related)
- Mechanical continuity: perfect (no lifecycle violations)
- Prose/engagement: degraded (likely due to emotional flatness)

**Design Principle:**
The boundary between chapters (seam) should carry everything the next chapter needs to know. If emotional state matters to the story (proven by review), it belongs in the boundary data.

## Implementation Plan
## Judgment Refinements ✓ INCORPORATED

**Status:** ✓ Judgment Approved 2026-06-17 | ✓ Refinements Incorporated 2026-06-17
**Authority:** [JUDGMENT-FR-513.md](JUDGMENT-FR-513.md)

**What was incorporated into the FR specification:**

✓ **Refinement 1: Grounding Validation**
- Relationships schema now includes `recap_citations: [...]` array (see lines 109-116 in schema)
- Prompt guidance: "Never invent relationships without recap evidence. If a relationship cannot be grounded in a turn recap, do not include it." (section 2)
- Acceptance criterion A8 with test: `test_relationships_are_grounded()`

✓ **Refinement 2: Relationship Status Cardinality**
- Status field updated: `status: [active | dormant | archived]` (line 109)
- Status meanings documented (after line 127): active (include in turn), dormant (exclude, paused >2 chapters), archived (exclude, conclusively resolved)
- Examples updated (lines 130-145) showing active, dormant, and archived relationships
- Acceptance criterion A9 with test: `test_dormant_relationships_excluded_from_turn_context()`

✓ **Refinement 3: Turn-1 Serialization Format**
- New section "3. Update turn_ops.py (Refinement 3: serialization)" with code example for compact serialization
- Python snippet shows filtering for `status == 'active'` and compact string format
- Acceptance criterion A10 with test: `test_turn_context_includes_active_relationships()`

✓ **Refinement 4: False-Positive Detection**
- Acceptance criterion A11 with test: `test_detects_ungrounded_relationships()`
- Test methodology: construct world_state with hallucinated relationship; verify system omits it or flags as invalid

**Status for enforcement:** ✓ READY
All four refinements are now integrated into the FR specification. Enforcement can proceed with risk mitigation in place.

---


**Phase 1 - Design (0.25 day):**
- Finalize relationships schema
- Draft prompt changes for chapter_close.yaml

**Phase 2 - Implementation (0.2 day):**
- Update chapter_close.yaml with relationships extraction
- Update turn_ops.py to carry forward relationships
- Update running_scene() to include relationships in turn-1 context

**Phase 3 - Testing (0.05 day):**
- Add test_relationship_persistence()
- Add test_relationship_grounding()
- Verify existing tests still pass

**Phase 4 - Validation (0.0 day):**
- Re-generate run 10019 with updated code
- Run book_reviewer; verify continuity score improves
- Spot-check: Hilde-Gunnar should persist as lovers, Svala's tension-management should be visible

**Total Effort:** ~0.5 day

## Judgment Refinements (Required Before Enforcement)

**Status:** ✓ Judgment Approved 2026-06-17
**Authority:** See [JUDGMENT-FR-513.md](JUDGMENT-FR-513.md) for full critical review.

**Refinement 1: Grounding Validation**
- Add validation rule to chapter_close.yaml: "Every relationship must cite at least one recap reference."
- If LLM cannot ground a relationship in recap evidence, omit it
- Prevents hallucinated relationships from contaminating world_state
- Test: `test_relationships_are_grounded()` verifies all relationships have recap citations

**Refinement 2: Relationship Status Cardinality**
- Schema includes: `status: [active | dormant | archived]` (not just active/dormant)
- Guidance: Active = involved in this/recent chapters; Dormant = paused >2 chapters; Archived = conclusively resolved
- Pruning prevents long stories from bloating turn context with stale relationships
- Test: `test_dormant_relationships_excluded_from_turn_context()` verifies Ch6 turn-1 excludes archived Ch3 relationships

**Refinement 3: Turn-1 Serialization Format**
- Turn context receives *compact* relationship summaries, not full JSON objects
- Example: "Hilde and Gunnar: active lovers (tension: public_secrecy, last: Ch4 final_scene)"
- Prevents context bloat in long stories (24+ relationships)
- Update: turn_ops.py running_scene() serialization function
- Test: `test_turn_context_includes_active_relationships()` verifies compactness and omission of dormant/archived

**Refinement 4: False-Positive Detection**
- Add test: `test_detects_ungrounded_relationships()`
- Construct world_state with hallucinated relationship (not in recaps)
- Verify system either flags it as ungrounded or omits it from turn context
- Validates boundary normalization is working

**Estimated Refinement Time:** 1-2 hours (mostly documentation + 4 test cases)

**Enforcement blockers:** None
These refinements strengthen robustness without changing core design. Approval to proceed after incorporation.

## Notes

- This FR is high-priority because it blocks narrative quality for multi-chapter stories with complex relationships
- It's a design upgrade (not a bug fix), but it's a blocker for the next story generation
- The work is mostly prompt refinement + carried-state management; no architectural changes
- Can proceed in parallel with other FR work if needed
- Judgment phase identified two moderate risks (hallucination + accumulation); refinements above address both
