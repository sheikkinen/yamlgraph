# Fandom Generation — Architecture v2 (Post FR-628/629)

**Status:** North-star for fiction-specific extensions. The generic wiki-memory
pattern is shipped; this document maps what remains if novel generation is
attempted again.

**Predecessor:** [plan-fandom-architecture.md](plan-fandom-architecture.md) (8
subsystems, 3-week estimate). That plan was superseded by FR-628 for the generic
case. This document retains only what is fiction-specific and unshipped.

---

## 1. What is already shipped

FR-625, FR-626, FR-628, FR-629 collectively delivered the generic wiki-memory
pattern. Mapped to the original 8-subsystem architecture:

| Original Subsystem | Shipped As | Asset |
|---|---|---|
| S1 Canon Store | Per-file YAML pages | `wiki/*.yaml` + `data_files` glob (FR-629) |
| S2 Access Layer | `write_data_file` + glob read | FR-625 + FR-629 |
| S4 Integrity Gate | Example-local `ref_gate.py` | FR-628, ~5 lines |
| S5 Authoring Pipeline | LLM `draft` node + gate loop | FR-628 graph |

These are **domain-agnostic**. Any future novel-generation attempt inherits them
as infrastructure — no need to rebuild the store, the write primitive, or the
gate pattern.

---

## 2. What remains (fiction-specific)

Three subsystems from the original plan have no generic equivalent. They exist
only for narrative fiction generation:

### S3 — Index / Retrieval (deferred, not needed yet)

**When it becomes necessary:** when the canon exceeds what fits in a single LLM
context window (~100k tokens). For a wiki under ~200 pages of structured YAML,
glob loads everything into state and the LLM receives the full dict. No retrieval
needed.

**Trigger:** if a future novel attempt hits context limits, build a bounded
retrieval tool (top-K by relevance over the wiki). Use ChromaDB or SQLite FTS5.
The interface is `search(query, k) → list[id]`; caller re-reads full pages from
state. The index is a cache — deletable and rebuildable.

**Estimated effort if triggered:** 0.5–1 day.

### S6 — Plot Pathfinder (the fiction-specific generative step)

**What it does:** given a timeline window + character roster, search for a
storyline that moves existing tensions toward resolution. Every beat must
reference only canon entities (gated).

**Why it's not generic:** the concept of "tension," "resolution," "character
goals," and "story arcs" is narrative-domain vocabulary. A tech-radar wiki
doesn't have plot paths.

**Shape (YAML graph):**

```yaml
nodes:
  retrieve_context:
    type: python
    tool: retrieve_window    # Read roster + open tensions from wiki
    state_key: context

  find_path:
    type: llm
    prompt: find_plot_path   # Propose beat sequence over fixed tensions
    state_key: plot_path

  gate_path:
    type: python
    tool: ref_gate           # Every beat reference must resolve to canon
    state_key: gate_result

edges:
  - from: START
    to: retrieve_context
  - from: retrieve_context
    to: find_path
  - from: find_path
    to: gate_path
  - from: gate_path
    to: END
```

**Prerequisites:**
- Canon must contain characters with goals, relationships with valence, and a
  timeline with windows. This means the wiki page schema must be richer than
  FR-628's flat `{id, type, references, summary}`.
- A `retrieve_window` tool that filters wiki pages by timeline + roster.

**Estimated effort:** 1–2 days (graph + prompt + retrieval tool).

### S7+S8 — Prose Generation + Close (the play loop)

**What they do together:**
1. S7 takes an approved plot path → drafts chapter prose (map over beats,
   grounded in retrieved canon context).
2. S8 extracts what *happened* in the prose → writes delta-ops back into the
   dynamic wiki (new events, relationship changes).

**Why they're paired:** S7's output is S8's input. They form a single pipeline
stage: `draft → extract_consequences → persist_deltas`.

**Shape:**

```yaml
# The play loop (one iteration per story window)
nodes:
  draft_chapters:
    type: map              # Fan out over beats
    prompt: draft_chapter
    state_key: chapters

  gate_prose:
    type: python
    tool: ref_gate         # No leaked entities in prose
    state_key: prose_gate

  extract_deltas:
    type: llm
    prompt: extract_consequences  # What changed? New events, relationship shifts
    state_key: deltas

  persist_deltas:
    type: python
    tool: apply_deltas     # Write delta-ops to wiki/dynamic/
    state_key: _written
```

**The carry-forward floor:** if `extract_deltas` returns zero ops, the existing
dynamic wiki is left intact. It cannot spontaneously empty.

**The bi-temporal rule:** a contradicting fact *invalidates* the old entry
(sets `valid_to` in front-matter), never deletes it. History is append-only.

**Prerequisites:**
- S6 (plot path) must be working — S7 consumes its output.
- Wiki schema must support `valid_from` / `valid_to` on dynamic pages.
- The `apply_deltas` tool must enforce the carry-forward floor.

**Estimated effort:** 2–3 days (two graphs + prompts + delta tool).

---

## 3. The enriched wiki schema (prerequisite for S6/S7/S8)

FR-628's wiki pages are flat: `{id, type, references, summary}`. Fiction needs
richer pages. The minimum extension:

```yaml
# wiki/characters/kaelen.yaml
type: character
id: kaelen
name: Kaelen
goals:
  - "Find dragonsteel to reforge his blade"
  - "Avenge the Ashfall destruction"
personality: disciplined, stoic, grudge-bearing
faction: ashguard
relationships:
  - {to: maren, kind: mentor, valence: trust}
  - {to: voss, kind: rival, valence: enmity}
references: [ashguard, maren, voss, dragonsteel]
timeline_entry: age_of_cinders
```

