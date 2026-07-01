# FR-643: novel_fandom — Single-Analyst Worldgen Loop

**Priority:** HIGH
**Type:** Feature (example)
**Status:** Rejected
**Effort:** 2 days
**Requested:** 2026-07-01
**Depends on:** FR-637, FR-640, FR-642

## Summary

Add a worldgen loop graph that reads the current canon wiki, analyzes it
for gaps via a single generic analyst prompt, produces typed tasks, generates
pages through the existing gated pipeline, and re-analyzes until richness
criteria pass or a budget cap is hit.

This proves the core hypothesis: **can an LLM analyze a fiction wiki, identify
structural gaps, and produce executable tasks that survive the ref_gate?**

## Value Statement

The E2E pathfinder run (FR-638) proved the world is too thin — the LLM invents
entities that should exist in the wiki but don't. A worldgen loop fills the
wiki systematically before pathfinding, replacing "hope the LLM gets it right"
with "ensure the world is rich enough."

## Problem

1. **The world is too thin.** The Ashfall canon has 10 seed pages. The
   pathfinder generates beats referencing entities that should exist but
   don't — the forge, intermediate events, character triggers. The LLM fills
   gaps with hallucination instead of traversing a rich wiki.

2. **No analytical layer.** The existing pipeline generates pages one at a
   time via `graph.yaml` (draft → gate → fix → persist). There's no step
   that examines the wiki as a whole and says "this world needs more events
   between the Ashfall and now" or "Voss has no triggers."

3. **The bootstrap gap.** The original Phase 2 plan proposed a manifest
   extraction pipeline, but that's a one-shot process. Real worldbuilding
   is iterative: generate → examine → fill gaps → re-examine.

## Design

### Architecture

```
┌──────────────────────────────────────────────────────┐
│  worldgen.yaml (outer loop)                          │
│                                                      │
│  reload_canon ──→ analyze ──→ merge ──→ check_done   │
│       ↑                                    │         │
│       │              ← NO ─────────────────┤         │
│       │                                    │         │
│       │         generate_pages ←───────────┘         │
│       │              │                               │
│       └──────────────┘            YES → END          │
└──────────────────────────────────────────────────────┘
```

### The data_files Reload Problem

`data_files` loads at compile time (once). Pages generated in iteration 1
are invisible in iteration 2. **Solution:** a `reload_canon` python node
at the loop start that reads `canon/*.yaml` at runtime and injects the
current wiki into state.

```python
# nodes/reload_canon.py
def reload_canon(state: dict) -> dict:
    """Re-read all canon/*.yaml at runtime for the current loop iteration."""
    from pathlib import Path
    import yaml

    canon_dir = Path(__file__).parent.parent / "canon"
    pages = {}
    for f in sorted(canon_dir.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
            if data and isinstance(data, dict) and "id" in data:
                pages[data["id"]] = data
    return {"canon_pages": pages, "canon_count": len(pages)}
```

### The Analyst

One generic prompt — not six specialists. Proves the hypothesis before
specializing.

```yaml
# prompts/world_analyst.yaml
system: |
  You are a fiction worldbuilding analyst. You examine a wiki of canon pages
  and a synopsis, then identify structural gaps — missing entities, thin
  descriptions, absent relationships, timeline voids.

  For each gap, produce a typed task. Every task must cite what in the
  synopsis motivates the gap.

  Task types (closed set):
  - add_page: Create a new page (character, event, faction, location, rule)
  - deepen_page: Regenerate an existing page with richer fields
  - add_relationship: Add a relationship between two entities
  - add_reference: Add a cross-reference

  Constraints:
  - Do NOT invent needs the synopsis doesn't imply
  - Do NOT propose tasks for lane:static pages
  - Maximum {max_tasks} tasks per analysis
  - Prioritize: structural gaps > depth > polish

user: |
  ## Synopsis
  {{ synopsis_text }}

  ## Current Canon ({{ canon_count }} pages)
  {% for id, page in canon_pages.items() %}
  ### {{ id }} ({{ page.type }})
  {{ page | tojson(indent=2) }}
  {% endfor %}

  ## Richness Report
  {{ richness_report }}

  Analyze this world. What structural gaps exist? Produce a task list.

schema:
  name: WorldAnalysis
  fields:
    tasks:
      type: list[AnalystTask]
      description: "Ordered list of worldbuilding tasks, highest priority first"
    summary:
      type: str
      description: "One paragraph summary of the world's current state and gaps"

  nested:
    AnalystTask:
      task_type:
        type: str
        description: "One of: add_page, deepen_page, add_relationship, add_reference"
      page_type:
        type: str
        description: "Target page type: character, event, faction, location, rule"
      target_id:
        type: str
        description: "Existing page id (for deepen/relationship/reference) or proposed new id"
      field:
        type: str
        description: "Specific field to enrich (for deepen_page) or empty for add_page"
      description:
        type: str
        description: "What to do, in natural language"
      synopsis_citation:
        type: str
        description: "The phrase from the synopsis that motivates this gap"
      priority:
        type: str
        description: "high, medium, or low"
```

