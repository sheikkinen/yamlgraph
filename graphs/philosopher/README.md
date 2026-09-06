# Philosopher Daemon

FR-184/FR-185/FR-194/FR-195/FR-196: Scans diary entries for recurring patterns and proposes graduations to Scripture.

## Usage

Run directly:

```bash
yamlgraph graph run graphs/philosopher/graph.yaml \
  --var diary_dir="docs/diary" \
  --var inbox_dir="proposals" \
  --var lookback_days=30 \
  --var graduation_threshold=3 \
  --var date="$(date +%Y-%m-%d)" \
  --var diary_prefix="Philosopher" \
  --full
```

## Phases

1. **scan** — Extract `**Trap:**`, `**Heuristic:**`, `**Seed:**` markers from diary files
2. **analyze** — Copilot detects patterns and proposes graduations (FR-185)
3. **distill** — Select single strongest candidate (FR-195)
4. **challenge** — Devil's advocate gate (FR-195)
5. **propose** — Write graduation proposals to `inbox_dir` (`proposals/`)
6. **reflect** — Write philosopher's own diary entry

## Portability

The graph is self-contained in `graphs/philosopher/`: `tools.py` loads the sibling `diary.py` by path (CAP-75 graph-scope tool loading).
It makes no claim about copying `.chaplain/`.
