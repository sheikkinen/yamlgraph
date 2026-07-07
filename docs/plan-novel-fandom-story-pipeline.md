# Novel Fandom — Story Pipeline Plan

**Date:** 2026-07-06
**Context:** Post-consistency arc (FR-637→689). Canon has 47 entities, 22 events, all at depth 3. Structurally complete, narratively flat. The diary diagnosis: vertical depth (each entity enriched) but horizontal silence (no connections between entities that create story pressure).

## Problem

The canon is a database, not a novel. It has ingredients but no recipe. Three specific gaps identified in the story review (diary: "the synopsis that de-escalates"):

1. **Heidrun is plot-solvent** — she speaks and knots untie. She must fail at least once.
2. **Arnulf's three days are off-page** — the climax happens unwitnessed and unmotivated.
3. **The young men's faction never acts** — dissent produces a name but never draws blood.

These are symptoms of `conflict_dissolution_bias`: the LLM resolves every tension via the path of least resistance.

## Lineage

This is the third generation of the premise→novel idea, and the previous two had a **plot layer** that Gen 3 dropped (diary: "the dropped plot layer"):

- **Gen 1** (`langgraph-poc-narrator/src_novel`): synopsis required 3–6 `PlotThread`s; `PlotElaboration` had *required* `complications` and `turning_point` fields; beats carried `sequence`, `act`, and cross-thread `connections`.
- **Gen 2** (`dungeon_master/api/plot`): formal plot model with a mechanical validator — CLOSED AFFECT: every emotional unit opened must be closed by a later beat or declared intentionally open (`api/plot/validate.py`, `test_plot_affect_closure.py`).
- **Gen 3** (novel_fandom): typed entity canon, no plot object at all. The layer went extinct because entities are easy to gate and pressure-over-time is not.

This plan resurrects the layer as **plot threads** — ported and gated, not reinvented.

## Pipeline Sequence

```
synopsis (~2k tokens)                    canon (47 entities, 22 events)
  │                                        │
  ▼                                        │
1a. threads — 3–6 plot threads           │
    from synopsis alone (Gen 1 style,     │
    extremely cheap)                      │
  │                                        │
  ├◄──────────────────────────────────┘
  ▼
1b. reconcile — ground threads in canon ids;
    mine latent threads from fears / tensions / rules
  │
  ▼
1c. throughlines — per-character arcs across events
  │
  ▼
1.5. world_pressure — pressure-bearing world entities (kinship, trade)
  │
  ▼
2. event_revision — close latent threads: add resistance events
  │
  ▼
3. chapter_plan — group events into chapters with thread-ledger tracking
  │
  ▼
4. scene_draft — prose per chapter
```

Each step reads the output of the previous. Canon stays immutable throughout — new artifacts are layered on top, never mutating existing entities.

**Ordering principle (from Gen 1):** plot before world. Threads are extracted from the synopsis — the boundary where plot information enters — not archaeologically re-mined from entity fields downstream (`the_one_law`). The canon pass (1b) grounds and enriches; it does not originate.

---

## Step 1: Threads + Throughlines

Two dual decompositions of the same story, produced by one graph. **Plot threads** slice by *conflict*; **throughlines** slice by *character*. The character slice alone cannot see de-escalation — an arc can look complete while every conflict quietly dissolves. The thread slice is what fights it.

### 1a. Plot Threads — from synopsis

