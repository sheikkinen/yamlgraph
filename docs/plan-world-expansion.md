# Plan: World Expansion Pipeline — Recursive Wiki Growth

**Date:** 2026-07-01
**Context:** FR-643 rejected (prayer + magic), reflection on DM expansion pattern
**Supersedes:** `plan-world-generation-loop.md` (analytical worldbuilding)

## The Insight Chain

Three failed designs taught one lesson:

1. **FR-643 (analyst loop):** Ask LLM to diagnose gaps → prayer.
2. **FR-643 judgement (deterministic gaps → LLM gen):** Better, but still
   a diagnostic system searching for what's wrong.
3. **Linear expansion (premise → synopsis → entities):** Correct pattern,
   but produces a skeleton. Kaelen is a name with goals, not a person
   with a childhood.

The correction: **expansion is recursive**. When you deepen Kaelen, his
backstory introduces Brennan (his mentor), the Ember Trials (an event),
the High Forge (a location). These are **red links** — references to
entities that don't have wiki pages yet. Fill them. They produce more
red links. The world grows from the inside out, like a real wiki.

Nobody diagnoses gaps. The pipeline structure defines what to generate.
Red link extraction finds what's new. Depth budget controls when to stop.

---

## 1. How Real Wikis Grow

Wikipedia doesn't have an analyst that examines the encyclopedia and
says "we need an article about forge metallurgy." Someone writes an
article about swords. It mentions forge metallurgy. That's a red link.
Someone sees it, writes the article. That article mentions damascus
steel. Red link. And so on.

The growth is driven by **content producing references to content that
doesn't exist yet.** The structure is:

```
write → extract red links → write pages for red links → repeat
```

No diagnosis. No gap analysis. The content itself declares what's missing
by referencing it.

---

## 2. The Expansion Pipeline

### Phase 1: Cold Start (Linear, One Pass)

The author provides a premise. The pipeline expands it through a fixed
chain. Each step takes the previous output and produces the next layer.

```
premise (human-authored)
    ↓
synopsis (LLM: expand premise into full-disclosure narrative)
    ↓
manifest (LLM: extract entity names + types + 1-sentence from synopsis)
    ↓
skeleton entities × N (LLM map: generate one page per manifest entry)
    ↓
    gate each page (ref_gate: all references resolve?)
    ↓
    persist to canon/
```

After Phase 1, the wiki has: premise, synopsis, and ~10-15 skeleton
entities (characters with names and goals, events with participants,
factions with members, etc.). This is the current seed canon — but
generated, not hand-authored.

Every step uses the existing `draft → gate → fix → persist` pipeline
from `graph.yaml`. No new machinery needed for Phase 1.

### Phase 2: Deepening (Iterative, Red-Link-Driven)

The skeleton world is thin. Characters have goals but no histories.
Events have participants but no consequences. The deepening loop
enriches existing pages and grows the world through red links.

```
┌─────────────────────────────────────────────────────┐
│  DEEPENING LOOP                                     │
│                                                     │
│  reload_canon                                       │
│      ↓                                              │
│  select_thin_entities (deterministic)                │
│      ↓  (entities that fail richness thresholds)    │
│  deepen × N (LLM map: "tell me this entity's        │
│      ↓       backstory / consequences / atmosphere") │
│  extract_red_links (deterministic)                   │
│      ↓  (entity names in output that aren't pages)  │
│  create_skeletons × N (LLM map: skeleton page per   │
│      ↓                  red link)                    │
│  gate + persist all                                  │
│      ↓                                              │
│  depth_check                                         │
│      ↓                                              │
│  max_depth reached? → END                            │
│  still thin?        → back to reload_canon           │
└─────────────────────────────────────────────────────┘
```

### Phase 3: Validation (Post-Condition, One Pass)

After deepening, run richness checks as a report — not a loop driver.
The report tells the human what the world looks like:

```
Richness Report:
  Characters:   8 (all have wants≠needs, 7/8 have triggers)
  Events:      12 (all have locations, causal chains connected)
  Factions:     3 (all have ≥2 members)
  Locations:    5 (all referenced by ≥1 event)
  Rules:        4 (all domains covered)
  Red links:    2 remaining (below threshold, acceptable)
  Depth:        3 levels from synopsis
```

