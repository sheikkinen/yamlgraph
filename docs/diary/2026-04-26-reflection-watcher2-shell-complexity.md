---

## 2026-04-26: Watcher2 — Shell Complexity Beyond Model Comprehension

**Context:** Troubleshooting repeated watcher2 crashes. The script has grown to 554 lines of bash with `set -euo pipefail`, ERR traps, worktree management, copilot session orchestration, CI remediation loops, and forensic analysis. Each debugging session requires tracing control flow across dozens of interacting state variables (`WT_DIR`, `MAIN_DIR`, `TOPIC_FILE`, `PIPELINE_STATE`, `ACCEPTANCE_MARKER`), subshell boundaries, and `cd` side effects. Even after fixing two bugs (relative graph path, cwd mutation via `cd "$WT_DIR"`), a third crash appeared at a line number that doesn't correspond to the obvious failure point — the ERR trap reports `line 554` but the actual fault is somewhere upstream, masked by bash's line-number reporting quirks in compound commands.

**Trap:** **framework_costume** — "FSM wearing DAG costume → if <50% nodes use core features, wrong tool." Watcher2 is a state machine (inbox → processing → worktree → plan → research → test → judge → enforce → merge → cleanup) implemented as a 554-line linear bash script with ad-hoc state variables instead of explicit states and transitions. Bash provides no structured error propagation, no typed state, no testable transitions. The `set -e` + ERR trap combination creates a brittle error model where failures cascade unpredictably and line numbers mislead.

**Heuristic:** **500 lines of shell is a system, not a script.** When a bash script exceeds ~200 lines and manages state across multiple phases, it has outgrown the medium. Shell scripts excel at gluing commands together; they fail at orchestrating multi-phase workflows with error recovery, state persistence, and diagnostic introspection. The cognitive cost of debugging exceeds the implementation cost of rewriting in a language with structured error handling and testable state transitions.

**Evidence chain:**
- Bug 1: `cd "$WT_DIR"` mutated cwd, causing `yamlgraph graph run .chaplain/...` to resolve relative to worktree (prompt not found)
- Bug 2: Relative graph path in `handle_failure()` — same root cause, different manifestation
- Bug 3: ERR trap reports line 554 (`done`), actual failure is upstream in RED verification — bash gives no stack trace, no variable dump, no structured diagnostics
- Pattern: each fix requires reading 50+ lines of surrounding context, tracing variable lifetimes across function boundaries, and mentally simulating `set -e` propagation rules

**Seed:** The FSM configs already drafted in gh-238/239/240 (`.chaplain/config/watcher-dispatcher.yaml`, `watcher-pipeline.yaml`) define the 27-state pipeline worker and 6-state dispatcher as explicit state machines. Could the watcher2 rewrite use YAMLGraph itself — a graph that orchestrates graphs — with each phase as a node, state as typed dict, and transitions as edges? The framework already has copilot nodes, shell tool nodes, and checkpointing. Eating our own dog food would validate the framework while solving the comprehension problem.
