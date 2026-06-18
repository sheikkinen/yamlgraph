# Emotional Continuity Ledger vs. World State: A Design Analysis

**Date:** 2026-06-17
**Context:** Book review identified emotional continuity gap; now examining whether to extend world_state or create parallel layer
**Question:** Where should emotional/narrative state live in the seam?

## Current State: World State Structure

The `world_state` prompt in `chapter_close.yaml` captures:

```
world_state:
  - characters: [name, faction, status, location, inventory]
  - objects: [name, holder, location]
  - facts: [discrete state changes]
```

Separately, `seam_packet` carries:

```
seam_packet:
  - resolved_events: [what's conclusively over]
  - open_threads: [unresolved pressures]
  - must_carry_facts: [hard facts chapter N+1 must preserve]
  - opening_constraints: [do/don't constraints]
  - character_lifecycle: [dead/alive/present gates]
```

**Design philosophy:** world_state is *mechanical* (facts, items, locations). seam_packet is *structural* (what's resolved, what threads hang).

## The Gap We Identified

Book review shows Hilde & Gunnar's intimacy (established in Ch2) vanishes in Ch3 because:

1. World state carries: "Hilde: status=alive, location=higher_ground, inventory=[...]"
2. World state does NOT carry: "Hilde and Gunnar are lovers; this relationship is a primary narrative driver"
3. Turn-1 of Ch3 sees the mechanical facts but not the emotional fact
4. Scene generation re-derives from scratch and produces strangers instead of lovers

**Missing:** A layer that carries emotional *facts* the way world_state carries mechanical facts.

## Three Design Options

### Option 1: Extend world_state to include emotional facts

Add a `relationships` array to world_state:

```yaml
world_state:
  characters: [...]
  objects: [...]
  facts: [...]
  relationships:  # NEW
    - between: [Hilde, Gunnar]
      type: romantic_bond
      status: active_lovers
      intensity: 5/5
      tensions: [clan_feud, public_secrecy]
      last_scene: "Ch2: intimate moment, Svala separated them"
```

**Pros:**
- Follows existing pattern (world_state = everything that's true about the world)
- Single source of truth
- Simpler boundary (no parallel ledgers)
- Prompt can treat relationships same as objects/characters

**Cons:**
- world_state becomes larger and more complex
- Mixed concerns (mechanical facts + emotional facts)
- Harder to reason about what counts as "state"
- Narrative intent bleeds into mechanical ledger

### Option 2: Extend seam_packet to include emotional ledger

Add `emotional_state` to seam_packet:

```yaml
seam_packet:
  resolved_events: [...]
  open_threads: [...]
  must_carry_facts: [...]
  opening_constraints: [...]
  character_lifecycle: [...]
  emotional_state:  # NEW
    - name: Hilde-Gunnar
      type: romantic_bond
      status: active_lovers
      narrative_role: primary_driver
      last_interaction: "Ch2: physical intimacy, Svala managed proximity"
      unresolved_tension: [public_reveal, clan_response]
```

**Pros:**
- Keeps mechanical and narrative separate
- Seam_packet already carries chapter-handoff logic
- Aligns with existing pattern (seam = what the next chapter must know)
- Emotional ledger is explicitly "what carries over," not just facts

**Cons:**
- seam_packet becomes heavier
- Adds complexity to an already complex structure
- Requires separate LLM extraction logic

### Option 3: Create parallel "narrative_state" alongside world_state

Keep world_state pure (mechanical), add separate narrative_state:

```
world_state:
  characters: [...]
  objects: [...]
  facts: [...]

narrative_state:
  relationships: [...]
  tensions: [...]
  arc_momentum: [...]
  emotional_beats: [...]
```

**Pros:**
- Clear separation of concerns
- Narrative_state is optional/domain-specific
- world_state stays simple and mechanical
- Easier to add more narrative layers later

**Cons:**
- Two parallel boundary structures
- More complex choreography at chapter boundaries
- Requires both to be carried forward, both to be validated

## Analysis: Which Fits the Architecture?

### The One Law Says: Normalize at Boundaries

From Scripture: "Normalize at the boundary where external data enters, not downstream."

The boundary between chapters is the seam. What the chapter-close LLM extracts is the contract for chapter-open.

**Currently extracted:** mechanical facts + structural constraints

**Missing:** emotional facts

The question is: are emotional facts *mechanical* (properties of the world that are true/false) or *narrative* (properties of the story structure)?

**Answer:** They're both.

- "Hilde and Gunnar are lovers" is a *mechanical fact* (it's either true or false; it affects what they'll do)
- "Their relationship is a primary narrative driver" is a *narrative fact* (it's true or false about the story structure; it affects what should happen next)

### Current world_state Already Has Narrative Content

Looking at the prompt again: "faction is a fixed token" and "inventory is concrete things that matter to the story."

This already mixes:
- Pure mechanics: location (mechanical)
- Narrative significance: inventory (only "concrete things that MATTER")

So world_state is not purely mechanical; it's "the important state of the world."

**Implication:** The boundary is not "mechanical vs. narrative." It's "important vs. unimportant."

### The Real Question: What Matters?

In a survival story: location, inventory, status matter.
In a romance within that story: relationships and emotional arcs also matter.

The book review proved that without emotional state, relationships evaporate. Therefore: **emotional state is important state.**

By the existing design, it belongs in world_state.

## Recommendation: Extend world_state (Option 1, with Caveats)

Extend world_state to include a `relationships` array alongside characters, objects, facts.

**Rationale:**
1. World_state is already "important state," not purely mechanical
2. Relationships are important state for narrative continuity
3. Follows existing pattern (single source of truth at boundary)
4. Simpler than parallel ledgers
5. Chapter-close LLM can extract relationships same way it extracts object locations

**Implementation:**

1. Update chapter_close.yaml prompt:
   - Add section: "relationships: Who matters to whom, emotionally?"
   - Examples: "Hilde and Gunnar: romantic_bond, active_lovers"
   - Rules: "Carry forward relationships unless they've changed; add new ones formed this chapter"

2. Update turn-1 opening context:
   - Include relationships alongside character descriptions
   - Scene generation knows: "Hilde and Gunnar are lovers; this relationship is a narrative driver"

3. Update tests:
   - Verify relationships persist across chapter boundaries
   - Verify relationship changes are grounded in chapter recaps

## What This Does NOT Do (Important)

This does NOT reintroduce synopsis-level framing:

- Synopsis says: "Romance... converges"
- World state would say: "Hilde and Gunnar are lovers as of Ch2, with ongoing public/secret tension"

- Synopsis is outline (what the author planned)
- World state is mechanics (what actually is true)

The distinction holds. We're carrying forward established facts, not book-level summary.

## Design Principle: Two Layers of Facts

**Layer 1 - Character/Object Facts (existing):**
- "Hilde is at location X with inventory [weapon, pouch]"
- "Svala has a staff"
- "A truce was struck"

**Layer 2 - Relationship Facts (new):**
- "Hilde and Gunnar are intimate lovers"
- "Svala is actively managing their proximity"
- "Arnulf and Hilde have unresolved conflict over honor"

Both are facts. Both matter. Both should be carried forward.

## Tension to Resolve: What Counts?

The seam_packet already has character_lifecycle for managing presence/absence gates.

If we add relationships, do we also need:
- Power dynamics?
- Loyalty states?
- Trust levels?
- Desire vectors?

**Answer:** No. Start with relationships. If we later need a finer-grained emotional ledger, we can expand.

The minimal model:
```yaml
relationships:
  - between: [name1, name2]
    type: [romantic_bond | alliance | enmity | hierarchy]
    status: [active | dormant | resolved]
    tensions: [list of unresolved pressures]
    last_scene: "brief context from chapter recaps"
```

This handles:
- Romantic bonds (Hilde-Gunnar)
- Alliances (Hilde-Svala-Reinmar against feud)
- Enmities (Hilde-Arnulf blood feud)
- Hierarchies (Hilde as war leader)

## Implementation Effort

**Prompt changes:** 1-2 hours (add relationships section to chapter_close.yaml)
**Code changes:** 1-2 hours (parse relationships from JSON, carry forward in inherited_world_state)
**Tests:** 2-3 hours (validate persistence, test changes grounded in recaps)

**Total:** ~0.5 day (lighter than a full FR)

But this should be a formal FR because it changes the seam contract.

## Seed: Can Relationships Be Deterministic?

Current world_state is extracted deterministically (facts the LLM observes).

If we add relationships, how do we ensure they're:
1. Grounded in what actually happened (not invented)
2. Deterministic (same recaps → same relationships)
3. Testable (we can verify a relationship is valid)

Example deterministic rules:
- If chapter recaps show "Hilde and Gunnar had intimate moment," add romantic_bond
- If recaps show Svala "managing their proximity," add tension: public_secrecy
- If recaps show "Arnulf held back," mark Hilde-Arnulf as "dormant" (separated)

Can we encode these rules? Or does the LLM have to infer?

---

**Analysis Closed:** 2026-06-17 20:45
**Recommendation:** Option 1 — extend world_state with relationships array
**Next Steps:**
1. Write FR: "Emotional State in World Ledger" (design, not bug fix)
2. Prototype in chapter_close.yaml with relationships section
3. Add tests for persistence and change grounding
4. Validate on run 10019 re-run to see if Hilde-Gunnar intimacy persists Ch2→Ch3

**Key Insight:**
The seam is the boundary where external play data becomes internal state. If relationships matter to the story (proven by book review), they belong in the state ledger, not left as implicit context-window proximity.

The mistake would be to add more complex turn-level reasoning to compensate for incomplete seam data. The fix is to carry the data forward correctly.
