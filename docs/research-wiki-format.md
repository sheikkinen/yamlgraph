# Research: Wiki Format for Canon Pages

**Date:** 2026-07-02
**Context:** FR-643v2 worldgen pipeline produces `canon/*.yaml` files. Need human-browsable output.

## Finding: One file, YAML frontmatter + markdown body

All major static wiki/site platforms use a single file per page:

```markdown
---
type: character
id: kaelen
name: Kaelen
faction: ashguard
---

# Kaelen

Backstory prose here...
```

- **Hugo** (Go): YAML/TOML/JSON frontmatter between `---` or `+++` delimiters. Custom fields under `params:`.
- **Jekyll** (Ruby): YAML frontmatter between `---`. Custom variables accessible via `{{ page.variable }}`.
- **MkDocs** (Python): YAML frontmatter via `meta` plugin. Primarily for metadata, less wiki-like.
- **Obsidian** (Electron): YAML frontmatter rendered as "Properties" panel. Wiki links via `[[page_id]]`. Graph view built-in.

### Key pattern

Structured data (type, id, relationships, dates) → **frontmatter**
Prose (backstory, description, atmosphere) → **markdown body**

No platform uses two files (YAML + markdown separately). The frontmatter IS the structured data.

## Tool comparison for canon visualization

| Tool | Install | Links | Graph view | Backlinks | Build step | Effort |
|------|---------|-------|------------|-----------|------------|--------|
| **Obsidian** | App download | `[[id]]` wiki links | Built-in force graph | Built-in panel | None (reads dir) | Lowest |
| MkDocs | `pip install` | `[name](id.md)` | None (plugin needed) | None | `mkdocs serve` | Medium |
| Hugo | Binary download | `[name](id.md)` | None | None | `hugo server` | Medium |
| Jekyll | Ruby gem | `[name](id.md)` | None | Plugin needed | `jekyll serve` | High |
| Custom HTML | None | `<a href>` | D3.js (build it) | Build it | Python script | Highest |

## Recommendation: Obsidian

**Why:**
1. Zero build step — point Obsidian at `canon/` directory, pages render immediately
2. `[[kaelen]]` wiki links resolve to pages. Broken links (red links) visible natively
3. Graph view shows relationship web without any code
4. Backlinks panel shows "referenced by" for free — no need to compute reverse links
5. Properties panel renders YAML frontmatter as structured fields
6. Tags, search, and filtering work out of the box
7. No server, no build, no dependencies beyond the app

**Trade-off:** Obsidian is a desktop app, not a hosted wiki. For sharing, would need Obsidian Publish ($) or a static site export. But for a single author reviewing generated world content, it's the lowest-friction option.

## Canon format change

Current: pure YAML (`.yaml`)
```yaml
type: character
id: kaelen
name: Kaelen
backstory: "prose here..."
```

Proposed: YAML frontmatter + markdown (`.md`)
```markdown
---
type: character
id: kaelen
name: Kaelen
faction: ashguard
birth_year: 824
references: [maren, voss, age_of_cinders]
relationships:
  - to: maren
    kind: mentor
    valence: trust
---

# Kaelen

**Role:** protagonist | **Faction:** [[ashguard]] | **Born:** year 824

## Backstory

Kaelen grew up in the shadow of the Great Forge...

## Relationships
- [[maren]] — mentor (trust)
- [[voss]] — rival (enmity)
```

### What moves where

| Field | Current location | Proposed location |
|-------|-----------------|-------------------|
| type, id, lane, depth | YAML body | Frontmatter |
| name, faction, role | YAML body | Frontmatter |
| birth_year, references | YAML body | Frontmatter |
| relationships | YAML body | Frontmatter + rendered in body |
| backstory, description, text | YAML body (string field) | Markdown body (prose) |
| goals, fears, triggers | YAML body (list) | Frontmatter + rendered in body |
| consequences (events) | YAML body (list) | Frontmatter + rendered in body |

### Impact on pipeline

- `reload_canon.py`: must parse frontmatter+markdown instead of pure YAML
- `persist_pages.py`: must emit frontmatter+markdown instead of `yaml.dump()`
- `deepen_entity` prompt: LLM output still structured (dict). Persist step renders prose fields to markdown body
- Pydantic validation: still works on frontmatter dict. Prose validation is separate
- `validate_pages.py`: references still in frontmatter, checkable without parsing markdown

### Libraries

- `python-frontmatter` (`pip install python-frontmatter`): read/write YAML frontmatter + markdown content. Mature, 1.6k GitHub stars.

```python
import frontmatter

# Read
post = frontmatter.load("canon/kaelen.md")
post.metadata  # {"type": "character", "id": "kaelen", ...}
post.content   # "# Kaelen\n\n## Backstory\n..."

# Write
post = frontmatter.Post(content="# Kaelen\n...", type="character", id="kaelen")
frontmatter.dump(post, "canon/kaelen.md")
```
