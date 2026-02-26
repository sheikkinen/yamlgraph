# FR-104: Parallel Chapter Generation with Worker Pools

## Status: Draft

## Problem

The eBook pipeline has 7 independent chapters. Currently they must run sequentially via separate `yamlgraph graph run` commands. Running all 7 in parallel risks API throttling. We need controlled parallelism.

## Analysis

**Chapter independence confirmed:**
- No chapter prompt reads output from another chapter
- All chapters read from source files (`.github/copilot-instructions.md`, `ARCHITECTURE.md`, scripts)
- Write→judge→amend cycle is self-contained per chapter

**Rate limit considerations:**
- Copilot nodes make multiple LLM calls per run (agent loop)
- Full parallelism (7 concurrent) likely triggers throttling
- Staggered parallelism (2-3 workers) is safer

## Proposal

Create `examples/ebook/run-chapters.sh` with workers parameter:

```bash
#!/bin/bash
# Run all chapters with controlled parallelism
# Usage: ./run-chapters.sh [workers] [output_dir]
#   workers: number of parallel chapter runs (default: 2)
#   output_dir: output directory (default: docs/ebook/v1)

WORKERS=${1:-2}
OUTPUT_DIR=${2:-docs/ebook/v1}

# Chapter definitions: graph-file:output-filename
CHAPTERS=(
  "graph-ch00.yaml:00-introduction.md"
  "graph-ch01.yaml:01-doctrine.md"
  "graph-ch02.yaml:02-precommit-gates.md"
  "graph-ch03.yaml:03-chaplain-pipeline.md"
  "graph-ch04.yaml:04-inquisitor.md"
  "graph-ch05.yaml:05-diary-system.md"
  "graph-ch06.yaml:06-traceability.md"
)

run_chapter() {
  local spec=$1
  local graph="${spec%%:*}"
  local filename="${spec##*:}"
  echo "Starting: $graph -> $filename"
  yamlgraph graph run "$graph" --var output_dir="$OUTPUT_DIR" --var filename="$filename" --full
  echo "Completed: $filename"
}

export -f run_chapter
export OUTPUT_DIR

printf '%s\n' "${CHAPTERS[@]}" | xargs -P "$WORKERS" -I {} bash -c 'run_chapter "$@"' _ {}
```

## Acceptance Criteria

1. `./run-chapters.sh` runs all 7 chapters with 2 workers (default)
2. `./run-chapters.sh 3` runs with 3 parallel workers
3. `./run-chapters.sh 1` runs sequentially (safe mode)
4. All chapters complete without throttling at workers=2
5. Logs show start/completion per chapter

## Actions

1. Create `examples/ebook/run-chapters.sh`
2. Test with workers=1 (baseline)
3. Test with workers=2 (target)
4. Test with workers=3 (aggressive)
5. Document throttling behavior at each level
6. Delete `examples/ebook/graph.yaml` (monolithic graph no longer needed)
7. Update `examples/ebook/README.md`

## Out of Scope

- Built-in `yamlgraph graph compose` command (future FR)
- Retry logic for throttled requests
- Progress visualization

## Dependencies

- FR-103 (per-chapter graphs) — completed
