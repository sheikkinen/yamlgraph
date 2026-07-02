# Feature Request: Obsidian-compatible wiki output for canon pages

**Priority:** MEDIUM
**Type:** Feature
**Status:** Granted
**Effort:** 1 day
**Requested:** 2026-07-02
**Depends:** FR-643v2 (worldgen pipeline)
**Research:** `docs/research-wiki-format.md`

## Summary

Convert canon page format from pure YAML to YAML frontmatter + markdown (`.md`). Pages become directly browsable in Obsidian — wiki links, graph view, backlinks, and properties panel work out of the box with zero build step.

## Value Statement

The worldgen pipeline produces 24 structured YAML files. The data is rich but invisible — you can't browse the world, follow relationships, or see the web of connections. The user is building a wiki; the output should be a wiki.

Obsidian reads a directory of `.md` files with YAML frontmatter. No server, no build, no config. Point it at `canon/` and the world is navigable.

## Problem

Current output:
```
canon/
  kaelen.yaml       ← structured data, not browsable
  maren.yaml
  age_of_cinders.yaml
  ...
```

To see Kaelen's backstory, you `cat canon/kaelen.yaml` and read a YAML string field. To see who references Kaelen, you `grep -r kaelen canon/`. To see the relationship web, you can't.

## Proposed Solution

### Tool: Obsidian

Chosen after comparing Hugo, Jekyll, MkDocs, custom HTML, and Obsidian (see `docs/research-wiki-format.md`). Obsidian wins on:
- Zero build step (reads directory directly)
- Wiki links (`[[kaelen]]`) with broken link detection (red links)
- Built-in graph view (force-directed relationship web)
- Backlinks panel ("referenced by" computed automatically)
- Properties panel (renders YAML frontmatter as structured fields)

### Format change

Each canon page becomes a `.md` file with YAML frontmatter:

```markdown
---
type: character
id: kaelen
name: Kaelen
faction: ashguard
birth_year: 824
role: protagonist
lane: dynamic
depth: 1
references: [maren, voss, age_of_cinders]
relationships:
  - {to: maren, kind: mentor, valence: trust}
  - {to: voss, kind: rival, valence: enmity}
goals: [Reforge the Emberbrand with dragonsteel, Avenge the Ashfall]
fears: [That the Ashfall was his fault]
---

# Kaelen

**Faction:** [[ashguard]] | **Born:** year 824

## Backstory

Kaelen grew up in the shadow of the Great Forge...

## Goals
- Reforge the Emberbrand with dragonsteel
- Avenge the Ashfall

## Relationships
- [[maren]] — mentor (trust)
- [[voss]] — rival (enmity)

## Fears
- That the Ashfall was his fault
- That Maren's faith in him is misplaced
```

### What changes

| Component | Change |
|-----------|--------|
| `render_wiki.py` (NEW) | Reads `canon/*.yaml`, emits `wiki/*.md` with frontmatter + markdown body. Prose fields rendered as sections, references as `[[wiki_links]]`. |
| `persist_pages.py` | No change — still writes `.yaml` to `canon/`. |
| `reload_canon.py` | No change — still reads `canon/*.yaml` via `yaml.safe_load()`. |
| `validate_pages.py` | No change — validates YAML dicts. |
| Canon Pydantic models | No change — models validate YAML dicts. |
| `deepen_entity` prompt | No change — LLM still returns structured dict. |
| Output directory | New `wiki/` directory (gitignored output artifact). |

### Rendering logic (in `render_wiki.py`)

Per entity type, extract prose fields from the structured output and render them as markdown sections:

```python
PROSE_FIELDS = {
    "character": ["backstory"],
    "event": [],           # consequences stay in frontmatter (list)
    "faction": ["description"],
    "location": ["description"],
    "rule": ["description"],
    "premise": ["text"],
    "synopsis": ["text"],
}
```

The render step:
1. Read each `canon/*.yaml` file
2. Separate prose fields from structured fields
3. Write structured fields as YAML frontmatter
4. Render prose fields as markdown sections
5. Convert `references` list items to `[[wiki_links]]` in the body
6. Render relationships as a linked list
7. Write to `wiki/<id>.md`

### Graph integration

`render_wiki` runs after `persist` in the worldgen graph (or as a standalone script):

```
... → persist → render_wiki → reload
```

Or standalone: `python examples/novel_fandom/nodes/render_wiki.py`

Cheap (no LLM, pure template expansion) and idempotent.

## Acceptance Criteria

- [ ] AC-1: `render_wiki.py` reads `canon/*.yaml` and emits `wiki/*.md` with YAML frontmatter + markdown body
- [ ] AC-2: References rendered as `[[wiki_links]]` in markdown body
- [ ] AC-3: Relationships rendered as linked list with kind and valence
- [ ] AC-4: Prose fields (backstory, description, text) rendered as markdown sections, not frontmatter strings
- [ ] AC-5: `wiki/*.md` files contain valid YAML frontmatter (parseable by `yaml.safe_load`)
- [ ] AC-6: Wiki links (`[[id]]`) in markdown body reference files that exist in `wiki/`
- [ ] AC-7: `wiki/` directory gitignored (output artifact)
- [ ] AC-8: Unit tests for YAML → wiki markdown render round-trip
- [ ] AC-9: Tests added with `@pytest.mark.req`
- [ ] AC-10: `canon/*.yaml` unchanged — YAML remains source of truth for the pipeline
- [ ] Manual: open `wiki/` in Obsidian, confirm graph view and working links

## Judgement

**Granted with 3 amendments (2026-07-02)**

1. **Keep YAML as source of truth.** Don't change `reload_canon.py` or `persist_pages.py`. Add a separate `render_wiki.py` that reads YAML and emits `wiki/*.md`. The wiki is an output artifact, not the source format. No `python-frontmatter` dependency in the pipeline.
2. **Render step runs after persist.** Add as post-persist node or standalone script. Cheap, idempotent, no LLM.
3. **Manual verification for Obsidian.** "Graph view shows relationship web" and "navigable wiki" can't be asserted in pytest. Replace with parseable frontmatter and valid wiki link checks.

## Alternatives Considered

- **Keep YAML, generate HTML separately**: Two representations to maintain. Drift guaranteed.
- **MkDocs**: Requires build step, no graph view, no backlinks without plugins.
- **Hugo**: Fast but Go dependency, no graph view, overkill for local browsing.
- **Custom D3.js HTML**: Maximum flexibility but maximum effort. Build it later if needed.

## Related

- FR-643v2 — worldgen pipeline (produces the pages)
- FR-646 — reflexion step (red links visible as broken wiki links)
- FR-647 — event propagation (timeline visible in frontmatter dates)
- `docs/research-wiki-format.md` — format research
