# Plan: The World Ledger as an Agent Memory System

**Status:** Design north-star (not yet an FR). Distilled from the FR-513 enforcement,
the run 10020-BC review, and a survey of LLM memory architectures.
**Scope:** `examples/dungeon_master/` forward-carry `world_state` ledger.

---

## 1. Why this document exists

Each chapter of a DM v2 story is played in its own turn loop, in its own LLM
context window. Nothing about chapter *N*'s text is automatically visible to
chapter *N+1*. The only thread between chapters is the **forward-carry ledger**:
the typed `world_state` a chapter closes with and the next chapter starts from
([world_state.py](../examples/dungeon_master/api/world_state.py)).

That ledger *is* an agent memory store — it just was not designed as one. FR-499
gave it typed lanes (characters, objects, facts); FR-513 added the emotional lane
(relationships) with a grounding gate. Run 10020-BC then proved both the value
(emotional state persisted Ch3→Ch4, the reset that broke 10019 did not recur) and
the limits (a chapter silently zeroed its relationships; a bond's *type* lagged
the prose by four chapters).

This document states how the ledger **should** work if we treat it explicitly as
memory, borrowing the operations that mature memory systems are built around.

---

## 2. What the research says memory is

Four reference architectures, and the operation each contributes:

| System | Core idea | Operation it pioneered |
|---|---|---|
| **Generative Agents** (Park 2023, arXiv:2304.03442) | A *memory stream* of observations; retrieval scores each memory by **recency × importance × relevance**; periodic **reflection** synthesizes raw memories into higher-level insights | Salience-ranked retrieval + reflection |
| **MemGPT** (Packer 2023, arXiv:2310.08560) | OS-style **tiered memory** — in-context (fast) vs external (slow) with paging/eviction; the model self-edits memory via function calls | Tiering + eviction |
| **A-MEM** (Xu 2025, arXiv:2502.12110) | Zettelkasten notes; a new memory **links** to related ones and triggers **memory evolution** — adding a memory updates the attributes of existing memories | Delta-update of prior memories |
| **Zep / Graphiti** (Rasmussen 2025, arXiv:2501.13956) | **Bi-temporal knowledge graph**: every edge carries valid-from / valid-to; a contradicting new fact **invalidates** the old one rather than overwriting it | Temporal conflict resolution |

The shared cognitive frame: memory is **encode → store → retrieve → consolidate →
forget → reconcile**. The first two are easy. The systems that work are defined by
the last four.

**The one finding that reorganizes everything:**

> Every system above uses **update-delta** semantics — append, invalidate, evolve,
> page. **None** asks the model to re-emit the entire store each step. Our ledger
> uses **regenerate** semantics: `chapter_close.yaml` asks the LLM to rewrite the
> whole ledger every chapter. A single forgetful chapter therefore resets state.

Both 10020 defects are symptoms of this one mismatch.

---

## 3. The ledger today, scored as memory

| Memory operation | Ledger today | Verdict |
|---|---|---|
| **Encode** (write) | LLM writes at chapter close, grounded in recaps (`recap_citations`) | ✅ present (write-at-boundary, FR-513) |
| **Store** | typed `dict` on the chapter card | ✅ present (FR-499) |
| **Retrieve** | full carry-forward; `active`-only filter for turn context (`format_world_state(..., relationships="active")`) | ⚠️ no ranking — injects *all* active, not *relevant* |
| **Forget / decay** | `status: active / dormant / archived` | ⚠️ exists but is LLM-judged, not mechanical |
| **Consolidate / reflect** | — | ❌ absent (Ch8 carried Hilde&Arnulf as both `hierarchy` *and* `alliance`) |
| **Reconcile / invalidate** | LLM silently replaces on rewrite | ❌ absent (`enmity → romantic_bond` arrived 4 chapters late) |

The grounding gate FR-513 added is the **encode** guard. To act like memory, the
ledger needs the **reconcile** and **retrieve** guards too.

---

## 4. The target design

