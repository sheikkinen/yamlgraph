# FR-655: Genesis graph — premise-driven world bootstrapping

**Priority:** MEDIUM
**Type:** Feature
**Status:** Granted
**Effort:** 1 day
**Requested:** 2026-07-02

## Summary

Build a `genesis.yaml` graph that takes the floodmark saga premise (`examples/dungeon_master/premises/floodmark-saga.txt`) and produces temporally-grounded seed canon. Reuses the existing dungeon_master **prompt** files (not subgraph invocation) for prose generation, then adds a single `structure_world` LLM node that converts prose into novel_fandom YAML canon with typed fields, absolute years, and causal chains. Persists via existing `persist_pages`.

## Value Statement

World authors provide a one-paragraph premise and get complete, internally-consistent seed canon with timeline, character arcs, and faction dynamics — ready for the worldgen expansion loop. The DM pipeline's prose-first approach ensures narrative quality; the structuring layer ensures schema compliance.

## Seed Input

The floodmark saga from `examples/dungeon_master/premises/floodmark-saga.txt`:

> Romance, Adventure, Erotica. 10,000 BC, the great thaw — The Floodmark Saga. The glaciers are bleeding into the lowlands and three loosed rivers are drowning the valley; every clan must climb or die. Hilde, war-leader of the Aschenwulf band, raids the rival Baerenschaedel clan at dawn just as the river breaks its banks...

## Existing dungeon_master Pipeline (Reuse)

| Graph | What it does | Output |
|-------|-------------|--------|
| `synopsis.yaml` | premise -> full-disclosure synopsis | prose synopsis |
| `character_roster.yaml` | synopsis -> cast list (names only) | one name per line |
| `character.yaml` | synopsis + name -> character card | prose character |
| `plot_plan.yaml` | premise -> structured PlotPlan (I,A,G,F,E) | validated plot |

## Problem

The DM pipeline produces prose; novel_fandom needs structured YAML with typed fields (birth_year, year, scope, relationships, references). The current bridge is manual.

## Proposed Solution

### Architecture

```
genesis.yaml
+-----------------------------------------+
|  PHASE 1: Prose (DM prompts, own nodes) |     canon/{type}/
|  +-----------------------------+        |     +--------------+
|  | synopsis (LLM, DM prompt)   |        |     | premise.yaml  |
|  | roster (LLM, DM prompt)     |        |     | synopsis.yaml |
|  | characters (map, DM prompt) |        |     | character/*.yaml
|  +-----------------------------+        |     | event/*.yaml  |
|                                         |     | faction/*.yaml|
|  PHASE 2: Structure (prose -> YAML)     |     | rule/*.yaml   |
|  +-----------------------------+        |     | location/*.yaml
|  | structure_world (single LLM)|--------+-->  +--------------+
|  | persist_seeds (persist_pages)|       |
|  +-----------------------------+        |
+-----------------------------------------+
```

### Phase 1: Prose generation (DM prompts as LLM nodes)

No subgraph invocation — reference the DM prompt YAML files directly as LLM nodes in genesis.yaml:
1. **synopsis** node using `examples/dungeon_master/prompts/synopsis.yaml` with `instruction=<premise>`, `draft=""`
2. **roster** node using DM roster prompt with the synopsis
3. **characters** map node using `examples/dungeon_master/prompts/character.yaml` over each roster name

### Phase 2: Structure extraction (single LLM pass)

**structure_world**: Synopsis + character cards → single structured output containing all entity types:
- `premise`: `{type, id, text, genre_tags, era, themes, calendar_note}` — converts raw premise prose
- `events`: `{id, year, scope, participants, consequences, causes}` — Year 0 = the flood
- `characters`: `{id, birth_year, role, relationships, fears, goals, triggers, backstory}` — birth_year relative to timeline
- `factions`: `{id, members, leader, resources, beliefs}`
- `rules`: `{id, domain, description}`
- `locations`: `{id, description}`

One pass avoids cross-referencing issues between separate extract nodes. Context ~8k tokens input.

**persist_seeds**: Reuse existing `persist_pages` node — write to `canon/{type}/` with `lane: dynamic, depth: 0`.

### Floodmark canon mapping

| Concept | Type | ID | Year |
|---------|------|----|------|
| The Great Thaw / Flood | event | the_flood | 0 |
| Dawn raid | event | dawn_raid | 0 |
| Arnulf swept downriver | event | arnulf_lost | 0 |
| Aschenwulf band | faction | aschenwulf | - |
| Baerenschaedel clan | faction | barenschadel | - |
| Hilde | character | hilde | ~-25 |
| Gunnar | character | gunnar | ~-28 |
| Arnulf | character | arnulf | ~-20 |
| Reinmar | character | reinmar | ~-35 |
| Survival truce | rule | survival_truce | - |
| Flood judgment rite | rule | flood_judgment | - |
| The high valley | location | high_valley | - |