This is informational. If the human wants deeper, they run Phase 2 again
with a higher `max_depth`.

---

## 3. Red Link Extraction

The pivotal mechanism. When an LLM generates a backstory for Kaelen:

> "Kaelen trained under old Brennan at the High Forge of Ashguard.
> During the Ember Trials, he first wielded dragonsteel..."

The red link extractor finds entity mentions that aren't wiki pages:

| Mention | Exists as page? | Action |
|---------|----------------|--------|
| Brennan | No | → red link → create skeleton character |
| High Forge of Ashguard | No | → red link → create skeleton location |
| Ember Trials | No | → red link → create skeleton event |
| Ashguard | Yes (faction) | → resolved, add reference |
| dragonsteel | No, but it's a material, not an entity | → ignore |

**Implementation options:**

**Option A: LLM extraction.** Ask the LLM to list new entities it
introduced and their types. Cheap (structured output from the same call
that generated the backstory). Risk: may miss some or hallucinate.

**Option B: Deterministic diff.** Compare entity names mentioned in the
output against the set of existing page ids. Requires a way to identify
entity mentions in prose — NER or pattern matching. More reliable for
known entities, but can't type new ones.

**Option C: Hybrid.** LLM generates backstory WITH an explicit
"new entities introduced" field in the schema. Gate checks that every
new entity is either an existing page or in the new-entities list.
Deterministic validation of LLM-declared novelty.

**Option C is correct.** The LLM already knows what it invented (it just
wrote it). Make it declare its inventions as structured output. The gate
validates. This is the existing pattern: structured output + gate.

**Schema for deepened page output:**

```yaml
schema:
  name: DeepenedEntity
  fields:
    updated_page:
      type: dict
      description: "The enriched page content"
    new_entities:
      type: list[NewEntity]
      description: "Entities introduced in the backstory that need wiki pages"

  nested:
    NewEntity:
      id:
        type: str
        description: "Proposed page id (snake_case)"
      type:
        type: str
        description: "character, event, faction, location, or rule"
      name:
        type: str
        description: "Display name"
      summary:
        type: str
        description: "One sentence describing this entity"
      relationship_to_parent:
        type: str
        description: "How this entity relates to the page being deepened"
```

The gate checks:
- Every entity referenced in `updated_page` is either an existing page
  or declared in `new_entities`
- No `new_entities` duplicate existing page ids
- All `new_entities` have valid types

---

## 4. Depth Budget

Without a budget, the world grows forever. Brennan's backstory introduces
his father. His father's backstory introduces a war. The war introduces
generals. Each general has a childhood...

**Depth is measured from the synopsis.** Each entity has a generation
depth:

| Depth | What lives here | Example |
|-------|----------------|---------|
| 0 | Premise, synopsis | ashfall_premise, ashfall_synopsis |
| 1 | Manifest entities (extracted from synopsis) | kaelen, maren, voss, ashguard |
| 2 | Red links from depth-1 backstories | brennan, ember_trials, high_forge |
| 3 | Red links from depth-2 backstories | brennan's father, first_forge |

**`max_depth` is a variable.** Set it in the graph or via CLI:

```bash
yamlgraph graph run worldgen.yaml --var max_depth=2
```

Depth 1 = skeleton world (~15 pages). Good for testing.
Depth 2 = fleshed world (~30-50 pages). Good for a short story.
Depth 3 = deep world (~80-150 pages). A novel-scale bible.

**Implementation:** Each page gets a `_depth` metadata field. The
select_thin_entities step only selects entities at depth < max_depth.
Red link skeletons inherit `parent_depth + 1`.

---

## 5. Select Thin Entities (Deterministic)

The loop needs to decide which entities to deepen. This is NOT diagnosis —
it's a filter. The criteria are structural and measurable:

**Character is thin if:**
- `backstory` field is empty or < 50 words
- `triggers` list is empty
- `wants == needs` (no internal conflict)
- < 2 relationships

**Event is thin if:**
- `consequences` list is empty
- No location reference
- < 2 participants

