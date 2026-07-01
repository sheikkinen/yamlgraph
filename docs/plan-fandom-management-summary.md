# Fandom Canon-First Generation — Management Summary

**Audience:** decision-makers / reviewers. One-page status of the fandom
(canon-first) generation initiative. Detail lives in the four linked plans.

---

## The idea in one line

Instead of generating a story from a premise (which leaks plot-invented facts
into the "world"), **build the world first as a typed, cross-linked wiki, then
generate stories by traversing it** — with a cheap deterministic check that blocks
any story from referencing something not in the wiki.

## Why it matters

A prior failure ([FR-550](../feature-requests/FR-550-dm-v2-rollback-world-codex.md))
proved that worlds derived *from* plot are incoherent. This inverts the
dependency: canon is authored/grounded first, plotting becomes a *search* over
fixed facts, and coherence is *checked against ground truth* rather than trusted
from the model's own self-report. The design converged independently with public
2026 prior art (Chase *Wiki Memory*, Karpathy *LLM Wiki*, Graphiti).

## Status: the hard part is already shipped

The generic "self-maintaining wiki" machinery is **built and proven**
(FR-625/626/628/629):

| Capability | State |
|---|---|
| Write canon back to disk (`write_data_file`) | ✅ shipped |
| Load whole wiki (glob `data_files`) | ✅ shipped |
| **Gated accumulation loop** (propose → verify refs → fix → persist) | ✅ shipped, working demo |
| Deterministic no-orphan gate (`ref_gate.py`) | ✅ shipped (~30 lines) |

Building it also flushed out and fixed three framework bugs (FR-630/631/632).
**Canon-first is no longer greenfield — it is a scale-up of a working kernel**
([examples/demos/wiki-memory/](../examples/demos/wiki-memory/)).

## What remains (fiction-specific only)

Per the scope-down ([plan-fandom-architecture-2.md](plan-fandom-architecture-2.md)),
~**4.5–6.5 days**, down from an original 3-week estimate — now planned as FRs:

| Phase | Work | FR | Est. |
|---|---|---|---|
| 1 | Enriched canon schema + hand-authored seed + example scaffold | [FR-637](../feature-requests/FR-637-novel-fandom-canon-schema-seed.md) | ~1 day |
| 2 | Plot pathfinder graph + `retrieve_window` tool | [FR-638](../feature-requests/FR-638-novel-fandom-plot-pathfinder.md) | ~1–2 days |
| 3 | Prose + close loop + `apply_deltas` (bi-temporal) | [FR-639](../feature-requests/FR-639-novel-fandom-prose-close-loop.md) | ~2–3 days |
| (4) | Search index — **only if** canon exceeds context window (~200 pages) | deferred | ~0.5 day |

## Governing decisions (locked by the judgement)

- **Scope:** an **example application** (`examples/novel_fandom/`), not a framework
  feature. Only the write tool + the gate are framework-level.
- **Committed choices:** edge-level deltas (match the ledger), a
  `lane: static|dynamic` field for immutability, single-writer concurrency,
  semantic-contradiction checks advisory (structural blocking).
- **Seeding fork resolved for Phase 1:** the seed canon is **hand-authored**
  (Option A — zero leak risk at small scale). LLM-bootstrap-then-freeze (Option B)
  is a later enhancement, viable only with the gate on the freeze boundary.

## The one load-bearing principle

**"The LLM authors meaning; deterministic code authors persistence."** Every
subsystem sits on one side of that line. The gate is what makes a
non-deterministic author safe to build on — fluent-but-wrong output cannot persist.

## Risk posture

**Low.** The expensive infrastructure is done and proven; remaining work is
well-scoped, incrementally testable (each phase a separate FR with a RED test),
and mostly YAML. The biggest open cost question (M1: does a novel-scale canon fit
in context?) is bounded by the Phase-4 index escape hatch.

## Document map

- [plan-fandom-generation.md](plan-fandom-generation.md) — **why** (thesis, prior art, tooling)
- [plan-fandom-architecture.md](plan-fandom-architecture.md) — full 8-subsystem design
- [plan-fandom-architecture-2.md](plan-fandom-architecture-2.md) — **what's left** after the kernel shipped (current implementation map)
- [plan-fandom-judgement.md](plan-fandom-judgement.md) — the binding decisions (C1–C5, M1–M3)
- **this file** — one-page management view
