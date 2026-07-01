# Plan: World Generation Loop — Analytical Worldbuilding

**Date:** 2026-07-01
**Context:** FR-637/640/642 (schema), FR-638 (pathfinder), FR-639 (prose+close), E2E run results
**Supersedes:** Phase 2 (bootstrap pipeline) in `plan-novel-fandom-wiki-core.md`

## The Insight

World generation is not extraction. It's **analytical worldbuilding** — a loop
of judges that examine the current wiki, identify gaps, generate tasks, execute
them through the existing gated pipeline, and re-examine. The pathfinder is the
final quality test: if it can find dramatic paths, the world is rich enough.

The existing codebase has the building blocks:
- Typed wiki pages with Pydantic validation (FR-637/640/642)
- Gated page generation: draft → ref_gate → fix → persist (graph.yaml)
- Tension extraction from character fields (retrieve_window)
- Plot pathfinder that traverses tensions (find_path.yaml)

What's missing: the **analytical layer** that examines the wiki as a whole and
says "this world needs more events between the Ashfall and now" or "Voss has
no trigger for when someone respects his craft."

---

## 1. The Loop

```
premise → synopsis → initial extraction (manifest + per-page generation)
                           ↓
                    ┌──────────────┐
                    │  WIKI STATE  │  (canon/*.yaml — the current world)
                    └──────┬───────┘
                           ↓
              ┌────────────────────────────┐
              │   ANALYZE (parallel)       │
              │                            │
              │   event_analyst            │
              │   rule_analyst             │
              │   character_analyst        │
              │   faction_analyst          │
              │   location_analyst         │
              │   coherence_analyst        │
              │                            │
              └────────────┬───────────────┘
                           ↓
              ┌────────────────────────────┐
              │   MERGE + PRIORITIZE       │
              │                            │
              │   Deduplicate tasks        │
              │   Rank by impact           │
              │   Cap at budget (N tasks)  │
              │                            │
              └────────────┬───────────────┘
                           ↓
                    task_list empty?
                    ├─ yes → DONE (world is rich enough)
                    │
                    ├─ no ↓
                    │
              ┌────────────────────────────┐
              │   GENERATE (per task)      │
              │                            │
              │   task → draft page (LLM)  │
              │        → ref_gate          │
              │        → fix (if needed)   │
              │        → persist to canon  │
              │                            │
              └────────────┬───────────────┘
                           ↓
                    loop budget exhausted?
                    ├─ yes → STOP (report remaining tasks)
                    ├─ no  → back to ANALYZE
                    └──────────────────────┘
```

The loop terminates when analysts find no more gaps OR when the loop budget
(total iterations or total pages generated) is exhausted.

---

## 2. The Analysts

Each analyst reads the full current canon + synopsis and produces a typed task
list. They are judges, not generators — they identify what's missing, thin,
or inconsistent.

### 2a. Event Analyst

**Question:** Are the world's events vivid, causally linked, and dense enough
to support drama?

**Checks:**
- **Temporal density:** Are there meaningful intermediate events between major
  timeline markers? "200 years with one event" is a gap.
- **Causal chains:** Does each event have consequences that connect to other
  events or character arcs? An event with no consequences is decorative.
- **Participant coverage:** Do all major characters participate in at least
  one event? A character with no events is disconnected.
- **Vividness:** Does each event have concrete consequences, not vague
  descriptions? "The world changed" is thin; "The forge fell silent and
  the dragonsteel stores were sealed" is vivid.

**Task types produced:**
- `add_event`: "Add an event between Ashfall and Age of Cinders showing how
  the Ashguard diminished" (with suggested participants, window, consequences)
- `deepen_event`: "Event age_of_cinders needs more specific consequences —
  what exactly did each faction lose?"
- `split_event`: "The Ashfall is too monolithic — split into the trigger event,
  the cataclysm itself, and the aftermath"

### 2b. Rule Analyst

**Question:** Are the world's constraints explicit, consequential, and
dramatically useful?

**Checks:**
- **Implied rules:** The synopsis mentions constraints that aren't codified as
  Rule pages. "No faction may relight the forge alone" is implied by the
  narrative but not stated as a rule.
- **Consequence clarity:** Each rule should state what happens when it's broken.
  A rule without consequences is a suggestion, not a constraint.
- **Domain coverage:** Are there rules for all relevant domains (magic_system,
  social_rule, physical_constraint)? A world with magic but no magic rules is
  underspecified.
- **Dramatic utility:** Do rules create tension? A rule that no character would
  ever want to break is inert. The best rules are ones characters NEED to break
  to get what they want.

