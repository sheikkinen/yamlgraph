# FR-637: novel_fandom Phase 1 — Enriched Canon Schema + Seed Canon

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-07-01

## Summary

Stand up the `examples/novel_fandom/` scaffold by extending the shipped FR-628
wiki-memory kernel from a flat 3-page tech-radar wiki to a **typed, multi-entity
fiction canon**: richer page schemas (characters with goals/relationships/valence,
events with a timeline, factions, locations), a hand-authored seed canon, and a
`lane: static|dynamic` immutability field enforced by the existing gate.

## Value Statement

Gives the fiction pipeline (Phases 2–3) a typed, gated ground-truth canon to
traverse — the prerequisite the pathfinder and prose loop consume — without
rebuilding any of the shipped persistence/gate infrastructure.

## Problem

FR-628 proved the gated-accumulation loop on flat pages
(`{id, type, references, summary}`). Fiction needs structured pages: a character
has *goals*, typed *relationships* with *valence*, a *timeline* placement; an
event has *participants*, *consequences*, and bi-temporal *validity*. Without the
enriched schema there is nothing for a plot pathfinder to read tensions from.

Per [plan-fandom-judgement.md](../docs/plan-fandom-judgement.md): this is an
**example application** (`examples/novel_fandom/`), not a framework feature; the
seed canon must be **concrete** (M2), and the static/dynamic split is enforced by
a `lane` field, not directories (v2 §5B).

## Proposed Solution

### Scaffold (mirrors FR-628 demo shape)

```
examples/novel_fandom/
├── graph.yaml               # copy-and-adapt FR-628 gated-accumulation loop (draft→gate→fix→persist)
├── schema/
│   └── canon.py             # Pydantic models: Character, Event, Faction, Location
├── nodes/
│   └── ref_gate.py          # reuse FR-628 gate + lane-immutability check
├── canon/                   # hand-authored seed (flat — data_files rejects **)
│   ├── kaelen.yaml
│   ├── maren.yaml
│   ├── voss.yaml
│   ├── ashguard.yaml
│   ├── emberwrights.yaml
│   └── age_of_cinders.yaml
├── prompts/
│   ├── draft_page.yaml
│   └── fix_refs.yaml
├── tests/
│   └── test_canon_schema.py
├── README.md
└── demo-output.log
```

> **Implementation note:** Canon files are flat (`canon/*.yaml`) instead of
> in subdirectories. FR-629's `data_files` glob rejects recursive `**` patterns.
> The `type` field in each page discriminates page types.

### Enriched page schema (typed, Pydantic-backed)

```yaml
# canon/characters/kaelen.yaml
type: character
id: kaelen
lane: static                 # immutable after creation
name: Kaelen
goals:
  - "Reforge the Emberbrand with dragonsteel"
  - "Avenge the Ashfall"
personality: disciplined, stoic, grudge-bearing
faction: ashguard
relationships:
  - {to: maren, kind: mentor, valence: trust}
  - {to: voss,  kind: rival,  valence: enmity}
references: [ashguard, maren, voss]
timeline_entry: age_of_cinders
```

The **gate is reused unchanged** for no-orphan (`references` must resolve). The one
addition is a `lane` check: a write to a `lane: static` page that already exists is
rejected.

### Decisions inherited (from the judgement)

- **Scope:** example application `examples/novel_fandom/`.
- **Seeding (C2 resolved for Phase 1):** **Option A — hand-authored seed.** Option B
  (LLM-bootstrap + freeze-gate) deferred to a future FR.
- **Split:** `lane: static|dynamic` field, gate-enforced (not directory-based).

## Acceptance Criteria

- [ ] `examples/novel_fandom/` scaffold exists; `yamlgraph graph lint graph.yaml` passes.
- [ ] Pydantic models for `Character`, `Event`, `Faction`, `Location` in `schema/canon.py`;
      every seed page validates against its model.
- [ ] Hand-authored seed canon: ≥3 characters, ≥2 factions, 1 timeline entry,
      fully cross-linked with **no orphans** (gate passes on the seed).
