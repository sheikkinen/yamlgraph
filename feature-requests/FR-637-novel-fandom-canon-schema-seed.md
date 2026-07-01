# FR-637: novel_fandom Phase 1 — Enriched Canon Schema + Seed Canon

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Proposed
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
├── graph.yaml               # reuse FR-628 gated-accumulation loop (draft→gate→fix→persist)
├── schema/
│   └── canon.py             # Pydantic models: Character, Event, Faction, Location
├── nodes/
│   └── ref_gate.py          # reuse FR-628 gate + lane-immutability check
├── canon/                   # hand-authored seed (Option A — zero leak risk)
│   ├── characters/kaelen.yaml
│   ├── characters/maren.yaml
│   ├── characters/voss.yaml
│   ├── factions/ashguard.yaml
│   ├── factions/emberwrights.yaml
│   └── timeline/age_of_cinders.yaml
├── tests/
│   └── test_canon_schema.py
├── README.md
└── demo-output.log
```

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

## Related

- [plan-fandom-architecture-2.md](../docs/plan-fandom-architecture-2.md) §3 (enriched schema), §5B (lane).
- [plan-fandom-judgement.md](../docs/plan-fandom-judgement.md) — C1 (scope), C2 (seeding), M2 (example canon).
- [FR-628](./FR-628-wiki-memory-gated-demo.md) — the kernel this scales up.
- [FR-627](./FR-627-canon-link-gate.md) — the reusable no-leak gate (no-orphan half shipped in FR-628).
- [FR-629](./FR-629-data-files-glob-support.md) — glob load of `canon/**/*.yaml`.