**Task types produced:**
- `add_rule`: "Add a rule: 'Any who touch the Emberbrand without dragonsteel
  gauntlets burn' (domain: magic_system)"
- `deepen_rule`: "ashfall_pact needs to specify what 'forfeits its claim' means
  in practice"

### 2c. Character Analyst

**Question:** Are the characters psychologically believable, dramatically
functional, and relationally complete?

**Checks:**
- **Motivation triad completeness:** Every character should have wants, needs,
  and fears. Wants≠needs creates internal conflict (the engine of drama).
  A character with wants=needs has no arc.
- **Trigger coverage:** Characters need at least one trigger — a stimulus that
  provokes a predictable emotional response. Triggers make characters reactive
  and scenes playable.
- **Relationship symmetry:** If A has a relationship to B, does B have a
  relationship to A? Asymmetry is sometimes intentional (unrequited), but
  absence is usually a gap.
- **Arc potential:** Does the arc_summary describe a transformation?
  "warrior → warrior" is not an arc. "guilt-driven avenger → reluctant
  forgiver" is.
- **Role balance:** Is there at least one protagonist, one antagonist, and
  one character whose allegiance is ambiguous? Three protagonists don't
  generate conflict.
- **Population:** Are there enough characters to populate the events and
  factions? A faction with one member is a person, not a faction.

**Task types produced:**
- `add_character`: "The Ashguard has only one member (kaelen). Add a second
  Ashguard character who disagrees with Kaelen's methods."
- `deepen_character`: "Voss has no triggers. Add triggers: one for when his
  craft is dismissed, one for when it's respected."
- `add_relationship`: "Maren and Voss are both Emberwrights but have no direct
  relationship. What is their dynamic?"

### 2d. Faction Analyst

**Question:** Are the factions distinct, politically coherent, and in
meaningful tension with each other?

**Checks:**
- **Distinctiveness:** Each faction should have a clear value system that
  conflicts with at least one other faction. Two factions that want the same
  thing the same way are redundant.
- **Power dynamics:** What does each faction control? Land, knowledge, weapons,
  legitimacy? Asymmetric power creates interesting politics.
- **Membership depth:** Each faction should have ≥2 members with different
  roles (leader, dissenter, loyalist). Single-member factions are aliases.
- **Inter-faction edges:** Are there explicit relationships between factions
  (alliance, rivalry, dependency, hostility)?

**Task types produced:**
- `add_character`: "Emberwrights need a dissenter who opposes Voss's ambition"
- `deepen_faction`: "Ashguard needs a description of what they control and
  what they've lost"
- `add_rule`: "What governs trade between Ashguard and Emberwrights?"

### 2e. Location Analyst

**Question:** Where does this world happen? Is geography meaningful?

**Checks:**
- **Event grounding:** Every major event should happen somewhere. An event
  without a location is floating.
- **Atmospheric distinction:** Each location should feel different (atmosphere,
  sensory details). Two locations that feel the same can merge.
- **Strategic significance:** Locations should matter — they control resources,
  restrict movement, or hold symbolic weight. A location that's just a name
  is set dressing.
- **Coverage:** The synopsis implies places that don't exist as Location pages.

**Task types produced:**
- `add_location`: "The synopsis mentions 'the old forge' — create a Location
  page with atmosphere, sensory details, and strategic significance"
- `deepen_location`: "Ashguard headquarters implied but not described"

### 2f. Coherence Analyst

**Question:** Does the world hold together as a system?

This is the cross-cutting analyst that checks what the others miss:

**Checks:**
- **Reference graph connectivity:** Are there orphan pages (referenced by
  nothing)? Are there islands (clusters with no cross-references)?
- **Timeline consistency:** Do events form a coherent timeline? Do valid_from
  and valid_to values make sense together?
- **Relationship transitivity:** If A is B's ally and B is C's enemy, what is
  A's relationship to C? Unstated transitive relationships are gaps.
- **Synopsis fidelity:** Does the wiki cover all the entities and events
  mentioned in the synopsis? Missing coverage means the synopsis is ahead of
  the wiki.
- **Naming consistency:** Are entity references consistent? Does "House Voss"
  appear sometimes and "voss" other times?

**Task types produced:**
- `add_reference`: "kaelen references emberbrand_rule but emberbrand_rule
  doesn't reference kaelen back"
- `add_relationship`: "Maren's relationship to Voss is 'caution' but Voss has
  no relationship to Maren"
- `add_event`: "Synopsis mentions the original Ashfall but no event page
  exists for it"