### Merge + Prioritize (Deterministic)

Dedup is structural, not semantic: two tasks with the same `target_id` +
`field` are duplicates. Keep the higher-priority one.

```python
# nodes/merge_tasks.py
def merge_tasks(state: dict) -> dict:
    """Deduplicate tasks by (target_id, field), keep highest priority."""
    tasks = state.get("analysis", {}).get("tasks", [])
    budget = state.get("task_budget", 5)

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    seen = {}
    for task in tasks:
        key = (task.get("target_id", ""), task.get("field", ""))
        existing = seen.get(key)
        if existing is None or priority_rank.get(
            task.get("priority", "low"), 2
        ) < priority_rank.get(existing.get("priority", "low"), 2):
            seen[key] = task

    merged = sorted(seen.values(), key=lambda t: priority_rank.get(t.get("priority", "low"), 2))
    return {"task_list": merged[:budget], "tasks_total": len(tasks), "tasks_after_dedup": len(seen)}
```

### Richness Checks (Deterministic, Loop Termination)

```python
# nodes/richness_check.py
def richness_check(state: dict) -> dict:
    """Deterministic world invariant checks. Returns report + done flag."""
    pages = state.get("canon_pages", {})
    checks = {}

    characters = {k: v for k, v in pages.items() if v.get("type") == "character"}
    events = {k: v for k, v in pages.items() if v.get("type") == "event"}
    factions = {k: v for k, v in pages.items() if v.get("type") == "faction"}
    rules = {k: v for k, v in pages.items() if v.get("type") == "rule"}
    locations = {k: v for k, v in pages.items() if v.get("type") == "location"}

    # Character depth: wants != needs
    depth_pass = all(
        c.get("wants") and c.get("needs") and c["wants"] != c["needs"]
        for c in characters.values()
    )
    checks["character_depth"] = depth_pass

    # Trigger coverage
    checks["trigger_coverage"] = all(
        len(c.get("triggers", [])) >= 1 for c in characters.values()
    )

    # Faction membership >= 2
    checks["faction_membership"] = all(
        len(f.get("members", [])) >= 2 for f in factions.values()
    )

    # Synopsis fidelity (all referenced entities exist)
    all_ids = set(pages.keys())
    all_refs = set()
    for p in pages.values():
        all_refs.update(p.get("references", []))
    checks["reference_integrity"] = all_refs.issubset(all_ids)

    # No orphan pages (pages with 0 inbound refs, excluding premise)
    inbound = {pid: 0 for pid in all_ids}
    for p in pages.values():
        for ref in p.get("references", []):
            if ref in inbound:
                inbound[ref] += 1
    orphans = [pid for pid, count in inbound.items()
               if count == 0 and pages[pid].get("type") != "premise"]
    checks["no_orphans"] = len(orphans) == 0

    # Location grounding: events have location references
    if events:
        grounded = sum(
            1 for e in events.values()
            if any(pages.get(r, {}).get("type") == "location" for r in e.get("references", []))
        )
        checks["location_grounding"] = grounded / len(events) >= 0.8
    else:
        checks["location_grounding"] = False

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    done = passed == total

    report_lines = [f"{'PASS' if v else 'FAIL'} {k}" for k, v in checks.items()]
    report = f"Richness: {passed}/{total}\n" + "\n".join(report_lines)

    return {
        "richness_report": report,
        "richness_passed": passed,
        "richness_total": total,
        "rich_enough": done,
        "orphan_pages": orphans,
    }
```

### Graph Definition