**Faction is thin if:**
- < 2 members
- No inter-faction relationships

**Location is thin if:**
- `atmosphere` list is empty
- `sensory` list is empty
- Not referenced by any event

These are field presence/count checks. No LLM. No Python magic beyond
trivial dict access. Could even be expressed in YAML if YAMLGraph had
a filter node type.

The selection produces a list of `(entity_id, reason)` pairs. The
`reason` becomes part of the deepening prompt: "Kaelen has no triggers.
Expand his backstory to reveal what provokes him."

---

## 6. The Three Clean Jobs

The entire pipeline uses LLMs for exactly one job: **generate content.**

| Step | Who | Job |
|------|-----|-----|
| Select thin entities | Deterministic | Filter by field presence |
| Deepen entity | **LLM** | "Tell me Kaelen's backstory" |
| Extract red links | LLM (structured output) | "What new entities did you introduce?" |
| Validate red links | Deterministic (gate) | "Do declared entities match references?" |
| Create skeletons | **LLM** | "Generate a skeleton page for Brennan" |
| Validate skeletons | Deterministic (gate) | "Does the page pass ref_gate?" |
| Persist | Deterministic | Write YAML files |
| Check depth | Deterministic | depth < max_depth? |

Two LLM jobs: deepen and create skeletons. Both are narrow generation
tasks with typed schemas and gates. No LLM ever decides what to do —
the pipeline decides, the LLM fills in content.

---

## 7. What This Reuses

| Existing component | Used in |
|-------------------|---------|
| `canon.py` Pydantic models | Validation of all generated pages |
| `graph.yaml` draft → gate → fix → persist | Skeleton creation (Phase 1) |
| `ref_gate` | Validates references in deepened + skeleton pages |
| `write_data_file` | Persists pages to `canon/` |
| `retrieve_window` tensions | Could feed the deepening prompt |
| Premise + Synopsis types (FR-642) | Phase 1 cold start |

**New components needed:**

| Component | Type | Lines (est.) |
|-----------|------|-------------|
| `reload_canon` node | Python | ~15 (framework workaround) |
| `select_thin` node | Python | ~40 (field presence checks) |
| `deepen_entity` prompt | YAML | ~40 |
| `extract_manifest` prompt | YAML | ~30 (Phase 1: synopsis → names) |
| `generate_skeleton` prompt | YAML | ~30 |
| `worldgen.yaml` graph | YAML | ~60 |
| Depth tracking in page schema | Python (canon.py) | ~5 (add `_depth: int` field) |

---

## 8. Example Trace

Starting from 10 seed pages. `max_depth=2`.

**Iteration 1 — select thin entities:**
```
THIN: kaelen (character) — no triggers, backstory < 50 words
THIN: voss (character) — no triggers, backstory < 50 words
THIN: maren (character) — wants == needs
THIN: age_of_cinders (event) — no location, 0 consequences
THIN: ashguard (faction) — 1 member
```

**Iteration 1 — deepen (map, 5 LLM calls):**

Deepening kaelen produces:
- Updated page: triggers added, backstory filled (300 words)
- New entities: `brennan` (character, mentor), `ember_trials` (event),
  `high_forge` (location)

Deepening voss produces:
- Updated page: triggers added, backstory filled
- New entities: `old_quarter` (location, exile home), `guild_schism` (event)

Deepening age_of_cinders produces:
- Updated page: consequences added, location reference added
- New entities: `ashfall_ruins` (location)

...total: 5 deepened pages + ~8 red links

**Iteration 1 — create skeletons (map, 8 LLM calls):**

8 skeleton pages created at depth 2. All pass ref_gate. Persisted.

**Wiki state after iteration 1:** 10 → 18 pages.

**Iteration 2 — select thin entities:**

Now checks depth-2 entities (brennan, ember_trials, etc.):
```
THIN: brennan (character, depth 2) — depth == max_depth, SKIP
THIN: ember_trials (event, depth 2) — depth == max_depth, SKIP
```

All depth-2 entities are at max_depth. No candidates. **Loop terminates.**

**Final wiki:** 18 pages, depth 2. Run richness report as post-validation.

