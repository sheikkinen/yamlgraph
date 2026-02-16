# Feature Request: Persistent Logbook via MCP

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 2–3 days
**Requested:** 2026-02-16

## Summary

Add persistent long-term memory to the MCP server via a logbook — an append-only structured log that tracks graph executions, decisions, and evolution across sessions. Three new MCP tools: `log_entry`, `search_log`, `list_recent`.

## Problem

Every AI agent session starts cold. There is no continuity between conversations:

1. **No execution history** — which graphs were run, with what inputs, producing what key findings? The agent cannot say "last time you ran this, the top recommendation was X."
2. **No decision trail** — judgements (e.g., "Phase 4 dropped: 3 blockers") live in chat context that evaporates. New sessions cannot pick up where previous ones left off.
3. **No evolution tracking** — problem statements, plans, and outputs evolve through iterations. That refinement history is valuable but currently lost.

The Innovator's Toolkit demonstrates this acutely: running the same problem statement through the pipeline after refactoring produced fundamentally different recommendations. Without a logbook, the agent has no way to compare or learn from prior runs.

## Proposed Solution

### Storage: SQLite (default) or Markdown

SQLite provides structured queries; markdown provides human readability. Default to SQLite with optional markdown export.

```yaml
# .yamlgraph/logbook.db (auto-created)
# Or configure in graph metadata:
logbook:
  type: sqlite          # sqlite | markdown
  path: .yamlgraph/logbook.db
```

### Three MCP Tools

```python
# 1. Append an entry
log_entry(
    topic="yamlgraph-adoption",     # grouping key
    entry_type="graph_run",         # graph_run | decision | note | evolution
    content="Ran toolkit v2 against refactored problem statement...",
    metadata={"graph": "toolkit.yaml", "duration_s": 420, "output_dir": "..."}
)

# 2. Search entries
search_log(
    query="yamlgraph adoption",     # full-text search
    entry_type="decision",          # optional filter
    since="2026-02-01"              # optional date filter
)

# 3. List recent entries
list_recent(
    limit=10,                       # number of entries
    topic="yamlgraph-adoption"      # optional topic filter
)
```

### Auto-Logging

When `run_graph` is called via MCP, automatically log:
- Graph name, input variables (truncated), timestamp
- Key output fields (configurable, e.g., first 500 chars of `final_report`)
- Duration, success/failure status

### Schema

```sql
CREATE TABLE logbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    topic TEXT,
    entry_type TEXT NOT NULL,  -- graph_run, decision, note, evolution
    content TEXT NOT NULL,
    metadata TEXT,             -- JSON blob
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_topic ON logbook(topic);
CREATE INDEX idx_type ON logbook(entry_type);
CREATE INDEX idx_timestamp ON logbook(timestamp);
```

## Use Cases

1. **Session continuity** — agent reads recent entries at session start, knows what happened before
2. **Run comparison** — "compare this toolkit run with the previous one on the same problem"
3. **Decision audit** — "what decisions were made about feature X and why?"
4. **Progress tracking** — "what has been accomplished this week on project Y?"
5. **Pattern detection** — "which graphs are run most frequently? which produce the best outcomes?"

## Acceptance Criteria

- [ ] `log_entry` MCP tool writes to SQLite logbook
- [ ] `search_log` MCP tool returns matching entries with full-text search
- [ ] `list_recent` MCP tool returns N most recent entries, filterable by topic/type
- [ ] Auto-logging on `run_graph` captures input/output/duration
- [ ] Logbook auto-created on first write (zero config)
- [ ] Tests added (unit: 6+, covering CRUD + search + auto-log)
- [ ] REQ-YG-07x requirements added to ARCHITECTURE.md
- [ ] CAP-20 capability registered

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| Append-only markdown | Human-readable, git-friendly | No structured queries, slow search |
| Redis | Fast, TTL support | External dependency, overkill for single-user |
| YAMLGraph graph as logbook | Dogfooding | Too meta, circular dependency risk |
| **SQLite (chosen)** | Zero-config, structured, fast FTS | Binary file, not directly editable |

## Open Questions

1. Should the logbook be per-project or global? Per-project (`.yamlgraph/logbook.db` in project root) seems right.
2. Should entries have TTL/retention policy, or grow unbounded?
3. Should the agent be *instructed* to log decisions (via copilot-instructions), or should it be automatic?
