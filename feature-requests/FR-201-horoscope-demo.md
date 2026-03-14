# Feature Request: Horoscope Demo — Parallel Daily Horoscope Generator

**Priority:** LOW
**Type:** Feature
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-14

## Summary

Add an `examples/demos/horoscope/` demo that generates daily horoscopes for all 12 zodiac signs in parallel using a map node, then assembles the results into a single Markdown file.

## Value Statement

New users see a real-world, self-contained example of map-node parallelism that produces a tangible artifact (a Markdown horoscope page), reinforcing the "60-80 % YAML, zero Python" promise.

## Problem

The existing `map/` demo fans out over a dynamically generated list. There is no demo that:

1. Fans out over a **static, well-known list** (the 12 zodiac signs).
2. Produces a **single formatted Markdown document** as its final output.
3. Demonstrates passing **today's date** as a runtime variable.

A horoscope generator is an ideal candidate: the domain is universally understood, the list is fixed, and the output is immediately readable.

## Proposed Solution

### Directory layout

```
examples/demos/horoscope/
├── graph.yaml
└── prompts/
    ├── horoscope.yaml
    └── assemble.yaml
```

### `graph.yaml`

```yaml
version: "1.0"
name: daily-horoscope
description: Generate daily horoscopes for all 12 zodiac signs in parallel

prompts_relative: true
prompts_dir: prompts

defaults:
  temperature: 0.9

state:
  date: str

nodes:
  generate:
    type: map
    over:
      - Aries
      - Taurus
      - Gemini
      - Cancer
      - Leo
      - Virgo
      - Libra
      - Scorpio
      - Sagittarius
      - Capricorn
      - Aquarius
      - Pisces
    as: sign
    node:
      prompt: horoscope
      state_key: reading
      variables:
        sign: "{state.sign}"
        date: "{state.date}"
    collect: readings

  assemble:
    prompt: assemble
    state_key: document
    variables:
      date: "{state.date}"
      readings: "{state.readings}"

edges:
  - from: START
    to: generate
  - from: generate
    to: assemble
  - from: assemble
    to: END

exports:
  document:
    format: markdown
    filename: horoscope.md
```

### `prompts/horoscope.yaml`

```yaml
schema:
  name: Horoscope
  fields:
    sign:
      type: str
      description: "Zodiac sign name"
    reading:
      type: str
      description: "Daily horoscope reading (2-3 sentences)"

system: |
  You are a whimsical astrologer. Write short, uplifting daily horoscopes.

user: |
  Write a daily horoscope for {sign} on {date}.
  Keep it to 2-3 sentences. Be creative and positive.
```

### `prompts/assemble.yaml`

```yaml
system: |
  You are a Markdown formatter. Assemble horoscope readings into
  a clean document. Do not alter the readings — only format.

user: |
  Assemble these horoscope readings into a single Markdown document
  for {date}. Use a level-2 heading for each sign.

  Readings:
  {readings}
```

### CLI invocation

```bash
yamlgraph graph run examples/demos/horoscope/graph.yaml \
  --var date="$(date +%Y-%m-%d)" --full
```

### `demo.sh` registration

Add a `demo_horoscope` function and a `horoscope)` case to `examples/demos/demo.sh`.

## Acceptance Criteria

- [x] `yamlgraph graph lint examples/demos/horoscope/graph.yaml` passes with no errors
- [ ] `yamlgraph graph run examples/demos/horoscope/graph.yaml --var date="2026-03-14" --full` executes successfully, producing 12 per-sign readings and one assembled Markdown document
- [x] Map node fans out over all 12 signs in parallel (verified by graph structure, not wallclock)
- [ ] Output state key `document` contains valid Markdown with one heading per sign
- [ ] `exports` section writes `horoscope.md` to the outputs directory
- [x] Demo registered in `examples/demos/demo.sh`
- [x] No Python code required (pure YAML graph + prompts)
- [x] Tests added (graph lint unit test at minimum)
- [x] Documentation: demo listed in demos README if one exists

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Use a Python tool to supply the sign list | Defeats the "zero Python" goal; a static `over:` list is simpler |
| Generate signs dynamically with an LLM node | Adds unnecessary LLM call; the zodiac is a fixed, known list |
| One prompt per sign (12 separate nodes) | Verbose; doesn't showcase `type: map` |
| Use `data_files:` for the sign list | Valid, but inline `over:` list is more self-contained for a demo |

## Related

- `examples/demos/map/graph.yaml` — existing map fan-out demo (dynamic list)
- `examples/demos/innovation_matrix/pipeline.yaml` — map with `max_items: 25`
- `examples/demos/hello/graph.yaml` — minimal demo pattern
- `feature-requests/034-novel-generator-demo.md` — prior demo FR
