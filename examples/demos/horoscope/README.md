# Daily Horoscope Demo

Parallel daily horoscope generator using a map node (FR-201).

## What It Does

1. **Generate** — fans out over all 12 zodiac signs in parallel via `type: map`
2. **Assemble** — collects readings and formats them into a single Markdown document
3. **Save** — writes output to `outputs/horoscope-YYYY-MM-DD.md`

## Usage

```bash
yamlgraph graph run examples/demos/horoscope/graph.yaml \
  --var date="$(date +%Y-%m-%d)" --full
```

Output saved to: `outputs/horoscope-2026-03-14.md` (date from `--var`)

## Key Concepts

- **Static `over:` list** — map node iterates over a fixed list (the 12 zodiac signs)
- **`collect:`** — aggregates parallel results into `state.readings`
- **Python tool for output** — `save_horoscope` writes dated file to `outputs/`
- **Minimal Python** — only a 15-line tool for file I/O

## Pipeline

```
START → generate (map: 12 signs) → assemble → save → END
              ↓                        ↓         ↓
        readings[]              document    outputs/horoscope-YYYY-MM-DD.md
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with map node and save tool |
| `prompts/horoscope.yaml` | Per-sign horoscope prompt with schema |
| `prompts/assemble.yaml` | Markdown assembly prompt |
| `tools.py` | `save_horoscope` function for dated file output |
