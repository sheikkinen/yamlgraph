# Plan: AI Game Engine — Phase 1: Physics Sandbox

## Problem Statement

Build a real TypeScript game engine framework where games are AI-generated — described declaratively in JSON, rendered in WebGL via Babylon.js. No GUI except the game itself: no level editor, no property inspector, no asset browser. The AI (via Copilot multi-step generation) replaces all design tools. The engine loads declarative game definitions and runs them.

**First target:** Physics sandbox — rigid bodies, constraints, free-form interaction in the browser.

## Core Design Principle

> **The JSON schema IS the engine's API surface for AI generation.**

The contract between AI and engine is a validated JSON schema. If the AI can produce valid JSON, it can produce a valid game. The engine's job is to make that JSON come alive.

## Architecture

```
┌─────────────────────────────────────────────┐
│  AI Generation (Copilot / LLM)              │  Produces game.json
├─────────────────────────────────────────────┤
│  Game Definition Layer (JSON + Schema)      │  Validated, declarative
├─────────────────────────────────────────────┤
│  Engine Core (TypeScript)                   │  Loads definitions, runs game
├─────────────────────────────────────────────┤
│  Babylon.js (WebGL + Havok Physics)         │  Rendering, physics, input
├─────────────────────────────────────────────┤
│  Browser (Canvas + WebGL context)           │  Platform
└─────────────────────────────────────────────┘
```

### Isomorphism with Game Engine Research

| Research Pattern | This Engine |
|---|---|
| Microkernel (minimal core + modules) | Thin engine core + JSON-defined game modules |
| ECS (data = POD, logic = systems) | JSON entities (data) + engine systems (logic) |
| ScriptableObjects (data-driven assets) | JSON game definitions |
| Event Bus (decoupled communication) | Babylon.js Observable pattern |
| DAG asset loading | Babylon.js scene loader + entity dependency resolution |
| Hot-reloading DLLs | Hot-reload JSON definitions without restarting |
| Opaque Handles | Entity registry with ID-based lookups |

## Project Structure

```
aigame/
├── package.json
├── tsconfig.json
├── vite.config.ts              # Dev server + HMR
├── src/
│   ├── core/
│   │   ├── engine.ts           # Engine bootstrap + game loop
│   │   ├── scene-manager.ts    # Create Babylon scene from definition
│   │   └── types.ts            # Core type definitions
│   ├── entities/
│   │   ├── entity-factory.ts   # Create entities from JSON definitions
│   │   ├── entity-registry.ts  # Track all live entities by ID
│   │   └── mesh-factory.ts     # Create meshes (box, sphere, cylinder, etc.)
│   ├── physics/
│   │   ├── physics-engine.ts   # Havok/Cannon.js setup
│   │   ├── body-factory.ts     # Create physics bodies from definitions
│   │   └── constraints.ts      # Joints, springs, hinges (Phase 1b)
│   ├── rendering/
│   │   ├── camera-factory.ts   # Camera types from definitions
│   │   ├── light-factory.ts    # Light types from definitions
│   │   └── material-factory.ts # Materials from definitions
│   ├── interaction/
│   │   ├── input-manager.ts    # Keyboard + pointer input
│   │   ├── pointer-actions.ts  # Click-to-spawn, drag, pick
│   │   └── interaction-system.ts # Process interaction definitions
│   ├── rules/
│   │   ├── rule-engine.ts      # Evaluate conditions, trigger actions
│   │   ├── conditions.ts       # Condition evaluators
│   │   └── actions.ts          # Action executors
│   ├── loader/
│   │   ├── definition-loader.ts # Load + validate game.json
│   │   ├── hot-reload.ts       # Watch + reload definitions
│   │   └── validator.ts        # Schema validation (ajv)
│   ├── debug/
│   │   └── overlay.ts          # Physics wireframes, entity labels, FPS
│   └── index.ts                # Public API
├── schemas/
│   ├── game.schema.json        # Root game definition schema
│   ├── scene.schema.json       # Scene config (camera, lights, env)
│   ├── entity.schema.json      # Entity definition
│   ├── physics.schema.json     # Physics body properties
│   ├── interaction.schema.json # Interaction definitions
│   └── rules.schema.json       # Game rules
├── games/                      # Example game definitions (AI-generatable)
│   └── sandbox/
│       └── game.json           # Physics sandbox definition
├── web/
│   └── index.html              # Minimal HTML host
└── tests/
    ├── unit/                   # Engine unit tests
    └── integration/            # Full game loading tests
```

