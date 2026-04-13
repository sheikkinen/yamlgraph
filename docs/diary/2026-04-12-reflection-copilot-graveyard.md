# Reflection: The ~/.copilot Graveyard

**Date:** 2026-04-12
**Trigger:** `tree ~/.copilot` analysis requested after the ephemeral storage trap was identified.

## Forensic Report

### Size Profile

| Directory | Size | Contents |
|---|---|---|
| `~/.copilot/` | **1.7 GB** | Total |
| `pkg/universal/` | **1.5 GB** | 14 Copilot CLI versions (0.0.414 → 1.0.24), never cleaned |
| `session-state/` | **173 MB** | 1,490 sessions, never cleaned |
| `logs/` | **20 MB** | Process logs |
| `skills/` | **16 KB** | 3 custom skills (code-reviewer, scripture-troubleshoot, security-reviewer) |

### Session Graveyard: 1,490 Dead Sessions

**Every session Copilot has ever run sits here.** Since Feb 10, 2026 — 61 days — no session has ever been deleted.

| Metric | Value |
|---|---|
| Total sessions | 1,490 |
| Total files across all sessions | 4,639 |
| Sessions with `plan.md` | 101 (6.8%) |
| Sessions with `session.db` | 37 (2.5%) |
| Sessions with files in `files/` | 3 (0.2%) |
| Events.jsonl total size | 157 MB |
| Largest single session | 3.4 MB |
| Oldest session | Feb 10, 2026 |
| Peak day | Mar 8 — 448 sessions |

**101 plan.md files** — architectural plans, implementation specs, FR reviews — all orphaned in UUID-named directories. Discoverable only if you know the session ID. Effectively lost knowledge.

**37 session.db files** — structured SQL data (todos, dependencies, test cases) — also orphaned. The structured data we discussed graduating from ephemeral to permanent — there are 37 prior instances of the same problem.

### Package Accumulation: 1.5 GB

14 Copilot CLI versions retained. Each ~100-130 MB. Only the latest (1.0.24) is active. The other 13 are dead weight:

```
0.0.414  0.0.415  0.0.416  0.0.417  0.0.418  0.0.419  0.0.423
1.0.2    1.0.3    1.0.4    1.0.5    1.0.19   1.0.21   1.0.24
```

### Session Velocity

- Mar 7-8 alone: **648 sessions** (44% of all sessions in 2 days)
- Apr 12 (today): **58 sessions** — including sub-agent sessions spawned by `task` tool
- Average: ~24 sessions/day

Most sessions are micro-lived: sub-agent `task` and `explore` calls each spawn their own session. They complete in seconds but persist forever.

## What This Means

### 1. No Garbage Collection Exists

`~/.copilot` has **no cleanup mechanism**. No TTL, no max-sessions, no prune-on-startup. It grows monotonically. At current rates:
- ~173 MB in 61 days → ~1 GB/year for sessions alone
- Package versions never pruned → ~100 MB per update retained forever

### 2. Plan.md Is a Mass Grave

101 plan files exist in session-state. These are the plans I and prior sessions created when asked to plan work. Some contain real architectural decisions (FR-096 review, FR-131 Inquisitor gate, FR-141 squash merge detection). All are invisible to the project — trapped behind UUID walls.

The earlier ephemeral-storage-trap reflection identified one instance. This reveals it's **systemic**: the tool's default behavior has been silently burying plans for 61 days.

### 3. The Session Is the Wrong Abstraction for Knowledge

A session represents a conversation. Knowledge artifacts (plans, decisions, architectural analysis) represent project state. Binding knowledge to conversation lifetime is an impedance mismatch. The conversation dies; the knowledge should survive.

## Trap: `infrastructure_self_exempt`

The session-state system is meta-tooling that exempts itself from the rules it helps enforce. The Scripture says: "Apply same rules to the guardrail as to what it guards." If project code had 1,490 orphaned temp directories consuming 173 MB with no cleanup, the Inquisitor would flag it. But the infrastructure that hosts the Inquisitor gets a pass.

## Actionable Items

1. **Prune old packages:** `~/.copilot/pkg/universal/` — keep only latest version. Saves ~1.3 GB.
2. **Prune dead sessions:** Sessions older than 30 days with no `plan.md` or `files/` content are pure waste.
3. **Audit the 101 plan.md files:** Some may contain decisions that were never graduated to the project. Surface and archive or discard.
4. **Convention going forward:** The ephemeral-storage-trap reflection already established the rule — plans that answer "would losing this hurt? → yes" go to `docs/` or `feature-requests/`, not session-state.

