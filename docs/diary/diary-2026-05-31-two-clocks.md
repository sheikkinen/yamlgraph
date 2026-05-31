# Diary: Two Clocks — Why the FSM and Graph Cannot Merge

## Observation

The session posed the question: should the FSM config (`watcher-pipeline-v2.yaml`) and the graph configs (`enforce-session.yaml`, etc.) be consolidated into one YAML format?

The answer is no — and the reason reveals something about computational models that the removal analysis missed.

## The Two Clocks

The FSM operates on a **minutes-to-hours clock**. It persists state across process restarts (SQLite-backed job queue), handles timeouts as first-class events (`timeout(600)`), routes external signals (stop, error) from any state via wildcard transitions (`from: "*"`), and uses guard keys to prevent re-entry during async execution. Its state is a *named point in a lifecycle* — you can point at it and say "we are in `enforce_session`."

The graph operates on a **seconds-to-minutes clock**. It runs eagerly to completion, builds structured LLM outputs through Pydantic schemas, fans out across providers (race), and compiles topology for static analysis. Its state is a *dict of accumulated values* — you query it, not point at it.

These are not two syntaxes for the same thing. They are two computational models:

| Property | FSM | Graph |
|---|---|---|
| Execution model | Reactive (event-driven) | Eager (topological) |
| Active entities | One state at a time | Multiple nodes concurrent |
| Persistence | Durable across restarts | In-memory (or checkpointer) |
| Error model | Event routing to failure states | Node-level retry/skip/fail |
| Time awareness | Timeout events, guards | Optional per-node timeout |
| Observable state | Named point (enum) | Value accumulation (dict) |

The bridge (915 lines, 116 diary entries) exists because translating between these models is inherently complex — not because the architecture is wrong.

## The Trap: Unification Bias

The impulse to consolidate two YAML configs into one is `framework_costume` in reverse — instead of adding a keyword for something primitives express, it would be *merging two primitives that serve different physics*. An event-driven state machine and a directed acyclic graph are not variants of each other. They compose — the FSM *calls* graphs — but they don't reduce.

The evidence: the Chaplain's FSM has 13 action entries. Five are `yamlgraph_async` (graph invocations). Four are `bash` (shell scripts). Two are `bash_context` (shell with state capture). One is `validate_gate` (deterministic CI check). One is `changelog_gen` (mechanical).

Only 5 of 13 actions involve graphs at all. The FSM is not "a graph with extra steps" — it's an orchestrator that dispatches to multiple execution backends (graphs, shell, gates), handles timeouts and failures across all of them, and maintains durable named state.

## The Real Simplification

The diary's extensions section proposed "graph-to-graph invocation as first-class edge." This is the correct narrow simplification: for the 60% of FSM states that are just "run graph X → emit event → transition to next state," a `call:` edge within a graph could eliminate the FSM intermediary. But the remaining 40% — global shutdown, timeout events, guard keys, durable persistence, multi-machine coordination — genuinely need an FSM.

The right architecture is not "one YAML to rule them all." It's:

- **Graph YAML** for LLM-heavy steps (structured output, prompt templating, fan-out)
- **FSM YAML** for lifecycle orchestration (durability, timeouts, named states, external events)
- **A thinner bridge** that makes graph-from-FSM invocation feel like a native FSM action type (which `yamlgraph_async` already is — the 915-line bridge might be *at its minimum useful size*)

## Metacognitive Reflection

**Trap encountered:** `unification_bias` — the assumption that two YAML files with similar syntax should be one YAML file with unified syntax. Syntactic similarity ≠ semantic equivalence (existing trap: `false_duplicate`). The FSM YAML and graph YAML look alike (nodes, edges, events/transitions) but model different physics.

**Cure applied:** Asked "what does each provide that the other cannot?" — the list was long in both directions. When two systems have non-overlapping capabilities of roughly equal size, they're peers, not candidates for absorption.

**Heuristic:** Before proposing consolidation of two declarative configs, enumerate what each provides that the other *cannot express*. If both lists have 4+ items, the systems are peers operating at different abstraction levels. Consolidation would not simplify — it would create a chimera.

## Seed

The FSM's superpower is named state (`"we are in enforce_session"`). The graph's superpower is structured accumulation (`state.analysis = {...}`). What if the bridge exposed both simultaneously: the FSM's named state as a read-only key in the graph's state dict, and the graph's accumulated values as queryable context in the FSM? The two clocks would remain separate engines, but their state spaces would be mutually visible. Is that observability, or coupling?
