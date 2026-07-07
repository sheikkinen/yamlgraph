# Feature Request: FR-692 — World Pressure Agent

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1–2 days
**Requested:** 2026-07-07
**Depends:** FR-691 (threads — the admission rule cites thread ids)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 3 of 7)

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

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Depends: FR-691; Blocks: FR-693
