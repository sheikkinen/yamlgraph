# Feature Request: Event propagation in worldgen pipeline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Granted
**Effort:** 2 days
**Requested:** 2026-07-02
**Depends:** FR-646 (reflexion step)

## Summary

Add an `anchor_events` pre-pass to the worldgen loop that establishes a per-character event timeline *before* deepening. The deepen prompt receives structured event context (which events affected this character, their life stage, spatial proximity) so backstories are temporally grounded on the first pass — not retrofitted after.

## Value Statement

The current deepening loop is entity-centric: it picks thin pages and enriches them in isolation. An event page like `age_of_cinders` lists `participants: [kaelen, maren, voss]` but the characters' backstories don't reciprocate with structured temporal detail. Kaelen's backstory says "surviving the Ashfall" but doesn't say how old he was, where he was standing, or how the event forked his life path. For smaller scoped events (a siege, a market fire), spatial proximity matters — was the character even in that location?

Without event propagation, the world has *mentions* of shared history but not *lived* history. Every character biography reads as if the events happened to someone else.

## Problem

### What exists

The `Event` schema has temporal fields:
```python
window: str = ""              # era label
valid_from: str | None = None  # epoch boundary
valid_to: str | None = None
participants: list[str]        # who was involved
consequences: list[str]        # what happened after
```

The `Character` schema has:
```python
timeline_entry: str = ""  # single string, unstructured
backstory: str = ""        # prose blob
```

### What's missing

1. **No character temporal anchor.** Characters have no birth year or lifespan field. "Was Kaelen alive during the Ashfall?" requires inference from prose.

2. **No spatial scoping on events.** `age_of_cinders` is a world event (affects everyone). A hypothetical `siege_of_ashguard` would only affect people at that location. Events have no `scope` or `affected_locations` field.

3. **No per-event impact on characters.** The link is one-directional: Event → participants. No reverse link: Character → events_experienced with structured impact data (age at time, location, emotional/goal consequences).

4. **Deepening can't cross-reference.** The `deepen_entity` prompt enriches one page at a time. It receives the page + existing canon but doesn't systematically ask "for each event this character participated in, what was the impact?"

### Concrete gap

`age_of_cinders.yaml`:
```yaml
participants: [kaelen, maren, voss]
consequences: ["The old forge lies dormant"]
```

`kaelen.yaml`:
```yaml
backstory: ""  # empty after deepening
driving_force: "Guilt over surviving the Ashfall when others didn't"
fears: ["That the Ashfall was his fault"]
```

Kaelen's `driving_force` and `fears` reference the Ashfall, but there's no structured record of: when in his life it happened, where he was, what he lost, how it connects to his goal of reforging the Emberbrand. The prose *implies* it but the data doesn't *encode* it.

## Proposed Solution

### Architecture: Pre-pass, not post-pass

Event propagation must happen *before* entity deepening, not after. If backstories are written without temporal/spatial context, the LLM produces vague prose ("survived the Ashfall") that must be retrofitted. If the event timeline is established first, the deepen prompt already knows Kaelen was a young soldier at the Great Forge when the Ashfall struck — and writes grounded backstory on the first pass.

```
anchor_events → [reload → select → deepen (with event_context) → reflect → collect → skeletons → gate → persist → reload]
```

The `anchor_events` node runs **once before the loop**. World events are seed facts — they don't change when characters are deepened. It scans all event pages, computes affected characters via spatial scoping, and builds a per-character `event_context` dict that every iteration's `deepen_entity` prompt can reference. If the loop creates new events (via skeletons), the next pipeline run catches them.

### Phase 1: Schema enrichment

Add temporal anchoring to `Character`, absolute dates + spatial scoping to `Event`, and calendar to `Premise`:

```python
# Character addition
class Character(BaseModel):
    ...
    birth_year: int | None = None   # absolute year (premise defines year 0)
```

```python
# Event additions
class Event(BaseModel):
    ...
    year: int | None = None                    # absolute year of event
    scope: Literal["world", "regional", "local"] = "world"
    affected_locations: list[str] = Field(default_factory=list)
```

```python
# Premise addition
class Premise(BaseModel):
    ...
    calendar_note: str = ""   # e.g. "Year 0 = founding of Ashguard"
```

No `era` on Character (derivable from birth_year + timeline). No `events_experienced` on Character (computed at runtime by `anchor_events`, stored in state as `event_context`).

### Phase 2: `anchor_events` Python node

A Python node that runs before `select_thin`. No LLM call — pure data computation.

```python
def anchor_events(state):
    """Build per-character event context from event pages and spatial scoping."""
    canon = state["canon_pages"]
    events = sorted(
        [p for p in canon.values() if p.get("type") == "event"],
        key=lambda e: e.get("year") or 9999,  # temporal order by absolute year
    )
    characters = {p["id"]: p for p in canon.values() if p.get("type") == "character"}

    # Per-character: list of events in their blast radius
    event_context = {cid: [] for cid in characters}

    for event in events:
        scope = event.get("scope", "world")
        affected_locs = set(event.get("affected_locations", []))
        participants = set(event.get("participants", []))
        event_year = event.get("year")

        for cid, char in characters.items():
            affected = False
            if scope == "world":
                affected = True
            elif scope == "regional":
                char_locs = {char.get("faction", "")} | set(char.get("references", []))
                affected = bool(char_locs & affected_locs) or cid in participants
            elif scope == "local":
                affected = cid in participants

            if affected:
                birth_year = char.get("birth_year")
                age_at_event = (
                    event_year - birth_year
                    if event_year is not None and birth_year is not None
                    else None
                )
                event_context[cid].append({
                    "event_id": event["id"],
                    "window": event.get("window", ""),
                    "year": event_year,
                    "age_at_event": age_at_event,
                    "consequences": event.get("consequences", []),
                    "scope": scope,
                })

    return {"event_context": event_context}
```

