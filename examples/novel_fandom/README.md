# Novel Fandom — Typed Fiction Canon

A fiction-domain example demonstrating LLM-bootstrapped world-building with typed
canon management. The genesis pipeline converts a plain-text premise into structured
canon YAML; downstream graphs add characters, advance plot, and draft prose.

## Overview

### Genesis Pipeline (FR-655)

The `genesis.yaml` graph bootstraps a seed canon from a one-paragraph premise:

1. **Load** — read premise text from file
2. **Synopsis** — LLM expands premise into full-disclosure prose
3. **Roster** — LLM extracts 2–4 principal character names
4. **Characters** — map node generates a dry RPG-style card per name
5. **Structure** — single LLM pass converts all prose into typed canon YAML
6. **Persist** — writes structured output to `canon/` subdirectories

### Accumulation Loop

The `graph.yaml` loop adds dynamic pages to canon with deterministic gates:

1. **No orphan references** — every `references` entry resolves to an existing page.
2. **Lane immutability** — `lane: static` pages cannot be overwritten by LLM.

## Schema

Pydantic models in [`schema/canon.py`](schema/canon.py):

| Type | Key Fields |
|------|-----------|
| **Premise** | `genre_tags`, `era`, `themes`, `calendar_note` |
| **Synopsis** | `text` (full-disclosure reveal-all prose) |
| **Character** | `birth_year`, `role` (protagonist/antagonist/mentor/trickster/supporting), `goals`, `personality`, `relationships` |
| **Event** | `year`, `scope` (personal/local/regional/global), `participants`, `consequences` |
| **Faction** | `name`, `description`, `members` |
| **Location** | `name`, `description` |
| **Rule** | `domain` (magic/social/political/economic/religious), `description` |

## Running

```bash
# Bootstrap canon from premise
yamlgraph graph run examples/novel_fandom/genesis.yaml \
  --var premise_file=examples/dungeon_master/premises/floodmark-saga.txt \
  --full

# Lint graphs
yamlgraph graph lint examples/novel_fandom/genesis.yaml
yamlgraph graph lint examples/novel_fandom/graph.yaml

# Add a dynamic character to existing canon
yamlgraph graph run examples/novel_fandom/graph.yaml \
  --var input="A salt-road stranger named Reinmar" \
  --full
```

## Structure

```
examples/novel_fandom/
├── genesis.yaml        # Premise → seed canon bootstrap (FR-655)
├── graph.yaml          # Gated accumulation loop (draft → gate → fix → persist)
├── find_path.yaml      # Plot pathfinder (retrieve tensions → LLM → gate → fix)
├── draft.yaml          # Prose drafting (map beats → chapters → prose gate)
├── close.yaml          # Close loop (extract deltas → apply to canon)
├── canon/              # Generated canon (character/, event/, faction/, etc.)
├── nodes/              # Python nodes (genesis_tools, persist_genesis, gates)
├── prompts/            # LLM prompt templates
├── schema/canon.py     # Pydantic page models
└── tests/              # Schema + gate tests
```

## Related

- [FR-655](../../feature-requests/FR-655-genesis-graph.md) — genesis pipeline
- [FR-637](../../feature-requests/FR-637-novel-fandom-canon-schema-seed.md) — canon schema + seed
- [FR-628](../../feature-requests/FR-628-wiki-memory-gated-demo.md) — the kernel
- [FR-638](../../feature-requests/FR-638-novel-fandom-plot-pathfinder.md) — Phase 2 (pathfinder)
- [FR-639](../../feature-requests/FR-639-novel-fandom-prose-close-loop.md) — Phase 3 (prose + close)
- [FR-642](../../feature-requests/FR-642-novel-fandom-wiki-core-types.md) — Premise + Synopsis types