## Acceptance Criteria

- [ ] `genesis.yaml` graph definition with DM prompt files referenced as LLM nodes (no subgraph invocation)
- [ ] Phase 1 nodes produce synopsis prose and character cards
- [ ] Single `structure_world` prompt converts prose to typed canon YAML (premise, events, characters, factions, rules, locations)
- [ ] Generated timeline has events with absolute years (Year 0 = the flood)
- [ ] Generated characters have birth_year consistent with timeline
- [ ] Generated factions reference characters as members
- [ ] Premise page generated from raw premise text
- [ ] All pages written to `canon/{type}/` via existing persist_pages with depth: 0
- [ ] Smoke test: genesis with floodmark -> worldgen -> verify timeline populated

## Alternatives Considered

- **Keep hand-authored seeds**: Works for one world, doesn't scale.
- **Bypass DM pipeline, generate structured directly**: Loses the quality of DM's prose-first approach. Converting prose -> structure is easier than generating structure cold.
- **Run DM and novel_fandom as completely separate systems**: Duplicates the premise -> synopsis -> characters pipeline.

## Related

- FR-651: deepen temporal fields (tactical complement)
- FR-652: normalize role enum (needed for genesis character output)
- FR-653: robust reflect schema (worldgen quality after genesis)
- FR-654: re-deepen seed characters (unnecessary if genesis produces rich seeds)
- `examples/dungeon_master/synopsis.yaml`
- `examples/dungeon_master/character_roster.yaml`
- `examples/dungeon_master/character.yaml`
- `examples/dungeon_master/premises/floodmark-saga.txt`

## Judgement

**Verdict: Granted with amendments.**

### What's sound
- Two-phase architecture (DM prose → structured YAML) is the right decomposition. DM's prose-first approach is battle-tested. Converting prose to structure is a single well-defined LLM task.
- Floodmark saga is a concrete, rich seed premise with named characters, factions, events, and rules already implied in the text.
- Reusing DM graphs via subgraph invocation (CAP-111/FR-255) avoids duplicating synopsis/character generation.
- Canon mapping table gives a clear ground truth for validation.

### Amendments

1. **Phase 1 is not one graph.** The DM pipeline is three separate graphs (synopsis.yaml, character_roster.yaml, character.yaml) each with their own state schema. genesis.yaml cannot just chain them as subgraph nodes — it needs to bridge state between them. Two approaches:
   - **(a) Script orchestration**: A Python driver script that calls `invoke_graph()` three times, extracting prose output between calls. genesis.yaml is Phase 2 only, receiving prose as `--var` inputs.
   - **(b) Single genesis graph**: Phase 1 replicated as LLM nodes inside genesis.yaml using the same DM prompts (they're just YAML files, sharable). No subgraph invocation needed.
   - **Recommendation: (b)**. Copying/referencing the 3 DM prompt files into genesis is simpler than state-bridging subgraphs. The prompts are the value, not the graph wiring.

2. **extract_timeline and structure_characters can be one node.** The LLM needs to see characters and events together to assign consistent birth_years. A single "structure_world" prompt that outputs `{premise, synopsis, timeline, characters, factions, rules, locations}` in one pass is cheaper and avoids cross-referencing issues. If context window allows (~8k token input), one shot is better than five.

3. **persist_seeds can reuse existing persist_pages.** The node already writes to `canon/{type}/` with normalize_page. No new persist logic needed — just call `_persist_impl` with a state dict containing the structured output in `deepened` format.

4. **Premise page must be generated too.** The floodmark premise.txt is prose — it needs conversion to the `{type: premise, id, text, genre_tags, era, themes, calendar_note}` schema. Add this to the structuring phase.

5. **Drop idempotency criterion.** A `--force` flag and empty-check add complexity for a one-shot graph. Simpler: user clears `canon/` before running genesis (or the script does it). The user already knows `git checkout -- canon/ && git clean -fd canon/` from this session.

6. **Effort: 1 day, not 2.** With approach (b) and a single structure_world prompt, the work is: 1 graph YAML + 3 prompts (synopsis, roster, structure_world) + smoke test. The DM prompts are already written.

### Scope freeze
One graph YAML, 3-4 prompts (reusing DM synopsis/character prompts), one structure_world extraction prompt, persist via existing persist_pages. Smoke test: genesis → worldgen → verify timeline.
