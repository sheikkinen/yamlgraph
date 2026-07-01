# FR-641: novel_fandom — LLM Canon Extraction with Freeze-Gate

**Priority:** LOW
**Type:** Feature (example)
**Status:** Rejected
**Effort:** 1–2 days
**Requested:** 2026-07-01

## Summary

Add an `extract_canon` node that takes a free-text premise, generates a synopsis
via LLM, extracts typed canon pages (Character, Event, Faction, Location, Rule)
from the prose, validates them through the existing reference gate, and writes
approved pages as `lane: dynamic` YAML files. A separate freeze step promotes
reviewed pages to `lane: static`. This is the LLM-bootstrap alternative to
hand-authoring the seed canon.

## Value Statement

Hand-authoring canon (FR-637/FR-640) is correct at 6-page scale but doesn't scale
to novels with 30+ characters, 10+ locations, and dozens of world rules. This FR
lets the LLM generate the canon from a premise while the gate enforces the same
structural integrity as hand-authored pages.

## Problem

FR-637 establishes hand-authored seed canon. FR-640 enriches the schema with
motivation triad, triggers, atmosphere, and world rules. Both assume a human
writes the YAML. For a full novel generation pipeline (Phases 2–3), the canon
needs to grow beyond what's practical to hand-author:

- A synopsis introduces characters, factions, locations, and rules implicitly
- Extracting them manually is tedious and error-prone
- The `langgraph-poc-narrator` proved that LLM extraction works at production
  scale (`build_story_bible_node` → `extract_world_rules` → `extract_characters`
  → `extract_locations`), but the POC had no integrity gate — extracted entities
  could hallucinate references or contradict each other

The gap: combine the POC's extraction capability with FR-637's reference gate
and lane immutability.

## Proposed Solution

### Pipeline

```
premise (input)
    → generate_synopsis (LLM node, produces prose synopsis)
    → extract_canon (LLM node, structured output → typed canon pages)
    → ref_gate (existing gate, validates cross-references)
    → write_canon (tool node, writes validated pages as lane: dynamic YAML)
```

### 1. `generate_synopsis` node

Standard LLM node. Takes a premise, produces a multi-page synopsis prose.
Prompt template in `prompts/generate_synopsis.yaml`.

### 2. `extract_canon` node

LLM structured-output node. Takes the synopsis prose and extracts typed pages
matching the FR-640 schema:

```yaml
# prompts/extract_canon.yaml
system: |
  Extract all fiction entities from the synopsis as typed canon pages.
  Each entity must have an id (snake_case), a type, and references to
  other entities it mentions. Use the enriched schema:
  - Characters: include role, driving_force, wants, needs, fears,
    arc_summary, triggers, relationships with valence
  - Locations: include location_type, atmosphere, sensory, significance
  - Factions: include members list
  - Events: include participants, consequences, temporal window
  - Rules: include domain, title, description

output_schema:
  name: ExtractedCanon
  fields:
    pages:
      type: list[dict]
      description: "List of canon page dicts, each with type, id, lane='dynamic', and type-specific fields"
```

### 3. Gate validation (reuse existing)

The existing `ref_gate.py` validates:
- Every `references` entry resolves to an existing page id
- No write to a `lane: static` page

