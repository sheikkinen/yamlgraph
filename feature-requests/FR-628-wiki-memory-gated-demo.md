# FR-628: Wiki Memory with Reference Gate — Gated Knowledge Accumulation Demo

**Priority:** MEDIUM
**Type:** Feature (demo)
**Status:** Judged — Authority GRANTED, clear to enforce (2026-07-01)
**Effort:** 1 day
**Requested:** 2026-07-01

## Summary

A demo that extends the `write_data_file` pattern (FR-626) with a deterministic
reference-integrity gate: the LLM proposes a new wiki page, a Python tool checks
that every cross-reference resolves to an existing page, and only verified pages
are persisted. Failed references loop back through the LLM for correction.

## Value Statement

Graph authors get a reusable pattern for building self-maintaining knowledge
bases that compound without rotting — the wiki-memory pattern with teeth.

## Problem

FR-626 proves the read→write cycle. But an unguarded wiki drifts: the LLM
invents a reference to a page that doesn't exist, and downstream runs build on
the phantom. This is the dominant failure mode of every production wiki-memory
system (Harrison Chase, Andrej Karpathy, Graphiti — all converge on "lint is not
optional").

The `write_data_file` demo has no cross-reference checking. The `verification-gate`
demo checks LLM output shape, not referential integrity against external state.
Neither shows the **gated accumulation loop**: propose → verify references → fix
or persist.

This pattern is the generic core extracted from the fandom canon-first plans
(`docs/plan-fandom-generation.md`, `docs/plan-fandom-architecture.md`). The
architecture called for 8 subsystems; this demo distills the load-bearing
invariant (no-orphan, no-leak) into a single graph with one leaf tool.

## Proposed Solution

### Domain: Technology Radar

A team maintains a wiki of tools, libraries, and patterns they evaluate. Three
page types (`tool`, `pattern`, `decision`), each with typed YAML front-matter
and cross-references. Generic enough that any developer understands it; structured
enough to require referential integrity.

### Demo structure

```
examples/demos/wiki-memory/
├── graph.yaml              # The gated accumulation graph
├── prompts/
│   └── draft_page.yaml     # Parse free text → typed wiki page
│   └── fix_refs.yaml       # Fix broken references given violations
├── nodes/
│   └── ref_gate.py         # ~30 lines: check all references resolve
├── wiki/                   # The wiki (seed state, grows across runs)
│   ├── javascript.yaml
│   ├── typescript.yaml
│   └── react.yaml
├── README.md
└── demo-output.log
```

### Wiki page shape

```yaml
# wiki/react.yaml
type: tool
id: react
category: frontend
references:
  - javascript
  - typescript
verdict: adopt
summary: Component-based UI library with virtual DOM.
```

Every `references` entry must resolve to a `*.yaml` file in `wiki/` with a
matching `id` field. No orphans.

### Graph design

```yaml
version: "1.0"
name: wiki-memory
description: Gated wiki accumulation — reference integrity enforced

data_files:
  wiki: "wiki/*.yaml"        # Glob: load all pages as dict keyed by stem (FR-629)

nodes:
  draft:
    type: llm
    prompt: draft_page
    state_key: drafted_page
    temperature: 0.3

  gate:
    type: python
    tool: ref_gate
    state_key: gate_result

  fix:
    type: llm
    prompt: fix_refs
    state_key: drafted_page
    loop_limit: 2

  persist:
    type: python
    tool: save_page
    state_key: _written

edges:
  - from: START
    to: draft
  - from: draft
    to: gate
  - from: gate
    to: persist
    condition: "state.gate_result.valid == true"
  - from: gate
    to: fix
    condition: "state.gate_result.valid == false"
  - from: fix
    to: gate
  - from: persist
    to: END
```

### The gate tool (~30 lines)

```python
def check_references(drafted_page: dict, wiki_dir: str) -> dict:
    """Check every reference in drafted_page resolves to an existing wiki page."""
    existing_ids = set()
    for f in Path(wiki_dir).glob("*.yaml"):
        with open(f) as fh:
            doc = yaml.safe_load(fh)
            if doc and "id" in doc:
                existing_ids.add(doc["id"])

    refs = drafted_page.get("references", [])
    missing = [r for r in refs if r not in existing_ids]

    if missing:
        return {"valid": False, "violations": missing}
    return {"valid": True, "violations": []}
```

### Usage pattern

```bash
# Run 1 — add a tool that references existing pages
yamlgraph graph run examples/demos/wiki-memory/graph.yaml \
  --var input="Vite is a next-gen build tool for JavaScript and TypeScript projects" \
  --full

# Run 2 — add a pattern referencing tools
yamlgraph graph run examples/demos/wiki-memory/graph.yaml \
  --var input="Component composition is a React pattern for building reusable UI" \
  --full

# Run 3 — attempt a tool with a broken reference (gate catches it)
yamlgraph graph run examples/demos/wiki-memory/graph.yaml \
  --var input="Bun is a fast JavaScript runtime that replaces Deno" \
  --full
# → gate rejects "deno" (no wiki/deno.yaml), LLM fixes by removing the reference
```

### Features showcased

| Feature | How |
|---|---|
| `data_files` | Load existing wiki at compile time |
| `write_data_file` (FR-625) | Persist new page back to wiki dir |
| Inline `schema:` | Typed wiki page (Pydantic, no external Python model) |
| `condition` routing | Gate pass/fail branching |
| `loop_limit` | Retry with violations as feedback (max 2 fix attempts) |
| Python leaf tool | The reference-integrity gate |

## Constraints

1. One Python file only (`ref_gate.py`, <50 lines). Everything else is YAML.
2. The gate is deterministic — `os.walk` + `yaml.safe_load` + set membership.
   No LLM call in the gate.
3. Seed wiki must contain 3 pages (enough to demonstrate cross-references).
4. Provider: `google` (cheapest for demo).
5. Demo must `graph lint` clean.
6. The gate tool is example-local (`nodes/ref_gate.py`), not a framework feature.
   If the pattern proves valuable, a future FR can promote it.

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/wiki-memory/graph.yaml` passes.
- [ ] Run 1: adds a valid page (all references resolve). Page persisted to `wiki/`.
- [ ] Run 2: adds a page referencing the page from run 1. Persisted.
- [ ] Run 3: LLM drafts a page with a non-existent reference. Gate rejects. LLM
      fixes. Gate passes. Page persisted without the orphan reference.
- [ ] `demo-output.log` captures all 3 runs showing gate pass, pass, reject→fix→pass.
- [ ] Seed wiki restored to 3-page initial state for git commit.
- [ ] README.md documents the pattern: read → draft → gate → fix/persist.
- [ ] No framework changes — entirely self-contained in `examples/demos/wiki-memory/`.

## Relationship to Other FRs

| FR | Relationship |
|---|---|
| FR-625 (`write_data_file`) | **Prerequisite** — shipped ✅ |
| FR-626 (write demo) | **Shipped ✅** — the ungated write-back demo. FR-628 builds on the same primitive but adds the gate loop. Both coexist: FR-626 = minimal write pattern, FR-628 = gated accumulation pattern. |
| FR-629 (`data_files` glob) | **Prerequisite** — shipped ✅. Enables per-file wiki pages: `wiki: "wiki/*.yaml"` discovers all pages without enumerating them. |
| FR-627 (canon-link gate) | **Distilled** — FR-627 proposed a framework-level gate for fandom fiction. This extracts the same invariant as an example-local tool. If the pattern proves reusable, FR-627 becomes the framework promotion FR. |
| `plan-fandom-generation.md` | **Extracted from** — the no-leak invariant and the gated-accumulation loop. |
| `plan-fandom-architecture.md` | **Miniaturized** — S1+S2+S4 (store, CRUD, gate) collapsed into one graph + one tool. |

## Prior Art

- [Harrison Chase — Wiki Memory](https://www.langchain.com/blog/wiki-memory) (2026-06-30): "persistent, structured, inspectable, updated over time."
- [Andrej Karpathy — LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): raw→wiki→schema; Ingest→Query→**Lint**.
- [Graphiti (Zep)](https://github.com/getzep/graphiti): prescribed ontology, strict edge types prevent drift.
- Community convergence: "drift is the dominant failure mode, and the lint pass is not optional."

---

## Judgement

**Authority: GRANTED with corrections.**

### Assessment

Well-motivated, well-scoped, timely. Domain choice (tech radar) is correct —
universal, no fiction baggage. The gate-loop pattern showcases 5 YAMLGraph
features in one graph. Effort estimate (1 day) is realistic.

### Corrections

1. ~~**`data_files` does not support directories.**~~ **RESOLVED by FR-629.**
   Glob support is now shipped. Use `wiki: "wiki/*.yaml"` to discover all pages
   as a dict keyed by stem. The original per-file design is now the correct
   implementation path. Gate reads from `state.wiki` (dict of all pages).

2. **Loop exhaustion fallback.** After 2 fix attempts, the graph errors via
   `loop_limit`. This is acceptable for a demo — document in README that the
   graph fails loudly if the LLM can't fix references in 2 attempts.

3. **One page type is sufficient.** The `type` field can exist in the schema
   without the gate enforcing it. Don't build type-specific validation unless
   it's tested. All 3 seed pages are type `tool`.

4. **No duplicate-id detection.** Note as a limitation in README. Acceptable
   for demo scope.

### Scope Freeze

- Per-file wiki pages (`wiki/*.yaml`) loaded via FR-629 glob support
- Gate reads from `state.wiki` (dict keyed by stem, loaded by glob)
- `write_data_file` persists new pages as individual files (`wiki/<id>.yaml`)
- One Python file, <30 lines
- 3 seed pages, all type `tool`
- `loop_limit: 2` on fix node; graph errors on exhaustion (documented)
- No duplicate-id detection (noted as limitation)
- No framework changes — entirely self-contained in `examples/demos/wiki-memory/`

### Enforcement Order

1. Create directory structure: `examples/demos/wiki-memory/`
2. Write seed pages: `wiki/javascript.yaml`, `wiki/typescript.yaml`, `wiki/react.yaml`
3. Write `nodes/ref_gate.py` (~20 lines, reads from `state.wiki` dict)
4. Write prompts: `draft_page.yaml` (with inline schema), `fix_refs.yaml`
5. Write `graph.yaml` using `data_files: wiki: "wiki/*.yaml"`
6. `yamlgraph graph lint` — must pass
7. Run 3 invocations; capture `demo-output.log`
8. Delete generated pages (keep only 3 seed pages for git)
9. Write README.md
10. Commit