## Game Definition Schema (Core Contract)

This is the most critical artifact — it defines what AI can express:

```json
{
  "$schema": "game.schema.json",
  "name": "Physics Sandbox",
  "version": "1.0",
  "scene": {
    "camera": {
      "type": "arc-rotate",
      "target": [0, 1, 0],
      "alpha": -1.57,
      "beta": 1.05,
      "radius": 15
    },
    "environment": {
      "skybox": "default",
      "ground": { "size": 50, "material": "grid", "physics": true },
      "gravity": [0, -9.81, 0],
      "ambient": { "color": "#404040" }
    },
    "lights": [
      { "type": "hemispheric", "direction": [0, 1, 0], "intensity": 0.8 },
      { "type": "directional", "direction": [1, -2, 1], "intensity": 0.5, "shadows": true }
    ]
  },
  "entity_templates": {
    "ball": {
      "mesh": { "type": "sphere", "diameter": 1 },
      "physics": { "mass": 1, "restitution": 0.7, "friction": 0.5, "shape": "sphere" },
      "material": { "type": "standard", "diffuse": "#ff3333" }
    },
    "crate": {
      "mesh": { "type": "box", "size": 1 },
      "physics": { "mass": 2, "restitution": 0.2, "friction": 0.8, "shape": "box" },
      "material": { "type": "standard", "diffuse": "#8B4513" }
    }
  },
  "entities": [
    { "template": "ball", "id": "ball1", "position": [0, 5, 0] },
    { "template": "crate", "id": "crate1", "position": [2, 3, 0] },
    {
      "id": "ramp",
      "mesh": { "type": "box", "width": 4, "height": 0.2, "depth": 6 },
      "position": [3, 2, 0],
      "rotation": [0, 0, -0.3],
      "physics": { "mass": 0, "shape": "box" },
      "material": { "type": "standard", "diffuse": "#666666" }
    }
  ],
  "interactions": [
    {
      "name": "spawn_ball",
      "trigger": { "type": "pointer_down", "button": "left" },
      "action": { "type": "spawn", "template": "ball", "at": "pointer_world" }
    },
    {
      "name": "drag_object",
      "trigger": { "type": "pointer_drag" },
      "action": { "type": "move_entity", "mode": "kinematic" }
    }
  ],
  "rules": [
    {
      "name": "cleanup_fallen",
      "condition": { "type": "entity_below", "y": -20 },
      "action": { "type": "destroy" },
      "apply_to": "all"
    }
  ],
  "debug": {
    "physics_wireframes": false,
    "entity_labels": false,
    "fps_counter": true
  }
}
```

## Implementation Todos

### Phase 1a: Foundation (engine boots, renders a scene from JSON)

1. **project-scaffold** — Initialize repo: package.json, tsconfig, vite, babylon.js, havok
2. **json-schemas** — Write JSON schemas for game definitions (game, scene, entity, physics)
3. **definition-loader** — Load game.json, validate against schema (ajv)
4. **engine-core** — Engine class: create Babylon engine + scene + render loop
5. **scene-manager** — Apply scene definition: camera, lights, environment, ground
6. **mesh-factory** — Create Babylon meshes from entity definitions (box, sphere, cylinder, plane, capsule)
7. **material-factory** — Create materials from definitions (standard, PBR)
8. **entity-factory** — Orchestrate: definition → mesh + material + position/rotation → scene
9. **entity-registry** — Track live entities by ID, support lookup/destroy
10. **sandbox-game-def** — Write first game.json: physics sandbox with balls, crates, ramp
11. **smoke-test-visual** — Engine loads sandbox game.json and renders correctly in browser

### Phase 1b: Physics (objects fall, collide, bounce)

