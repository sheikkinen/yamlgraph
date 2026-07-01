# FR-643v2: novel_fandom — World Expansion (Deepening + Red Links)

**Priority:** HIGH
**Type:** Feature (example)
**Status:** Enforcing
**Effort:** 2 days
**Requested:** 2026-07-01
**Depends on:** FR-637, FR-640, FR-642

## Summary

Add a deepening loop that enriches existing canon pages and grows the
wiki through red links — entity references that don't have pages yet.
The pipeline decides what to deepen (deterministic thinness filter), the
LLM generates content, and a gate validates. No LLM ever diagnoses gaps.

## Value Statement

The E2E pathfinder run proved the world is too thin for drama. A 10-page
skeleton wiki forces the LLM to hallucinate entities. The deepening loop
fills the wiki by expanding what exists — deepening a character produces
backstory that introduces new characters, events, and locations. Those
become pages. Those pages get deepened. The world grows from the inside.

## Problem

1. **Skeleton characters.** Kaelen has goals and triggers but no
   backstory — no childhood, no mentor, no formative events. The
   pathfinder generates beats about his past but has nothing to traverse.

2. **No locations.** Zero Location pages exist. Events float without
   geography. The synopsis mentions "the old forge" and "the ruins" but
   they aren't pages.

3. **Sparse events.** One event (age_of_cinders) covers 200 years.
   No intermediate events. No consequences described.

4. **No growth mechanism.** The existing `graph.yaml` creates one page
   at a time from human input. There's no pipeline that systematically
   expands the world.

## Design

### The Pattern: Expand → Extract → Expand

```
                    ┌──────────────┐
                    │  WIKI STATE  │  (canon/*.yaml)
                    └──────┬───────┘
                           ↓
              select_thin (deterministic)
              "who needs depth?"
                           ↓
              deepen × N (LLM map)
              "tell me Kaelen's backstory"
                           ↓
              collect_red_links (deterministic)
              "backstory mentions Brennan, Ember Trials — no pages"
                           ↓
              create_skeletons × N (LLM map)
              "generate a skeleton page for Brennan"
                           ↓
              gate + persist all
                           ↓
              depth_check (deterministic)
              "still thin at depth < max? → loop"
              "max_depth reached? → END"
                           ↓
                    back to reload_canon
```

### The Three Jobs

| Job | Who | What |
|-----|-----|------|
| Decide what to deepen | Deterministic (`select_thin`) | Field presence checks per type |
| Generate content | LLM (deepen + skeleton prompts) | Narrow: "given X, write Y" |
| Validate | Deterministic (gate) | References resolve, types valid |

No LLM diagnoses. No LLM decides what to do next.

### Schema Addition: `backstory` Field

Characters in the seed have motivation fields (wants, needs, triggers)
but no narrative prose. Add `backstory: str = ""` to Character. This is
the primary thinness dimension — the field the deepening loop fills.

```python
class Character(BaseModel):
    # ... existing fields ...
    backstory: str = ""  # NEW — narrative prose, filled by deepening
```

### Schema Addition: `_depth` Field

Every page type gets a depth field tracking how far from the synopsis
this entity was introduced:

```python
# In every page model (Character, Event, Faction, Location, Rule):
depth: int = Field(default=0, alias="_depth")
```

Depth 0 = premise/synopsis. Depth 1 = entities from the seed/manifest.
Depth 2 = red links from depth-1 backstories. Etc.

### Thinness Criteria

`select_thin` filters entities at `depth < max_depth` that fail
structural checks. No LLM. No semantic judgment.

**Character is thin if:**
- `backstory` is empty or < 50 words
- `triggers` list is empty
- < 2 relationships

**Event is thin if:**
- `consequences` list is empty
- < 2 participants

**Faction is thin if:**
- < 2 members

**Location is thin if:**
- `atmosphere` list is empty AND `sensory` list is empty

These are field-count checks. Coupled to `canon.py` schema — document
this: when a field is added, review thin criteria.

**Amendment 5 (folded):** Sort by `thin_score` (number of failing
criteria) descending, so thinnest entities are deepened first. Fits
within `max_items: 5` truncation.

### Deepening Prompt

Per-type prompts. Each takes the entity + synopsis + surrounding canon
context and produces enriched content + declared new entities.

