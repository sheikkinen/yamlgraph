# DM Web UI v2 — The Journey Is the Story

**Status:** Planning (pre-FR)
**Supersedes the interaction model of:** FR-468 (DM Web UI v1)
**Reuses:** `preplan.yaml`, `prompts/*`, `nodes/story_io.py`, the parchment theme

---

## 1. Why v2

v1 optimizes for the **end result**: `preplan()` builds the skeleton, then
*immediately* runs the turn loop's first `weave`, and the UI shows only the final
woven beat. The user is handed a finished paragraph and asked "accept?".

That cuts out the part that matters. **The journey to the story is the point** —
reading the synopsis, walking the planned chapters, nudging a beat here, deciding
*which* moment is worth fully rendering. v2 reframes the app from a
*beat-acceptance treadmill* into a **navigable, editable story workbench** where
generation is something the DM invokes deliberately, not a thing that already
happened.

### The core shift

| | v1 (forward loop) | v2 (navigable document) |
|---|---|---|
| Mental model | "Accept the next beat" | "Explore and shape the outline, then render what I choose" |
| Generation | Eager — weave runs before you see anything | On demand — you pick a beat and generate it |
| Navigation | None — forward only | Breadcrumb jumps to any chapter / beat |
| Source of truth | Linear checkpointer (`thread_id`) | A persisted **story document** the UI reads/edits |
| Synopsis | Hidden (only logline leaks out) | A first-class card you regenerate / edit / accept |

---

## 2. The session, step by step

This is the flow the v2 UI must support:

1. **Preplan** *(as today)* — premise + chapter/cast counts → synopsis, plot,
   chapters, cast skeleton (`story.json`).
2. **Review the synopsis** — the synopsis arrives as a **card on the main panel**.
   The DM can **regenerate** it (re-roll), **edit** it inline, or **accept** it to
   proceed. Nothing is woven yet.
3. **Browse the outline** — the DM walks the **chapters** and their **beats**
   (planned stubs), making **small edits** here and there. The breadcrumb and a
   chapter/beat list drive navigation; any beat or chapter summary is editable in
   place.
4. **Render a chosen beat** — for a beat the DM selects, a **"Generate beat"**
   button runs the expensive weave (parallel character plans → woven prose) for
   *that* beat only. The result lands back in the document, editable.

**Breadcrumb is navigation**, not just a status readout: clicking a chapter dot
or crumb jumps the main panel to that chapter / beat.

---

## 3. Conceptual model

### Hierarchy

```
Story
 ├─ synopsis   (logline, conflict, themes, tone, arc)   ← reviewed/edited (step 2)
 ├─ cast       (name, role, goal, voice)
 └─ chapters[]
     ├─ title / act / summary / setting                 ← browsed/edited (step 3)
     └─ beats[]                                          ← browsed/edited (step 3)
         ├─ stub     : one-line planned intention        (cheap, from preplan)
         ├─ woven    : full prose                         (expensive, on demand — step 4)
         └─ status   : planned | generated | committed
```

> **Terminology.** A **beat** is one narrative moment. A **turn** in v1 was the
> *act* of generating+committing one beat; v2 keeps "beat" as the noun and drops
> "turn" from the UI vocabulary (it survives only inside the weave graph).

### Beat lifecycle

```
planned ──(Generate beat)──► generated ──(Accept / edit)──► committed
   ▲            │
   └────(regenerate / re-roll)
```

- **planned** — a stub line the preplan produced; cheap, no LLM weave.
- **generated** — the weave has run; full prose sits in `woven`, awaiting the DM.
- **committed** — the DM accepted (verbatim or edited); written to the chapter file.

---

## 4. Central architectural decision (for the Judge)

**v1's forward-only interrupt loop cannot express v2's navigation.** A
checkpointed `turn-loop.yaml` resumes linearly; you cannot "jump back to ch.1
beat 2 and re-render it" without unwinding the checkpoint. v2 wants random access
and per-beat regeneration.

**Proposal: decouple navigation from generation.**

- **Story document = source of truth.** Persist the whole story (synopsis, cast,
  chapters, per-chapter beat list with stub/woven/status) as JSON per session.
  The UI reads and edits this document directly. Navigation, editing, and
  ordering are plain document operations — no graph involved.
- **Generation = stateless, single-shot graph calls.** Two narrow graphs invoked
  on demand against the document:
  - **preplan (extended)** — also outlines **beat stubs** per chapter.
  - **weave-beat (new, single beat)** — runs `plan_all` (parallel character
    plans) + `weave` for **one** chosen beat, given that beat's chapter context
    and the committed history before it. No interrupt, no loop, returns the prose.

This retires the checkpointed `turn-loop.yaml` from the *web* path (the CLI/demo
can keep it). The trade-off: we give up the elegant interrupt loop in exchange for
free navigation, per-beat regeneration, and inline editing — which is the entire
point of v2.

> **Open question O1:** keep `turn-loop.yaml` for the CLI and add a separate
> `weave-beat.yaml` for the web, or unify? Leaning: **add `weave-beat.yaml`**,
> leave the CLI loop untouched (smaller blast radius).

---

## 5. What changes, per layer

### Logic (YAML graphs)

- **`preplan.yaml` (extend):** after `chapters`, add a `beats` node (a `map` over
  chapters, or one prompt) that emits an ordered list of **beat stubs** per
  chapter — each a one-line intention. Persist into `story.json`.
  *New prompt:* `prompts/beats.yaml` (chapter goal + cast → 2–5 beat stubs).
- **`weave-beat.yaml` (new):** inputs = one chapter's goal/setting, the chosen
  beat's stub, the cast, and recent committed history; runs `plan_all` + `weave`;
  outputs the woven prose. No checkpointer, no interrupt — a pure function graph.