- [ ] `ref_gate.py` rejects a write to an existing `lane: static` page (RED test first).
- [ ] `ref_gate.py` flags an injected orphan reference in the seed (RED test first).
- [ ] `tests/test_canon_schema.py` covers schema validation + both gate behaviors,
      tagged `@pytest.mark.req("REQ-YG-XXX")`; capability entry added.
- [ ] `demo-output.log` present (demo-gate) showing the loop loading + gating the seed.
- [ ] README documents the schema and the hand-authored-seed decision.

## Alternatives Considered

- **Extend FR-628 demo in place** — rejected: fiction schema would pollute the
  generic tech-radar demo; keep the generic kernel clean, fork a new example.
- **Directory-based static/dynamic split** — rejected per v2 §5B: a `lane` field is
  simpler and works with a single glob.
- **LLM-bootstrap the seed (Option B)** — deferred: unnecessary risk at 6-page scale;
  hand-authoring is trivial and zero-leak.

## Judgement

**Verdict: APPROVED — scope is clear, minimal, and well-grounded.**

### What's right

1. **Clean dependency chain.** All prerequisites are shipped (FR-628 kernel, FR-629 glob,
   FR-630/631 boundary fixes). No speculative dependencies.
2. **Correct scope boundary.** This is an example application in `examples/novel_fandom/`,
   not a framework change. The judgement's C1 decision is respected.
3. **Reuse over reinvention.** The gate is reused unchanged from FR-628; the only
   addition is the `lane` immutability check — a single conditional.
4. **Hand-authored seed (Option A).** At 6 pages this is the right call. Zero-leak,
   zero-cost, zero-risk. Option B (LLM-bootstrap) correctly deferred.
5. **Schema is concrete.** Goals, relationships with valence, timeline entries —
   these are the typed tensions that Phase 2's pathfinder needs to traverse.
   Without them, FR-638 has nothing to read.
6. **Acceptance criteria are testable.** Each criterion is a RED-first test or a
   mechanical check (lint, gate, demo-output.log).

### Corrections

1. **Location: `examples/novel_fandom/`, not `examples/demos/novel_fandom/`.** The FR
   says `examples/novel_fandom/` — correct. This is a full example (like `examples/npc/`),
   not a minimal demo. Confirm the scaffold does NOT go under `examples/demos/`.
2. **Page types in schema.** The FR lists `Character`, `Event`, `Faction`, `Location` in
   `schema/canon.py`. The seed only includes characters, factions, and a timeline entry.
   `Location` schema can be defined but needs no seed page in Phase 1 — acceptable
   forward declaration. Do not add seed pages for types that aren't used.
3. **REQ-YG-XXX placeholder.** The acceptance criteria reference `REQ-YG-XXX` — a real
   requirement ID must be minted (create a `CAP-*.yaml` entry) before enforcement begins.
4. **graph.yaml reuse.** The FR says "reuse FR-628 gated-accumulation loop" but the
   graph must be a new file at `examples/novel_fandom/graph.yaml` that mirrors the
   structure, not a symlink. The gate tool import path changes. Confirm copy-and-adapt,
   not import.

### Scope freeze

- 4 Pydantic models (`Character`, `Event`, `Faction`, `Location`)
- 6 hand-authored seed YAML files (3 characters, 2 factions, 1 timeline)
- 1 `lane` check added to the gate (single `if`)
- Tests for schema validation + lane guard + orphan detection
- README + demo-output.log

Nothing else.

## Related

- [plan-fandom-architecture-2.md](../docs/plan-fandom-architecture-2.md) §3 (enriched schema), §5B (lane).
- [plan-fandom-judgement.md](../docs/plan-fandom-judgement.md) — C1 (scope), C2 (seeding), M2 (example canon).
- [FR-628](./FR-628-wiki-memory-gated-demo.md) — the kernel this scales up.
- [FR-627](./FR-627-canon-link-gate.md) — the reusable no-leak gate (no-orphan half shipped in FR-628).
- [FR-629](./FR-629-data-files-glob-support.md) — glob load of `canon/**/*.yaml`.
