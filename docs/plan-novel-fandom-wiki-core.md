# Plan: Novel Fandom Wiki Core — Premise-Driven Canon Bootstrap

**Date:** 2026-07-01
**Context:** FR-641 (rejected), dungeon_master synopsis pipeline, floodmark fixtures

## Problem

The novel_fandom canon has 8 hand-authored seed pages. FR-641 proposed LLM-bootstrap
but was rejected for three reasons: single-pass extraction unproven, freeze governance
undefined, graph shape bypasses the gated-accumulation pattern. This document explores
how to integrate dungeon_master's proven premise→synopsis→roster→outline pipeline into
the wiki model, and charts the path forward.

---

## 1. What Dungeon Master Already Solved

The DM pipeline has a **layered generation** process, each layer producing one concern:

```
premise (1 paragraph, e.g. floodmark-saga.txt)
  → synopsis.yaml      # LLM: full-disclosure reveal-all prose (no structure)
  → character_roster    # LLM: 2-4 principal names (one per line)
  → character.yaml ×N   # LLM: one character sheet per name (prose, not structured)
  → chapter_outline     # LLM: {title, summary}[] — structured JSON (parse_json: true)
  → plot_plan.yaml      # LLM: typed PlotPlan + 4 invariant checks + repair loop
```

**Key properties:**
- Each step produces ONE concern (synopsis, names, one character, chapter splits, plan)
- Each step is a separate graph invocation — the session orchestrates sequentially
- The character step runs N times (once per name in roster) — embarrassingly parallel
- The plot_plan has a **gated repair loop** (author → validate → repair → validate)
- Output grows in structure: prose → names → prose-per-entity → JSON → typed Pydantic

**Floodmark** is not a pipeline — it's a typed test fixture (`PlotPlan` literal in Python)
with 6 falsification variants, used to validate the 4 narrative invariants independently
of any LLM. It proves the invariant checks work before an LLM ever touches them.

---

## 2. What Novel Fandom Has Today

```
canon/ (8 static YAML pages: 3 characters, 2 factions, 1 event, 2 rules)
  ↓ data_files glob
graph.yaml       — editor: draft(llm) → gate → fix → persist (one page at a time)
find_path.yaml   — pathfinder: retrieve_context(det.) → find_path(llm) → gate → fix
draft.yaml       — prose: map(beats→chapters) → extract_mentions → prose_gate
close.yaml       — close: extract_deltas(llm) → apply_deltas(det.)
```

**What's missing from the wiki model:**
- No **Synopsis** layer — the premise/synopsis lives outside the canon
- No **Chapter structure** — `draft.yaml` maps beats to chapters but the outline
  isn't persisted in the wiki
- No **PlotPlan** equivalent — the pathfinder finds dramatic paths but doesn't
  formalize them as typed, validatable plans
- No **bootstrap pipeline** — one-page-at-a-time editor can't populate from scratch

---

## 3. Extending the Wiki Model

### 3a. New page types to add to `schema/canon.py`

| Type | Purpose | Key Fields |
|------|---------|-----------|
| **Premise** | The seed of everything — a paragraph of thematic intent | `text`, `genre_tags`, `era`, `themes` |
| **Synopsis** | Full-disclosure reveal-all prose (DM-style) | `text`, `version` (iterative rewrites) |


**Design choice:** These are wiki pages like everything else — same `id`, `type`,
`lane`, `references` contract. The synopsis references the premise. Each chapter
outline references the synopsis and the characters it features. The existing gates
enforce referential integrity automatically.

### 3b. How the layers relate

```
Premise (1 page, lane: static)
  └→ Synopsis (1 page, lane: dynamic → frozen to static after review)
       ├→ Character ×N (each references synopsis)
       ├→ Faction ×M
       ├→ Location ×K
       ├→ Rule ×J
       └→ Event ×E (each references synopsis + participants)
```

This is a **tree of provenance** — every page traces back to the premise through
references. The existing `ref_gate` checks this automatically.

---

## 4. Bootstrap Pipeline — Three Alternatives

### Alternative A: Session-Orchestrated (DM Pattern)

Run separate graph invocations sequentially, as dungeon_master does:

```
1. synopsis.yaml        — premise → synopsis (human reviews, iterates)
2. character_roster.yaml — synopsis → list of names
3. character.yaml ×N     — per-name: synopsis + name → Character page → gate → fix
4. world_extract.yaml    — synopsis → Factions + Locations + Rules → gate → fix (per page)
5. chapter_outline.yaml  — synopsis → ChapterOutline[] → gate → fix
```