```yaml
# wiki/events/ashfall.yaml
type: event
id: ashfall
window: age_of_cinders
participants: [kaelen]
consequences:
  - "Kaelen lost his forge"
  - "Ashguard faction scattered"
valid_from: "2026-07-01"
valid_to: null              # Still canonical
references: [kaelen, ashguard]
```

**The gate still works unchanged** — it checks `references` resolve. The richer
fields (goals, relationships, valence, timeline) are consumed by the pathfinder
prompt, not by the gate.

---

## 4. Build sequencing (if fiction is attempted)

```
[SHIPPED] FR-628 wiki-memory demo (generic gate pattern)
    │
    ▼
[1 day] Enriched wiki schema + seed canon (3 characters, 2 factions, 1 timeline)
    │
    ▼
[1-2 days] S6 Plot Pathfinder graph + retrieve_window tool
    │
    ▼
[2-3 days] S7+S8 Prose + Close loop + apply_deltas tool
    │
    ▼
[0.5 day] S3 Index (only if canon exceeds context window)
```

**Total: 4.5–6.5 days** (down from the original 3-week estimate, because S1, S2,
S4 are shipped and the infrastructure patterns are proven).

---

## 5. Decision points (decide before starting)

### A. Seeding the canon

Same fork as the original plan §9:
- **Option A:** Hand-author the seed canon (purest; zero leak risk).
- **Option B:** LLM-bootstrap each tier, gate at freeze boundary (faster setup,
  but requires disciplined freeze).

FR-628 proved Option B works at small scale (the LLM drafts pages, the gate
catches bad references). For a novel-scale canon (50+ entities), Option B with
the gate is the practical choice.

### B. Single wiki dir vs. static/dynamic split

The original plan proposed `canon/static/` (immutable) and `canon/dynamic/`
(delta-mutated). FR-628 uses a single flat `wiki/` directory.

For fiction, the split matters: static canon (geography, deities, races) should
never change mid-story; dynamic canon (events, relationship valence) changes
every chapter close. The split is enforced by the gate: writes to
`wiki/static/**` are rejected.

**Recommendation:** Add a `lane: static|dynamic` field to the page schema. The
gate checks it — `lane: static` pages cannot be updated after initial creation.
Simpler than directory-based enforcement; works with a single glob pattern.

### C. How big before you need an index?

Back-of-envelope: 200 pages × ~500 tokens/page = 100k tokens. That fits in
Claude/Gemini context. If the wiki stays under 200 pages, **skip S3 entirely**.
Most novel-length fiction wikis (20–50 characters, 10–20 locations, 30+ events)
fit comfortably.

---

## 6. Prior art (novel-generation attempts in this repo)

| Asset | What it proved | What failed |
|---|---|---|
| `examples/dungeon_master/` (9 graphs) | Chapter-by-chapter generation with turn loops, character rosters, forward-carry state | FR-550: world derived from plot leaked plot into world |
| `examples/plot_modeller/` (13 graphs) | Affect classification, salience gates, goal/personality vocabulary | Self-report gate graded author's own claims, not the prose |
| `roundtrip_skeleton.yaml` | End-to-end premise→outline→draft pipeline | Top-down derivation; the inversion this plan corrects |
| FR-628 `wiki-memory/` | Gated accumulation loop, per-file pages, reference integrity | Generic domain; no fiction-specific vocabulary |

The next attempt inherits: gated writes (FR-628), per-file discovery (FR-629),
the boundary law (LLM authors meaning, code persists), and the no-leak gate.
It does not need to re-prove any of those.

---

## 7. Related

- [plan-fandom-generation.md](plan-fandom-generation.md) — the thesis (canon-first inversion).
- [plan-fandom-architecture.md](plan-fandom-architecture.md) — the original 8-subsystem design (superseded for generic case).
- [plan-fandom-judgement.md](plan-fandom-judgement.md) — the ruling that led to scope reduction.
- [FR-628](../feature-requests/FR-628-wiki-memory-gated-demo.md) — the shipped generic pattern.
- [FR-629](../feature-requests/FR-629-data-files-glob-support.md) — glob support enabling per-file wikis.
- [plan-ledger-memory.md](plan-ledger-memory.md) — the dynamic-canon mutation model (carry-forward, bi-temporal).

---

## 8. Judgement (2026-07-01)

**Verdict: APPROVED as north-star. No authority to implement — this is a shelf
document, not a work order.**

### Notes for the next implementer

1. **The `lane: static|dynamic` gate extension (§5B):** the existing `ref_gate.py`
   only checks `references` resolve. Static-lane enforcement requires a one-line
   addition: `if page.lane == "static" and page already exists → reject`. The FR
   that builds S6 must specify this gate extension.

2. **Prose quality is out of scope.** This plan gates structural integrity
   (no-leak, no-orphan), not narrative quality. The plot_modeller proved that
   self-report metrics fail. Quality evaluation (if needed) is a separate FR.

3. **Context window estimate (§5C) assumes structured YAML only.** If pages
   include long prose bodies (history sections, relationship descriptions), the
   200-page threshold drops to ~50–80 pages. Whoever hits the limit will know —
   the plan already says "skip S3 until you hit it."

### Activation trigger

Someone creates an FR for S6 (pathfinder) or the enriched wiki schema. Until
then, this plan sits on the shelf.
