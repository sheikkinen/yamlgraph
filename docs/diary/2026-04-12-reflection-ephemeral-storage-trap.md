# Reflection: Ephemeral Storage for Permanent Artifacts

**Date:** 2026-04-12
**Trigger:** Game engine architecture plan (12KB, 30 todos, schema design, project structure) was stored in `~/.copilot/session-state/` — an ephemeral folder that dies with the session — instead of `docs/` or `feature-requests/`.

## What Happened

The `[[PLAN]]` mode instruction says: *"Save the plan to session workspace."* I followed that instruction verbatim. The plan was a complete architecture document for a new project — not scratch notes, not a checklist, not session-local state. It was a permanent artifact stored in a temporary location.

The user asked "where is the plan" — 8 hours after it was written. The fact that the question needed to be asked is the failure signal. Permanent artifacts must be discoverable through the project's established paths, not through session memory.

## Damage Report

| Item | Status |
|---|---|
| Plan content | ✅ Intact (session still alive) |
| Data loss | ❌ None yet — but one session-close from total loss |
| Discoverability | ❌ Failed — plan invisible to `ls docs/`, `ls feature-requests/`, git, grep |
| Doctrine compliance | ❌ Violated — plans should be FRs or docs, not session ephemera |
| SQL todos | ⚠️ Also ephemeral — session database dies with session |

**Blast radius if session had ended:** Complete loss of architecture plan + 30 todo items + dependency graph. Only the summary in chat history would survive — insufficient to reconstruct the schema design and project structure.

## Trap: `vendor_default_as_help`

The `[[PLAN]]` mode instruction is a **tool default** — it tells the agent where to put session-scoped plans. But not all plans are session-scoped. The instruction doesn't say "always put plans here regardless of artifact lifetime." It says "save the plan to session workspace" — which I followed without asking: *does this artifact belong in ephemeral storage?*

The trap is treating a tool's default behavior as correct behavior without checking the artifact's lifecycle requirements against the storage's lifecycle guarantees.

**Classification test that should have been applied:**

| Question | Answer | Storage |
|---|---|---|
| Would losing this hurt? | Yes | Permanent (docs/, feature-requests/) |
| Is this only useful during this session? | No | Permanent |
| Does this define architecture for a new project? | Yes | Definitely permanent |
| Is this a scratchpad for current work? | No | N/A |

Every answer pointed to permanent storage. The default was followed anyway.

## Cure Applied

Plan copied to `docs/plan-aigame-engine.md`. Discoverable via git, grep, ls. Survives session death.

## Heuristic

**Artifact lifecycle must match storage lifecycle.** Before writing to ephemeral storage, ask: "If this session ends now, is the loss acceptable?" If no, it's a permanent artifact wearing ephemeral clothes.

## Seed

The SQL `todos` table has the same problem — 30 structured todos with dependency graphs, all in a session-scoped SQLite database. If the plan graduates to a feature request, should the todos graduate to the FR's acceptance criteria? The structured data (dependency DAG, status tracking) is richer than flat markdown checkboxes — but it's trapped in an ephemeral container. Is there a pattern for "graduate session state to permanent artifact"?
