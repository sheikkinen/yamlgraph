# FR-640: novel_fandom — Enriched World Model

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-07-01

## Summary

Extend the FR-637 canon schema with world-content fields derived from the
production-tested `langgraph-poc-narrator` and `langgraph-npc` data models:
motivation triad on characters
(`driving_force`/`wants`/`needs`/`fears`/`arc_summary`/`role`), reactive
`triggers` (from the NPC project), atmosphere and sensory detail on locations,
and a new `Rule` page type for world constraints. Seed canon updated to
exercise the new fields.

## Value Statement

The plot pathfinder (FR-638) needs to *read tensions* from the canon — character
wants≠needs, fears as obstacle levers, world rules as solution constraints. The
current schema has goals but not the inner-conflict split that generates dramatic
beats. This FR adds the fuel the pathfinder consumes.

## Problem

The POC narrator (`src/langgraph-poc-narrator`) evolved a richer world model
through ~6 months of iterative novel generation. Comparison reveals FR-637's
schema lacks five concepts the POC found essential:

1. **Motivation triad.** The POC's `CharacterProfile` has `driving_force` (why
   they act), `wants` (conscious desire), `needs` (unconscious need). The tension
   between wants and needs is the engine of internal conflict. FR-637 has only a
   flat `goals` list — it records *what* but not the *wants-vs-needs* split.

2. **Fears.** A character's fears are the levers that antagonists pull and that
   plot complications activate. Without them, the pathfinder can't generate
   obstacle-driven beats. Absent from FR-637.

