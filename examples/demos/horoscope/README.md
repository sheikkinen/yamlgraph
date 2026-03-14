# Daily Horoscope Demo

Parallel daily horoscope generator using a map node (FR-201).

## What It Does

1. **Generate** — fans out over all 12 zodiac signs in parallel via `type: map`
2. **Assemble** — collects readings and formats them into a single Markdown document

## Usage

```bash
yamlgraph graph run examples/demos/horoscope/graph.yaml \
  --var date="$(date +%Y-%m-%d)" --full
```

## Key Concepts

- **Static `over:` list** — map node iterates over a fixed list (the 12 zodiac signs)
- **`collect:`** — aggregates parallel results into `state.readings`
- **`exports:`** — writes the assembled document to `horoscope.md`
- **No Python required** — pure YAML graph + prompts

## Pipeline

```
START → generate (map: 12 signs) → assemble → END
              ↓                        ↓
        readings[]              document (markdown)
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with map node and exports |
| `prompts/horoscope.yaml` | Per-sign horoscope prompt with schema |
| `prompts/assemble.yaml` | Markdown assembly prompt |
