# Philosopher Daemon

**FR-184/FR-194** — Automated pattern detection across diary entries with world context enrichment.

## Usage

```bash
# On-demand scan (default mode)
.chaplain/philosopher.sh

# Or run graph directly
yamlgraph graph run examples/philosopher/graph.yaml \
  --var diary_dir="docs/diary" \
  --var inbox_dir=".chaplain/inbox" \
  --var lookback_days=30 \
  --var graduation_threshold=3 \
  --var date="$(date +%Y-%m-%d)" \
  --var diary_prefix="Philosopher" \
  --full
```

## Graph Topology

```
START → scan → analyze → propose → load_context → reflect → write_diary → END
```

| Node | Type | Purpose |
|------|------|---------|
| `scan` | python | Extract `**Trap:**`, `**Heuristic:**`, `**Seed:**` markers from diary files |
| `analyze` | copilot | Detect patterns meeting graduation threshold |
| `propose` | python | Write graduation proposals to `.chaplain/inbox/` |
| `load_context` | python | Load external world context from `docs/world-context.md` (FR-194) |
| `reflect` | copilot | Generate Philosopher's own diary reflection, enriched with world context |
| `write_diary` | python | Append reflection to `docs/diary/` |

## Output Format

### Graduation Proposals

Written to `.chaplain/inbox/graduate-{type}-{name}.md`:

```markdown
# Graduate trap: quick_confidence

**Occurrences:** 4 times across 4 diary entries

**Type:** trap

**Evidence:**
- diary-2026-01-01.md
- diary-2026-01-02.md
- diary-2026-01-03.md
- diary-2026-01-04.md

## Proposal

Add `quick_confidence` to Scripture under `traps:` section.
```

### Diary Reflection

Appended to `docs/diary/diary-{date}.md` with prefix "Philosopher":

```markdown
**Context:** The Philosopher scanned diary entries for recurring patterns.

**Observations:** Found 3 graduation candidates...

**Heuristic:** Systematic scanning catches graduations human review misses.

**Seed:** Can cross-session trap detection reveal deeper patterns?
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DIARY_DIR` | `docs/diary` | Directory containing diary entries |
| `INBOX` | `.chaplain/inbox` | Output directory for proposals |
| `LOOKBACK_DAYS` | `30` | How far back to scan |
| `GRADUATION_THRESHOLD` | `3` | Min occurrences for graduation |
| `WORLD_CONTEXT_PATH` | `docs/world-context.md` | Path to external world context file (FR-194) |

## Authority Chain

The Philosopher **never edits Scripture directly**. It proposes to inbox; the Chaplain Plans, Judges, and Enforces. This preserves the existing authority chain.