---

## 3. The Task Type Taxonomy

All analyst outputs produce tasks from a closed set:

| Task Type | Description | Target |
|-----------|-------------|--------|
| `add_page` | Create a new page (character, event, faction, location, rule) | New page |
| `deepen_page` | Enrich an existing page with more/better fields | Existing page |
| `add_relationship` | Add a typed relationship between two entities | Existing page |
| `add_reference` | Add a cross-reference | Existing page |
| `split_event` | Break one event into sub-events | Existing event → N new events |

Each task carries:
- `type`: from the table above
- `page_type`: character / event / faction / location / rule
- `target_id`: existing page id (for deepen/add_relationship/add_reference)
- `description`: what to do, in natural language
- `analyst`: which analyst produced this task
- `priority`: high / medium / low (analyst's assessment)
- `context`: relevant canon excerpts the generator should see

---

## 4. The Generation Step

Each task from the merged list feeds into the existing gated pipeline:

**For `add_page`:**
```
task.description + synopsis + relevant canon excerpts
  → draft page (LLM, using the existing draft_page prompt adapted per type)
  → ref_gate (existing — checks orphan refs + lane immutability)
  → fix if needed (existing fix_refs prompt)
  → persist to canon/
```

**For `deepen_page`:**
```
task.description + current page + synopsis
  → revise page (LLM — same page type, same id, enriched fields)
  → ref_gate
  → fix if needed
  → persist (overwrites existing dynamic page; blocked for static pages)
```

**For `add_relationship` / `add_reference`:**
```
Deterministic — no LLM needed.
Read target page → add relationship/reference → validate → persist.
```

**For `split_event`:**
```
task.description + current event + synopsis
  → generate N sub-events (LLM, map node)
  → ref_gate each
  → fix if needed
  → persist all + update original event's references
```

---

## 5. Richness Criteria — When Is the World "Enough"?

The loop needs termination criteria beyond "analysts found nothing." These are
the **world invariants** — the equivalent of DM's 4 narrative invariants, but
for a world rather than a plot:

| Invariant | Check | Threshold |
|-----------|-------|-----------|
| **Character depth** | Every character has wants ≠ needs | 100% of characters |
| **Trigger coverage** | Every character has ≥ 1 trigger | 100% of characters |
| **Relationship symmetry** | If A→B exists, B→A exists | ≥ 80% of edges |
| **Faction membership** | Every faction has ≥ 2 members | 100% of factions |
| **Event density** | ≥ 1 event per major timeline span | No >100yr gaps |
| **Rule coverage** | ≥ 1 rule per domain used in the world | All active domains |
| **Location grounding** | Every event has ≥ 1 location reference | ≥ 80% of events |
| **Synopsis fidelity** | Every entity named in synopsis exists as a page | 100% |
| **Reference connectivity** | No orphan pages (pages with 0 inbound refs) | 0 orphans |
| **Pathfinder viability** | Pathfinder finds ≥ 3 distinct paths | ≥ 3 paths |

Some of these are deterministic checks (the wiki linter from Phase 3). Others
require LLM judgment (event vividness, arc potential). The deterministic ones
gate the loop; the LLM ones guide the analysts.

---

## 6. YAMLGraph Architecture

### Option A: Single orchestrator graph with analyst subgraphs

```yaml
# worldgen.yaml
nodes:
  analyze:
    type: map
    over: "{state.analyst_types}"
    as: analyst
    collect: analyses
    node:
      type: llm
      prompt: world_analyst    # Parameterized by analyst type
      state_key: analysis

  merge_tasks:
    type: python
    tool: merge_and_prioritize  # Dedup, rank, cap at budget

  generate_pages:
    type: map
    over: "{state.task_list}"
    as: task
    max_items: 10
    collect: generated
    node:
      type: llm
      prompt: generate_from_task
      state_key: page

  gate_pages:
    type: python
    tool: batch_ref_gate

  check_richness:
    type: python
    tool: richness_check       # Deterministic invariant checks

edges:
  START → analyze → merge_tasks → generate_pages → gate_pages → check_richness
  check_richness → END           (rich_enough == true OR budget_exhausted)
  check_richness → analyze       (more work needed)

loop_limits:
  analyze: 5                    # Max 5 worldgen iterations
```

### Option B: Separate analyst graphs, session-orchestrated

Each analyst is its own graph (like DM's character.yaml, synopsis.yaml).
A session script or parent graph runs them sequentially.

**Tradeoff:** Option A is self-contained. Option B is more testable per-analyst
but needs an orchestrator. Given that the DM uses session orchestration for a
similar pattern, Option B might be more natural — but Option A is what
YAMLGraph does natively with map nodes.

---

## 7. What This Replaces

The original 5-phase plan becomes:

| Old Phase | New Phase | Change |
|-----------|-----------|--------|
| Phase 1: Wiki core types | **Done** (FR-642) | — |
| Phase 2: Bootstrap pipeline | **Phase 2a: Initial extraction** | Synopsis → manifest → per-page gen (simpler, one pass) |
| — | **Phase 2b: World generation loop** | The analytical loop described here |
| Phase 3: Wiki linter | **Folded into 2b** | Richness checks are the deterministic analysts |
| Phase 4: E2E run | **Phase 3: E2E validation** | premise → synopsis → worldgen → pathfind → draft → close |
| Phase 5: Formal invariants | **Folded into 2b** | World invariants table above |

The wiki linter isn't a separate phase — it's the deterministic half of the
analysis step. The formal invariants aren't future work — they're the
termination criteria.

---

## 8. Relationship to DM's Architecture

| DM Pattern | Novel Fandom Equivalent |
|------------|------------------------|
| synopsis.yaml | Same — premise → full-disclosure synopsis |
| character_roster.yaml | Manifest extraction (names + types + 1-sentence) |
| character.yaml × N | Per-task page generation through gate → fix |
| plot_plan.yaml (validate → repair loop) | World generation loop (analyze → generate → check) |
| 4 narrative invariants | World invariants (character depth, event density, etc.) |
| floodmark fixtures | Hand-authored canon (existing 10 seed pages) as test baseline |

The DM validates a **plot** against invariants. Novel fandom validates a
**world** against invariants. Same pattern, different granularity.

---

## 9. Risk: Analyst Hallucination

The analysts are LLMs judging completeness. They might:
- Invent gaps that don't exist ("the world needs a river" when the story is
  about forges, not geography)
- Miss real gaps (fails to notice Maren has no trigger for her past betrayal)
- Produce redundant tasks (three analysts all ask for the same missing event)

**Mitigations:**
- **Budget cap:** Max N tasks per iteration, max M iterations. Can't spiral.
- **Dedup in merge:** Tasks referencing the same page/gap are merged.
- **Synopsis anchor:** Every analyst must cite what in the synopsis motivates
  the gap. "I think the world needs a river" is rejected without a synopsis
  citation. "The synopsis mentions 'the old forge lies dormant' but no
  Location page exists for the forge" is grounded.
- **Deterministic checks first:** Run the richness invariants before the LLM
  analysts. If all deterministic checks pass, skip the LLM analysts entirely.
  Only call LLMs when the quantitative checks reveal gaps.
- **Human review gate (optional):** After merge, present the task list for
  approval before generating. Matches the DM's accept/reject pattern.

---

## 10. Resolved Questions

1. **Analyst prompt design:** Separate prompts per analyst. Each analyst has
   its own YAML prompt file (e.g., `event_analyst.yaml`, `rule_analyst.yaml`).
   Different concerns need different system instructions, output schemas, and
   few-shot examples. Parameterized prompts collapse distinctions that matter.

2. **Deepen vs. regenerate:** Edit in place. Analysts produce targeted edits
   to existing pages, not replacements. This preserves manual refinements and
   human curation. `lane: static` pages remain untouched (by design).
   `lane: dynamic` pages receive surgical field-level updates.

3. **Analyst ordering:** Parallel execution. All analysts run simultaneously
   (map node). Conflicting or redundant tasks are resolved in a post-processing
   prioritization step: deduplicate, rank by synopsis relevance, resolve
   conflicts where two analysts propose contradictory edits to the same page.
   This is cheaper than sequential ordering and avoids artificial dependencies
   between analysts.

4. **Pathfinder as quality gate:** Premature. The pathfinder may survive as a
   concept, but this will be evaluated when there is a full world wiki with
   visualization. Until then, the richness invariants (Section 5) are the
   loop termination criteria.

---

## 11. Judgement

**Date:** 2026-07-01
**Verdict: CONDITIONAL — split required before authority is granted.**

The insight is correct. The pain is real. The E2E pathfinder run proved
the world is too thin — the LLM fills gaps the wiki should contain. A
worldbuilding loop before pathfinding is the right architectural move.

But the plan has one fundamental blocker, two internal contradictions,
and is over-designed for the current evidence.

### 11a. Blocker: `data_files` Does Not Reload

The entire loop depends on analysts reading the **updated** wiki each
iteration. But `data_files` loads at **compile time**, not per execution.
Pages written by `write_data_file` in iteration 1 are invisible to
analysts in iteration 2.

**Evidence:** `yamlgraph/data_loader.py` line 93–140.
`load_data_files()` is called once in `graph_loader.py` line 188
during graph initialization. The glob is resolved once, results merged
into initial state.

**Required resolution:** A python node must re-read `canon/*.yaml` at
the start of each loop iteration and inject the current wiki into state.
This replaces the declarative `data_files` path with explicit runtime
loading. The architects of the loop must account for this in the graph
design — the existing `data_files` mechanism cannot serve the loop.

### 11b. Contradiction: Edit-in-Place vs. Regeneration

Resolved question #2 says "edit in place — surgical field-level updates."
But Section 4 describes `deepen_page` as:

```
task.description + current page + synopsis
  → revise page (LLM — same page type, same id, enriched fields)
```

This is **not** surgical editing. It sends the entire page to an LLM and
asks for a revised version. That's regeneration wearing an edit costume.
True edit-in-place would need a diff/patch mechanism or field-level
merge logic.

**Required resolution:** Either:
- Accept that "deepen" means "regenerate the page with richer fields"
  (honest naming, simpler implementation), or
- Build a field-level merge node that takes the LLM's output and patches
  only the changed fields into the existing page (preserves manual edits,
  more complex)

The first option is correct for MVP. Call it what it is.

### 11c. Contradiction: Pathfinder in Invariants Table

Richness invariant #10 (Section 5): "Pathfinder viability — ≥ 3 paths."
Resolved question #4 (Section 10): "Premature. Deferred until
visualization exists."

These contradict. The invariants table is the termination criteria.
If pathfinder viability is premature, remove it from the table.

### 11d. Underspecified: Merge + Prioritize

"Deduplicate tasks, rank by impact, cap at budget." Six parallel analysts
produce tasks with natural-language descriptions. Two analysts may
describe the same gap differently. Deduplication of natural-language
tasks is itself an LLM problem — not a set intersection.

Options:
- Accept duplicates and let the gate/generation step handle conflicts
  (simpler, wastes some budget)
- Add an LLM merge step (another hallucination vector, adds cost)
- Constrain task output format so dedup is deterministic (e.g., require
  `target_id` and `field` — two tasks touching the same field on the
  same page are duplicates)

The third option is correct: make dedup a structural operation, not a
semantic one.

### 11e. Missing: Phase 2a Bootstrap

The plan describes the loop (Phase 2b) in 450 lines but leaves Phase 2a
("premise → synopsis → initial extraction") as a one-sentence hand-wave.
The bootstrap is the cold-start problem: you can't analyze a wiki that
doesn't exist. The manifest extraction (names + types + 1-sentence per
page) and initial per-page generation must be defined before the loop
has anything to analyze.