```yaml
# worldgen.yaml
version: "1.0"
name: novel-fandom-worldgen
description: Analytical worldgen loop — analyze wiki, generate missing pages, repeat
prompts_relative: true
prompts_dir: prompts

data_files:
  canon: "canon/*.yaml"

state:
  canon_pages: dict
  canon_count: int
  synopsis_text: str
  richness_report: str
  rich_enough: bool
  analysis: dict
  task_list: list
  task_budget: int
  generated_pages: list
  iteration: int

variables:
  task_budget: 5
  max_tasks: 5

tools:
  reload_canon:
    type: python
    path: nodes/reload_canon.py
    function: reload_canon
  richness_check:
    type: python
    path: nodes/richness_check.py
    function: richness_check
  merge_tasks:
    type: python
    path: nodes/merge_tasks.py
    function: merge_tasks
  save_page:
    type: write_data_file
    state_key: _written

nodes:
  reload:
    type: python
    tool: reload_canon

  check_richness:
    type: python
    tool: richness_check

  analyze:
    type: llm
    prompt: world_analyst
    state_key: analysis
    temperature: 0.3

  merge:
    type: python
    tool: merge_tasks

  generate_pages:
    type: map
    over: "{state.task_list}"
    as: task
    max_items: 5
    collect: generated_pages
    node:
      type: llm
      prompt: generate_from_task
      state_key: page

  persist_pages:
    type: map
    over: "{state.generated_pages}"
    as: page
    max_items: 5
    collect: _written_paths
    node:
      type: python
      tool: save_page
      variables:
        path: "canon/{state.page.id}.yaml"
        data: "{state.page}"

edges:
  - from: START
    to: reload

  - from: reload
    to: check_richness

  - from: check_richness
    to: analyze
    condition: rich_enough == false

  - from: check_richness
    to: END
    condition: rich_enough == true

  - from: analyze
    to: merge

  - from: merge
    to: generate_pages

  - from: generate_pages
    to: persist_pages

  - from: persist_pages
    to: reload

loop_limits:
  reload: 4
  analyze: 3
```

### Task-to-Page Generation Prompt

```yaml
# prompts/generate_from_task.yaml
system: |
  You are a fiction worldbuilding generator. Given a task describing a gap
  in a fiction wiki, generate the content to fill it.

  Output a valid canon page matching the requested page_type schema.
  All references must point to existing page ids provided in context.
  Set lane: dynamic on all generated pages.

user: |
  ## Task
  Type: {{ task.task_type }}
  Page type: {{ task.page_type }}
  Target: {{ task.target_id }}
  Field: {{ task.field }}
  Description: {{ task.description }}
  Synopsis citation: {{ task.synopsis_citation }}

  ## Synopsis
  {{ synopsis_text }}

  ## Existing Canon Pages (ids)
  {% for id in canon_pages.keys() %}
  - {{ id }} ({{ canon_pages[id].type }})
  {% endfor %}

  Generate the page content.

schema:
  name: GeneratedPage
  fields:
    id:
      type: str
      description: "Page id (snake_case, unique)"
    type:
      type: str
      description: "Page type matching task.page_type"
    lane:
      type: str
      description: "Always 'dynamic'"
    content:
      type: dict
      description: "Full page content matching the page type schema"
```

## Scope Exclusions

- **No specialist analysts.** One generic analyst only. Specialization is FR-B.
- **No Phase 2a bootstrap.** The existing 10 seed pages + premise + synopsis
  are the starting canon. Manifest extraction is a separate FR.
- **No pathfinder integration.** The loop terminates on richness checks only.
  Pathfinder viability is deferred.
- **No visualization.** Wiki growth tracking is FR-B.
- **No parallel analysts.** One analyst, one call per iteration.

## Acceptance Criteria

- [ ] `worldgen.yaml` graph lints clean (`yamlgraph graph lint`)
- [ ] `reload_canon` python node reads `canon/*.yaml` at runtime
- [ ] `richness_check` python node checks ≥ 6 world invariants
- [ ] `merge_tasks` deduplicates by `(target_id, field)`
- [ ] Analyst prompt produces typed tasks with `synopsis_citation`
- [ ] Loop terminates when `rich_enough == true` OR `loop_limits` exceeded
- [ ] Generated pages pass the existing `ref_gate` (no orphan references)
- [ ] E2E run on Ashfall seed canon produces ≥ 3 new pages
- [ ] All new code has unit tests with `@pytest.mark.req`
- [ ] Generated pages are valid against `canon.py` Pydantic models

## Cost Model

Per iteration: 1 analyst call + up to 5 generation calls = 6 LLM calls.
Max 3 iterations = 18 LLM calls.
At ~$0.01–0.03 per call (Sonnet/Gemini Flash): **$0.18–$0.54 per full run.**

## Alternatives Considered

1. **Six specialist analysts from day one.** Rejected — proves nothing that
   one analyst doesn't prove, at 6× the prompt authoring cost. Specialization
   is optimization; the hypothesis is about the loop.

2. **LLM-based dedup/merge.** Rejected — adds another hallucination vector.
   Structural dedup by `(target_id, field)` is deterministic and sufficient
   for a single analyst.

