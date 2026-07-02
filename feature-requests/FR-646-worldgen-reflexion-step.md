# Feature Request: Reflexion step in worldgen pipeline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Granted
**Effort:** 1 day
**Requested:** 2026-07-02

## Summary

Add an LLM critic node (`reflect`) to the worldgen loop that reviews full canon after each deepening cycle and identifies concepts mentioned in prose but lacking pages.

## Value Statement

The world expansion pipeline catches structural gaps (missing fields) and declared red links (new_entities from deepening), but misses semantic red links — concepts like "Dragonsteel" that appear 5 times across 4 pages without ever getting their own page. A reflexion step pairs generation with review.

## Problem

FR-643v2 worldgen runs 3 iterations and expands 10 → 18 pages. But after the run, "Dragonsteel" — a load-bearing concept in the magic system — still has no page. It's mentioned in:
- `emberbrand_rule`: "reforged with dragonsteel quenched in living flame"
- `ashfall_pact`: "forfeits its claim to dragonsteel stores"
- `kaelen`: goal "Reforge the Emberbrand with dragonsteel"
- `synopsis`: "the last dragonsteel blade" and "the only remaining source"

The generator never declares it as a `new_entity` because deepening focuses on enriching the *current* page, not auditing cross-page concept coverage. The `select_thin` node skips `rule` pages entirely, so `emberbrand_rule` is never deepened and never gets a chance to declare dragonsteel.

This is a class of gap that structural thinness checks can't find — it requires reading comprehension across pages.

## Proposed Solution

Add a `reflect` LLM node between `deepen` and `collect_red_links`:

```
reload → select → deepen → reflect → collect_red_links → skeletons → gate → persist
```

### Prompt: `reflect_canon.yaml`

```yaml
system: |
  You are a fiction wiki editor reviewing a world bible for gaps.
  You are NOT the author — you are the critic.

  Look for concepts mentioned in prose that have no wiki page
  (materials, places, characters named but never defined).

  Be specific. Name the concept, cite which pages mention it.

user: |
  ## Current Canon ({{ canon_count }} pages)
  {% for id, page in canon_pages.items() %}
  ### {{ id }} ({{ page.type }})
  {{ page.name }} — {{ page.description[:100] }}…
  refs: {{ page.references | map(attribute='to') | list }}
  {% endfor %}

  ## Just Deepened
  {% for d in deepened %}
  - {{ d.updated_page.id }}: {{ d.updated_page.type }}
  {% endfor %}

  Review this canon. What concepts are named but undefined?

schema:
  name: CanonReflection
  fields:
    missing_entities:
      type: list[dict]
      description: >
        Entities that need pages. Each dict: id (snake_case),
        type (character/event/faction/location/rule),
        name (display name), summary (one sentence),
        cited_in (list of page ids that mention it)
    verdict:
      type: str
      description: "One sentence: is this canon complete?"
```

### Graph changes (`worldgen.yaml`)

```yaml
nodes:
  reflect:
    type: llm
    prompt: reflect_canon
    state_key: reflection
    temperature: 0.3
    variables:
      canon_pages: "{state.canon_pages}"
      canon_count: "{state.canon_count}"
      deepened: "{state.deepened}"

edges:
  - from: deepen
    to: reflect       # was: deepen → collect
  - from: reflect
    to: collect        # new edge
```

### collect_red_links.py changes

Accept `missing_entities` from reflection alongside `new_entities` from deepening:

```python
# Existing: collect new_entities from deepened results
# Add: collect missing_entities from reflection
reflection = state.get("reflection", {})
if isinstance(reflection, dict):
    for entity in reflection.get("missing_entities", []):
        if isinstance(entity, dict) and "id" in entity:
            if entity["id"] not in existing_ids and entity["id"] not in seen:
                red_links.append(entity)
                seen.add(entity["id"])
```

### Why this isn't the rejected FR-643

| FR-643 (rejected) | FR-646 (this) |
|---|---|
| LLM diagnoses gaps AND generates fixes | LLM only critiques; pipeline routes fixes |
| Single node does everything | Critic separated from generator |
| "Prayer to almighty LLM" | Structured output feeds mechanical pipeline |
| Replaced structural thinness checks | Supplements existing checks |

The critic's `missing_entities` has the same shape as the generator's `new_entities`. Both feed into `collect_red_links` → `create_skeletons`. The critic never generates content — it only names what's missing.

### State additions

```yaml
state:
  reflection: dict    # CanonReflection output
```

## Acceptance Criteria

- [ ] AC-1: `reflect` LLM node added after `deepen`, before `collect`
- [ ] AC-2: Prompt reviews canon summaries and identifies unnamed concepts (missing entities only — no contradiction detection)
- [ ] AC-3: `missing_entities` from reflection fed into `collect_red_links`
- [ ] AC-4a: Unit test: mock reflection with `missing_entities: [{id: "dragonsteel", ...}]` → `collect_red_links` includes it
- [ ] AC-4b: Integration test (`@pytest.mark.slow`): worldgen on seed canon produces a `dragonsteel` red link
- [ ] AC-6: Loop limit includes `reflect` node
- [ ] AC-7: Unit tests for collect_red_links accepting both sources
- [ ] AC-8: Tests added with `@pytest.mark.req`
- [ ] AC-9: `reflect_canon.yaml` sends page summaries (id, type, name, truncated description, references), not full JSON. Total prompt < 4K tokens for 30 pages.

## Judgement

**Granted with 3 amendments (2026-07-02)**

1. **Drop `inconsistencies` from scope.** Missing entity detection and contradiction detection are different problems. Ship `missing_entities` only. Contradictions are a separate FR.
2. **Context window budget.** Prompt sends page summaries (id, type, name, description[:100], references) instead of full JSON. Keeps prompt under 4K tokens at 30 pages.
3. **AC-4 split.** "Produces a dragonsteel red link" requires real LLM. Split into unit (mock reflection → collect merges it) and integration (real LLM, `@pytest.mark.slow`).

## Alternatives Considered

- **Regex scanner (plan-for-3 original)**: Extract capitalized terms mechanically. Cheaper, no LLM cost, but brittle — can't distinguish "the Ashfall" (event, has page as `age_of_cinders`) from "Dragonsteel" (material, no page). The term-to-page-id mapping problem is itself a semantic task.
- **Add `_rule_thin` check**: Would deepen rules, which might declare dragonsteel as `new_entity`. But this only works if the generator happens to mention it — no guarantee.
- **Manual seed pages**: Human adds `dragonsteel.yaml`. Works for one concept, doesn't scale to discovery.

## Related

- FR-643v2 — worldgen pipeline (this extends it)
- FR-643 — rejected analyst loop (this is the disciplined version)
- `examples/demos/reflexion/` — existing reflexion demo pattern
- `yamlgraph/node_factory/llm_nodes.py` — LLM node compilation