**What:** Extract 3–6 named tensions from the **synopsis alone** (~2k tokens — extremely cheap, Gen 1's exact move). The synopsis is the boundary where plot information enters the system; extract there, don't re-mine downstream. Each thread: carriers, stakes, required opposition, raise/release beats in synopsis order.

### 1b. Reconcile — ground in canon, mine the latent

**What:** A second pass with full canon (~23k) that does two things:

1. **Ground** — map each thread's carriers/raises/releases to canon ids so the mechanical gates can bite. A thread naming a character or beat the canon lacks becomes a *deficit entry* for steps 1.5/2 rather than an error.
2. **Mine latent threads** — the canon contains plot information the synopsis doesn't run, shredded into per-entity fields by genesis:

| Source | State | Example |
|---|---|---|
| Character `fears`/`backstory` | *Latent* — named but eventless | Hilde's fear: "the feud will resurrect itself through Arnulf **or the younger generation**" — a thread the story never runs |
| Faction `internal_tensions` | *Latent* | Aschenwulf young warriors "see her relationship with Gunnar as a betrayal of the dead" — a loaded gun no event fires |
| Rules | *Structural* | `blood_feud_custom` "only demands balance" — every unavenged death in the raid is an open thread *by law* |

Reconciliation reads fears × rules × factions *together* — the cross-entity pass the single-entity `deepen` tool architecturally couldn't do. Latent threads become the work queue for steps 1.5 and 2.

**Diagnostic for free:** diffing 1a (synopsis-only) against 1b (canon-grounded) measures how much plot the entity fields actually add. If 1b adds nothing but ids, the genesis reordering (below) is a pure win.

**Output:** `story/thread/<thread_id>.yaml`:

```yaml
id: young_men_grievance
kind: feud                    # closed enum: feud | bond | belief | survival | succession
carriers: [arnulf, ...]       # character ids, must resolve (ref_check)
sources: [blood_feud_custom, aschenwulf]   # canon ids this thread derives from
opposition: "..."             # required, non-empty (Gen 1's `complications`)
stakes: "..."                 # what is lost if unresolved
raises: [dawn_raid, arnulf_returns]        # event ids, must exist
releases: []                  # event ids; empty ⇒ status ≠ released
status: latent                # open | escalating | released | latent
```

**Mechanical gates:**
1. **Citation integrity** — every carrier/source/raise/release id resolves against canon (existing `ref_check` pattern)
2. **Ledger walk** — a release without a prior raise fails; ported from Gen 2's affect-closure validator, per-thread instead of per-(char, kind)
3. **Cap and distinctness** — 3–6 threads, distinct carrier-sets, non-trivial `opposition`. A thread nobody opposes is a theme, not a thread; unbounded extraction finds "threads" everywhere
4. **Id stability across regenerations** — the reconcile prompt receives the prior `story/thread/` set and must preserve ids for threads that persist; new threads get new ids; dropped threads are listed in a `dropped` output with a reason. Every thread id referenced in `story/thread_waivers.yaml` and `story/chapter_plan.yaml` must resolve against the current thread set (same `ref_check` pattern). Without this, every regeneration silently orphans waivers and ledger entries

**Known limitation:** `status` is an LLM claim — the ledger walk checks consistency (releases follow raises), not truth. The FR-review raw read covers substance.

### 1c. Throughlines

**What:** For each major character (8), walk the 22-event timeline and write: how does this person change from event to event? Not the event — the *cost* of living through it.

**Output:** `story/throughline/<character_id>.yaml` — per-character arc with:
- emotional state at each event they participate in
- what they lose or gain
- where their arc goes slack (no change between consecutive events)

**Acceptance criteria:**
- Every major character (role ≠ minor) has ≥1 identified slack point, or an explicit "arc is taut" claim citing the event pair that proves it
- A throughline with zero deltas across all events for a major character fails the gate but the artifact is persisted — that is Berno-tier flatness in a load-bearing character, and the signal is in the prose; failing the run before writing it would destroy the evidence
- Each emotional-state entry cites the event id it responds to (mechanically checkable against canon)
- The timeline walk order is the `sequence` field on events (prerequisite FR below) — the throughline must not invent an intra-year ordering the canon does not state

### Step 1 shape

**Input:** Synopsis (~2k tokens) for 1a; full canon (~23k tokens) as `data_files` for 1b/1c.

**Pipeline:** Single graph, three LLM nodes (extract threads from synopsis → reconcile against canon → throughlines), structured output. `Thread` and `Throughline` Pydantic schemas first.

**Why first:** Threads name the tensions; throughlines locate where they go slack per character. Together they produce the deficit list everything downstream consumes.

**Size:** Small. Three calls, one of them ~2k input.

---

## Step 1.5: World Pressure (targeted world-building)

**What:** Add the minimal world entities that manufacture the people and forces who apply the missing pressure. Not width for its own sake — the canon is already a database that isn't a novel, and 20 more populated entities is inventory, not story (`growth_as_default`). Every new entity must be load-bearing for a named tension.

Two targeted expansions:

1. **Kinship — family trees for both clans.** `blood_feud_custom` says the feud "passes through family lines," but the kinship graph is nearly empty (Hilde–Arnulf–father, and that's it). The Bärenschädel kin who lost members to Hilde's dawn raid are unnamed — which is *why* the young men's faction has no face. A family tree mechanically produces the antagonist the story lacks: some named cousin whose father died in the raid *must* seek balance under the rule. The world's own law demands the conflict; the LLM doesn't have to invent it against its de-escalation bias. This is `spec_kill` applied to narrative: encode the pressure in data, and generation can't dissolve it.
2. **Reinmar's trade network.** He is clanless in a clan-obsessed setting, walking a salt-road that appears in exactly one location file — a device wearing a coat. 2-3 nodes on the salt-road plus one obligation he carries give him motive, history, and leverage, and give the high valley an outside world that can arrive uninvited in act three.

**Explicitly out of scope:** generic organizations, economies, pantheons, or any entity no tension in the story review demands.

**Input:** Canon + threads and throughlines from step 1 (latent threads name the tensions that need bodies).

**Output:** New character/faction/location pages in `canon/` — additive only, same byte-identity and gate rules as step 2. Estimated 6-10 new entities: named grievance-holders in both clans with kinship relationships, 2-3 salt-road entities.

**Pipeline:** Agent graph reusing `create_character` / `create_faction` / `create_location` graph-tools (FR-658 infrastructure). Then rerun step 1 to regenerate threads and throughlines over the enlarged cast.

**Admission rule (the gate):** For each new entity, the agent must cite the **thread id** it serves, and the cited thread must exist in `story/thread/` at creation time. Validation order: create entities → rerun step 1 → gate checks that each new entity appears in the `carriers` or `sources` of its cited (id-stable) thread. An entity absent from its thread after regeneration fails the gate; remediation is deletion of the orphan entity files (additive-only means rollback is `git checkout` of nothing — just remove the new files) and a rerun of step 1. An entity that serves no thread is inventory and is rejected — count what bears pressure, not what fills fields.

**Why between 1 and 2:** Throughlines diagnose where pressure is missing; world entities manufacture who applies it. Step 2 then draws its resistance events from a real cast — a named cousin with a dead father — instead of asking the LLM to conjure "a young man from both clans" ex nihilo.

**Size:** Medium. Agent with 6-10 create calls, plus a step 1 rerun.

---

## Step 2: Event Revision (latent-thread closure)

**What:** Step 2 is not creative — it is **closure of a deficit list the canon itself generated**. Every `latent` thread from step 1 must either gain events (raises, and where the story demands it, releases) or be explicitly waived with a reason. The LLM doesn't invent pressure against its de-escalation bias; it instantiates events for threads the rules and fears already opened. `spec_kill` at the data layer.

The known deficit list already covers the three review gaps:

- An event where Heidrun's wisdom fails or is rejected (thread: her authority vs. the young men's law)
- Events dramatizing Arnulf's three days of isolation (not summary — scenes of what he does, who approaches, what he refuses)
- An event where the young men's faction acts — steals weapons, poisons a water source, ambushes a Bärenschädel hunter — something with a cost. The actor is a *named* grievance-holder from step 1.5's kinship expansion, not an anonymous "young man."

**Exit gate (mechanical):** After regeneration, zero threads with `status: latent` remain unwaived. Waivers live in `story/thread_waivers.yaml` with a reason each.

**Input:** Canon (including step 1.5 world entities) + regenerated threads and throughlines.

**Output:** New event files in `canon/event/` — **additive only**. Existing canon files must be byte-identical after the run (enforced: `git diff --exit-code` on all pre-existing paths). Every new event passes the same `ref_check` and `semantic_dedup` gates as genesis output. Threads and throughlines are **not** patched in place: after event revision, step 1 is rerun as the final action of step 2, regenerating both from the enlarged canon. This keeps steps decoupled — derived artifacts are always a pure function of canon.

**Pipeline:** Agent graph with `create_event` graph-tools (reusing existing FR-658 infrastructure). The agent reads the latent-thread deficit list, creates resistance events. Then rerun the step 1 graph.

**Why second:** De-escalation gaps can't be fixed without knowing *which* tensions lack events. The thread extraction provides that list; throughline slack points locate where in each arc the events land.

**Why this is not the rejected Option B:** The diary rejected cross-entity *mutation* — editing existing entities puts the 55-FR consistency arc at risk. Step 2 is additive: new event pages only, gated identically to genesis output, with a mechanical byte-identity check on everything that existed before. The agent must not "helpfully" touch `hilde.yaml` to reference a new event; if a new event needs to be discoverable from a character, that is what `participants` on the event is for.

**Prerequisite — event ordering:** 19 of 22 events sit at `year: 0` with no intra-year ordering, and step 2 adds 3-5 more into the same year. The `Event` schema needs a `sequence: int` field (one small FR: schema field + backfill of the 22 existing events from synopsis order + `ref_check` uniqueness check). Without it, step 1c's timeline walk and step 3's "revised event sequence" are unexpressible in canon and each silently invents an ordering the canon does not state. This FR therefore precedes step 1, not step 2 — the throughline walk is its first consumer.

**Size:** Medium. Agent with 3-5 create calls. Reuses existing graph-tool pipelines.

---

## Step 3: Chapter Plan

**What:** Group the revised event sequence (22 original + 3-5 new) into 8-12 chapters. Each chapter gets:

- POV character
- Events covered
- Thread ledger: which threads are open, which close, which escalate in this chapter (thread ids, not free text)
- The one thing that changes irreversibly in this chapter
- Emotional register (rage / grief / tenderness / dread / etc.)

**Input:** Canon + threads + throughlines + revised events.

**Output:** `story/chapter_plan.yaml` — ordered list of chapters with the above fields.

**Pipeline:** Single graph, possibly multi-step (first group events, then assign POV and tension state per group).

**Thread-ledger gate (mechanical half):** The LLM *produces* the per-chapter ledger; it must not *judge* it — a self-graded ledger is `gate_checks_shape_not_substance`. Each chapter carries an `act: int` field (1-3) so "final act" is a mechanical term, not a rhetorical one. A Python script parses `chapter_plan.yaml` against `story/thread/*.yaml` and fails the run if: (a) a chapter releases a thread id that was never raised, (b) the open-thread count monotonically decreases across the chapters before the first `act: 3` chapter, or (c) a thread's chapter-level raise/release sequence contradicts its canon-level `raises`/`releases`. LLM writes, Python judges. The script starts from Gen 2's affect-closure walk (`dungeon_master/api/plot/validate.py`) — port, don't design — and ships with its own test.

**Why third:** Without throughlines and resistance events, chapter grouping optimizes for chronology. With them, it optimizes for emotional arc — which chapters carry grief, which carry dread, where the reader gets a breath.

**Size:** Medium. 1-2 LLM calls. Full canon + throughlines as context.

---

## Step 4: Scene Drafting

**What:** For each chapter, produce dramatized prose: dialogue, setting, interiority, sensory detail. Characters speak in voice. Events are shown, not told.

**Input:** Chapter plan + throughlines + all canon entities referenced in the chapter.

**Output:** `story/drafts/chapter-XX.md` — prose per chapter, 2000-4000 words each.

**Pipeline:** Sequential fold over chapters, not a parallel map. Each chapter call receives the chapter plan entry + relevant canon entities + throughlines for the POV character + a rolling summary of all previously drafted chapters. A parallel map would guarantee voice drift and factual contradictions between chapters — chapter 7 must know what chapter 6 said. Cost of sequencing is acceptable: 8-12 calls either way; only wall-clock time differs.

**Why last:** Prose without structure is random scenes. Structure without throughlines is plot summary. Both need to exist before drafting begins.

**Size:** Large. 8-12 LLM calls, each generating 2-4k words. Most expensive step.

---

## Design Principles

1. **Canon grows, never changes.** Step 2 adds new event pages to `canon/` under the same gates as genesis; existing canon files are byte-identical after every run (mechanically enforced). The dynamic-lane mutation channel (`close.yaml` delta ops) exists in the architecture but is **explicitly out of scope** for this pipeline — no step invokes it; byte-identity is checked against all pre-existing canon paths regardless of lane. All derived artifacts — throughlines, chapter plan, drafts — live in a sibling `story/` directory: derived, regenerable, outside the canon consistency guarantee. `story/` needs no lane field because everything in it is disposable.

2. **Derived artifacts are pure functions of canon — with stable identity.** Threads and throughlines are regenerated whenever canon changes (steps 1.5 and 2 end by rerunning step 1), never patched in place. This is what makes steps independently rerunnable: no step's output is another step's mutable state. Regeneration preserves thread ids (gate 4 in step 1b) — purity of content, stability of identity; without id stability, waivers and chapter ledgers dangle after every rerun. Threads *feed* canon growth (step 2 creates events from them) but are not themselves canon — keeping the immutability story clean.

3. **Context window is sufficient.** Full canon is ~23k tokens (~30k after step 1.5's 6-10 entities). Even with throughlines and chapter plan added, total context stays under 50k — well within a single LLM call.

4. **The thread ledger is the creative gate — LLM writes it, Python judges it.** Threads carry raise/release histories; the chapter plan carries a per-chapter ledger over thread ids. Deterministic scripts validate both (citation integrity, ledger walk, non-monotonic open count). The gate is never self-graded — same separation as the dedup gate, but for narrative pressure. Algorithm ported from Gen 2's affect-closure validator.

5. **New artifact types get schemas.** `Thread`, `Throughline`, and `ChapterPlan` Pydantic models are added to `schema/` before their steps run. No untyped dicts wander the pipeline (Commandment 5).

6. **Plot before world.** Threads are extracted at the synopsis boundary, where plot information enters — not re-mined from entity fields downstream. World entities are admitted only in service of a thread (step 1.5's citation rule). Gen 1 had this ordering; Gen 3's genesis lost it, and horizontal silence was the price.

---

## Future Work: Genesis Reordering

The Floodmark canon's "horizontal silence" was not a missing tool — it was a **phase-ordering defect at genesis**. Gen 3's genesis runs synopsis → entities; entities generated without a thread skeleton have nothing to connect them, so the connections were never computed and no per-entity field could hold them. The fears and `internal_tensions` this plan mines as "latent threads" are plot information the genesis shredded into per-entity fields — `the_one_law` violated at the synopsis boundary.

Fix for the *next* canon: insert thread extraction between synopsis and entity structuring in `genesis.yaml` (one call on ~2k tokens). Entity structuring then receives threads as context — characters are generated *as carriers*, factions *as opposition*, and the admission rule applies from birth. Horizontal silence becomes structurally impossible rather than retroactively curable.

The 1a/1b diff in this pipeline is the evidence-gathering step: if canon reconciliation adds only ids to synopsis-extracted threads, the reordering is proven a pure win, and the genesis FR follows.

---

## Implementation Order

Start with the event-sequence field (mechanical, hours), then step 1 (threads + throughlines) — the smallest, cheapest, most diagnostic creative step. Its latent-thread list determines whether step 2 is a light touch (add 3 events) or a rewrite (the story needs restructuring). Each subsequent step gets its own FR when the previous step's output is reviewed — the review is a raw-output read (`read_raw_output_first`), not a metric. The 1a/1b diff is likewise judged by reading, not by a similarity score — building a diff metric here would be `metric_archaeology_before_reading_output`.

FR sequence:

1. **FR: event sequence field** — `sequence: int` on `Event` (port of Gen 1's `Beat.sequence`), backfill 22 events from synopsis order + uniqueness check (prerequisite for steps 1c and 3 — the throughline timeline walk is its first consumer)
2. **FR: threads + throughlines** — `Thread` + `Throughline` schemas + step 1 graph (synopsis extraction → canon reconciliation → throughlines) + citation/ledger/cap/id-stability gates + 1a/1b diff in the FR review
3. **FR: world pressure** — step 1.5 agent: kinship + trade entities under the thread-citation admission rule, byte-identity enforcement, step 1 regeneration
4. **FR: event revision** — step 2 agent + latent-closure exit gate + byte-identity enforcement + step 1 regeneration
5. **FR: chapter plan** — `ChapterPlan` schema + step 3 graph + thread-ledger gate script (ported from `dungeon_master/api/plot/validate.py`)
6. **FR: scene drafting** — step 4 sequential fold + rolling summary
7. **FR: genesis reordering** (conditional) — thread extraction between synopsis and structuring in `genesis.yaml`, if the 1a/1b diff shows entity fields add no plot

Known accepted limitation for draft 1: no revision loop on prose. Step 4 output is a first draft; a critique-revise cycle is a later pipeline, not scope creep into this one.
