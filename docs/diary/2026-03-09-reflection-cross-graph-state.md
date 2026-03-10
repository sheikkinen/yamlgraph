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

---

## Continuation: Long-Term Memory and Learning Use Cases

### The Memory Gap

Current YAMLGraph executions are stateless across runs. Each graph invocation starts fresh, discarding:
- What worked before (successful patterns)
- What failed (traps encountered)
- Domain knowledge accumulated (codebase conventions)
- User preferences (style, verbosity, focus areas)

The diary exists as human-readable record but isn't queryable by graphs.

### Concrete Use Cases

**1. Trap Recognition — "I've Seen This Before"**

```yaml
nodes:
  recall_traps:
    type: memory_read
    query: "traps similar to {state.current_error}"
    state_key: known_traps

  apply_cure:
    type: llm
    prompt: apply-known-cure
    variables:
      error: "{state.current_error}"
      similar_traps: "{state.known_traps}"
```

When the enforce pipeline hits a pre-commit failure, it could recall: "Last 3 times this happened, the cure was X."

**2. Pattern Graduation — Recurring Seeds**

The diary shows "verification gate" appeared 5× before becoming FR-164. A memory system could:
- Track seed recurrence across diary entries
- Auto-propose graduation when threshold reached
- Cite prior occurrences as evidence

```yaml
nodes:
  check_seed_recurrence:
    type: memory_read
    query: "seed: {state.new_seed}"
    filter: "created_at > 7 days ago"
    state_key: prior_seeds

  graduate_if_recurring:
    type: router
    condition: "len(state.prior_seeds) >= 3"
    routes:
      true: propose_fr
      false: store_seed
```

**3. Codebase Convention Learning**

As the enforce pipeline implements FRs, it learns:
- File naming patterns (`test_*.py`, `FR-XXX-*.md`)
- Import conventions (relative vs absolute)
- Error handling patterns (`PipelineError.from_exception`)

```yaml
nodes:
  recall_conventions:
    type: memory_read
    query: "conventions for {state.file_type}"
    state_key: conventions

  implement_with_context:
    type: copilot
    prompt: implement-fr
    variables:
      conventions: "{state.conventions}"
```

**4. User Preference Adaptation**

Track implicit preferences from PR feedback:
- Comment style (terse vs. detailed)
- Test coverage expectations
- Documentation depth

```yaml
nodes:
  load_preferences:
    type: memory_read
    query: "user preferences for code style"
    state_key: preferences
```

**5. Audit Pattern Recognition**

Inquisitor could learn which violations recur and weight them:

```yaml
nodes:
  recall_violation_history:
    type: memory_read
    query: "violations similar to {state.finding}"
    state_key: history

  calculate_severity:
    type: llm
    prompt: weight-by-recurrence
    # Violations that recur 5× get higher priority than first-time findings
```

### Memory Architecture Options

**A. Append-Only Log (Simple)**
```
.chaplain/memory/
├── seeds.jsonl          # append-only seed log
├── traps.jsonl          # append-only trap log
└── conventions.jsonl    # learned patterns
```

**B. Vector Store (FR-094 LanceDB)**
```python
# Semantic search over past experiences
results = memory.search("authentication error in copilot node", limit=5)
```

**C. Knowledge Graph**
```
Trap(quick_confidence) --cured_by--> Cure(judge_as_junior_pr)
Seed(verification_gate) --graduated_to--> FR(FR-164)
Convention(test_naming) --applies_to--> FileType(test)
```

### The Learning Loop

```
Execute → Observe outcome → Extract pattern → Store in memory
    ↑                                              │
    └──────────────── Recall on next run ──────────┘
```

Current state: Execute → Observe → *discard*

Target state: Execute → Observe → Extract → **Store** → Execute → **Recall** → Observe → ...

### Heuristic

*Memory is the bridge between stateless execution and continuous improvement. Without it, each run is a fresh start; with it, the system can learn from experience.*

### Seed

Should the diary format be machine-parseable (frontmatter + structured sections) so memory nodes can index it directly? Or should memory be a separate store that the diary references?
