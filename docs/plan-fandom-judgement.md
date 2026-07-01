# Judgement: Fandom Canon-First Generation Plans

**Date:** 2026-06-30
**Plans judged:**
- [plan-fandom-generation.md](plan-fandom-generation.md) — thesis, prior art, sequencing
- [plan-fandom-architecture.md](plan-fandom-architecture.md) — 8 subsystems, two loops, interface contracts

**Verdict: CONDITIONALLY APPROVED — scope reduction required before authority is granted to any implementing FR.**

---

## What is clear, minimal, and internally consistent

**1. The inversion thesis is sound.** FR-550 proved that deriving a world from plot leaks plot into the world. The canon-first inversion — build the typed graph, then traverse it — is the correct shape. The prior art survey (Chase wiki-memory, Karpathy LLM wiki, Graphiti bi-temporal) validates the direction and adds credibility. This is not invention; it is convergence.

**2. The boundary law is well-stated.** "The LLM authors meaning; deterministic code authors persistence" — clean, testable, and already proven in the ledger work (FR-513–518). Every subsystem is sorted into exactly one column. Good.

**3. The no-leak constraint is the load-bearing wall.** §4 of the generation plan and the S4 gate in the architecture plan correctly identify this as the single invariant that makes canon-first real. The existing `test_no_world_codex.py` is a working prototype. FR-627 formalizes it.

**4. The sequencing is dependency-correct.** Build order (S1+S2 → S4 → S5 → S3 → S6 → S7+S8) respects the "can't gate what you can't write" chain. Steps 1–2 contain no LLM and can land independently.

**5. Acceptance criteria are concrete and testable.** No-leak, static immutability, carry-forward floor, traversal-not-invention — each has a parenthetical test shape.

---

## Contradictions, ambiguities, and excess

**C1. Scope identity crisis — YAMLGraph framework feature or example application?**

The architecture plan maps subsystems to the three-layer law (§3) but describes an 8-subsystem system with its own CRUD layer, index, and reconciliation engine. This is an **application**, not a framework feature. The plans never say this explicitly.

**Resolution required:** State clearly that this is `examples/fandom/` (or `examples/canon_fiction/`), not a framework extension. The only framework FRs are FR-625 (write_data_file) and FR-627 (canon-link gate as a reusable tool). Everything else is example-scoped application code.

**C2. The §9 fork is not resolved — it is deferred.**

Both plans acknowledge the seeding fork (hand-authored vs. LLM-bootstrap) but say "decide before drafting the FR." The architecture plan says "architecture supports both; B is safe only because S4 sits on the freeze boundary." This is correct but insufficient — the first implementing FR *must* declare which option it uses. Without that decision, the authoring pipeline (S5) has two possible shapes.

**Resolution required:** The FR that builds S5 must commit to Option A or B. The plans can stay agnostic; the FR cannot.

**C3. The CRUD granularity question is load-bearing, not open.**

Architecture §8 asks: "is `update_page(delta)` the right unit, or should S8 emit edge-level ops directly?" This is not a minor detail — it determines the shape of S2's interface, S4's gate logic, and S8's output contract. The plan itself leans edge-level ("to match the delta-ledger") but doesn't commit.

**Resolution required:** Commit to edge-level ops in the FR for S2. The ledger discipline (FR-513–518) already uses this granularity. Match it.

**C4. Semantic contradiction detection is correctly deferred but needs a kill switch.**

Architecture §8 correctly keeps semantic contradiction advisory and structural contradiction blocking. But the plan doesn't state what happens when advisory findings accumulate. Per Scripture (`audit_as_ritual`): 3+ audits without fix = ritual.

**Resolution required:** The S4 FR (FR-627) must define a threshold at which advisory semantic contradictions escalate to blocking, or explicitly state they never will (and why).

**C5. Eight subsystems for a first cut is over-engineered.**

The generation plan's §7 sequencing is correct but the architecture plan dresses 8 subsystems with full interface contracts before any code exists. For a first implementable slice, S1+S2+S4 are sufficient to prove the thesis. S3 (index), S5 (tiered authoring), S6 (pathfinder), S7 (prose), S8 (close) are downstream features.

**Resolution required:** The first FR batch should be:
1. FR-625 (write_data_file) — framework prerequisite
2. FR-626 (accumulating-wiki demo) — proves the persistence primitive
3. FR-627 (canon-link gate) — the no-leak invariant
4. A new FR for the typed canon schema (Pydantic models for the 8 page types)

S5–S8 are future FRs. The architecture plan is the north star; the first FRs are the foothold.

---

## Missing pieces

**M1. No cost estimate.** The generation plan lists 6 sequencing steps and the architecture plan lists 8 subsystems. Neither estimates token cost for the LLM steps (S5 authoring, S6 pathfinding, S7 prose, S8 close) or the size of the canon store that must fit in context. For a 200-entity wiki with 8 page types, the context budget matters.

**M2. No example canon.** The plans reference Drizzt and Geralt but don't include even a 3-page sample canon (one character, one location, one faction) to ground the schema discussion. The FR for the typed canon schema should include a concrete example.

**M3. No concurrency model.** If two play-loop iterations run concurrently (or the build loop and play loop overlap), S2's "propose → gate → commit" needs atomicity. The plans assume single-writer. State this explicitly as a constraint.

---

## Ruling

| Item | Decision |
|---|---|
| Generation plan (thesis + prior art) | **Approved** as design north-star |
| Architecture plan (8 subsystems) | **Approved** as north-star; **not** as implementation spec |
| First FR batch | FR-625 → FR-626 → FR-627 → typed canon schema FR |
| Seeding fork (§9) | Deferred to S5 FR; must commit at FR time |
| CRUD granularity | Edge-level ops (match ledger discipline) |
| Semantic contradiction | Advisory only; escalation threshold defined in FR-627 |
| Scope | **Example application**, not framework feature |

Authority to implement is granted to FR-625, FR-626, and FR-627 (which already have their own judgements). The typed canon schema FR must be written and judged before S5–S8 work begins. The architecture plan is the map; the FRs are the territory.
