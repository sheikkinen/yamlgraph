# 2026-03-09: Cross-Graph State Sharing — The Chaplain Pipeline Perspective

## Context

FR-168 (Cross-Graph Session Continuity) is approved. It threads the Copilot CLI session ID from plan-judge to enforce. But examining the broader Chaplain pipeline reveals a pattern: state doesn't flow between pipeline stages, forcing redundant work.

## The Pipeline Flow

```
watch.sh → polls inbox/
  └─> copilot graph (plan → judge → summarize → write_diary)
      └─> if approved: enforce_worktree.sh
          └─> enforce graph (implement → test → precommit → submit_pr)
              └─> finalize_merge.sh (CHANGELOG, FR status, diary stub)

inquisitor.sh (separate) → audits → writes diary → proposes FRs
```

## State That Currently Doesn't Flow

| From | To | Lost State |
|------|----|------------|
| plan-judge | enforce | Session context, codebase exploration |
| enforce | finalize | Files changed, test results, PR number |
| inquisitor | watch | Audit findings, violation severity |
| diary entries | plan | Historical patterns, recurring traps |

## Emerging Needs

1. **Session continuity** (FR-168 scope): Thread session_id across graph boundaries
2. **Structured handoff**: Beyond session_id — FR metadata, exploration findings, constraints
3. **Audit → priority signal**: Inquisitor findings could influence inbox queue order
4. **Cross-run memory**: Recurring diary seeds (e.g., "verification gate" 5×) suggest semantic memory

## Implementation Approaches

**A. File-based handoff** — Write `tmp/handoff-FR-XXX.json`, read via `--var`. Simple, manual cleanup.

**B. State file protocol** — `.chaplain/state/` directory with structured JSON. Graphs read/write via tool nodes.

**C. LanceDB memory nodes** (FR-094 approved) — `memory_read`/`memory_write` as first-class node types.

**D. Graph composition** — Plan-judge-enforce as subgraph nodes within a single meta-graph. State flows naturally.

## Observation

The pipeline is evolving from shell scripts orchestrating separate graphs toward a meta-graph that composes subgraphs with shared state.

The shared state need isn't just "session continuity" — it's making the Chaplain pipeline a first-class YAMLGraph citizen.

## Heuristic

*When N shell scripts pass data via files/env vars, consider whether they should be N subgraph nodes in a single graph with proper state flow.*

## Seed

Should `.chaplain/watch.sh` be replaced by `.chaplain/graph.yaml` — a meta-graph that orchestrates inbox polling, plan-judge, enforce, and inquisitor as subgraph nodes? What would the state schema look like?
