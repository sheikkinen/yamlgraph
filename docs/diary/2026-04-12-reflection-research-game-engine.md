# Reflection: Research — Game Engine Architecture

**Date:** 2026-04-12
**Trigger:** Review of `docs/research-game-engine.md` — a 62KB survey of game engine modularity, design patterns, and subsystem architecture across Unity, Godot, Unreal, and O3DE.

## What Was Done

A comprehensive research document was produced covering:
- Monolithic vs. microkernel architecture (static vs. dynamic libraries)
- Entity-Component-System (ECS) and Data-Oriented Design
- Event buses, message passing, and dataflow architectures
- Asset pipelines with DAG dependency resolution and opaque handles
- Hierarchical state management and the "Modulith" concept
- Comparative analysis of four major engines

77 sources consulted, all accessed 2026-04-12. The document is survey-quality — broad, well-structured, properly cited.

## The Mirror

The research reads like a description of someone else's house, but the furniture is familiar. Nearly every pattern identified in game engine architecture has a direct analog already living in YAMLGraph:

| Game Engine Pattern | YAMLGraph Analog |
|---|---|
| Microkernel / Modulith (minimal core + plugin modules) | Minimal `graph_loader` core + YAML-defined node modules |
| DAG dependency resolution for asset loading | Graph compilation pipeline: YAML → GraphConfig → StateGraph |
| ECS (data = POD structs, logic = stateless systems) | YAML prompts (data) + node_factory systems (stateless functions) |
| ScriptableObjects (data-driven, designer-friendly assets) | YAML prompts + inline schemas — the entire "60-80% in YAML" thesis |
| Event Bus / Message Passing (decoupled subsystem communication) | LangGraph state passing between nodes — no direct coupling |
| Assembly Definitions (enforced dependency boundaries) | `import-linter` three-layer architecture enforcement |
| Hot-reloading DLLs (modify + inject without restart) | Edit YAML prompts/graphs without touching Python code |
| Opaque Resource Handles (magic number validation) | State keys with `check_requirements()` validation |
| Hierarchical State Machines (serializable, headless-testable) | Router nodes with conditional edges, testable without LLM |
| Three-Layer (Hardware / Engine / Game Logic) | Three-Layer (CLI / YAML Graphs / Python Tools) |

The isomorphism is striking. YAMLGraph is, architecturally, a game engine for LLM pipelines. The "game loop" is the graph execution. The "assets" are prompts and schemas. The "subsystems" are node types. The "ECS components" are state keys — plain data, no behavior.

## Trap: Working System Inertia

The danger of this research isn't that it's wrong — it's that it could seduce toward building something new when the structural patterns are already present. The trap `working_system_inertia` inverts here: instead of "'it works' blocks seeing it clearly," the risk is "this looks exciting → must build it" when the architecture already embodies these principles.

The useful question isn't "how do we adopt these patterns?" — it's "which of these patterns do we violate, and where?"

Quick audit against the blueprint:

1. **Enforce structural modularity via DLLs** → YAMLGraph uses Python modules with import-linter. ✓ (enforced, not just advised)
2. **ECS architecture** → State keys are POD (strings in TypedDict), nodes are stateless functions. ✓ (by convention, not by type system — a node *could* mutate state)
3. **Async event bus** → LangGraph handles this. ✓ (delegated to framework)
4. **DAG-driven resource management** → Graph compilation resolves node dependencies. ✓ (but no request coalescing or caching for prompt loading — worth watching)
5. **Data-driven configuration** → YAML prompts + schemas. ✓ (the founding principle)

The only gap worth noting: prompt loading has no caching layer. If the same prompt YAML is referenced by 10 nodes, it's parsed 10 times. In game engine terms, there's no "request coalescing." This is fine at current scale but is the kind of thing that matters at engine-scale workloads.

## Trap: Framework Costume

The research describes game engines wearing various architectural costumes. The Scripture warns: "FSM wearing DAG costume → if <50% nodes use core features, wrong tool." Applied reflexively: is this research wearing a "YAMLGraph feature" costume when it's actually pure domain exploration?

I think it's honest research — Commandment 1 fulfilled. The document doesn't propose changes. It surveys the landscape. The value is in the *vocabulary* it provides for describing patterns YAMLGraph already uses, and in surfacing the one concrete gap (prompt caching).

## Insight

**The Three-Layer pattern is not just an application architecture — it's a universal engine architecture.** Game engines discovered it independently: Hardware abstraction / Engine subsystems / Game logic. YAMLGraph discovered it independently: CLI / YAML graphs / Python tools. The convergent evolution suggests the pattern is load-bearing, not aesthetic.

**Heuristic:** When a pattern emerges independently in unrelated domains, it's likely a structural necessity rather than a stylistic choice. Trust it harder.

## Seed

The research identifies "hot-reloading" as the killer feature of modular DLL architecture — modify a subsystem and inject it without restarting the engine. YAMLGraph already supports this for YAML (edit a prompt, re-run the graph), but what about *stateful* hot-reloading? Could a running graph with checkpointed state pick up a modified prompt mid-execution without losing its accumulated state? The game engine analogy is: swap `GameLogic.dll` without dropping a frame. The YAMLGraph analog would be: swap `prompts/analyze.yaml` without losing the graph's checkpoint. This is the intersection of hot-reloading and checkpointing — two features that exist independently but have never been combined.
