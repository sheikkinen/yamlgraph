# Diary: Six Proposals, Five Already Built

**Date:** 2026-05-31
**Context:** Evaluating seven strategic feature proposals against the existing yamlgraph codebase
**Trap:** `working_system_inertia` inverted — proposals describe what exists, but under new names

## Observation

Seven feature proposals arrived for evaluation. The instinct was to assess each on its merits — feasibility, scope, timeline. The forensic response was to inventory the codebase first. The result: five of six rejected proposals describe capabilities that already exist as compositions of existing primitives, just not marketed under the proposed brand name.

## The Scorecard

| Proposal | Verdict | Why |
|----------|---------|-----|
| Mission Control UI | **Accepted → FR-467** | Genuine cross-system observability gap (FSM ↔ Graph) |
| Declarative Event Broker | Rejected | FSM action config already IS a declarative event router |
| Declarative Sandboxing | Rejected | Fly/Firecracker microVMs already provide VM-level isolation |
| Declarative RAG | Rejected | RAG graph is 3 nodes / 45 lines. The "boilerplate" is ETL, not reasoning |
| Game Engine | Rejected | 80% already exists as composable examples (soul, NPC, storyboard) |
| FSM + Graph Consolidation | Rejected | Two computational models (lifecycle vs. eager completion), not two syntaxes |

## The Pattern

Five rejections share one root cause: **the proposal names a capability the system already has, but as a composition rather than a monolith.** The RAG pipeline is `python_tool + llm_node + prompt`, not `rag_node`. The game engine is `soul_data + npc_map + interrupt_resume + image_pipeline`, not `game_engine_mode`. The event broker is `event_map + context_map + transitions`, not `broker_service`.

This is the framework working as designed. Capabilities emerge from composition, not from dedicated features. But composition is invisible to feature proposals — they see the absence of a named subsystem and conclude the capability is missing.

## The One Accept

FR-467 (Mission Control) passed because it addresses a **boundary problem**: FSM lifecycle events and Graph execution traces exist in separate systems with no correlation mechanism. This isn't a missing composition — it's a missing bridge. The distinction: compositions combine existing primitives within one system; bridges connect primitives across systems.

## The Decision Heuristic

Before accepting a new framework feature:

1. **Inventory** — what existing primitives cover this use case?
2. **Compose** — can they be combined in a graph or example?
3. **Test** — does removing the graph framework make the code shorter?

If the answer to #3 is yes, the proposal is a script wearing a graph costume (`framework_costume`). If #1 covers 80%+, the proposal is a naming exercise, not a feature. Only if #1 reveals a genuine gap — especially at a system boundary — is the proposal a real feature.

## Trap

`false_duplicate` inverted. Usually, syntactic similarity misleads us into thinking two things are the same when they're not. Here, syntactic *dissimilarity* (different names, different framing) misleads proposals into thinking capabilities are missing when they're present. The inventory step catches this — but only if you inventory before evaluating.

## Heuristic

**Composition is invisible to feature proposals.** A capability that emerges from combining three existing primitives looks like an absence to someone who expected a dedicated subsystem. The antidote is always the same: inventory before evaluation.

## Seed

If five of seven proposals describe existing compositions, the framework's *discoverability* is the real gap. Not new features — better examples, better naming, better documentation of what emerges from combining existing nodes. The `examples/` directory is the product catalog; is it legible?
