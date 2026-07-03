# Feature Request: FR-667 — Genesis Stub Pipeline

**Priority:** HIGH
**Type:** Refactor
**Status:** Judged: APPROVED with amendment
**Effort:** 1 day
**Requested:** 2026-07-03
**Judged:** 2026-07-03

## Summary

Streamline genesis from an 8-9 LLM call pipeline producing rich characters
to a 2 LLM call pipeline producing stubs. Genesis should do
premise → synopsis → stubs. Character enrichment happens once, in worldgen.

## Problem

Genesis and worldgen both generate character content, creating redundancy,
inconsistency, and the conditions for the parallel-invention duplicate
explosion.

### Current genesis flow (8-9 LLM calls)

```
load_premise → synopsis (LLM)
  → roster (LLM) → parse_roster → character cards (MAP: 4-6 LLM calls)
  → structure_world (LLM) → persist_genesis
```

### Current worldgen flow (per loop iteration)

```
reload → select_thin → deepen (MAP: 5-10 LLM calls) → reflect (LLM)
  → collect → create_skeletons (MAP) → gate → persist → LOOP
```

### The overlap

| Field | Genesis creates it | Worldgen re-creates it |
|-------|-------------------|----------------------|
| backstory | structure_world (thin — 1 LLM for 7+ chars) | deepen_entity (rich — 1 LLM per char) |
| goals, fears, triggers | structure_world | deepen_entity |
| relationships | structure_world (with orphan `to:` targets) | deepen_entity (with tool-checked refs) |
| birth_year | structure_world (often wrong) | anchor_events (deterministic fix) |
| personality | genesis_character prose → structure_world | deepen_entity |

Genesis `structure_world` must generate all fields for all entity types in
one LLM call. The output is inevitably thin — one call can't produce 50-word
backstories for 7 characters plus 10 events with consequences. Then worldgen's
`select_thin` flags the same characters as "backstory < 50 words" and sends
them through `deepen` — a second LLM call that does what genesis should have
done in the first place.

### The cost

- **Wasted LLM calls:** roster (1) + character cards (4-6) = 5-7 calls producing
  prose that gets converted to JSON and then overwritten by worldgen.
- **Identity fragmentation:** `structure_world` invents relationship `to:` targets
  (aldric, hermann, alric) that become orphan IDs. These multiply through
  worldgen's parallel map slots into 6 ghost files per person.
- **Schema drift:** genesis character cards use a prose format (SUMMARY, ROLE,
  DRIVE, BOND, FLAW). `structure_world` converts these to a JSON schema
  (backstory, goals, fears, triggers). Worldgen's deepen prompt uses neither —
  it enriches based on what `select_thin` judges as thin.

## Proposed Flow

### Streamlined genesis (2 LLM calls)

```
load_premise → synopsis (LLM) → generate_stubs (LLM) → validate → persist
```

1. **`synopsis`** (LLM, keep as-is): premise → full-disclosure synopsis prose.
2. **`generate_stubs`** (LLM, replaces roster + character cards + structure_world):
   synopsis → structured JSON with ALL entities, minimal fields only.
3. **`validate`** (Python, new): referential integrity check (FR-664).
4. **`persist`** (Python, keep as-is): write stubs to canon.

### Stub schema — minimal fields per type

```yaml
character:
  required: [id, type, name, role, faction, birth_year, lane, depth]
  optional: [status, summary]  # status: dead for historical figures

event:
  required: [id, type, year, scope, participants, consequences, lane, depth]
  optional: [window, affected_locations]

faction:
  required: [id, type, name, members, lane, depth]

location:
  required: [id, type, name, lane, depth]
  optional: [location_type]

rule:
  required: [id, type, domain, title, lane, depth]

premise:
  required: [id, type, text, genre_tags, era, themes, calendar_note, lane, depth]

synopsis:
  required: [id, type, text, references, lane, depth]
```

No backstory, no goals, no fears, no triggers, no relationships, no personality,
no driving_force, no wants, no needs, no arc_summary. These are worldgen's job.

### What worldgen sees

Every genesis entity is thin by definition — stubs have no backstory, no
triggers, <2 relationships. `select_thin` flags them all. Worldgen `deepen`
is the single enrichment path with full canon context and agent tools (FR-657).

## Acceptance Criteria

1. **AC-1**: New prompt `generate_stubs.yaml` replacing `genesis_roster`,
   `genesis_character`, and `structure_world` prompts. Takes synopsis text,
   returns structured JSON with stub-schema entities only.

2. **AC-2**: Updated `genesis.yaml` graph: `load → synopsis → stubs → validate
   → persist`. Three nodes removed (roster, parse_roster, characters).

3. **AC-3**: Referential integrity rule in stub prompt: every ID in
   `participants`, `members`, `references` must be defined in the output.
   Characters referenced in events must exist as character stubs.
   Dead/historical characters included with `status: dead`.

4. **AC-4**: `persist_genesis` calls `validate_referential_integrity` (FR-664)
   before writing.

5. **AC-5**: Delete retired prompts and tools: `genesis_roster.yaml`,
   `genesis_character.yaml`, `structure_world.yaml`, and `parse_roster`
   from `genesis_tools.py`. No deprecation markers — dead code is dead.