12. **physics-engine** — Initialize Havok plugin, apply gravity from definition
13. **body-factory** — Create physics impostors from entity physics definitions
14. **ground-physics** — Ground plane with physics (mass: 0, static body)
15. **physics-debug** — Toggle physics wireframe overlay

### Phase 1c: Interaction (user can interact with the world)

16. **input-manager** — Keyboard + pointer event abstraction
17. **pointer-spawn** — Click to spawn entities from templates at pointer world position
18. **pointer-drag** — Pick and drag physics objects
19. **interaction-system** — Load interaction definitions from game.json, wire triggers → actions

### Phase 1d: Rules Engine (game logic from JSON)

20. **rule-engine** — Per-frame evaluation: conditions → actions
21. **conditions** — Entity property checks (position, velocity, collision)
22. **actions** — Destroy, spawn, modify property, log
23. **cleanup-rule** — "Destroy entities that fall below y=-20"

### Phase 1e: Hot Reload + Debug

24. **hot-reload** — Watch game.json, rebuild scene on change (Vite HMR integration)
25. **debug-overlay** — FPS counter, entity count, physics stats
26. **debug-labels** — Optional floating labels on entities showing ID

### Phase 1f: Packaging + Testing

27. **unit-tests** — Schema validation, entity factory, rule engine
28. **integration-test** — Load sandbox game.json headlessly, verify entity count + physics state
29. **readme** — Project README: what it is, how to use, how AI generates games
30. **example-games** — 2-3 additional game definitions AI can generate (domino chain, marble run, tower collapse)

## Key Design Decisions

1. **Babylon.js, not Three.js** — Built-in Havok physics, animation system, inspector (debug only). More "engine-like."

2. **JSON definitions, not YAML** — Native to both TypeScript (JSON.parse) and AI (structured output). Schema validation via ajv. YAML would add a dependency for marginal benefit.

3. **Entity templates** — Flyweight pattern from research. Define once, instantiate many. AI generates templates + instances separately.

4. **No scripting in definitions** — Game definitions are pure data. No embedded JS. Behavior is expressed through the interaction/rules declarative system. This is safer for AI generation and simpler to validate.

5. **Vite for dev server** — HMR for hot-reloading, fast builds, ESM-native.

6. **Havok physics** — Babylon.js's production physics engine. Deterministic, fast, supports constraints. Falls back to Cannon.js if Havok WASM can't load.

7. **Debug overlay is IN-GAME** — Consistent with "no GUI except the game." Debug info is rendered as game UI elements, toggled via keyboard shortcuts.

## What Makes This a Framework, Not a Demo

- **Validated schema contract** — AI generates against a schema, not free-form
- **Entity templates + instancing** — Composition, not hardcoded objects
- **Extensible interaction/rules system** — Declarative behavior, not hardcoded callbacks
- **Hot-reload** — Edit definition → see changes instantly
- **Multiple game definitions** — Same engine loads sandbox, dominos, marble run
- **Testable** — Headless mode for CI, schema validation catches bad definitions

## Future Phases (not in scope for Phase 1)

- **Phase 2:** Constraints (joints, springs, hinges, ragdolls)
- **Phase 3:** Animation (keyframe, procedural, physics-driven)
- **Phase 4:** Sound (spatial audio, event-triggered)
- **Phase 5:** Entity behaviors (finite state machines in JSON)
- **Phase 6:** Multi-scene / level transitions
- **Phase 7:** Particle effects
- **Phase 8:** Multiplayer (WebSocket state sync)
- **Phase 9:** AI runtime generation (LLM generates game.json live via API)

## Risks

1. **Havok WASM loading** — Babylon.js Havok requires async WASM init. May need fallback to Cannon.js for simpler physics.
2. **Declarative expressiveness ceiling** — Pure JSON rules may hit limits for complex game logic. Phase 5 (FSM behaviors) addresses this.
3. **AI schema compliance** — LLMs may generate invalid JSON. Schema validation + clear error messages are critical.
4. **Hot-reload state loss** — Reloading definitions destroys physics state. Acceptable for dev; serialize/restore could be added later.