**Pro:** Proven pattern (DM does this). Each graph is simple. Human steers at each step.
**Con:** Requires a session orchestrator (DM has `session.py`). Novel_fandom has no session layer.

### Alternative B: Gated Accumulation Pipeline (Single Graph)

One graph with sequential extraction, each entity going through gate → fix:

```yaml
# bootstrap.yaml
nodes:
  gen_synopsis:     type: llm    # premise → synopsis
  extract_roster:   type: llm    # synopsis → character names (structured)
  gen_characters:   type: map    # per-name → Character page
  gate_characters:  type: python # ref_gate on each
  fix_characters:   type: llm    # repair orphan refs
  extract_world:    type: llm    # synopsis → factions, locations, rules
  gate_world:       type: python
  fix_world:        type: llm
  gen_outline:      type: llm    # synopsis + cast → chapter outlines
  gate_outline:     type: python
  fix_outline:      type: llm
  persist:          type: python # write all validated pages

edges:
  START → gen_synopsis → extract_roster → gen_characters → gate_characters
  gate_characters → extract_world (valid) | fix_characters → gate_characters (invalid)
  extract_world → gate_world → gen_outline (valid) | fix_world → gate_world (invalid)
  gen_outline → gate_outline → persist (valid) | fix_outline → gate_outline (invalid)
```

**Pro:** One graph, one invocation. Gated accumulation pattern (matches FR-637/638/639).
Every page goes through gate → fix. No session layer needed.
**Con:** Large graph. Factions/locations/rules still extracted in one batch call (need to
decide: one-by-one or batch-then-validate-each?).

### Alternative C: Layered Subgraphs (Hybrid)

Compose smaller graphs as subgraphs within a parent:

```yaml
# bootstrap.yaml
nodes:
  synopsis:     type: subgraph, graph: synopsis.yaml
  roster:       type: subgraph, graph: extract_roster.yaml
  characters:   type: subgraph, graph: gen_character.yaml  # map inside
  world:        type: subgraph, graph: extract_world.yaml   # gated
  outline:      type: subgraph, graph: gen_outline.yaml     # gated

edges: START → synopsis → roster → characters → world → outline → END
```

**Pro:** Each subgraph is independently testable. Parent graph is a clean pipeline.
Matches DM's "separate graphs" without needing a session orchestrator.
**Con:** Requires YAMLGraph's subgraph support to pass state between layers cleanly.
More files to maintain.

---

## 5. The Batch-vs-Iterate Question (FR-641's Core Flaw)

FR-641 proposed extracting ALL entities in one LLM call. The dungeon_master solved
this differently:

| DM Approach | Novel Fandom Equivalent |
|-------------|------------------------|
| Roster: extract names only (trivial, no cross-refs) | Extract entity names + types from synopsis |
| Character: one graph per name, run N times | One page per invocation, through gate → fix |
| Chapter outline: one structured call (parse_json) | One structured call for outlines, then validate each |

**The insight:** Don't extract full entities in batch. Extract **names and types** in
batch (cheap, low cross-ref risk), then generate **full pages one at a time** through
the gated loop. This is exactly how DM does characters.

**Proposed sequence:**
1. Synopsis → extract entity manifest: `[{id: "kaelen", type: "character"}, {id: "ashguard", type: "faction"}, ...]`
2. For each entry in manifest: synopsis + name + type → full page → gate → fix → persist
3. Synopsis + validated cast → chapter outlines → gate → persist

Step 2 is a map node with the existing gate → fix loop inside. No single-pass extraction.
No orphan-reference problem. Each page sees all previously-persisted pages in the canon
(carry-forward).

---

## 6. Freeze Governance — Three Options

| Option | Mechanism | When |
|--------|-----------|------|
| **Manual freeze** | CLI command: `--var freeze=kaelen` promotes `dynamic → static` | Human reviews and decides |
| **Auto-freeze after N pipeline runs** | Count successful pathfind→draft→close cycles without gate violations | Measurable: N=3 means the page survived 3 story arcs |
| **LLM judge freeze** | A judge prompt evaluates: "Is this page consistent with the static canon?" | Requires a judge prompt + criteria |