### 11f. Missing: Cost Model

One loop iteration: 6 analyst LLM calls + up to 10 generation LLM calls
+ gate calls = 16+ LLM calls. Five iterations = 80+ calls. At
~$0.01–0.03 per call (Sonnet), that's $0.80–$2.40 per full worldgen.
Acceptable for a real use case; expensive for a demo example.

The plan should state the expected cost per iteration and per full run.

### 11g. Over-Designed: Six Analysts Before One Is Proven

The plan specifies 6 specialized analysts with distinct prompts, check
lists, and task types. But the core hypothesis is untested: **can an LLM
analyze a wiki, identify gaps, and produce executable tasks that survive
the gate?**

Before building 6 analysts: prove the loop with **one generic analyst**
that reads the entire wiki + synopsis and produces a task list. If one
analyst produces useful tasks that the gate accepts, specialize. If it
doesn't, six won't help — the problem is in the loop, not the analyst.

### 11h. Recommendation: Split Into Two FRs

**FR-A: Single-analyst worldgen loop (prove the loop)**
- One analyst prompt (generic world analyst)
- Python node to reload canon at loop start (solves the `data_files` blocker)
- Deterministic richness checks as termination criteria (drop pathfinder invariant)
- `deepen_page` = regeneration (honest naming)
- Structural dedup by `target_id` + `field`
- Budget cap: 3 iterations, 5 tasks per iteration
- Acceptance: run on Ashfall seed canon, loop produces ≥ 3 new pages that pass the gate

**FR-B: Specialist analysts (scale what works)**
- Six separate analyst prompts
- Phase 2a bootstrap (manifest extraction)
- Cost model
- Visualization of wiki growth

This follows the Scripture: "Start with bare bones implementation and
incrementally add functionality."