3. **Character role and arc.** `role` (protagonist/antagonist/supporting/minor)
   determines POV budget and importance weighting. `arc_summary` ("grief-stricken
   orphan → curse-breaker") is a compact trajectory. Both absent.

4. **Location atmosphere and sensory.** The POC's `LocationProfile` has `atmosphere`
   (mood words: isolated, windswept, haunted) and `sensory` (salt spray, creaking
   wood, cold spots) plus a typed `location_type`. FR-637's `Location` has only a
   `description` string — a catch-all that doesn't decompose for prose generation.

5. **Triggers.** The `langgraph-npc` project's character schema includes
   `triggers` — reactive rules like "if someone mentions military service →
   becomes hostile". A trigger is a compressed beat-generator: the condition is
   the setup, the reaction is the payoff. The pathfinder can activate triggers to
   generate conflict beats mechanically. Absent from both the POC and FR-637.

6. **World rules.** The POC's `WorldRule` with five domain types
   (`magic_system`, `character_state`, `physical_constraint`, `social_rule`,
   `temporal_rule`) and evidence/violation beat-linking is entirely absent from
   FR-637. This is the physics engine of the fiction world — what's possible and
   what isn't. Without it, LLM-generated plots can violate established constraints.

**Source:** Design patterns from prior narrator POC and NPC character sheet
projects (external to this workspace). Fields adopted based on production
experience with novel-scale generation.

## Proposed Solution

### 1. Extend `Character` model

```python
class Character(BaseModel):
    type: Literal["character"] = "character"
    id: str
    lane: Literal["static", "dynamic"]
    name: str
    # --- existing ---
    goals: list[str] = Field(default_factory=list)
    personality: str = ""
    faction: str = ""
    relationships: list[Relationship] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    timeline_entry: str = ""
    # --- new from POC ---
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = "supporting"
    driving_force: str = ""      # core motivation: why they act
    wants: str = ""              # conscious desire
    needs: str = ""              # unconscious need (wants ≠ needs = internal conflict)
    fears: list[str] = Field(default_factory=list)
    arc_summary: str = ""        # compact trajectory: "X → Y"
    triggers: list[str] = Field(default_factory=list)  # reactive rules: "if X → Y"
```

### 2. Extend `Location` model

```python
class Location(BaseModel):
    type: Literal["location"] = "location"
    id: str
    lane: Literal["static", "dynamic"]
    name: str
    # --- existing ---
    description: str = ""
    references: list[str] = Field(default_factory=list)
    # --- new from POC ---
    location_type: str = ""                                 # freeform (not Literal — world-dependent)
    atmosphere: list[str] = Field(default_factory=list)   # mood words
    sensory: list[str] = Field(default_factory=list)       # physical details
    significance: str = ""                                  # story role
```

### 3. Add `Rule` page type

```python
class Rule(BaseModel):
    """A world constraint that the story must obey."""
    type: Literal["rule"] = "rule"
    id: str
    lane: Literal["static", "dynamic"]
    domain: Literal["magic_system", "character_state", "physical_constraint", "social_rule", "temporal_rule"]
    title: str
    description: str = ""
    references: list[str] = Field(default_factory=list)
```

Register in `PAGE_MODELS` alongside the existing four types.

### 4. Update seed canon

Extend the 3 existing character files with the new fields. Add 1–2 rule pages.

```yaml
# canon/kaelen.yaml (extended)
type: character
id: kaelen
lane: static
name: Kaelen
role: protagonist
goals:
  - "Reforge the Emberbrand with dragonsteel"
  - "Avenge the Ashfall"
driving_force: "Guilt over surviving the Ashfall when others didn't"
wants: "Vengeance against House Voss"
needs: "To forgive himself for surviving"
fears:
  - "That the Ashfall was his fault"
  - "That Maren's faith in him is misplaced"
arc_summary: "guilt-driven avenger → reluctant forgiver"
triggers:
  - "If someone questions Ashguard's honour → becomes aggressive and reckless"
  - "If offered forgiveness by an Emberwright → freezes, torn between pride and need"
personality: "disciplined, stoic, grudge-bearing"
faction: ashguard
relationships:
  - {to: maren, kind: mentor, valence: trust}
  - {to: voss, kind: rival, valence: enmity}
references: [ashguard, maren, voss, age_of_cinders, emberbrand_rule]
timeline_entry: age_of_cinders
```

```yaml
# canon/emberbrand_rule.yaml (new)
type: rule
id: emberbrand_rule
lane: static
domain: magic_system
title: "Emberbrand Reforging"
description: "The Emberbrand can only be reforged with dragonsteel quenched in living flame. Dragonsteel is held exclusively by the Emberwrights."
references: [kaelen, emberwrights]
```

### Design decisions

- **All new fields are optional with defaults.** Existing seed files validate
  without changes. New fields are additive.
- **`Rule` is a page type, not a separate system.** It participates in the same
  reference graph and lane immutability as Character/Event/Faction/Location. The
  gate checks it identically.
- **No `basics` (physical appearance) field.** The POC had it but it's prose-gen
  fuel, not pathfinder fuel. Defer to Phase 3.
- **`triggers` as flat strings, not a typed model.** The NPC project uses free-text
  triggers ("if X → Y"). A typed `Trigger(condition, reaction)` model would be
  more structured, but free-text is simpler and sufficient for Phase 1 pathfinder
  consumption. Can be tightened in a future FR if the pathfinder needs machine-
  readable conditions.

## Acceptance Criteria

- [ ] `Character` model gains `role`, `driving_force`, `wants`, `needs`, `fears`,
      `arc_summary`, `triggers` — all optional with defaults; existing seed validates
      unchanged.
- [ ] `Location` model gains `location_type`, `atmosphere`, `sensory`, `significance`
      — all optional with defaults.
- [ ] `Rule` page type added to `schema/canon.py` and registered in `PAGE_MODELS`.
- [ ] Seed canon: 3 character files extended with motivation triad. 1–2 rule pages
      added. All cross-references valid (gate passes).
- [ ] `ref_gate.py` validates Rule pages identically to other types (lane + orphan).
- [ ] Tests cover: Rule schema validation, Character with new fields validates,
      Location with new fields validates, gate rejects orphan rule reference.
- [ ] Tests tagged with REQ IDs from CAP-176.

## Alternatives Considered

- **Discover motivation fields dynamically (pipeline writes them back).** Rejected
  for Phase 1 seed: 6 hand-authored pages are trivial to enrich, and the pathfinder
  needs these fields to exist *before* it runs. Dynamic discovery is a Phase 3
  concern (LLM-bootstrap + freeze-gate).
- **Keep `WorldRule` as a separate non-canon system.** Rejected: world rules
  reference canon entities and should participate in the same orphan gate. Making
  them a page type is simpler and reuses existing infrastructure.
- **Add all POC fields (basics, key_scenes, evidence_beats, potential_violations).**
  Rejected: only fields the pathfinder consumes are in scope. Prose-gen fields
  (basics, sensory anchors for tension) belong in Phase 3.

## Judgement

**Verdict: APPROVED — clean additive schema extension.**

This is the right FR at the right time. The pathfinder (FR-638) needs motivation
fields to generate tension-driven beats. All new fields are optional with defaults,
so the existing seed and tests remain valid without modification. Low risk.

### What's right

1. **Additive, non-breaking.** Every new field has a default. Existing canon and
   tests pass unchanged. This is the correct way to enrich a schema.
2. **Sourced from production evidence.** The motivation triad (wants≠needs), fears,
   and world rules come from a ~6-month POC narrator. These aren't speculative —
   they're fields that proved necessary for novel-scale generation.
3. **`Rule` as a page type.** Correct decision: rules reference canon entities and
   should participate in the same orphan gate. No separate system needed.
4. **`triggers` as flat strings.** Correct for Phase 1. A typed `Trigger(condition,
   reaction)` model would be premature — tighten only if the pathfinder needs
   machine-readable conditions.
5. **Scope is tight.** Only fields the pathfinder consumes. Prose-gen fields
   (`basics`, `key_scenes`) correctly deferred.

### Corrections

1. **`location_type` Literal is too narrow.** The proposed values (`building`,
   `natural`, `supernatural`, `urban`, `vessel`) are POC-specific. For a fiction
   canon that could describe any world, use a plain `str` instead of a `Literal`.
   The POC's location types fit a specific setting; a reusable schema shouldn't
   hard-code them. If type validation is needed later, it belongs in the prompt
   or a world-specific config, not the Pydantic model.

2. **REQ-YG-XXX placeholder.** Acceptance criteria must reference real requirement
   IDs. Mint a CAP entry (CAP-176) before enforcement.

3. **Source references are unverifiable.** The FR cites `langgraph-poc-narrator` and
   `langgraph-npc` but neither exists in this workspace. The FR's claim that these
   fields are production-tested is accepted on trust, but the cited paths should be
   corrected or removed to avoid confusion. The FR stands on its own merits.

### Scope freeze

- 7 new fields on `Character` (role, driving_force, wants, needs, fears,
  arc_summary, triggers) — all optional
- 4 new fields on `Location` (location_type as `str`, atmosphere, sensory,
  significance) — all optional
- 1 new `Rule` page type (5 fields: domain, title, description, references, lane)
- Seed canon: extend 3 characters, add 1–2 rule pages
- Tests: Rule validation, enriched Character/Location validation, gate on Rule
- No new gate logic, no new graph, no new tools

Nothing else.

## Related

- [FR-637](./FR-637-novel-fandom-canon-schema-seed.md) — the schema this extends.
- [FR-638](./FR-638-novel-fandom-plot-pathfinder.md) — the consumer that reads
  these fields to generate beats from tensions.
- Prior narrator POC and NPC projects — source of motivation triad, triggers,
  and world rules patterns (external to this workspace).
