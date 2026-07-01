# FR-629: `data_files` Glob Pattern Support

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented (2026-07-01) — commit `4430f068`. `data_files` accepts glob patterns (e.g. `wiki/*.yaml`), loaded as a dict keyed by file stem.
**Effort:** 0.5 day
**Requested:** 2026-07-01

## Summary

Extend the `data_files` directive to accept glob patterns (e.g. `wiki/*.yaml`),
loading all matching files into state as a dict keyed by filename stem.

## Value Statement

Graph authors get automatic discovery of files created by `write_data_file`,
making the read→write cycle symmetric: write creates individual files, read
discovers them without enumerating each one at authoring time.

## Problem

`data_files` currently accepts only a single file path per key. When
`write_data_file` creates new files across runs (e.g. wiki pages, accumulated
knowledge), the graph cannot discover them — only files explicitly listed in the
YAML are loaded.

This forces a workaround: store all data in a single ever-growing file
(FR-626/FR-628 pattern). That works for demos but defeats the benefits of
per-file storage:

- **No `git diff` per entity** — all changes are in one blob
- **Merge conflicts compound** — concurrent writes to one file conflict
- **Path ≠ identity** — violates the OKF/wiki convention where filename = entity id
- **`write_data_file` is asymmetric** — it writes individual files that
  `data_files` can't read back

The pattern this enables is the wiki-memory loop at scale: each run writes a
page to `wiki/<id>.yaml`, and the next run's `data_files` discovers all existing
pages automatically.

## Proposed Solution

Detect glob metacharacters (`*`, `?`, `[`) in a `data_files` value. When present,
expand via `Path.glob()` and return a dict keyed by filename stem.

### Usage

```yaml
# Before (enumerate each file manually)
data_files:
  js: wiki/javascript.yaml
  ts: wiki/typescript.yaml
  react: wiki/react.yaml

# After (discover all files matching pattern)
data_files:
  wiki: "wiki/*.yaml"    # → dict: {"javascript": {...}, "typescript": {...}, "react": {...}}
```

### Return shape

```python
# For a glob pattern, state key receives a dict:
state["wiki"] = {
    "javascript": {<contents of wiki/javascript.yaml>},
    "typescript": {<contents of wiki/typescript.yaml>},
    "react": {<contents of wiki/react.yaml>},
}
```

Keys are the filename stems (without extension). Values are the parsed YAML
contents of each file (same as single-file `data_files` today).

### Implementation sketch

In `yamlgraph/data_loader.py`, inside `load_data_files()`:

```python
import fnmatch

GLOB_CHARS = {"*", "?", "["}

for key, value in data_files.items():
    if not isinstance(value, str):
        raise DataFileError(...)

    if any(c in value for c in GLOB_CHARS):
        # Glob mode: expand pattern, return dict keyed by stem
        pattern_path = graph_dir / value
        base_dir = pattern_path.parent.resolve()

        # Security: base_dir must be within graph_dir
        try:
            base_dir.relative_to(graph_dir)
        except ValueError:
            raise DataFileError(
                f"data_files[{key}]: Glob pattern '{value}' escapes graph directory."
            ) from None

        matched = {}
        for file_path in sorted(graph_dir.glob(value)):
            # Security: each resolved file must be within graph_dir
            resolved = file_path.resolve()
            try:
                resolved.relative_to(graph_dir)
            except ValueError:
                continue  # skip symlinks escaping boundary

            with open(resolved, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            matched[file_path.stem] = data if data is not None else {}

        loaded[key] = matched
    else:
        # Existing single-file behavior (unchanged)
        ...
```

### Edge cases

| Case | Behavior |
|---|---|
| Glob matches 0 files | `state[key] = {}` (empty dict, not error) |
| Glob matches 1 file | `state[key] = {"stem": {...}}` (still a dict) |
| Pattern escapes graph dir | `DataFileError` raised |
| Symlink escapes graph dir | Silently skipped |
| Non-YAML file matched | `DataFileError` (same as today) |
| Empty file | Value is `{}` (same as today) |

## Constraints

1. **Backward compatible** — existing single-file paths work exactly as before.
   Glob behavior triggers only when metacharacters are present.
2. **Security** — same path-traversal guard as today. Every resolved path must
   be within the graph directory.
3. **Deterministic ordering** — files sorted by name for reproducible state.
4. **No recursive globs (`**`)** — keep it flat. `wiki/*.yaml` yes,
   `wiki/**/*.yaml` no. Recursive discovery adds complexity without proven need.
   Can be added later.
5. **Return type is always dict** — no list mode. Dict keyed by stem is the
   simplest interface that preserves identity (filename = key).

## Acceptance Criteria

- [ ] `data_files: wiki: "wiki/*.yaml"` loads all matching files into
      `state.wiki` as `dict[str, Any]`.
- [ ] Empty directory → empty dict (no error).
- [ ] Path traversal in glob pattern raises `DataFileError`.
- [ ] Symlinks escaping graph dir are silently skipped.
- [ ] Files sorted alphabetically for deterministic ordering.
- [ ] Single-file paths (no glob chars) behave exactly as before.
- [ ] `**` patterns raise `DataFileError` with a clear message (not supported).
- [ ] Unit tests cover: 0 matches, 1 match, N matches, traversal guard, symlink
      guard, `**` rejection.
- [ ] `graph lint` validates glob patterns (warns on 0 matches).
- [ ] Documentation updated in `reference/graph-yaml.md`.

## Relationship to Other FRs

| FR | Relationship |
|---|---|
| FR-625 (`write_data_file`) | **Completes the symmetry** — write creates files, glob reads them back |
| FR-626 (write demo) | Single-file workaround remains valid; glob is optional upgrade |
| FR-628 (wiki-memory gate) | **Enables per-file wiki pages** — FR-628 ships with single-file workaround first; after FR-629, can upgrade to per-file pages |
| FR-021 (`data_files`) | **Extends** — adds glob as a second mode alongside single-file |

---

## Judgement

**Authority: GRANTED.**

### Assessment

Clean, minimal framework extension. The problem is real (write creates files that
read can't discover), the solution is narrow (~30 lines in one file), and the
security model is already proven. The symmetry argument is compelling — without
this, `write_data_file` creates artifacts invisible to subsequent runs unless the
graph author pre-enumerates them.

### Corrections

1. **Remove unused `fnmatch` import** from implementation sketch — detection uses
   `any(c in value for c in GLOB_CHARS)` and expansion uses `Path.glob()`.
   Unnecessary imports fail `ruff`.

2. **`graph lint` on 0 matches should be INFO, not WARN** — an empty wiki at
   first run is normal (the `write_data_file` hasn't created any pages yet).

### Scope Freeze

- Modify `yamlgraph/data_loader.py`: add glob branch (~25 lines)
- Reject `**` with clear error message
- Add unit tests in `tests/unit/test_data_loader.py` (0 matches, 1 match,
  N matches, traversal guard, symlink guard, `**` rejection)
- Update `reference/graph-yaml.md` documentation
- `graph lint` info on 0 matches (not warn)
- No changes to state builder, node factory, or any other module

### Enforcement Order

1. RED: Write failing test for glob loading (0, 1, N files)
2. RED: Write failing test for `**` rejection
3. RED: Write failing test for glob path-traversal
4. GREEN: Implement glob branch in `data_loader.py`
5. Verify all tests pass
6. Update `reference/graph-yaml.md`
7. `graph lint` integration (info on 0 matches)
8. Commit