6. **AC-6**: Re-run genesis. Verify:
   - ≤2 LLM calls (synopsis + stubs)
   - All entity stubs written with correct schema
   - Zero orphan IDs (referential integrity passes)
   - All entities flagged as thin by `select_thin`

7. **AC-7**: Re-run worldgen on stub canon. Verify deepen enriches all
   entities and no duplicate clusters appear.

## Implementation Approach

### 1. Stub prompt (`prompts/generate_stubs.yaml`)

```yaml
system: |
  You are a world-builder creating STUB entities from a synopsis.
  Produce a JSON object with all entities the story requires.
  STUBS ONLY — minimal fields. No backstory, no personality, no prose.

  Rules:
  - Every character mentioned by name gets a stub.
  - Dead or historical characters get status: "dead".
  - REFERENTIAL INTEGRITY: every ID in participants, members, references
    must appear as an entity in your output. No dangling IDs.
  - Use snake_case IDs. Year 0 = central cataclysmic event.

  Return ONLY valid JSON — no markdown fences, no commentary.
```

Schema output: same top-level structure as current `structure_world`
(premise, synopsis, characters, events, factions, rules, locations) but
with stub-only fields.

### 2. Graph simplification

```yaml
nodes:
  load:
    type: python
    tool: load_premise

  synopsis:
    type: llm
    prompt: genesis_synopsis
    state_key: synopsis

  stubs:
    type: llm
    prompt: generate_stubs
    state_key: structured_world
    variables:
      premise_text: "{state.premise_text}"
      synopsis: "{state.synopsis}"

  validate:
    type: python
    tool: validate_genesis    # FR-664 referential integrity

  persist:
    type: python
    tool: persist_genesis

edges:
  - from: START
    to: load
  - from: load
    to: synopsis
  - from: synopsis
    to: stubs
  - from: stubs
    to: validate
  - from: validate
    to: persist
  - from: persist
    to: END
```

### 3. Prompt and tool deletion

- `genesis_roster.yaml` → DELETE
- `genesis_character.yaml` → DELETE
- `structure_world.yaml` → DELETE
- `genesis_tools.py:parse_roster` → DELETE

## Constraints

- Genesis output format remains compatible with worldgen — same YAML file
  structure, same `canon/` directory layout, same type subfolders.
- `persist_genesis.py` interface unchanged — it receives `structured_world`
  dict regardless of how many fields each entity has.
- No changes to worldgen graph — it already handles thin entities.
- `select_thin` criteria unchanged — stubs are thin by definition.

## Risks

- **Stub quality**: One LLM call producing stubs from synopsis only (no
  character cards as context) may miss secondary characters or assign wrong
  factions. Mitigation: the synopsis prompt already requires naming every
  character. If the synopsis names them, the stub generator can assign them.
- **Birth year accuracy**: Without character card context, birth_year estimates
  may be rougher. Mitigation: `anchor_events` in worldgen already fixes
  timeline inconsistencies deterministically.

## Sequence

```
FR-664 (ref integrity gate) — can land independently, guards any genesis shape
  ↓
FR-667 (this FR) — streamlines genesis to stubs, uses FR-664 gate
  ↓
FR-665 (worldgen dedup) — catches parallel invention in worldgen, still needed
```

## Related

- [Diary: 2026-07-03 Parallel Invention Trap](../docs/diary/2026-07-03-parallel-invention-trap.md) — root cause analysis
- [FR-655](FR-655-genesis-graph.md) — original genesis pipeline (superseded)
- [FR-656](FR-656-tighten-genesis-prompt.md) — prompt tightening (superseded by stub approach)
- [FR-664](FR-664-genesis-referential-integrity.md) — validation gate (prerequisite)
- [FR-665](FR-665-worldgen-semantic-dedup.md) — worldgen dedup (downstream defense)
- [FR-657](FR-657-agentic-event-deepening.md) — agent tools for worldgen enrichment

## Judgement

**Verdict: APPROVED with amendment.**

### Assessment

Best FR of the three. Kills 5-7 wasted LLM calls. Eliminates the genesis/worldgen
enrichment overlap entirely. Stubs-only output verified to be thin by all
`select_thin` criteria (backstory < 50 words, no triggers, < 2 relationships,
no description, no references). Clean graph: 5 nodes, 2 LLM calls. The stub
schema is well-defined and produces entities compatible with `persist_genesis`
and downstream `worldgen`.

The architectural insight is correct: genesis should identify, worldgen should
enrich. One enrichment path, not two.

### Amendment 1: Delete, don't deprecate (AC-5)

AC-5 says "Deprecated prompts marked or removed." Remove ambiguity.

**Required change:** DELETE `genesis_roster.yaml`, `genesis_character.yaml`,
`structure_world.yaml`, and the `parse_roster` function from `genesis_tools.py`.
No deprecation markers, no compatibility shims. Dead code is dead. The git
history preserves them if anyone needs to read them.

### Risk Acknowledgement

The stub prompt produces entities from synopsis only — no character card prose
as context. Risk: secondary characters unnamed in the synopsis may be missed.
This is acceptable — worldgen `deepen` creates new entities via red links for
any character referenced in backstory prose. The synopsis prompt already
requires naming every significant character. If someone is important enough
to be in the story, they're in the synopsis.

### Enforcement Sequence

Land after FR-664 (uses the ref integrity gate). Land before FR-665 (stubs
reduce the orphan surface that dedup must handle).