A single principle, applied at the chapter seam (the boundary where one chapter's
state becomes the next's):

> **The close emits a *diff* against carried state, deterministic code applies it,
> and carry-forward is the floor. The store is never regenerated from scratch.**

### 4.1 Encode — delta, not regenerate (Zep + A-MEM)

The chapter-close LLM stops emitting a fresh full ledger. It emits **operations**
against the inherited ledger:

```yaml
operations:
  - op: add            # a bond/fact/object the recaps newly establish
  - op: reaffirm       # still true this chapter (resets decay clock)
  - op: update         # a field changed (status, type, tensions, location)
  - op: invalidate     # conclusively ended (death, rupture, alliance broke)
```

Every op still carries `recap_citations` — the FR-513 grounding gate stays, now
applied per-operation. Deterministic code in `world_state.py` applies the diff to
the inherited ledger and persists the result.

**Why this is load-bearing:** "no operations" now means "carry forward unchanged,"
never "empty." The Ch5 zero-dropout becomes impossible by construction. This is
the single highest-leverage change.

### 4.2 Reconcile — bi-temporal invalidation (Zep / Graphiti)

When an `update` or `invalidate` op contradicts an existing edge, code does not
delete the old fact — it **closes** it with a marker and opens the new one:

```python
# conceptual — an edge gains a lifespan, not a silent overwrite
{"between": ["Hilde", "Gunnar"], "type": "enmity",
 "valid_from": "Ch1", "valid_to": "Ch2"}        # invalidated, kept for history
{"between": ["Hilde", "Gunnar"], "type": "romantic_bond",
 "valid_from": "Ch2", "valid_to": null}          # current
```

Turn context reads only currently-valid edges (`valid_to is null`). History stays
queryable for the close LLM and the book reviewer. **This is what kills the
type-lag**: a contradiction forces an explicit invalidate, rather than waiting for
the model to happen to overwrite the stale edge.

### 4.3 Forget — mechanical decay with a persistence floor (Generative Agents)

Status must not be only LLM-judged:

- **Decay (code):** an edge not `reaffirm`-ed for *N* chapters is demoted
  `active → dormant` automatically. Mechanical recency, not the model's memory of
  what it last mentioned.
- **Revival (LLM):** the close may `reaffirm` a dormant edge back to active when
  the recaps bring it back. LLM proposes, code disposes — the same boundary split
  FR-513 already uses for grounding.
- **Floor (code):** the inherited active set is the minimum; a silent close can
  never shrink it below carry-forward.

### 4.4 Retrieve — ranked top-K, not the whole set (Generative Agents + MemGPT)

Turn-1 currently injects *all* active relationships. It should inject the **top-K
relevant to this turn's cast**:

- **relevance:** is a party of this edge on stage this turn?
- **importance:** tension count, or an LLM-scored salience.
- **recency:** how recently `reaffirm`-ed.

This is the paging discipline MemGPT exists to enforce: a 40-chapter story must not
drag 30 bonds into every turn. Bounded context, ranked by salience.

### 4.5 Consolidate — reflection / evolution (A-MEM)

A periodic pass merges redundant edges (the duplicate `hierarchy` + `alliance`
Hilde&Arnulf rows) and can synthesize higher-order facts ("the Aschenwulf line now
defers to Reinmar's route authority"). Valuable but **second-order** — a cleanup
pass, not a correctness fix. Sequence it last.

---

## 5. The boundary discipline (why each guard lives where it does)

The ledger already obeys "normalize at the boundary." The memory upgrade extends
the same doctrine to the operations the boundary lacks:

| Guard | Owner | Rationale |
|---|---|---|
| Grounding (drop ungrounded op) | code (`parse_world_state`) | LLM proposes a citation; code enforces its presence (FR-513, shipped) |
| Diff application | code | the model never writes the store directly; it proposes ops |
| Invalidation / temporal markers | code | contradictions are resolved mechanically, not by hoping for an overwrite |
| Decay + floor | code | recency is arithmetic, not the model's recollection |
| Revival, op authorship, salience scoring | LLM | judgement the recaps require |

The split is constant: **the LLM authors meaning; the code authors persistence.**
"Purely LLM" would trust the model's full rewrite each chapter — which is exactly
the regenerate failure mode this plan removes.

---

## 6. Sequencing (cheapest, highest-leverage first)

1. **Delta close + carry-forward floor** (§4.1, §4.3-floor). Fixes the Ch5
   zero-dropout by construction. Highest leverage; smallest surface. → **FR-514**
2. **Bi-temporal reconcile** (§4.2). Fixes the type-lag. Adds `valid_from`/
   `valid_to` to edges; turn context filters to current. → **FR-515**
3. **Ranked retrieval** (§4.4). Bounds turn context for long stories. Independent
   of 1–2. → **FR-516**
4. **Mechanical decay** (§4.3-decay). Makes `dormant` a code outcome, not an LLM
   guess. → **FR-517**
5. **Consolidation pass** (§4.5). Cleanup; do last. → **FR-518**

Each is a separate FR with its own RED test and acceptance criteria. None requires
an architectural change — they extend `world_state.py` (apply-the-diff, decay,
temporal filter) and `chapter_close.yaml` (emit ops, not a full ledger).

---

## 7. Acceptance shape (what "acts like memory" means, testably)

- **Persistence floor:** a chapter close that emits zero operations leaves the
  inherited active set intact. *(Test: empty-ops close → carry-forward unchanged.)*
- **Reconciliation:** an `enmity` edge contradicted by a `romantic_bond` op is
  invalidated in the same close, not in a later one. *(Test: contradicting op →
  old edge `valid_to` set, new edge current.)*
- **Grounding preserved:** every applied op still carries `recap_citations`; an
  ungrounded op is dropped. *(FR-513 invariant, per-operation.)*
- **Bounded retrieval:** turn context contains at most *K* relationships, ranked by
  cast relevance; off-stage and dormant/archived bonds are excluded. *(Test: a
  40-edge ledger yields ≤K rows for a 3-character turn.)*
- **Decay:** an edge un-reaffirmed for *N* chapters is `dormant` without the LLM
  saying so. *(Test: aged edge demoted by code.)*

---

## 8. Related

- [FR-513](../feature-requests/FR-513-dm-v2-emotional-state-in-world-ledger.md) — the emotional lane + grounding gate (shipped; the encode guard).
- [docs/process.md](process.md) — the continuity incident / review / reflection workflow.
- [world_state.py](../examples/dungeon_master/api/world_state.py) — the ledger and its boundary parser/formatter.
- [chapter_close.yaml](../examples/dungeon_master/prompts/chapter_close.yaml) — the close extraction contract (becomes the op-emission contract).
- [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) — `inherited_world_state`, `running_scene` (the carry and retrieve seams).
- Diary: [the bond that reset at every chapter break](diary/diary-2026-06-17-the-bond-that-reset-at-every-chapter-break.md).
