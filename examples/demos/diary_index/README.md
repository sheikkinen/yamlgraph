# Diary Index Demo

Cross-reference index of the YAMLGraph diary corpus (FR-254).

## What It Does

1. **List Files** — globs `docs/diary/*.md`, reads each file
2. **Extract All** — fans out via `type: map` + `type: llm`, extracts traps/heuristics/seeds/FR refs from each entry
3. **Aggregate** — deterministic Python aggregation: counts, sorts, builds reverse indexes
4. **Write Index** — persists the structured index to `docs/diary-index.yaml`

## Usage

```bash
yamlgraph graph run examples/demos/diary_index/graph.yaml --full
```

Output saved to: `docs/diary-index.yaml`

## Expected Cost

- **Model:** `claude-haiku-4-5` (~$0.25/MTok input)
- **Corpus:** ~450 entries × ~2KB avg = ~900K input tokens
- **Estimated cost:** $0.25–0.50 per full run
- **Latency:** 2–5 minutes with map node parallelism

## Key Concepts

- **`type: map` + `type: llm`** — parallel LLM extraction over a dynamic list
- **`max_items: 500`** — overrides the default 100-item limit for large corpora
- **Deterministic aggregation** — `aggregate` node is `type: python`, not `type: llm`
- **`sorted_add` reducer** — collects map results into state via append
- **Python tool for output** — `write_index` persists YAML to disk

## Output Format

```yaml
entries:
  - filename: "2026-01-10-reflection.md"
    date: "2026-01-10"
    title: "Quick Confidence Trap"
    category: "reflection"
    traps: [quick_confidence, downstream_fix]
    heuristics: [test_before_reading]
    seeds: []
    fr_references: [FR-100]

traps_index:
  - trap: downstream_fix
    count: 42
    filenames: [...]

seeds_index:
  - seed: "Can we auto-detect quick_confidence in PR reviews?"
    count: 3
    filenames: [...]

fr_index:
  - fr: FR-100
    count: 7
    filenames: [...]

heuristics_candidates:
  - heuristic: test_before_reading
    count: 5
    filenames: [...]

statistics:
  total_entries: 452
  total_unique_traps: 18
  total_unique_seeds: 45
  total_unique_frs: 67
  entries_by_category:
    reflection: 180
    audit: 45
    git-report: 120
    ...
```

## Pipeline

```
START → list_files → extract_all (map: N entries) → aggregate → write_index → END
              ↓              ↓                          ↓            ↓
        diary_files[]   extractions[]               index     docs/diary-index.yaml
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with map + python nodes |
| `prompts/extract_entry.yaml` | Per-entry extraction prompt with inline schema |
| `tools.py` | `list_diary_files`, `aggregate_index`, `write_index` functions |

## Related

- FR-254: Feature request
- `examples/demos/horoscope/` — Reference pattern for map → aggregate → save
- `docs/diary/` — The diary corpus being indexed
