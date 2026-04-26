# Reflection: FR-290 Watcher-FSM Phase 0 Configs

**Date:** 2026-04-26
**FR:** FR-290
**Scope:** Declarative FSM configs for watcher2 dispatcher and pipeline

## Cognitive Process

The task was to translate a bash-scripted watcher daemon into two declarative YAML
state machines — a dispatcher (controller) and a pipeline (worker). The domain was
already well-understood from months of operating watcher2.sh, so the challenge was
not discovery but *formalization*: encoding implicit control flow as explicit states,
transitions, and events.

## Trap: Infrastructure Self-Exempt

The watcher2.sh script had grown organically with implicit error handling — `|| true`
guards, nested if/elif chains, and retry logic buried in function bodies. When
formalizing this as FSM configs, the temptation was to replicate the bash structure
rather than rethink it. The FSM formalism forced cleaner separation: each concern
(retry, timeout, failure routing) became an explicit transition rule rather than a
hidden code path.

## Insight: Dict-format Events for Context Propagation

NC-120's `context_map` feature requires dict-format events (`{event: name, context_map: {...}}`)
rather than bare strings. This caught us during linting — E012 flagged interpolation
variables that weren't declared in any context_map. The fix wasn't to suppress the
warning but to properly declare how context flows between states. The linter enforced
what the documentation only suggested.

## Heuristic

**Formalize before automating.** When migrating imperative scripts to declarative
configs, resist copying the control flow structure. Instead, enumerate the states
and let the transitions emerge from the state invariants. The FSM linter catches
what code review misses.

## Seed

Can the statemachine-engine validate *cross-machine* contracts — ensuring the
dispatcher's `spawn_pipeline` event produces context that satisfies the pipeline's
`start` event input requirements? This would catch integration bugs at config time
rather than runtime.