**Recommendation:** Start with manual freeze (simplest, proven by DM's accept/reject flow).
Auto-freeze is a future FR once the pipeline runs end-to-end.

---

## 7. Comparison to DM's PlotPlan

The DM's v3 `PlotPlan` is a formal narrative contract: typed beats with pre/post conditions,
world-truth atoms, belief tracking, affect closure. The novel_fandom's `find_path.yaml`
produces informal beats (`{actors, references, tension, resolution}`).

**Gap:** Novel fandom has no formal narrative invariants — the path_gate only checks
that references resolve to canon, not that the plot is structurally sound.

**Future direction (not this FR):** A `FandomPlotPlan` model with:
- Beat ordering constraints (A must precede B)
- Character arc progression (wants → needs → resolution)
- Tension lifecycle (opened → escalated → resolved, no orphan tensions)

This would be the novel_fandom equivalent of DM's 4-invariant validator. But it
belongs in a later FR after the bootstrap pipeline proves the wiki model works.

---

## 8. Recommended Path Forward

### Phase 1: Wiki Core Extension (new FR)
- Add `Premise`, `Synopsis` page types to `schema/canon.py`
- Existing gates work automatically (same `references` contract)
- No new graphs yet — just the model extension + tests

### Phase 2: Bootstrap Pipeline (new FR, depends on Phase 1)
- **Alternative B** (single graph, gated accumulation):
  - `gen_synopsis` → `extract_manifest` → `map(gen_page → gate → fix)` → `persist`
- Manifest extraction: names + types + one-sentence description
- Each page generated independently from synopsis alone (DM pattern)
- Full page generation one-at-a-time through existing gate → fix loop
- Manual freeze via CLI flag

### Phase 3: Wiki Linter (new FR, depends on Phase 2)
- Post-bootstrap cross-page consistency checks:
  - Duplicate entity names across pages
  - Unreferenced pages (islands in the reference graph)
  - Relationship symmetry (if A→B rival, does B reference A?)
  - Faction membership consistency (character.faction ∈ canon factions)
  - Event participant resolution (all participants are known characters)
- Deterministic Python node — no LLM, runs the full canon as input
- Reports violations; a separate fix graph can repair them through gate → fix

### Phase 4: End-to-End Pipeline Run (FR-641 resubmission prereq)
- Run: premise → bootstrap → lint → pathfind → draft → close
- Validates the entire pipeline including the new page types
- Proves the bootstrap produces a canon the downstream graphs can consume

### Phase 5: Formal Narrative Invariants (future)
- Typed `FandomPlotPlan` model (inspired by DM's `PlotPlan`)
- Beat ordering + character arc + tension lifecycle checks
- Gated repair loop (like DM's `plot_plan.yaml`)

---

## 9. What This Means for FR-641

FR-641 should be **rewritten**, not patched. The rewrite would:

1. **Drop single-pass extraction** → use manifest + per-page generation
2. **Add Synopsis and ChapterOutline** to the wiki model (FR-641 didn't have these)
3. **Use gated accumulation** (Alternative B) → matches the established pattern
4. **Start with manual freeze** → governance is defined and simple
5. **Split into Phase 1 + Phase 2** → smaller, judgeable FRs

The current FR-641 is a straight pipeline (`premise → extract → write`). The replacement
is a layered, gated pipeline (`premise → synopsis → manifest → map(gen → gate → fix) → outline → gate → fix → persist`).

---

## 10. Open Questions — Resolved

1. **Should synopsis be iterative?** **No.** Accept the first draft. No interrupt
   support needed. Keeps the bootstrap pipeline simple and automatable.

2. **Manifest granularity:** **Names + types + one-sentence description.** The
   one-sentence description gives the per-page generator enough context without
   cross-entity inconsistency risk (it's a single sentence, not a full schema).

3. **Canon carry-forward during bootstrap:** **No carry-forward.** Each page is
   generated independently from the synopsis alone (DM pattern). Cross-page
   inconsistencies (orphan refs, mismatched names) are caught by a **wiki linter**
   that runs post-bootstrap and reports all issues. The existing `ref_gate` catches
   orphan references; a wiki linter adds: duplicate names, unreferenced pages,
   relationship symmetry (if A→B exists, does B→A?), faction membership consistency.

4. **Chapter outline → pathfinder bridge:** **Postponed.** Drop `ChapterOutline`
   from the wiki model for now. Keep the existing Event type + pathfinder concept.
   The pathfinder already traverses canon tensions to find dramatic paths — that's
   sufficient. Chapter structure is a future concern if/when the pipeline needs
   longer-form output.