- **`synopsis` regeneration:** reuse the existing `synopsis` prompt as a
  single-node call for the "re-roll synopsis" action.

### Side effects (Python tools)

- **Story document store** (`api/story_doc.py`, new): load/save the per-session
  story JSON; helpers to address a beat (`chapter_index`, `beat_index`), update a
  stub, set woven prose, mark committed, and reorder. This replaces the
  checkpointer as the web persistence layer.
- Reuse `_slugify`, chapter-file writing from `story_io.py` for committed beats.

### Presentation (FastAPI + templates)

- **Session adapter (`api/session.py`, rework):** stop eagerly weaving in
  `preplan()`. Methods become document operations + on-demand generation:
  `preplan()`, `regenerate_synopsis()`, `edit_synopsis()`, `accept_synopsis()`,
  `edit_chapter()`, `edit_beat_stub()`, `generate_beat(ch, beat)`,
  `accept_beat(ch, beat, text)`, `navigate(ch, beat)`.
- **Routes (`api/routes/story.py`, extend):** add endpoints for synopsis
  review, outline browsing/editing, `POST /story/beat/generate`, and navigation.
  Keep HTMX `#app-body` swaps.
- **Templates:** new main-panel **modes** (synopsis-review, outline-browse,
  beat-view) selected by the current navigation target; the breadcrumb becomes a
  clickable nav control; the left aside keeps logline + chapter context.

---

## 6. Navigation model

The breadcrumb reflects and drives the current target:

```
Story · Synopsis            (step 2)
Story · Ch 2/3 · Outline    (step 3, chapter level)
Story · Ch 2/3 · Beat 1/4   (step 3/4, beat level)
```

- Chapter dots → jump to a chapter's outline.
- A beat strip within a chapter → jump to a beat.
- Each beat shows its **status** (planned / generated / committed) so the DM sees
  at a glance what still needs rendering.
- Navigation is a GET-like swap of `#app-body` to the addressed view; edits are
  POSTs that write the document then re-render the same view.

---

## 7. Phases

- **Phase A — Synopsis review.** Preplan stops at the skeleton (no eager weave);
  main panel shows the synopsis card with **regenerate / edit / accept**.
  *Witness:* preplan renders a synopsis card, no woven beat present; accept
  advances to the outline.
- **Phase B — Outline browse + edit + breadcrumb nav.** Chapter/beat list from
  preplanned **stubs**; inline edit of chapter summary and beat stubs; breadcrumb
  jumps between chapters/beats. Requires the extended preplan (`beats.yaml`) and
  the story-document store.
  *Witness:* navigating to a chapter shows its beat stubs; editing a stub persists;
  breadcrumb links target the right view.
- **Phase C — On-demand beat generation.** "Generate beat" button runs
  `weave-beat.yaml` for the chosen beat; result is editable; accept commits to the
  chapter file and flips status.
  *Witness:* generating a planned beat yields prose and flips status to generated;
  accept writes the chapter file and marks committed.

Each phase: its own `REQ-YG-XXX`, witness test (LLM mocked at
`llm_nodes.execute_prompt`), changelog fragment, diary entry, and demo-log update
(demo-gate).

---

## 8. Open questions for the Judge

- **O1.** Separate `weave-beat.yaml` for web vs. keep `turn-loop.yaml` for CLI?
  (Leaning: separate.)
- **O2.** Does preplan generate beat stubs for **all** chapters up front (more
  cost, full browse) or **lazily per chapter** on first visit (cheaper, but a
  chapter shows empty until opened)? (Leaning: lazy per chapter.)
- **O3.** Is the story document a new `api/story_doc.py` JSON store, or do we lean
  on a LangGraph checkpointer with a document-shaped state? (Leaning: plain JSON
  store — navigation is not a graph concern.)
- **O4.** Committed-history context for `weave-beat`: feed all prior committed
  beats, or a windowed `recent_history` like the current `prep_turn`? (Leaning:
  windowed, reuse `prep_turn`'s logic.)
- **O5.** Do we keep v1's single-Accept editable card as the **beat-view** mode,
  or is that now only reached after "Generate beat"? (Leaning: beat-view = the v1
  card, shown only for generated beats.)
- **O6.** Reordering/inserting/deleting beats — in scope for v2 or a later pass?
  (Leaning: out of scope; browse + edit + generate only.)

## 9. Acceptance criteria (sketch — to be frozen at FR time)

- [ ] Preplan no longer eagerly weaves; first view is the **synopsis card**.
- [ ] Synopsis supports **regenerate / edit / accept**.
- [ ] Outline view lists **chapters and their beat stubs**; chapter summaries and
      beat stubs are **editable inline** and persist to the story document.
- [ ] **Breadcrumb navigates** (synopsis ↔ chapter ↔ beat).
- [ ] A **"Generate beat"** action weaves a single chosen beat on demand; the
      result is editable and **Accept** commits it to the chapter file.
- [ ] Per-beat **status** (planned / generated / committed) is visible.
- [ ] No eager full-story generation anywhere in the web path.
- [ ] Phase-wise: witness test + changelog fragment + diary entry + demo-log.

---

### Doctrine notes

- This plan is the **Plan** stage. Next: split into an FR (or phased FRs A/B/C),
  freeze scope via the Judge, then enforce TDD (RED→GREEN per phase).
- v2 is still a **pure-Presentation + thin side-effect** addition plus **two
  narrow graphs**; it must not entangle navigation into graph state
  (import-linter three-layer boundary stays intact).
- Retiring the eager-weave path means updating FR-468's docs/demo so the README
  no longer implies a forward-only loop on the web.