---

## 9. Relationship to Prior Plans

| Document | Status | What survives |
|----------|--------|---------------|
| `plan-novel-fandom-wiki-core.md` | Superseded | Phase 1 concept (manifest extraction) |
| `plan-world-generation-loop.md` | Superseded | Richness criteria as post-validation |
| FR-643 (analyst loop) | Rejected | `reload_canon` workaround, depth budget |
| FR-641 (LLM extraction) | Rejected | Nothing — correct rejection |

The analysts are dead. The diagnostic loop is dead. What remains:

- **Expansion pipeline** (cold start) — from the DM pattern
- **Deepening loop** (red-link-driven) — from the wiki growth insight
- **Richness checks** (post-validation) — from FR-643, repositioned
- **Depth budget** — new, replaces loop iteration count

---

## 10. Implementation Sequencing

**FR-643v2: Cold start + one deepening iteration (prove the pattern)**
- Synopsis → manifest → skeleton entities (Phase 1)
- Select thin → deepen → extract red links → create skeletons (one pass)
- Richness report (post-validation, no loop yet)
- Acceptance: starts from premise, produces ≥ 15 pages, all pass ref_gate

**FR-644: Full deepening loop with depth budget**
- `max_depth` variable, `_depth` field in pages
- Loop: select → deepen → red links → skeletons → reload → select
- Depth as loop terminator
- Acceptance: `max_depth=2` produces ≥ 25 pages from Ashfall premise

**FR-645: Deepen-in-place (edit, not replace)**
- Field-level merge: LLM output patches specific fields
- Preserves human edits to other fields
- `lane: static` pages untouched

---

## 11. Open Questions

1. **Backstory field.** Characters need a `backstory: str` field for the
   deepening prompt to target. Currently absent from `canon.py`. Add it
   in FR-643v2 or as a separate schema FR?

2. **Red link dedup across entities.** If deepening both Kaelen and Maren
   introduces "Brennan," do we get two skeleton Brennans? The gate should
   catch this (duplicate page id), but the pipeline needs to handle it —
   either merge or first-wins.

3. **Deepening prompt per type.** "Tell me Kaelen's backstory" is
   different from "tell me the consequences of the Ashfall." Different
   page types need different deepening prompts. One parameterized prompt
   with type-specific sections, or separate prompts? (Resolved in FR-643
   as: separate prompts.)

4. **How does the deepened page merge with the existing page?** If Kaelen
   has `wants: "vengeance"` (human-authored) and the deepening changes it
   to `wants: "justice"`, what wins? For FR-643v2: full replacement
   (honest about it). For FR-645: field-level merge with human priority.

---

## 12. Judgement

**Date:** 2026-07-01
**Verdict: CONDITIONAL — sound architecture, five issues to resolve.**

The insight chain is real. Three failed designs converged on one correct
pattern: expansion + red links + depth budget. The plan correctly
separates the three jobs (pipeline decides, LLM generates, gate
validates). The wiki growth analogy is precise and the architecture
follows from it naturally.

This is the strongest of the four designs. Grant authority with the
following corrections:

### 12a. The Example Trace Lies About the Seed Canon

The trace says "kaelen — no triggers, backstory < 50 words." But the
actual `canon/kaelen.yaml` has two triggers and a rich set of fields
(wants ≠ needs, arc_summary, driving_force, 2 relationships, 5
references). Most seed characters are already **not thin** by the
plan's own criteria.

The trace assumes a thinner seed than actually exists. This matters
because Phase 2 only deepens thin entities. If the seed is already rich,
Phase 2 has nothing to deepen and the loop ends immediately.

**Resolution:** Phase 1 (cold start from premise) is the real entry
point, not "start from the existing seed." The existing 10-page seed
was hand-authored as test data. When the pipeline runs from premise,
Phase 1 produces skeletons that ARE thin. The trace should reflect a
cold-start scenario, not the enriched seed.

Alternatively: the thin criteria need a "has backstory" check. The seed
characters are rich in motivation fields but have no backstory prose.
`backstory` doesn't exist in `canon.py` yet — the plan notes this in
Open Question 1 but doesn't resolve it. **Add `backstory: str = ""`
to Character in canon.py as part of FR-643v2.**

