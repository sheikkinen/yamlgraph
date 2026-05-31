# Diary: The Game Engine That Already Exists

## Observation

The session posed a new initiative: game engine. The instinct was to design one. The forensic response was to inventory what already exists — and discover that 80% of the AI layer is already built, unintentionally.

## The Accidental Game Engine

| Component | Game function | Already exists as |
|---|---|---|
| Character personality | Soul/trait system | `examples/demos/soul/` — YAML data_files injected into prompts |
| NPC behavior | Perceive → decide → narrate | `examples/npc/` — map nodes for parallel NPC processing |
| World state | Locations, relationships, inventory | FSM context (durable, named states, SQLite-backed) |
| Turn resolution | Human acts, world responds | Interrupt node + resume (NPC encounter pattern) |
| Asset generation | Scene art per turn | `examples/image_pipeline/` + `examples/storyboard/` |
| Game loop | Tick → dispatch all agents | FSM timer events + `yamlgraph_async` dispatch |
| Spectator view | Watch the simulation | statemachine-engine WebSocket + Kanban board |
| Session persistence | Save/load game | LangGraph checkpointer + FSM job queue |

The NPC encounter is already a playable turn-based game with HTMX UI. The soul pattern already defines character personalities as structured YAML. The FSM already handles durable state, timeouts, and named lifecycle points. The image pipeline already generates visual assets from text prompts.

## Three Framings

**A. Narrative Game Engine** (text + images, turn-based) — lowest effort. Package what exists. The NPC encounter generalized: multiple locations, persistent NPCs, quest state in FSM, scene visualization via image pipeline. This is integration, not invention.

**B. Agent Game Engine** (agents play against each other) — medium effort. Most aligned with the operator's thesis ("primary consumers of software are agents"). Each NPC is a graph. The world is an FSM. The game loop is a tick event dispatching all agent graphs in parallel. The WebSocket Kanban becomes a spectator view. Output: emergent behavior data, not entertainment.

**C. Generative Game Development Engine** (make games, not play them) — medium-high effort. YAMLGraph as game *authoring* pipeline: concept → world-building → character creation → quest structure → asset generation → playable prototype. Same shape as the ebook pipeline. Output: Godot scenes, Ink scripts, or static HTML.

## The Thesis Test

Framing B is the most interesting because it tests the two-clocks architecture under adversarial load. The FSM provides the world clock (tick events, location transitions, durable state). The graphs provide the agent clock (perceive → decide → act in seconds). The bridge translates between them. If the architecture holds, the game engine works. If it breaks, the failure reveals the next boundary to harden.

First commit: world FSM + character soul + turn graph + tick event + observe tool. That's the NPC encounter generalized from "one room, one turn" to "multiple rooms, continuous ticks." Five files.

## Metacognitive Reflection

**Trap encountered:** `growth_as_default` — the instinct to design a new system. The cure was `ask_before_generate` — inventory what exists before proposing what to build. The inventory revealed that the "game engine" is a reframing of existing assets, not a new initiative.

**Heuristic:** When a new initiative sounds large, inventory existing assets first. If 80% exists as unrelated examples, the initiative is *integration* — connecting things that already work — not *invention*. The cheapest architecture is the one you've already built without knowing it.

## Seed

The NPC encounter, the Chaplain pipeline, and the proposed game engine are all the same architecture: FSM (macro-state, named, durable) dispatching to graphs (micro-steps, eager, structured). The NPC uses `interrupt` for human-in-the-loop. The Chaplain uses `copilot` for agent-in-the-loop. The game engine would use both. Is "FSM + Graph" a general application pattern — the way MVC was for web apps? If so, what's the minimal framework that makes this pattern repeatable? Not YAMLGraph-the-framework, but the *pattern* extracted from it: declare your lifecycle states, declare your step logic, bridge them with typed events.
