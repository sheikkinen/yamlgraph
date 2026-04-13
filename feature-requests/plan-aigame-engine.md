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

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 1 | `project-scaffold` | Initialize project | New repo: package.json (babylon.js, havok, ajv, vite), tsconfig.json (strict), vite.config.ts, web/index.html shell | — | pending |
| 2 | `json-schemas` | Write JSON schemas | JSON schemas for game definitions: game.schema.json (root), scene.schema.json, entity.schema.json, physics.schema.json, interaction.schema.json, rules.schema.json. Use JSON Schema draft-07. | project-scaffold | pending |
| 3 | `definition-loader` | Definition loader + validator | Load game.json via fetch, validate against schemas using ajv. Clear error messages for AI-generated invalid JSON. | json-schemas | pending |
| 4 | `engine-core` | Engine core class | Engine class: create Babylon Engine + Scene, render loop, resize handling. Single entry point: `Engine.create(canvas, gameDefinition)` | project-scaffold | pending |
| 5 | `scene-manager` | Scene manager | Apply scene definition to Babylon scene: camera (arc-rotate, free, follow), lights (hemispheric, directional, point, spot), environment (skybox, ground, gravity, ambient). | engine-core | pending |
| 6 | `mesh-factory` | Mesh factory | Create Babylon meshes from entity defs: box, sphere, cylinder, plane, capsule, torus. Support size/width/height/depth/diameter params. | engine-core | pending |
| 7 | `material-factory` | Material factory | Create materials from defs: StandardMaterial (diffuse, specular, emissive colors), PBRMaterial (albedo, metallic, roughness). Hex color parsing. | engine-core | pending |
| 8 | `entity-factory` | Entity factory | Orchestrate entity creation: resolve template → create mesh → apply material → set position/rotation/scaling → register in entity registry. | mesh-factory, material-factory, entity-registry | pending |
| 9 | `entity-registry` | Entity registry | Track live entities by ID. Lookup, destroy, iterate. Handle template-based spawning with auto-generated IDs. | engine-core | pending |
| 10 | `sandbox-game-def` | Sandbox game definition | Write games/sandbox/game.json: physics sandbox with ball/crate templates, ramp, ground. First AI-generatable game definition. | json-schemas | pending |
| 11 | `smoke-test-visual` | Visual smoke test | Engine loads sandbox game.json → renders scene in browser. Manual verification: objects visible, camera works, materials correct. | definition-loader, entity-factory, sandbox-game-def, scene-manager | pending |

### Phase 1b: Physics (objects fall, collide, bounce)

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 12 | `physics-engine` | Physics engine setup | Initialize Havok WASM plugin, apply gravity from scene definition. Fallback to Cannon.js if Havok fails to load. | engine-core | pending |
| 13 | `body-factory` | Physics body factory | Create physics aggregates/impostors from entity physics defs: mass, restitution, friction, shape (sphere, box, cylinder, mesh). | entity-factory, physics-engine | pending |
| 14 | `ground-physics` | Ground plane physics | Ground with mass=0 static physics body. Configurable from scene.environment.ground.physics. | body-factory | pending |
| 15 | `physics-debug` | Physics debug wireframes | Toggle Babylon physics debug renderer: wireframe shapes, contact points. Keyboard shortcut (F3). | physics-engine | pending |

### Phase 1c: Interaction (user can interact with the world)

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 16 | `input-manager` | Input manager | Abstract keyboard + pointer events. Key state tracking, pointer world position via ray casting. | engine-core | pending |
| 17 | `pointer-spawn` | Click-to-spawn interaction | Click anywhere → spawn entity from template at pointer world position. Configurable per interaction definition. | entity-factory, input-manager | pending |
| 18 | `pointer-drag` | Drag physics objects | Pick and drag physics objects with pointer. Kinematic override during drag, restore physics on release. | body-factory, input-manager | pending |
| 19 | `interaction-system` | Interaction system | Load interaction definitions from game.json. Wire trigger types (pointer_down, pointer_drag, key_press) to action types (spawn, move, destroy). | definition-loader, pointer-spawn, pointer-drag | pending |