### Phase 3: Enrich `deepen_entity` prompt

Add event context to the deepen prompt so the LLM writes temporally grounded backstories:

```yaml
# Addition to deepen_entity.yaml user template
{% if event_context and event_context[entity.id] %}
## Events experienced
{% for ev in event_context[entity.id] %}
- {{ ev.event_id }} (year {{ ev.year }}, age {{ ev.age_at_event }}): {{ ev.consequences | join("; ") }}
{% endfor %}

When deepening this character, ground their backstory in these events:
where were they, what did they lose or gain?
{% endif %}
```

The `deepen` map node needs `event_context` added to its `variables:` config so the prompt can access it.

### Graph changes (`worldgen.yaml`)

`anchor_events` is the new entry point, running once before the loop starts:

```yaml
nodes:
  anchor_events:
    type: python
    function: nodes.anchor_events.anchor_events
    state_key: event_context

edges:
  - from: START
    to: anchor_events     # NEW: one-time pre-pass
  - from: anchor_events
    to: reload            # then enter the loop
```

The `deepen` map node adds `event_context: "{state.event_context}"` to its variables. The event_context persists in state across all loop iterations.

## Acceptance Criteria

- [ ] AC-1: `Character` schema gains `birth_year: int | None = None`
- [ ] AC-2: `Event` schema gains `year: int | None = None`, `scope: Literal["world", "regional", "local"]`, and `affected_locations: list[str]`
- [ ] AC-3: `Premise` schema gains `calendar_note: str = ""`
- [ ] AC-4: `anchor_events` Python node computes per-character event context respecting scope (world/regional/local)
- [ ] AC-5: `anchor_events` computes character age at each event from `birth_year` and `event.year` (integer arithmetic, not LLM)
- [ ] AC-6: `anchor_events` runs once before the worldgen loop (not per-iteration)
- [ ] AC-7: `deepen_entity.yaml` prompt includes event context for characters (events, age at event, temporal position)
- [ ] AC-8: Unit test: world-scope event → all characters in event_context
- [ ] AC-9: Unit test: local-scope event → only participants in event_context
- [ ] AC-10: Unit test: age arithmetic — birth_year=824, event year=847 → age_at_event=23
- [ ] AC-11: Seed canon updated: `age_of_cinders.yaml` has `year:`, `kaelen.yaml` has `birth_year:`, `premise.yaml` has `calendar_note:`
- [ ] AC-12: Integration test (`@pytest.mark.slow`): deepening Kaelen with event context produces temporally grounded backstory (mentions age/location during Ashfall)
- [ ] AC-13: Existing worldgen tests unaffected (new fields are optional with defaults)
- [ ] AC-14: Tests added with `@pytest.mark.req`

## Open Questions

1. ~~**Era vocabulary**~~: Resolved — premise defines eras via `calendar_note`. Characters have `birth_year`, not `era` (era is derivable).
2. **New events from loop**: If the loop creates new event pages (via skeletons), their event context won't be available until the next pipeline run. Acceptable for v1 — world events are seed data.
3. ~~**Absolute dates**~~: Resolved — mandatory. `Event.year`, `Character.birth_year`, `Premise.calendar_note`. Age computed mechanically.

## Judgement

**Granted with 4 amendments (2026-07-02)**

1. **Absolute dates are mandatory.** `Event.year: int | None`, `Character.birth_year: int | None`, `Premise.calendar_note: str`. Age at event is integer arithmetic, not LLM inference. Seed data must include years.
2. **Drop `era` from Character.** Derivable from `birth_year` + event timeline. Two temporal anchors on one entity is a contradiction factory.
3. **Drop `events_experienced` from Character.** Runtime `event_context` in state is canonical. Storing on the page creates stale data when events are edited.
4. **Seed data must ship with absolute dates.** Integration test is untestable without years on `age_of_cinders`, `birth_year` on `kaelen`, `calendar_note` on `premise`.

## Alternatives Considered

- **Post-pass separate graph (original FR-647 design)**: Runs after worldgen completes. Rejected: backstories already written without temporal grounding, requiring expensive retrofit. Pre-pass is cheaper and produces better first-pass output.
- **Extend `deepen_entity` prompt only**: Add "check events you participated in" without a dedicated anchor node. Simpler but the LLM receives no structured event context — has to rediscover events from full canon dump on every call.
- **Timeline page type**: A dedicated chronological entity that all pages reference. Architecturally clean but heavy — new page type, ordering constraints, and the existing Event type already carries temporal data.
- **Manual enrichment**: Human writes event impacts. Doesn't scale.

## Related

- FR-646 — reflexion step (prerequisite: finds missing entities)
- FR-643v2 — worldgen pipeline (this extends the world-building workflow)
- `examples/novel_fandom/schema/canon.py` — Event and Character models
