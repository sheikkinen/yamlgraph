# The architecture was already paid for

**Date:** 2026-06-30
**Arc:** canon-first ("fandom") generation — prior-art grounding, FR-627 gate, full system architecture
**Artifacts:** docs/plan-fandom-generation.md (§10–§12), feature-requests/FR-627-canon-link-gate.md, docs/plan-fandom-architecture.md

## What happened

A research → synthesis → authoring arc. Grounded the canon-first design in external
prior art (Chase *Wiki Memory*, Karpathy *LLM Wiki*, Graphiti), distilled the
Karpathy/Graphiti **commit-gate pattern** into [FR-627](../../feature-requests/FR-627-canon-link-gate.md)
(the deterministic no-orphan / no-leak gate generalizing FR-550), then envisioned the
whole system as 8 subsystems across three planes
([plan-fandom-architecture.md](plan-fandom-architecture.md)).

Two things surprised me when I went looking outward.

- **Graphiti had shipped what we specced.** Bi-temporal validity windows, fact
  *invalidation not deletion*, prescribed-vs-learned ontology — we wrote that
  independently as [FR-515](../../feature-requests/FR-515-dm-v2-bitemporal-ledger-reconciliation.md)
  before I'd ever read the Graphiti README.
- **The ecosystem named our open fork.** Seeded-ontology *strict vs emergent* is
  exactly the §9 author-by-hand-vs-LLM-bootstrap fork. The wild had a vocabulary for
  the choice we'd framed as undecided.

## The trap

**`architecture_as_invention`.** When the user said "envision the architecture," the
default pull is continuation_bias wearing an architect's hat: generate plausible boxes
and arrows. Plausible structure is cheap and *feels* like design. An 8-subsystem
diagram looks authoritative whether or not any box is load-bearing.

What kept it honest was a constraint I almost didn't impose: **every subsystem had to
map to an existing asset or FR, or it didn't get to exist.** S2 CRUD → FR-625. S4 gate
→ FR-627. S5 tiers → FR-552/626. S8 reconcile → FR-515. The one box with no anchor
(S3 index) is flagged "not built." The architecture is not invention; it is a
*recombination of constraints already paid for* — paid for in prior FRs, prior
incidents (FR-550's leak), and the three-layer import law. Invented architecture has
boxes that trace to imagination; earned architecture has boxes that trace to a receipt.

The near-miss underneath: **`prior_art_as_authority`**. The convergence with Graphiti/
Karpathy is so clean it tempts you to import their defaults wholesale — Karpathy's
*untyped* wikilinks, the ecosystem's *advisory* lint. But the plan's entire value is
where it *diverges*: a **typed** graph (answers Chase's "best format?" open question)
and a **blocking** gate (answers "drift is the dominant failure mode"). Convergence
validates the direction; it must not dictate the choices.

## The cure that generalized

The strongest move in the architecture wasn't the gate — it was making the no-leak law
**structural** instead of only procedural. S5 authoring builds canon bottom-up in
topological tiers (skeleton → structures → agents → relations), so a character
*cannot* name a faction that doesn't exist yet: the no-orphan invariant is enforced by
**build order**, not just by a runtime check. That is `normalize at the boundary`
applied to authoring — make the violation unrepresentable in the construction sequence,
don't just catch it downstream. The gate becomes the backstop, not the sole defense.

## The heuristic

> Earned architecture traces every box to a receipt — an existing asset, a prior FR, a
> paid-for incident — and flags the boxes that don't. Independent convergence with
> external prior art is the strongest signal the *direction* is right and the weakest
> license to import the *choices*: keep what you'd have built anyway, diverge exactly
> where your constraints are sharper (typed over untyped, blocking over advisory).

## Seed

If Graphiti already shipped our FR-515 reconcile and the ecosystem already names our
§9 fork — when does *adopting a library* beat *building the subsystem*? S3 (index) and
S2 (CRUD) are the two boxes with the least YAMLGraph-specific content and the most
mature external options (Graphiti, ChromaDB, Mem0). What is the test that decides
"this subsystem is commodity — import it" vs "this is our boundary — own it"? Candidate:
own the subsystems that touch the no-leak gate (the typed seam is ours); rent the ones
that are pure retrieval mechanics. Is incident-density the right ruler for that call too?