```yaml
# prompts/deepen_character.yaml
system: |
  You are a fiction worldbuilder. You receive a character page and the
  world synopsis. Write a rich backstory for this character.

  Your backstory MUST:
  - Reference only existing entities OR declare new ones explicitly
  - Connect to the synopsis narrative
  - Reveal formative events, relationships, and emotional triggers

  Output the updated character page with backstory filled in, plus a
  list of any new entities your backstory introduces.

user: |
  ## Synopsis
  {{ synopsis_text }}

  ## Character to Deepen
  {{ entity | tojson(indent=2) }}

  ## Existing Canon ({{ canon_count }} pages)
  {% for id, page in canon_pages.items() %}
  - {{ id }} ({{ page.type }})
  {% endfor %}

  ## Why This Character Is Thin
  {{ thin_reason }}

  Write the backstory. Declare any new entities you introduce.

schema:
  name: DeepenedCharacter
  fields:
    updated_page:
      type: dict
      description: "The full character page with backstory and enriched fields"
    new_entities:
      type: list[NewEntity]
      description: "New entities introduced in the backstory"

  nested:
    NewEntity:
      id:
        type: str
        description: "Proposed snake_case page id"
      type:
        type: str
        description: "character, event, faction, location, or rule"
      name:
        type: str
        description: "Display name"
      summary:
        type: str
        description: "One sentence"
```

**Amendment 1 (folded):** One `deepen_entity.yaml` prompt with Jinja2
type conditionals, not four separate prompts. Map node can't route per
item type. Per-type prompts are a future optimization.

```
{% if entity.type == "character" %}
Write a rich backstory...
{% elif entity.type == "event" %}
Describe consequences and aftermath...
{% elif entity.type == "faction" %}
Describe internal dynamics...
{% elif entity.type == "location" %}
Describe atmosphere, sensory details...
{% endif %}
```

### Red Link Collection (Deterministic)

After deepening N entities in parallel, collect all declared
`new_entities`, deduplicate by `id`, and filter out ids that already
exist as pages.

```python
# nodes/collect_red_links.py
def collect_red_links(state: dict) -> dict:
    """Deduplicate new entities from parallel deepen calls."""
    deepened_results = state.get("deepened", [])
    canon_pages = state.get("canon_pages", {})

    seen = {}
    for result in deepened_results:
        for entity in result.get("new_entities", []):
            eid = entity.get("id", "")
            if eid and eid not in canon_pages and eid not in seen:
                seen[eid] = entity

    red_links = list(seen.values())
    return {"red_links": red_links, "red_link_count": len(red_links)}
```

### Skeleton Generation Prompt

```yaml
# prompts/generate_skeleton.yaml
system: |
  Generate a skeleton wiki page for a fiction entity. Include all required
  fields for the page type. Set lane: dynamic. Set depth to {{ parent_depth + 1 }}.
  Keep content minimal — just enough to be a valid page. This entity will
  be deepened in a later iteration.

user: |
  ## Entity to Create
  ID: {{ red_link.id }}
  Type: {{ red_link.type }}
  Name: {{ red_link.name }}
  Summary: {{ red_link.summary }}

  ## Synopsis Context
  {{ synopsis_text }}

  ## Existing Canon (ids only)
  {% for id in canon_pages.keys() %}
  - {{ id }} ({{ canon_pages[id].type }})
  {% endfor %}

  Generate the skeleton page.
```

### Graph Definition

```yaml
# worldgen.yaml
version: "1.0"
name: novel-fandom-worldgen
description: Expand wiki — deepen thin entities, grow via red links
prompts_relative: true
prompts_dir: prompts

data_files:
  canon: "canon/*.yaml"

state:
  canon_pages: dict
  canon_count: int
  synopsis_text: str
  thin_entities: list
  deepened: list
  red_links: list
  skeletons: list
  max_depth: int
  done: bool

variables:
  max_depth: 2

tools:
  reload_canon:
    type: python
    path: nodes/reload_canon.py
    function: reload_canon
  select_thin:
    type: python
    path: nodes/select_thin.py
    function: select_thin
  collect_red_links:
    type: python
    path: nodes/collect_red_links.py
    function: collect_red_links
  persist_pages:
    type: python
    path: nodes/persist_pages.py
    function: persist_pages

nodes:
  reload:
    type: python
    tool: reload_canon

  select:
    type: python
    tool: select_thin

  deepen:
    type: map
    over: "{state.thin_entities}"
    as: entity_task
    max_items: 5
    collect: deepened
    node:
      type: llm
      prompt: deepen_entity
      state_key: result
      temperature: 0.7

  collect:
    type: python
    tool: collect_red_links

  create_skeletons:
    type: map
    over: "{state.red_links}"
    as: red_link
    max_items: 10
    collect: skeletons
    node:
      type: llm
      prompt: generate_skeleton
      state_key: skeleton
      temperature: 0.3

  persist:
    type: python
    tool: persist_pages

edges:
  - from: START
    to: reload

  - from: reload
    to: select

  - from: select
    to: END
    condition: done == true

  - from: select
    to: deepen
    condition: done == false

  - from: deepen
    to: collect

  - from: collect
    to: create_skeletons
    condition: red_link_count > 0

  - from: collect
    to: persist
    condition: red_link_count == 0

  - from: create_skeletons
    to: gate

  # Amendment 4 (folded): gate validates refs against merged canon
  - from: gate
    to: persist

  - from: persist
    to: reload

loop_limits:
  reload: 4
  deepen: 3
```

