# Memento: The FRs the Record Ate

Recovered snapshots of the 39 feature requests deleted during the early FR
era (2026-01-23 → 2026-02-19), before "FR as permanent source of truth"
became doctrine. Each file is the exact blob from the commit *preceding* its
deletion (`<deleting-commit>^`). Recovered 2026-08-23 as a companion to
[docs/origin-story.md](../../origin-story.md), Act IV — *The Record That Ate
Itself*.

These are historical artifacts, not live FRs: unjudged by modern standards,
numbered chaotically (two 011s, five 012s, two 021s), some unnumbered
entirely. That chaos is the point — it is what the traceability spine was
built against.

## Provenance

| Deleted by | Date | Commit subject | Files |
|-----------|------|----------------|-------|
| `944ca655` | 2026-01-23 | chore: remove implemented feature requests, add template | 001–004, 006-subgraph-interrupt-state, and 7 unnumbered (`add-simple-redis-checkpointer`, `bug-prompts-relative-*`, `chainmap-serialization`, `fix-async-redis-checkpointer`, `graph-relative-prompts`, `json-extraction`) |
| `5eab27b7` | 2026-01-28 | chore: reject FR-011 (event emitter + studio UI) | 011-yamlgraph-web-ui — the first *rejected* FR, deleted rather than preserved as precedent |
| `b1d57ba1` | 2026-02-04 | docs: major documentation cleanup and consolidation | 006-subgraph-checkpointer-inheritance, 011a, 011b, 012-0/1/2/3, 012, 013, 021-data-files |
| `f0ea9022` | 2026-02-04 | chore: move fsm-yamlgraph brainstorming to docs-planning | brainstorming-fsm-yamlgraph |
| `542bd1df` | 2026-02-19 | chore(cleanup): remove 14 stale/implemented FRs | 007–010, 014, 017–019, 021-python-map-subnodes, 022, 023, 035, 042, 044a |
| `eec93d4c` | 2026-02-19 | chore(cleanup): remove FR-040 (replaced by Pattern 12 docs) | 040-default-quality-gates |

## Notable exhibits

- **001-interrupt-node.md** — the first FR ever written; interrupt nodes and
  the checkpointer factory, implemented 2026-01-19.
- **011-yamlgraph-web-ui.md** (+ 011a/011b) — the first rejection. Under
  modern doctrine (FR-737) a rejected FR is binding precedent; in January it
  was simply deleted. Its territory (event emitter, studio UI) has been
  re-litigated since.
- **035-mcp-server.md** — proposed the MCP server that today exposes every
  graph as a Copilot tool (CAP-19).
- **brainstorming-fsm-yamlgraph.md** — the seed of the FSM/chaplain runtime
  lineage, evicted to docs-planning.
- **bug-prompts-relative-\*.md** — the unnumbered "just fix it" era: FR
  files named like commit messages, numbering optional.

## Recovery method

```bash
# for each deleting commit c and deleted path f:
git show "$c^:$f" > docs/memento/feature-requests/$(basename "$f")
```

Deleting commits were enumerated with
`git log --diff-filter=D --name-only -- 'feature-requests/*.md'`.
Later deletions (FR-071 onward) are renames, moves to sibling projects, or
governed retirements with their own records — they are not mementos and are
intentionally excluded.