### Phase 1d: Rules Engine (game logic from JSON)

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 20 | `rule-engine` | Rule engine | Per-frame evaluation loop: iterate rules, check conditions against entities, execute actions. Configurable apply_to (all, tagged, specific ID). | entity-registry | pending |
| 21 | `conditions` | Condition evaluators | Condition types: entity_below (y threshold), entity_property (comparison ops), collision (on contact with specific entity/tag). | rule-engine | pending |
| 22 | `actions` | Action executors | Action types: destroy (remove entity), spawn (create from template), set_property (modify entity property), log (debug output). | entity-factory, rule-engine | pending |
| 23 | `cleanup-rule` | Cleanup fallen entities rule | Verify rule: entities falling below y=-20 are automatically destroyed. Test with sandbox game. | actions, conditions, sandbox-game-def | pending |

### Phase 1e: Hot Reload + Debug

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 24 | `hot-reload` | Hot reload definitions | Watch game.json for changes via Vite HMR. On change: dispose scene entities, reload definition, rebuild scene. Preserve camera position. | definition-loader, scene-manager | pending |
| 25 | `debug-overlay` | Debug overlay | In-game debug overlay: FPS counter, entity count, physics body count. Toggle with F1. Rendered as Babylon GUI. | engine-core | pending |
| 26 | `debug-labels` | Entity debug labels | Optional floating labels above entities showing their ID. Toggle with F2. Implemented as Babylon GUI TextBlocks. | entity-registry | pending |

### Phase 1f: Packaging + Testing

| # | ID | Title | Description | Depends On | Status |
|---|---|---|---|---|---|
| 27 | `unit-tests` | Unit tests | Vitest tests: schema validation (valid/invalid defs), entity factory (mesh creation), rule engine (condition evaluation), material factory (color parsing). | definition-loader, entity-factory, rule-engine | pending |
| 28 | `integration-test` | Integration tests | Load sandbox game.json in headless Babylon (NullEngine), verify: entity count, physics bodies created, rule engine ticks. | body-factory, smoke-test-visual | pending |
| 29 | `readme` | Project README | README.md: what the engine is, design philosophy (AI-generated, no GUI), how to run, how to create game definitions, schema reference. | smoke-test-visual | pending |
| 30 | `example-games` | Example game definitions | Write 2-3 additional game.json files: domino chain reaction, marble run with ramps/tubes, tower collapse. Prove the schema is expressive. | cleanup-rule, interaction-system | pending |

### Dependency Graph

```
project-scaffold ──┬── json-schemas ──┬── definition-loader ──┐
                   │                  └── sandbox-game-def ───┤
                   ├── engine-core ──┬── scene-manager ───────┤
                   │                 ├── mesh-factory ────┐   │
                   │                 ├── material-factory ─┤   │
                   │                 ├── entity-registry ──┤   │
                   │                 ├── physics-engine ─┐ │   │
                   │                 ├── input-manager ──┤ │   │
                   │                 ├── debug-overlay    │ │   │
                   │                 └── rule-engine ─────┤ │   │
                   │                                     │ │   │
                   └─────────────────────────────────────┘ │   │
                                                           │   │
                   entity-factory ◄── mesh + material + reg┘   │
                        │                                      │
                   ┌────┴────────────────┐                     │
                   ▼                     ▼                     │
              body-factory          pointer-spawn              │
              (+ physics-engine)    (+ input-manager)          │
                   │                     │                     │
              ┌────┴────┐          pointer-drag                │
              ▼         ▼          (+ input-manager)           │
         ground-physics  │              │                      │
                         ▼              ▼                      │
                    pointer-drag   interaction-system ◄── def-loader
                                        │                      │
              conditions ◄── rule-engine │                     │
              actions ◄── rule-engine + entity-factory         │
                   │                     │                     │
                   ▼                     │                     │
              cleanup-rule               │                     │
                   │                     │                     │
                   ▼                     ▼                     │
              example-games ◄──── interaction-system           │
                                                               │
              smoke-test-visual ◄── def-loader + entity-factory│
                   │                + sandbox-game-def          │
                   │                + scene-manager             │
                   ▼                                           │
              integration-test ◄── body-factory                │
              readme                                           │
              unit-tests ◄── def-loader + entity-factory + rule-engine
```

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
