# Chinese Horoscope Demo

Parallel daily Chinese zodiac horoscope generator using a map node.

## What It Does

1. **Generate** - fans out over all 12 Chinese zodiac animals in parallel via `type: map`
2. **Assemble** - collects readings and formats them into a single Markdown document
3. **Save** - writes output to `outputs/chinese-horoscope-YYYY-MM-DD.md`

## Usage

```bash
yamlgraph graph run examples/demos/chinese-horoscope/graph.yaml \
  --var date="$(date +%Y-%m-%d)" --full
```

Output saved to: `outputs/chinese-horoscope-2026-07-29.md` (date from `--var`)

## Key Concepts

- **Static `over:` list** - map node iterates over the 12 Chinese zodiac animals
- **`collect:`** - aggregates parallel results into `state.readings`
- **Python tool for output** - `save_chinese_horoscope` writes a dated file to `outputs/`
- **Minimal Python** - only a small tool for file I/O

## Pipeline

```text
START -> generate (map: 12 animals) -> assemble -> save -> END
              |                         |          |
        readings[]                 document   outputs/chinese-horoscope-YYYY-MM-DD.md
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition with map node and save tool |
| `prompts/chinese_horoscope.yaml` | Per-animal Chinese zodiac horoscope prompt with schema |
| `prompts/assemble.yaml` | Markdown assembly prompt |
| `tools.py` | `save_chinese_horoscope` function for dated file output |