### Loop Termination

The loop ends when:
1. `select_thin` finds no entities at `depth < max_depth` → `done = true`
2. `loop_limits` exceeded (safety cap: 3 deepen iterations)

These work together, not against each other:
- `max_depth=1`: only seed entities deepened, red links become depth-2
  skeletons (not deepened). Loop runs once.
- `max_depth=2`: seed entities deepened, depth-2 skeletons deepened,
  depth-3 skeletons created as placeholders. Loop runs twice.
- Loop limit caps runaway at 3 regardless of max_depth.

**Tradeoff (documented):** entities at `max_depth` remain skeletons.
This is authorial intent — the user controls depth via `--var max_depth=N`.
The richness report (not part of this FR) would show what remains thin.

### Persist Node

Batch persist: takes `deepened` (updated pages) + `skeletons` (new pages)
and writes all to `canon/`. Uses existing `write_data_file` mechanics
(atomic write, YAML only, no path traversal).

```python
# nodes/persist_pages.py
def persist_pages(state: dict) -> dict:
    """Write deepened + skeleton pages to canon/."""
    from pathlib import Path
    import yaml

    canon_dir = Path(__file__).parent.parent / "canon"
    written = []

    # Amendment 2 (folded): Validate against Pydantic before writing
    from schema.canon import PAGE_MODELS

    def _validate_and_write(page, canon_dir, overwrite=True):
        if not page or "id" not in page or "type" not in page:
            return None
        model_cls = PAGE_MODELS.get(page["type"])
        if not model_cls:
            return None
        try:
            model_cls(**page)  # Pydantic validation
        except Exception:
            return None  # Skip invalid pages
        path = canon_dir / f"{page['id']}.yaml"
        if not overwrite and path.exists():
            return None
        # Amendment 3 (folded): Atomic write pattern
        import tempfile, os
        fd, tmp = tempfile.mkstemp(dir=canon_dir, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(page, f, default_flow_style=False,
                           allow_unicode=True, sort_keys=False)
        os.replace(tmp, path)
        return str(path)

    for result in state.get("deepened", []):
        p = _validate_and_write(result.get("updated_page", {}), canon_dir)
        if p:
            written.append(p)

    for skeleton in state.get("skeletons", []):
        p = _validate_and_write(skeleton, canon_dir, overwrite=False)
        if p:
            written.append(p)

    return {"written_paths": written, "written_count": len(written)}
```

## Scope Exclusions

- **No Phase 1 cold start.** Uses existing 10-page seed canon. Synopsis →
  manifest extraction is a separate FR.
- **No richness report.** Post-validation reporting is a separate FR.
- **No pathfinder integration.** Deferred until wiki is visualizable.
- **No field-level merge.** Deepening overwrites the page. Honest about it.
- **No `lane: static` protection.** All seed pages are now `lane: dynamic`.

## Acceptance Criteria

- [ ] `backstory: str = ""` added to Character in `canon.py`
- [ ] `_depth: int = 0` added to all page models in `canon.py`
- [ ] `worldgen.yaml` graph lints clean
- [ ] `select_thin` correctly identifies thin entities per type
- [ ] `deepen_character.yaml` prompt produces backstory + new_entities
- [ ] `collect_red_links` deduplicates by id, filters existing pages
- [ ] `generate_skeleton.yaml` produces valid pages at `parent_depth + 1`
- [ ] Loop terminates when no thin entities at `depth < max_depth`
- [ ] E2E run at `max_depth=2` produces ≥ 5 new pages from Ashfall seed
- [ ] All generated pages validate against `canon.py` Pydantic models
- [ ] All new code has unit tests with `@pytest.mark.req`
- [ ] Seed canon pages changed from `lane: static` to `lane: dynamic`

## Cost Model

Per iteration: up to 5 deepen calls + up to 10 skeleton calls = 15 LLM calls.
Max 3 iterations = 45 LLM calls.
At ~$0.01–0.03 per call: **$0.45–$1.35 per full run.**

Practical: `max_depth=2` runs ~2 iterations = ~30 calls = ~$0.60.

## Alternatives Considered

1. **Analyst loop (FR-643).** Rejected — LLM diagnoses gaps = prayer.
2. **Deterministic gap list (FR-643 judgement).** Better but still
   diagnostic. Why ask "what's missing?" when you can say "go deeper."
3. **Linear expansion only.** Produces skeletons. Characters need
   backstory, which introduces entities, which need pages. Linear
   can't do this — it requires iteration.
4. **Phase 1 + Phase 2 in one FR.** Too much. Test one thing: does
   deepening + red links grow a wiki from an existing seed?

## Related

