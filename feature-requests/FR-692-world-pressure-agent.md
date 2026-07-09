# Feature Request: FR-692 — World Pressure Agent

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1–2 days
**Requested:** 2026-07-07
**Depends:** FR-691 (threads — the admission rule cites thread ids)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 3 of 7)
**Capability:** CAP-196 (novel-fandom-world-pressure)
**Requirements:** REQ-YG-532 (pressure admission gate), REQ-YG-533 (kinship reciprocity gate)

## Summary

Agent pass that adds targeted world-pressure entities to canon (additive-only): kinship trees for the two clans and the Reinmar trade network. Every new entity must cite the thread id(s) it pressurizes — no thread citation, no admission.

## Value Statement

The story gains antagonistic structure (kin who object, traders whose interests cut across the truce) without unbounded world-building — the thread deficit list bounds what gets built.

## Problem

The canon has no antagonist role and no social pressure on the ledge romance: Hilde and Gunnar have no named kin who object, and the truce has no economic stakes. World elaboration without a plot skeleton was rejected in planning (plot before world — plan design principle 6); with FR-691's threads in hand, world-building becomes deficit-driven.

## Proposed Solution

Agent graph `examples/novel_fandom/world_pressure.yaml` reusing the FR-658 `create_*` graph-tools (dedup + ref_check gates apply automatically):

- **Kinship trees**: parents/siblings for Hilde, Gunnar, Arnulf; fix the 3 non-reciprocal relationships (reinthilde→hilde/gunnar, berno→gunnar) while touching those files' relationship blocks — additive fields only.
- **Reinmar trade network**: the trader faction's dependencies on both clans; at least one character whose livelihood the truce threatens.
- **Admission rule (mechanical)**: each new entity's YAML carries `pressurizes: [thread_id, …]`; a Python gate rejects entities citing zero threads or nonexistent thread ids.

Canon-grows-never-changes: existing entity files gain fields only where reciprocity repair requires it; `git diff` reviewed for anything beyond additions.

## Acceptance Criteria

- [ ] New entities created via `create_*` tools; all pass dedup + ref_check + admission gate
- [ ] 3 non-reciprocal relationships repaired; diff shows additive-only changes
- [ ] Every new entity cites ≥1 valid thread id; gate test fails on citation-free fixture (RED first)
- [ ] Regenerated threads (FR-691 rerun) show the new entities absorbed as carriers/sources with stable thread ids
- [ ] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **Open-ended world elaboration before plotting** — rejected in plan: generates volume, not pressure; threads must exist first to bound admission.

## Judgement (2026-07-08 — scope frozen)

Authority granted with the mechanical core as the enforced deliverable; the LLM
world-building agent is wiring proven by a **bounded** acceptance run, not an
open-ended brainstorm (`growth_as_default`). Frozen scope:

1. **Schema** — `pressurizes: list[str]` (default empty) added to `Character`,
   `Faction`, `Location`. Optional at the Pydantic layer so pre-existing canon
   keeps validating — mirrors FR-690's `sequence` optionality. The story
   pipeline (not Pydantic) makes citation mandatory for *newly created* entities.
2. **Admission gate** — pure `check_pressure_admission(entities, thread_ids)` in
   `nodes/world_pressure_gates.py`: every candidate entity must have a non-empty
   `pressurizes` **and** every cited id ∈ `thread_ids`. Runs over the pass's
   candidate entities only; pre-existing canon is exempt (no retroactive
   citation). One implementation, two callers (test + graph node).
3. **Reciprocity gate** — pure `check_reciprocity(characters, reciprocal_kinds)`:
   for every `A --kind--> B` with `kind ∈ reciprocal_kinds`, assert a reverse
   edge `B --*--> A` exists (any kind = mutual acknowledgment). FR-scoped
   `reciprocal_kinds = {"mother", "father", "clanmate"}` → surfaces exactly the 3
   known non-reciprocal edges. Broader kind coverage is deferred.
4. **Reciprocity repair** — additive reverse edges only: `hilde.yaml`
   (`daughter → reinthilde`), `gunnar.yaml` (`daughter → reinthilde`,
   `clanmate → berno`). `git diff` must show additions only.
5. **Agent graph** — `examples/novel_fandom/world_pressure.yaml` reusing the
   FR-658 `create_*` graph-tools plus an admission node; lint-clean. Acceptance:
   a bounded set of kin/trade entities (each citing ≥1 valid thread id) admitted
   through `create_*` + admission gate; FR-691 rerun shows absorption.

**Deviations from the plan:** the plan's "entity must appear in carriers/sources
*after* step-1 rerun" absorption rule is a **non-deterministic acceptance
observation**, not a blocking unit gate (it depends on the LLM miner). The
blocking unit gate is citation integrity (non-empty + resolves to a live thread
id). Absorption is verified and documented on the acceptance run.

## Enforcement (2026-07-08 — Enforced)

- **RED** `9f2fcd07` — `pressurizes` schema field + always-valid gate stubs +
  8 condemning fixtures (admission ×6, reciprocity ×2). Schema + valid fixtures
  pass immediately; invalid fixtures RED. CAP-196 registered (REQ-YG-532/533).
- **GREEN** — `check_pressure_admission` + `check_reciprocity` implemented
  (pure functions, `{valid, violations}`), graph adapters `gate_admission` /
  `gate_reciprocity`. The three known non-reciprocal edges repaired additively
  (`hilde → reinthilde`, `gunnar → reinthilde`, `gunnar → berno`); `git diff`
  shows additions only. Agent graph `world_pressure.yaml` + prompt
  `world_pressure_agent.yaml` + `list_threads` loader; graph lints clean.
- **Acceptance:** reciprocity gate green on real canon (4 kinship principals),
  admission gate blocks citation-free / dangling-citation fixtures. 15 FR-692
  tests + 47 ref-integrity/FR-691 tests pass; canon edits break nothing.

**Deviation #1 (IDs):** allocated CAP-196 / REQ-YG-532–533 (next free); the FR
body predates allocation.

**Deviation #2 (LLM canon-mutation run deferred):** `world_pressure.yaml` is
delivered as lint-clean wiring, but the LLM entity-creation run is
**operator-driven**, not auto-run in enforcement. Rationale: it mutates *source*
canon (unlike FR-691's regenerable `story/` artifacts) with non-deterministic
LLM output and warrants human review (blast radius). The deterministic
enforceable core (schema + two gates + reciprocity repair) is the CI-kept
deliverable; the admission gate is applied to the pass's candidate set during
that operator-driven run.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Depends: FR-691; Blocks: FR-693
