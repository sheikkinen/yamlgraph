# NPC Generator - YAMLGraph Example

D&D NPC creation pipeline ported from Python to pure YAML graphs.

## Graphs

### NPC Creation (`npc-creation.yaml`)

Generate complete D&D NPCs from a concept:

```bash
yamlgraph graph run examples/npc/npc-creation.yaml \
  -v 'concept=grumpy dwarf blacksmith with a secret past'
```

**Pipeline flow:**
```
START → identity → personality → knowledge → behavior → [stats] → END
```

**Options:**
- `-v 'race=Dwarf'` - Specify race
- `-v 'character_class=Fighter'` - Specify class
- `-v 'location=The Red Dragon Inn'` - Where they're found
- `-v 'include_stats=true'` - Generate D&D 5e stats

### Encounter Turn (`encounter-turn.yaml`)

Process a single NPC turn in an encounter:

```bash
yamlgraph graph run examples/npc/encounter-turn.yaml \
  -v 'npc_name=Thorek Ironbellow' \
  -v 'location=The Rusty Anchor tavern' \
  -v 'recent_events=A hooded figure just entered'
```

**Pipeline flow:**
```
START → perceive → decide → narrate → END
```

### Encounter Multi (`encounter-multi.yaml`)

Multi-turn encounter with multiple NPCs using map nodes for parallel processing:

```bash
python examples/npc/run_encounter.py

# With NPC files from npc/npcs/ directory
python examples/npc/run_encounter.py --npc-dir npc/npcs/

# Custom location
python examples/npc/run_encounter.py -l "The Dragon's Lair"
```

**Features:**
- Multiple NPCs in same encounter
- Parallel processing: all NPCs perceive/decide/act simultaneously
- Map nodes for fan-out/fan-in pattern
- Combined turn summary weaving all NPC actions
- Image generation showing all characters
- Human-in-the-loop: pauses for DM input each turn

**Pipeline flow:**
```
START → await_dm ──(end)→ END
            │
            └→ perceive_all (map) → decide_all (map) → narrate_all (map)
                                                              │
                                                              ↓
                   summarize → describe_scene → generate_scene_image → next_turn → await_dm
```

**Node types used:**
- `interrupt` - await_dm (pauses for human input)
- `map` - perceive_all, decide_all, narrate_all (parallel NPC processing)
- `llm` - summarize, describe_scene
- `python` - generate_scene_image (Replicate API)
- `passthrough` - next_turn (increment counter, append history)

**Requirements:**
- `REPLICATE_API_TOKEN` environment variable for image generation

### Automated Demo (`demo.py`)

Run a complete automated demonstration with NPC creation and pre-scripted encounters:

```bash
# Default: 3 NPCs, 5 rounds
python examples/npc/demo.py

# Quick demo: 2 NPCs, 3 rounds
python examples/npc/demo.py --npcs 2 --rounds 3

# With images
python examples/npc/demo.py --images

# Skip NPC creation (use default NPCs)
python examples/npc/demo.py --skip-creation

# Full options
python examples/npc/demo.py -n 4 -r 5 -i
```

**Features:**
- Creates NPCs from random concepts (bartender, bard, soldier, etc.)
- Runs encounters with 10 pre-scripted DM scenarios
- No user input required - fully automated
- Optional image generation for each turn

**Pre-scripted scenarios include:**
1. Adventurers burst in needing help
2. Strange glowing crystal revealed
3. Hooded figure offers to buy the crystal
4. City watch arrives looking for someone
5. Explosion rocks the building
6. And more dramatic events...

## Prompts

All prompts are in `prompts/` using Jinja2 templates with inline schemas:

**NPC Creation:**
- `npc_identity.yaml` - Name, race, appearance, voice
- `npc_personality.yaml` - Traits, ideals, bonds, flaws
- `npc_knowledge.yaml` - World, local, and secret knowledge
- `npc_behavior.yaml` - Goals, triggers, combat style
- `npc_stats.yaml` - D&D 5e ability scores

**Encounter:**
- `encounter_perceive.yaml` - What the NPC notices
- `encounter_decide.yaml` - What action to take
- `encounter_narrate.yaml` - Scene description
- `encounter_summarize.yaml` - Turn summary for history

**Image:**
- `scene_describe.yaml` - Convert narration to image prompt

## Shared Dependencies

Uses `examples/shared/replicate_tool.py` for image generation (shared with storyboard example).

## Example Output

```
🚀 Running graph: npc-creation.yaml

📝 Generating identity...
   ✓ Thorek Ironbellow, Dwarf Blacksmith

📝 Generating personality...
   ✓ Gruff, Protective, Haunted by past

📝 Generating knowledge...
   ✓ 3 world facts, 4 local rumors, 2 secrets

📝 Generating behavior...
   ✓ Neutral disposition, 3 goals, 4 triggers

============================================================
RESULT
============================================================
{
  "name": "Thorek Ironbellow",
  "race": "Dwarf",
  "appearance": "Stocky even for a dwarf, with burn scars...",
  ...
}
```

## Ported From

Originally implemented in Python:
- `npc/showcase/npc_builder.py` (~250 LOC)
- `npc/showcase/nodes/npc_nodes.py`

Now pure YAML: ~200 lines across 3 graphs.
