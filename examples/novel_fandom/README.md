# Novel Fandom — Typed Fiction Canon

A fiction-domain example application demonstrating typed canon management with
reference-integrity and lane-immutability gates. Built on the FR-628 wiki-memory
kernel.

## Overview

The canon is a set of typed YAML pages (characters, events, factions, locations)
that are cross-linked by `references`. A deterministic gate ensures:

1. **No orphan references** — every entry in `references` must resolve to an
   existing canon page.
2. **Lane immutability** — pages marked `lane: static` cannot be overwritten.
   New pages created by the LLM are always `lane: dynamic`.

## Schema

All pages share a common base: `id`, `type`, `lane`, `references`. Each type
adds domain-specific fields:

| Type | Key Fields |
|------|-----------|
| **Premise** | `text`, `genre_tags`, `era`, `themes` |
| **Synopsis** | `text` (full-disclosure reveal-all prose) |
| **Character** | `goals`, `personality`, `faction`, `relationships` (typed: `to`, `kind`, `valence`) |
| **Event** | `window`, `participants`, `consequences`, `valid_from`, `valid_to` (bi-temporal) |
| **Faction** | `name`, `description`, `members` |
| **Location** | `name`, `description` |

Pydantic models in [`schema/canon.py`](schema/canon.py) validate every page.

## Seed Canon

Hand-authored (Option A — zero leak risk). Ten pages, fully cross-linked:

- **Premise:** The Ashfall thematic seed — guilt, legacy, truth vs stability
- **Synopsis:** Full-disclosure reveal-all prose expanding the premise
- **Characters:** Kaelen (Ashguard, rival to Voss), Maren (Emberwrights, mentor
  to Kaelen), Voss (Emberwrights, rival to Kaelen)
- **Factions:** The Ashguard, The Emberwrights
- **Timeline:** Age of Cinders (the current era)
- **Rules:** Emberbrand Rule (magic system), Ashfall Pact (social rule)

All seed pages are `lane: static` — the LLM cannot overwrite them.

## Running

```bash
# Lint the graph
yamlgraph graph lint examples/novel_fandom/graph.yaml

# Add a new dynamic character
yamlgraph graph run examples/novel_fandom/graph.yaml \
  --var input="A wandering scholar named Rhael from the Emberwrights" \
  --full
```

## Structure

```
examples/novel_fandom/
├── graph.yaml          # Gated accumulation loop (draft → gate → fix → persist)
├── canon/              # Seed canon (flat, globbed as canon/*.yaml)
├── nodes/ref_gate.py   # Reference + lane gate
├── prompts/            # LLM prompt templates
├── schema/canon.py     # Pydantic page models
└── tests/              # Schema + gate tests
```

## Design Decisions

- **Flat canon directory** (not subdirectories) — `data_files` glob rejects
  recursive `**` patterns (FR-629). The `type` field discriminates page types.
- **Hand-authored seed** — at 10 pages, LLM-bootstrapping adds risk without value.
  Option B (LLM-bootstrap + freeze-gate) deferred to a future FR.
- **`lane` field, not directories** — simpler, works with a single glob pattern.

## Related

- [FR-637](../../feature-requests/FR-637-novel-fandom-canon-schema-seed.md) — canon schema + seed
- [FR-628](../../feature-requests/FR-628-wiki-memory-gated-demo.md) — the kernel
- [FR-638](../../feature-requests/FR-638-novel-fandom-plot-pathfinder.md) — Phase 2 (pathfinder)
- [FR-639](../../feature-requests/FR-639-novel-fandom-prose-close-loop.md) — Phase 3 (prose + close)
- [FR-642](../../feature-requests/FR-642-novel-fandom-wiki-core-types.md) — Premise + Synopsis types