Extracted pages arrive as `lane: dynamic` — the gate allows writes. Orphan
references cause the gate to reject the page, triggering a `fix_refs` loop
(same as FR-637's gated-accumulation pattern).

### 4. `write_canon` tool node

Writes validated pages as YAML files to `canon/`:

```python
def write_canon_page(page: dict, canon_dir: Path) -> Path:
    """Write a validated canon page to a YAML file."""
    page_id = page["id"]
    path = canon_dir / f"{page_id}.yaml"
    if path.exists():
        existing = yaml.safe_load(path.read_text())
        if existing.get("lane") == "static":
            raise ValueError(f"Cannot overwrite static page: {page_id}")
    path.write_text(yaml.dump(page, default_flow_style=False, allow_unicode=True))
    return path
```

### 5. Freeze step (manual or automated)

After review, promote pages from `dynamic` to `static`:

```bash
# CLI command or tool
yamlgraph graph run examples/novel_fandom/freeze.yaml --var page_id=kaelen
```

Or a simple tool that rewrites `lane: dynamic` → `lane: static` in the YAML file
after human or LLM judge approval.

### Graph shape

```yaml
# examples/novel_fandom/extract.yaml
nodes:
  generate_synopsis:
    type: llm
    prompt: examples/novel_fandom/prompts/generate_synopsis
    state_key: synopsis

  extract_canon:
    type: llm
    prompt: examples/novel_fandom/prompts/extract_canon
    state_key: extracted_pages
    variables:
      synopsis: "{state.synopsis}"

  validate_and_write:
    type: python
    module: examples.novel_fandom.nodes.canon_writer
    function: validate_and_write_pages
    state_key: write_results
    variables:
      pages: "{state.extracted_pages}"

edges:
  - from: START
    to: generate_synopsis
  - from: generate_synopsis
    to: extract_canon
  - from: extract_canon
    to: validate_and_write
  - from: validate_and_write
    to: END
```

### Design decisions

- **Extracted pages are always `lane: dynamic`.** Never auto-promote to static.
  The freeze step is a deliberate approval gate — human or LLM judge.
- **Reuse existing gate, don't fork.** The `ref_gate.py` from FR-637 already
  handles orphan detection and lane immutability. No new gate logic needed.
- **One extraction pass, not three.** The POC ran `extract_world_rules` →
  `extract_characters` → `extract_locations` as three separate LLM calls. A
  single structured-output call is cheaper and avoids cross-extraction
  inconsistencies (e.g., a character referencing a location that the location
  extractor hasn't created yet).
- **No synopsis persistence.** The synopsis is a means to an end — the canon
  pages are the product. The synopsis lives in graph state, not on disk.
  If needed later, it can be persisted as an Event page.

## Acceptance Criteria

- [ ] `extract.yaml` graph exists; `yamlgraph graph lint` passes.
- [ ] `generate_synopsis` prompt produces multi-paragraph prose from a premise.
- [ ] `extract_canon` prompt produces typed canon pages matching FR-640 schema
      (Character with motivation triad + triggers, Location with atmosphere,
      Rule with domain).
- [ ] Extracted pages validate against `schema/canon.py` Pydantic models.
- [ ] `ref_gate` rejects extracted pages with orphan references (RED test first).
- [ ] `write_canon` writes validated pages as `lane: dynamic` YAML files.
- [ ] `write_canon` refuses to overwrite `lane: static` pages (RED test first).
- [ ] Freeze mechanism promotes `dynamic` → `static` for a reviewed page.
- [ ] Integration test: premise → extract → gate → write → freeze round-trip.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-XXX")`.

## Alternatives Considered

- **Hand-author all canon (FR-637 approach).** Correct at 6-page scale. Doesn't
  scale to 30+ entities. This FR is the scale-up path.
- **Three separate extraction calls (POC approach).** Rejected: single structured-
  output call is cheaper and avoids cross-extraction orphan references.
- **Auto-freeze after gate passes.** Rejected: gate checks structural integrity
  (no orphans), not semantic quality (is this character's motivation triad
  coherent?). A separate approval step is needed.
- **Hybrid: hand-authored skeleton + LLM enrichment.** A valid middle ground
  (hand-author id/name/faction/relationships, LLM fills motivation triad). Could
  be implemented as a variant of this FR's extract node that takes partial pages
  as input. Deferred — the full extraction path is more general.

## Judgement

**Verdict: REJECTED — premature, dependency chain incomplete, scope overreach.**

### Why rejected

1. **Dependency chain not met.** FR-640 (enriched schema) is proposed but not shipped.
   FR-641's extraction prompt targets FR-640 fields (motivation triad, triggers,
   Rule). You cannot extract into a schema that doesn't exist yet. Sequence:
   FR-640 → FR-638 (pathfinder) → FR-639 (prose+close) → then consider extraction.

2. **No consumer exists.** The pathfinder (FR-638) hasn't been built. Nobody reads
   the extracted canon yet. Extraction without a consumer is a demo, not a feature.
   Build the consumer first, prove the schema is right by using it, *then* automate
   the authoring.

3. **The problem it solves doesn't exist yet.** The FR says hand-authoring "doesn't
   scale to 30+ characters." The current canon has 6 pages. The pipeline has never
   run at 30-entity scale. The pain of hand-authoring at scale is hypothetical.
   Build the pipeline (FR-638 → FR-639), run it on the 6-page seed, observe what
   the pathfinder actually needs, *then* decide if LLM extraction is the right
   scaling mechanism.

4. **Single-pass extraction is unproven.** The FR rejects the POC's 3-pass
   approach (rules → characters → locations) in favor of a single structured-output
   call. This is a design bet, not a proven improvement. At 30+ entities with
   cross-references, a single call may exceed context or produce inconsistent
   references. The FR should be a spike, not a shipped feature, until the
   single-pass approach is validated.

5. **Freeze mechanism is underspecified.** "A simple tool that rewrites `lane:`"
   is hand-waving. What triggers the freeze? Human review? LLM judge? What's the
   review criterion? This is a governance question, not a tooling question, and
   the FR doesn't answer it.

6. **The graph shape violates existing patterns.** The `extract.yaml` graph has
   no gate-fix loop — it's a straight pipeline. If the extraction produces orphan
   references, it writes them anyway (the `validate_and_write` tool does its own
   gating). This bypasses the gated-accumulation pattern that FR-628/637 established.
   If extraction is added, it should use the same draft→gate→fix→persist loop.

### What to do instead

1. Ship FR-640 (schema enrichment).
2. Ship FR-638 (pathfinder) — run it on the enriched seed.
3. Ship FR-639 (prose + close loop) — run the full pipeline.
4. **Then** evaluate: does the 6-page seed produce good pathfinder output? What's
   missing? Is the bottleneck *authoring* (scale) or *schema* (fields)?
5. If the bottleneck is authoring at scale, re-propose extraction as a new FR with
   the dependency chain complete and the single-pass vs. multi-pass question
   answered by a spike.

### Resubmission criteria

- FR-640, FR-638, FR-639 all shipped.
- At least one full pipeline run (pathfind → draft → close) completed.
- Single-pass extraction validated in a spike (informal, no FR needed).
- Freeze governance defined: who/what approves promotion to static?

## Dependencies

- **FR-637** (shipped): canon schema, gate, seed files.
- **FR-640** (proposed): enriched schema with motivation triad, triggers, Rule
  type. This FR's extraction prompt targets the FR-640 schema.

## Related

- [FR-637](./FR-637-novel-fandom-canon-schema-seed.md) — hand-authored seed canon.
- [FR-640](./FR-640-novel-fandom-enriched-world-model.md) — enriched schema this
  extracts into.
- [FR-638](./FR-638-novel-fandom-plot-pathfinder.md) — pathfinder that consumes
  the extracted canon.
- `langgraph-poc-narrator/src_novel/nodes/analysis.py` — POC's
  `build_story_bible_node` extraction pipeline (3-pass approach this improves on).
