# FR-650: Canon pages organized by type in subfolders

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-02

## Summary

Organize canon pages into subfolders by their `type` field (`canon/character/`, `canon/event/`, etc.) instead of a flat directory.

## Value Statement

World authors get navigable canon structure as the page count grows beyond seed files, with Obsidian vault compatibility via typed folders.

## Problem

After 3 worldgen loops the canon directory has 25 files in a flat structure. At scale (50–100+ pages) this becomes unnavigable. Pages already carry a `type` field — the filesystem should reflect it.

Current:
```
canon/
  kaelen.yaml
  ashfall_pact.yaml
  ashguard.yaml
  ...23 files flat
```

Target:
```
canon/
  character/   (7)
  event/       (3)
  faction/     (2)
  rule/        (3)
  location/    (3)
  item/        (1)
  material/    (1)
  phenomenon/  (1)
  premise/     (1)
  synopsis/    (1)
```

## Proposed Solution

Four files change. No schema changes. The `id` remains the unique key — folder is physical organization only. References between pages stay as bare ids since readers use `rglob`.

### 1. `nodes/reload_canon.py` — read recursively

```python
# Before
for f in sorted(canon_dir.glob("*.yaml")):

# After
for f in sorted(canon_dir.rglob("*.yaml")):
```

### 2. `nodes/persist_pages.py` — write into type subfolder

Three write paths need the same subfolder logic:

**(a) `_validate_and_write` — deepened pages:**
```python
page_type = page.get("type", "misc")
type_dir = canon_dir / page_type
type_dir.mkdir(parents=True, exist_ok=True)
target = type_dir / f"{page['id']}.yaml"
# tempfile also in type_dir for atomic os.replace
fd, tmp_path = tempfile.mkstemp(dir=type_dir, suffix=".tmp", prefix=".persist_")
```

**(b) Skeleton target path:**
```python
page_type = page.get("type", "misc")
type_dir = canon_dir / page_type
type_dir.mkdir(parents=True, exist_ok=True)
target = type_dir / f"{page['id']}.yaml"
```

**(c) Skeleton exists-check** — search recursively since the file may already be in a type subfolder:
```python
# Before
if target.exists():
    continue

# After
if any(canon_dir.rglob(f"{page['id']}.yaml")):
    continue
```

Skeleton `mkstemp` also uses `type_dir`:
```python
fd, tmp_path = tempfile.mkstemp(dir=type_dir, suffix=".tmp", prefix=".persist_")
```

### 3. `nodes/render_wiki.py` — read recursively

```python
# Before
canon_path.glob("*.yaml")

# After
canon_path.rglob("*.yaml")
```

### 4. `nodes/ref_gate.py` — type-aware save_path

```python
# Before
result["save_path"] = f"canon/{own_id}.yaml"

# After
page_type = drafted.get("type", "misc")
result["save_path"] = f"canon/{page_type}/{own_id}.yaml"
```

### 5. Migrate existing seed files

Move 10 seed files from `canon/` into their type subfolders. Track seeds with `git add -f`.

### 6. `.gitignore`

Add `canon/*/` to ignore dynamic subfolders. Seed files remain tracked via `git add -f`.

## Acceptance Criteria

- [ ] `reload_canon` reads pages from all type subfolders via `rglob`
- [ ] `persist_pages` writes new pages into `canon/{type}/` subfolder (all 3 write paths)
- [ ] `persist_pages` skeleton exists-check uses `rglob` to find existing pages across subfolders
- [ ] `persist_pages` `mkstemp` uses `type_dir` for atomic `os.replace`
- [ ] `render_wiki` reads pages from all type subfolders
- [ ] `ref_gate` derives `page_type` from `drafted` and produces correct save_path
- [ ] Existing seed files migrated to subfolders
- [ ] Pipeline runs end-to-end with subfolder layout
- [ ] One test verifies type-subfolder creation by persist_pages
- [ ] `.gitignore` updated with `canon/*/`

## Alternatives Considered

- **Virtual folders in Obsidian only**: Obsidian supports folder-by-tag, but that doesn't help filesystem navigation or `ls`.
- **Type prefix in filename** (`character-kaelen.yaml`): Breaks existing id-based references without adding navigability.

## Related

- FR-649: persist boundary normalization (just committed)
- FR-648: Obsidian wiki output
- [nodes/reload_canon.py](../examples/novel_fandom/nodes/reload_canon.py)
- [nodes/persist_pages.py](../examples/novel_fandom/nodes/persist_pages.py)
- [nodes/render_wiki.py](../examples/novel_fandom/nodes/render_wiki.py)
- [nodes/ref_gate.py](../examples/novel_fandom/nodes/ref_gate.py)

## Judgement

**Verdict: Granted with amendments.**

### What's sound
- Clear, minimal, internally consistent. Four files, one concept (`glob` → `rglob` for readers, `type` subfolder for writers).
- No schema changes. `id` stays the unique key. References stay bare ids.
- The `type` field already exists on every page — the filesystem should reflect it.

### Amendments

1. **persist_pages has THREE write paths, not two.** The FR says "both write paths" but there are three: (a) `_validate_and_write` deepened pages, (b) skeleton fallback in `_persist_impl`, and (c) the skeleton path also has `target = canon_dir / f"{page['id']}.yaml"` and `target.exists()` check. All three must use type subfolder. The `target.exists()` check for skeletons must also search recursively (a skeleton might already exist in a type subfolder from a previous run).

2. **Skeleton exists-check needs `rglob`.** Currently skeletons skip writing if `target.exists()`. With subfolders, skeletons might have `type` and the file could already be at `canon/{type}/{id}.yaml`. Change the exists-check to search by id across subfolders: `any(canon_dir.rglob(f"{page['id']}.yaml"))`.

3. **`tempfile.mkstemp(dir=...)` must use `type_dir`, not `canon_dir`.** Both write paths create temp files with `dir=canon_dir`. After the change, temp files must go into the type subfolder so `os.replace()` works atomically (same filesystem).

4. **ref_gate: `page_type` is not in scope.** The FR shows `result["save_path"] = f"canon/{page_type}/{own_id}.yaml"` but `page_type` is not derived. Use `drafted.get("type", "misc")`.

5. **`.gitignore` needs `canon/*/` pattern for dynamic subfolders.** Seed subfolders are tracked; dynamic pages in those same subfolders are not. This requires per-file `.gitignore` entries for seed files (tracked) vs everything else (ignored). **Simpler alternative:** keep all of `canon/` untracked and list seed files explicitly in git (they're already committed). Add `canon/*/` to `.gitignore` alongside tracking seeds with `git add -f`.

6. **Drop acceptance criterion "Tests updated for new path structure"** — existing tests use injectable `canon_dir` with temp directories. They'll work with subfolders automatically since tests create their own dir structure. Add one test that verifies type-subfolder creation instead.

### Scope freeze
Four files + seed migration + .gitignore + one test. No other changes.