- [plan-world-expansion.md](../docs/plan-world-expansion.md) — full architecture + judgement
- FR-643: Rejected — analyst loop (prayer + magic)
- FR-637: Canon schema foundation
- FR-640: Enriched world model (character motivation triad)
- FR-642: Premise + Synopsis types
- FR-638: Plot pathfinder (consumer of a rich wiki)

---

## Judgement

**Date:** 2026-07-01
**Verdict: GRANTED with five amendments. Scope is frozen after amendments.**

The architecture is sound. The three-job separation (pipeline decides, LLM
generates, gate validates) is the correct design. The red link mechanism
is elegant — content declares its own gaps. The depth budget is a clean
termination model. Previous flaws (prayer, magic, overcorrection) are
resolved.

### Amendment 1: `deepen_entity` prompt routing

The graph definition has a single `deepen` map node using prompt
`deepen_entity`. But the design section specifies four separate prompts:
`deepen_character.yaml`, `deepen_event.yaml`, `deepen_faction.yaml`,
`deepen_location.yaml`.

A map node's inner LLM node has one fixed prompt. It can't route per
item type.

**Options:**
- (a) One `deepen_entity.yaml` prompt with Jinja2 conditionals per type
- (b) A router node before the map that groups by type, then separate
  map nodes per type
- (c) One prompt, let the LLM figure it out from context

**Resolution:** (a) is simplest. One prompt with
`{% if entity.type == "character" %}...{% elif %}...{% endif %}`. This
is a prompt concern, not an architecture concern. Per-type prompts are
a future optimization (FR-B). Amend: use a single `deepen_entity.yaml`
prompt with type-conditional sections.

### Amendment 2: `updated_page: dict` is untyped

The deepening schema returns `updated_page: dict`. This means the LLM
can return anything — wrong fields, missing required fields, invented
types. The Pydantic models in `canon.py` exist precisely to prevent
this.

**Resolution:** `persist_pages` must validate every page against the
Pydantic model before writing. Add a validation step:
`PAGE_MODELS[page["type"]](**page)`. If validation fails, skip the page
and log the error. This is a 3-line addition to `persist_pages`.

The alternative — per-type output schemas in the deepen prompt — is
better but requires 5 separate prompts. Save for FR-B.

### Amendment 3: `persist_pages` bypasses `write_data_file` security

The custom `persist_pages` node does raw `open(path, "w")`. The existing
`write_data_file` tool provides:
- Atomic writes (tempfile + `os.replace`)
- Path traversal rejection
- Self-modification guards (won't write to graph/prompts dirs)

**Resolution:** Use `write_data_file` tool via map node for persistence,
or replicate its atomic write pattern in `persist_pages`. At minimum:
use `tempfile.mkstemp` + `os.replace` and validate the target path is
within `canon/`. This is an example, not production, but setting the
pattern right matters for the demo.

### Amendment 4: `ref_gate` is not in the loop

The diagram shows "gate + persist all" but the graph definition has no
gate node. Deepened pages and skeletons go straight to persist without
reference validation. The existing `ref_gate` checks:
- Orphan references (references to non-existent pages)
- Lane immutability (now moot with all-dynamic)

In the loop context, the gate must check references against the
**updated** canon (including pages from this iteration's deepen step),
not just the pre-loop state. A deepened Kaelen may reference Brennan,
and Brennan's skeleton is created in the same iteration. The gate must
see both.

**Resolution:** Add a gate step between `create_skeletons` and
`persist`. The gate receives the merged set: `canon_pages` ∪ deepened
updated pages ∪ skeletons. Run `ref_gate`-style validation on each.
This can be a python node that calls `check_references` per page with
an augmented canon dict.

### Amendment 5: `select_thin` thinness vs. existing seed

The seed characters (kaelen, maren, voss) have triggers, wants≠needs,
and 2+ relationships. By the thinness criteria, they're only thin on
`backstory`. The events, factions, and locations are thin on multiple
dimensions.

This means iteration 1 selects: all 3 characters (backstory only) +
1 event (consequences, participants) + 2 factions (members). That's 6
entities, but `max_items: 5` on the deepen map truncates to 5. One
entity won't get deepened.

**Resolution:** Acceptable — the skipped entity gets deepened in
iteration 2. But `select_thin` should sort by "how thin" (number of
failing criteria) so the thinnest entities are deepened first. Add
a `thin_score` count field and sort descending.

### Summary

| Amendment | Action |
|-----------|--------|
| 1. Prompt routing | Single `deepen_entity.yaml` with Jinja2 type conditionals |
| 2. Untyped output | Add Pydantic validation in `persist_pages` before write |
| 3. Unsafe persist | Use atomic write pattern, validate target path |
| 4. Missing gate | Add gate node between create_skeletons and persist |
| 5. Thin sorting | Sort by thin_score (failing criteria count) |

**Authority granted. Freeze scope. Enforce with TDD.**