3. **Subgraph per task** (map over tasks, each running draft → gate → fix).
   Considered for FR-B. For FR-A, a flat map + batch persist is simpler and
   sufficient to test the hypothesis.

## Judgement

**Date:** 2026-07-01
**Verdict: REJECTED — architectural inversion required. Rewrite as FR-643v2.**

### Flaw 1: Prayer to Almighty LLM

The analyst prompt sends the entire wiki (10+ pages as JSON) + synopsis +
richness report to one LLM call and asks it to:
- Cross-reference 7 page types
- Identify gaps across 6 dimensions (depth, triggers, membership, references,
  locations, orphans)
- Produce structured tasks with valid target_ids
- Cite the specific synopsis phrase that motivates each gap
- Prioritize correctly

This is not engineering. It's hope with a schema wrapper. The LLM will
produce plausible-looking tasks that cite the synopsis in vaguely relevant
ways, and some will be useful by accident. But the diagnosis is unreliable
because the prompt conflates analysis with generation.

The `richness_check` node already knows the exact gaps:
- Which characters have `wants == needs` or empty triggers
- Which factions have < 2 members
- Which events lack location references
- Which pages are orphans

It computes these, formats a pass/fail report, and throws the specifics
away. Then the analyst LLM re-discovers them (badly). The diagnosis is
already deterministic — only the generation needs an LLM.

### Flaw 2: Python Magic

Three custom python nodes totaling ~85 lines of opaque code:
- `reload_canon`: Framework workaround (data_files doesn't reload)
- `richness_check`: 50 lines of dict comprehensions and set operations
- `merge_tasks`: Dedup logic for LLM-produced tasks

These require Python expertise to debug, modify, or extend. They're not
reusable, not tested in isolation (the FR says "unit tests" but the logic
is tightly coupled to the page schema), and they duplicate knowledge that
exists in `canon.py` (which pages have which fields).

### The Inversion

**The richness checks should produce the task list directly.**

Current design:
```
richness_check → pass/fail report → LLM analyst → task list → LLM generator
                 (diagnosis)         (re-diagnosis)             (generation)
```

Correct design:
```
richness_check → typed gap list → LLM generator
                 (diagnosis)      (generation only)
```

Each failing invariant produces concrete, typed gaps:
- `character_depth FAIL` → `[{target: "kaelen", gap: "wants == needs"},
  {target: "voss", gap: "no triggers"}]`
- `faction_membership FAIL` → `[{target: "ashguard", gap: "1 member, need ≥2"}]`
- `location_grounding FAIL` → `[{target: "age_of_cinders", gap: "no location ref"}]`

These are deterministic. No LLM needed for diagnosis. The LLM's job is
narrow: given a specific gap ("Ashguard has 1 member, needs ≥2"), generate
the content to fill it ("create a second Ashguard character"). That's a
much smaller, more testable, more reliable LLM call.

### What FR-643v2 Should Look Like

1. **`richness_check` produces gaps, not just pass/fail.** Each check
   returns the specific entities that fail and what they need. This IS
   the task list. No analyst. No merge. No dedup.

2. **One generation prompt per gap type.** Not one mega-prompt. A gap of
   type "character needs triggers" uses a different prompt than "faction
   needs members" or "event needs location." Small, testable prompts.
   This is what YAMLGraph does well.

3. **`reload_canon` stays** but is documented as a framework workaround
   with a note that a future `data_files` runtime reload feature would
   eliminate it.

4. **The loop is simpler:** `reload → check → (gaps empty? END : generate
   → persist → reload)`. No analyze node. No merge node.

5. **The hypothesis changes:** Not "can an LLM analyze a wiki?" but "can
   deterministic gap detection + targeted LLM generation produce a rich
   world?" This is a better hypothesis — it's testable per gap type.

### Cost Impact

Current: 1 analyst + 5 generators = 6 calls/iteration.
Revised: 0 analysts + N generators (only for failing checks) = N calls/iteration.
If 3 checks fail with 2 gaps each = 6 generation calls. Same cost, no wasted
analyst call, and every generation call has a deterministic motivation.

## Related

- [plan-world-generation-loop.md](../docs/plan-world-generation-loop.md) — full architecture + judgement
- FR-637: Canon schema foundation
- FR-640: Enriched world model (character motivation triad)
- FR-642: Premise + Synopsis types
- FR-638: Plot pathfinder (the consumer of a rich wiki)
- FR-639: Draft + Close loop (downstream pipeline)
- FR-641: Rejected — LLM canon extraction (superseded by this loop approach)