## Extended Forensics: The Full Copilot Footprint

### Three Storage Tiers

Copilot state is scattered across three locations:

| Tier | Path | Size | Purpose |
|---|---|---|---|
| **CLI home** | `~/.copilot/` | 316 MB (post-prune) | Sessions, logs, packages, config, skills |
| **VS Code global** | `~/Library/.../globalStorage/github.copilot-chat/` | 42 MB | Embeddings, agent definitions, session metadata |
| **VS Code workspace** | `~/Library/.../workspaceStorage/*/GitHub.copilot-chat/` | ~14 MB | Workspace chunks, memory, debug logs |

**Total Copilot disk footprint: ~372 MB** (down from ~1.8 GB pre-prune).

### The Memory Layer

A single memory file exists at `memory-tool/memories/repo/python-env.md`:
```
- Editable install can become stale after working from temporary worktrees
- When .venv/bin/yamlgraph raises ModuleNotFoundError, reinstall with pip install -e .
```

Two operational hints. That's the entire persistent memory for 61 days and 1,490 sessions of work. The memory system exists but is barely used — two facts survived from thousands of interactions.

### Workspace Chunks (Embedding Index)

`workspace-chunks.db` — a SQLite database with vector embeddings for semantic search:
- **8 files indexed**, 184 chunks total, using `metis-1024-I16-Binary` embeddings
- Files indexed: `copilot-instructions.md`, `CHANGELOG.md`, 2 examples, 1 FR, 2 test files, 1 util
- **Last updated: Feb 19** — stale by 52 days
- Only 8 of ~200+ project files indexed — the codebase has grown significantly since

### Session Metadata Registry

`copilotcli.session.metadata.json` (443 KB) — tracks 734 sessions with worktree properties:
- 701 sessions `writtenToDisc=true`
- Contains git base commits, branch names, file change lists
- This is a *second* session registry, separate from the 1,490 directories in `session-state/`
- The two registries are mismatched: 734 vs 1,490 entries

### Agent Definitions

Three built-in agent `.md` files stored in globalStorage:
- `ask-agent/Ask.agent.md` (2.4 KB)
- `explore-agent/Explore.agent.md` (2 KB)
- `plan-agent/Plan.agent.md` (5.3 KB)

These define the agent personas for sub-agent `task` calls. Updated on each CLI version bump.

### Embeddings (Static, Bulky)

| File | Size | Age |
|---|---|---|
| `api.json` | 15 MB | Sep 2025 (7 months old) |
| `commandEmbeddings.json` | 15 MB | Mar 2026 |
| `settingEmbeddings.json` | 12 MB | Jan 2026 |
| `toolEmbeddingsCache.bin` | 81 KB | Feb 2026 |

42 MB of embeddings, most stale. These power VS Code's semantic search for commands/settings.

### Checkpoint System

Every session gets a `checkpoints/index.md` (1,493 files total). In the current session, the checkpoint index is empty — no checkpoints were created. The system exists structurally but appears unused in CLI mode (checkpoints are a VS Code Chat feature for rewind).

### The `research/` Directory Mystery

1,328 sessions have a `research/` subdirectory. All are empty. The directory is created at session init but never populated — a structural ghost.

## Updated Summary

| Resource | Count/Size | Status |
|---|---|---|
| Dead sessions | 1,490 dirs, 173 MB | Never cleaned |
| Orphaned plans | 101 `plan.md` files | Lost knowledge |
| Orphaned databases | 37 `session.db` files | Lost structured data |
| Empty `research/` dirs | 1,328 | Structural ghost |
| Empty checkpoint indices | 1,493 | Structural ghost |
| Stale embeddings | 42 MB | 3-7 months old |
| Session metadata registries | 2 (mismatched: 734 vs 1,490) | Inconsistent |
| Memory facts retained | **2** | 61 days, 1,490 sessions → 2 facts |
| Workspace chunk index | 8 files / 184 chunks | 52 days stale |

## Seed

The memory system's yield — 2 facts from 1,490 sessions — reveals the real storage problem isn't disk space. It's **knowledge retention**. The sessions contain thousands of architectural decisions, bug analyses, and implementation insights. The memory system captured 2 operational hints. The 101 plan files captured more, but they're buried. The diary system (git-tracked) captured the most, because it's the only tier designed for permanent knowledge. The question: should the diary *be* the memory system? A diary entry is a memory that's been through the fire of reflection — refined, contextualized, and committed. Raw session memory is unprocessed input. The graduated heuristic is: memory that survives reflection survives. Memory that doesn't wasn't worth keeping.