### 12b. Depth Budget vs. Thinness Termination: Two Competing Stops

The loop has two termination conditions:
1. `max_depth reached` (depth budget)
2. `no thin entities at depth < max_depth` (nothing to deepen)

These interact in unexpected ways. At `max_depth=2`:
- Depth-1 entities get deepened (good)
- Red links from depth-1 become depth-2 skeletons (good)
- Depth-2 skeletons are thin but at `max_depth` → never deepened
- Loop ends with thin depth-2 entities

The world has well-developed core characters but hollow supporting
cast. This is arguably correct — supporting characters don't need
full backstories — but the plan doesn't acknowledge the tradeoff.

**Resolution:** Document this explicitly. Depth budget is authorial
intent: "I want depth-1 characters fully developed and depth-2 as
named placeholders." The user controls this via `max_depth`. The
richness report (Phase 3) shows what remains thin so the user can
increase depth if they want.

### 12c. Red Link Dedup Is Underspecified

Open Question 2 identifies the problem: deepening Kaelen and Maren
might both introduce "Brennan." The plan says "the gate should catch
this" but doesn't specify how.

Two deepening calls run in parallel (map node). Both produce a
`new_entities` list with `{id: brennan, type: character}`. Both pass
their individual gates. Then `create_skeletons` runs on the merged
list and tries to create two `canon/brennan.yaml` files.

**Resolution:** The merge step between "deepen × N" and "create
skeletons × N" must deduplicate `new_entities` by `id`. This is a
deterministic set operation: `seen_ids = existing_pages ∪ already_queued;
skip if id in seen_ids`. Add a `collect_red_links` python node
between deepen and create_skeletons.

### 12d. Phase 1 Is Hand-Waved

"Every step uses the existing `draft → gate → fix → persist` pipeline
from `graph.yaml`. No new machinery needed for Phase 1."

This is wrong. `graph.yaml` takes a single `input: str` describing what
to draft. Phase 1 needs:
- A synopsis generation prompt (new)
- A manifest extraction prompt (new)
- A map node over manifest entries feeding graph.yaml as subgraph

The plan lists `extract_manifest` prompt in the new components table
but doesn't include a synopsis generation prompt or the Phase 1 graph
definition. Phase 1 is at least 2 new prompts + 1 new graph.

**Resolution:** FR-643v2 should skip Phase 1 entirely. Use the existing
hand-authored seed canon (premise + synopsis + 10 pages). Phase 1 is
a separate FR. The hypothesis to prove is: "does deepening + red links
grow a wiki?" Not: "can we cold-start from a premise?" Test one thing.

### 12e. `select_thin` Is Still Python Magic

40 lines of Python checking field presence per type. The plan
acknowledges this: "Could even be expressed in YAML if YAMLGraph had
a filter node type." But it doesn't have one, so we're back to a
python node with type-specific dict access.

This is less magic than FR-643's 85 lines across 3 nodes. But
`select_thin` encodes domain knowledge (what makes a character thin)
in Python, not in YAML or in a prompt. When the schema changes (add
`backstory` field), the python node must change too.

**Resolution:** Acceptable for now. The thin criteria are structural
(field emptiness, list length), not semantic. A 40-line python node
with clear per-type checks is honest code, not magic. Document the
coupling to `canon.py` schema — when a field is added to the model,
the thin criteria should be updated.

### 12f. Summary

| Issue | Severity | Resolution |
|-------|----------|------------|
| Trace lies about seed | Medium | FR-643v2 starts from existing seed, add `backstory` field |
| Two competing stops | Low | Document the depth-vs-thinness tradeoff explicitly |
| Red link dedup | Medium | Add `collect_red_links` dedup node |
| Phase 1 hand-waved | Medium | Skip Phase 1 in FR-643v2, separate FR |
| select_thin is Python | Low | Acceptable, document schema coupling |

**With these five corrections, the plan is sound. Draft FR-643v2
covering Phase 2 only (deepening + red links on existing seed),
with backstory field, collect_red_links dedup, and explicit depth
termination semantics.**
