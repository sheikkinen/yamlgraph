# Novel Fandom — Story Pipeline Plan

**Date:** 2026-07-06
**Context:** Post-consistency arc (FR-637→689). Canon has 47 entities, 22 events, all at depth 3. Structurally complete, narratively flat. The diary diagnosis: vertical depth (each entity enriched) but horizontal silence (no connections between entities that create story pressure).

## Problem

The canon is a database, not a novel. It has ingredients but no recipe. Three specific gaps identified in the story review (diary: "the synopsis that de-escalates"):

1. **Heidrun is plot-solvent** — she speaks and knots untie. She must fail at least once.
2. **Arnulf's three days are off-page** — the climax happens unwitnessed and unmotivated.
3. **The young men's faction never acts** — dissent produces a name but never draws blood.

These are symptoms of `conflict_dissolution_bias`: the LLM resolves every tension via the path of least resistance.

## Pipeline Sequence

```
canon (47 entities, 22 events)
  │
  ▼
1. throughlines — per-character emotional arcs across events
  │
  ▼
2. event_revision — fix de-escalation: add resistance events
  │
  ▼
3. chapter_plan — group events into chapters with tension tracking
  │
  ▼
4. scene_draft — prose per chapter
```

Each step reads the output of the previous. Canon stays immutable throughout — new artifacts are layered on top, never mutating existing entities.

---

## Step 1: Throughlines

**What:** For each major character (8), walk the 22-event timeline and write: how does this person change from event to event? Not the event — the *cost* of living through it.

**Input:** Full canon (~23k tokens) as `data_files`.

**Output:** `canon/throughline/<character_id>.yaml` — per-character arc with:
- emotional state at each event they participate in
- what they lose or gain
- where their arc goes slack (no change between consecutive events)

**Pipeline:** Single graph, single LLM node, full canon in context, structured output.

**Why first:** Throughlines reveal which characters are flat and which carry the story. They also expose *where* resistance is needed — the slack points in a throughline are where the de-escalation fix should insert pressure. This output feeds both step 2 (event revision) and step 3 (chapter plan).

**Size:** Small. One prompt, one call. ~23k input, ~8 structured outputs.

---

## Step 2: Event Revision

**What:** Using throughlines to identify slack points, add 3-5 new resistance events that increase story pressure. Specifically:

- An event where Heidrun's wisdom fails or is rejected
- Events dramatizing Arnulf's three days of isolation (not summary — scenes of what he does, who approaches, what he refuses)
- An event where the young men's faction acts — steals weapons, poisons a water source, ambushes a Bärenschädel hunter — something with a cost

**Input:** Canon + throughlines from step 1.

**Output:** New event files in `canon/event/`, plus updates to throughlines reflecting the new events.

**Pipeline:** Agent graph with `create_event` graph-tools (reusing existing FR-658 infrastructure). The agent reads throughlines, identifies slack points, creates resistance events.

**Why second:** De-escalation gaps can't be fixed without knowing *where* the pressure drops. Throughlines provide that map.

**Size:** Medium. Agent with 3-5 create calls. Reuses existing graph-tool pipelines.

---

## Step 3: Chapter Plan

**What:** Group the revised event sequence (22 original + 3-5 new) into 8-12 chapters. Each chapter gets:

- POV character
- Events covered
- Tension ledger: which tensions are open, which close, which escalate
- The one thing that changes irreversibly in this chapter
- Emotional register (rage / grief / tenderness / dread / etc.)

**Input:** Canon + throughlines + revised events.

**Output:** `canon/chapter_plan.yaml` — ordered list of chapters with the above fields.

**Pipeline:** Single graph, possibly multi-step (first group events, then assign POV and tension state per group).

**Why third:** Without throughlines and resistance events, chapter grouping optimizes for chronology. With them, it optimizes for emotional arc — which chapters carry grief, which carry dread, where the reader gets a breath.

**Size:** Medium. 1-2 LLM calls. Full canon + throughlines as context.

---

## Step 4: Scene Drafting

**What:** For each chapter, produce dramatized prose: dialogue, setting, interiority, sensory detail. Characters speak in voice. Events are shown, not told.

**Input:** Chapter plan + throughlines + all canon entities referenced in the chapter.

**Output:** `drafts/chapter-XX.md` — prose per chapter, 2000-4000 words each.

**Pipeline:** Map node over chapters. Each chapter is one LLM call with chapter plan entry + relevant canon entities + throughlines for POV character.

**Why last:** Prose without structure is random scenes. Structure without throughlines is plot summary. Both need to exist before drafting begins.

**Size:** Large. 8-12 LLM calls, each generating 2-4k words. Most expensive step.

---

## Design Principles

1. **Canon is immutable.** Steps 1-3 add new artifact types (`throughline/`, new events, `chapter_plan.yaml`). Step 4 writes to `drafts/`, not `canon/`. The 55-FR consistency guarantee is never at risk.

2. **Each step is independently runnable.** If throughlines are good but event revision needs iteration, rerun step 2 without touching step 1's output.

3. **Context window is sufficient.** Full canon is ~23k tokens. Even with throughlines and chapter plan added, total context stays under 40k — well within a single LLM call.

4. **The tension ledger is the creative gate.** Chapter plan includes a per-chapter tension count. If tensions monotonically decrease before the final act, the plan fails — same principle as the dedup gate, but for narrative quality.

---

## Implementation Order

Start with step 1 (throughlines). It's the smallest, cheapest, and most diagnostic. Its output determines whether step 2 is a light touch (add 3 events) or a rewrite (the story needs restructuring). Each subsequent step gets its own FR when the previous step's output is reviewed.
