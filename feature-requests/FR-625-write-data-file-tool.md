# FR-625: Built-in `write_data_file` Tool

**Status:** Judged — Authority GRANTED with corrections (2026-06-30)
**Priority:** Medium
**Type:** Feature
**Effort:** 0.5 day
**Requested:** 2026-06-30

## Problem

YAMLGraph has `data_files` for reading structured YAML/JSON into graph state at compile time. There is no symmetric write primitive. Any graph that needs to persist structured output back to a file (for cross-run state, wiki memory, or incremental knowledge accumulation) must define a custom Python tool.

This makes the wiki memory pattern — where a graph reads existing knowledge, augments it, and writes it back — require per-project Python boilerplate instead of being a declarative YAML-only pattern.

Existing workarounds:
- `diary_index` demo uses a custom `write_index` Python tool
- `novel_generator` has no cross-run state at all (stateless between invocations)
- Any user wanting persistent graph artifacts writes their own file-writing tool

## Proposal

Add a built-in tool `write_data_file` in `yamlgraph/tools/` that writes structured data (dict/list) to a YAML or JSON file within the workspace.

### Usage in a graph

```yaml
data_files:
  world: wiki/world_bible.yaml          # READ existing wiki (existing feature)

tools:
  save_wiki:
    type: builtin
    builtin: write_data_file

nodes:
  compress_knowledge:
    type: llm
    prompt: compress_to_wiki
    state_key: updated_wiki
    variables:
      existing: "{state.world}"
      new_content: "{state.prose_sections}"

  persist_wiki:
    type: python
    tool: save_wiki
    state_key: _wiki_written
    variables:
      path: wiki/world_bible.yaml
      data: "{state.updated_wiki}"

edges:
  - from: compress_knowledge
    to: persist_wiki
  - from: persist_wiki
    to: END
```

### Implementation

```python
# yamlgraph/tools/write_data_file.py

def write_data_file(path: str, data: Any, *, format: str = "auto") -> str:
    """Write structured data to a YAML or JSON file.

    Args:
        path: Relative path within workspace (no traversal allowed)
        data: Dict or list to serialize
        format: "yaml", "json", or "auto" (inferred from extension)

    Returns:
        Absolute path of written file
    """
```

### Security boundary

1. **Path must be relative.** Absolute paths rejected.
2. **No traversal.** `..` segments rejected after normalization.
3. **Workspace-scoped.** Resolved against graph file's directory (same as `data_files` resolution).
4. **Atomic write.** Write to tempfile, then `os.replace()` to avoid partial writes.
5. **No self-modification.** Refuse to write the graph file itself or any file under its `prompts_dir` (graph-relative detection at compile time, not runtime path matching).

### Format detection (v1: YAML-only)

| Extension | Format |
|---|---|
| `.yaml`, `.yml` | YAML (PyYAML `safe_dump`, block style, allow_unicode) |
| other | Error (v1 — JSON deferred until `data_files` also supports JSON read) |

## Judgement (2026-06-30)

**Verdict: Authority GRANTED with corrections.**

Valid built-in tool — symmetry with `data_files` read is the right argument. The
`schema_loader` tool (FR-426) proves the registration pattern. 0.5 day effort is
realistic.

**Correction 1 (scope — YAML-only in v1).** `data_files` only supports YAML reads.
Adding JSON write without JSON read creates format asymmetry. v1 writes YAML only;
JSON deferred until `data_files` gains JSON support.

**Correction 2 (tool type — follow schema_loader pattern).** `type: builtin` with
a `builtin:` subkey adds a dispatch mechanism that doesn't exist. Use its own type
string `type: write_data_file` (same pattern as `type: schema_loader`).

**Correction 3 (title — drop "Wiki Memory Primitive").** This is a file-write tool,
not a memory system. The wiki memory pattern is a *use case* documented in
`reference/`, not the tool identity. Confusing it with FR-617 (actual memory node)
misleads.

**Correction 4 (self-modification guard — simplify).** Runtime detection of "graph
or prompt paths" requires access to compiled config inside a Layer 3 tool (layer
violation). Instead: capture `graph_path` and `prompts_dir` at tool registration
time (compile-time closure), refuse writes to those paths. Simpler, deterministic,
no layer crossing.

**Frozen scope.** YAML-only write; graph-relative path resolution; atomic write;
path traversal guard; self-modification guard via compile-time closure;
`type: write_data_file` registration; round-trip integration test with `data_files`
read.

## Constraints

1. Layer 3 only — no imports from Layer 2 (graph_loader, executor).
2. No filesystem writes outside the workspace boundary.
3. Deterministic serialization (block style YAML, allow_unicode, sort_keys=False).
4. Creates intermediate directories if needed (`os.makedirs(parents=True)`).
5. Tool type: `type: write_data_file` (own type string, same pattern as `schema_loader`).

## Acceptance Criteria

- [ ] `yamlgraph/tools/write_data_file.py` implements the tool.
- [ ] Registered in built-in tool registry (alongside `shell` tool).
- [ ] Unit test: writes YAML, reads back, content matches.
- [ ] Unit test: writes JSON, reads back, content matches.
- [ ] Unit test: rejects absolute path.
- [ ] Unit test: rejects `../` traversal.
- [ ] Unit test: rejects overwriting graph YAML.
- [ ] Unit test: creates parent directories.
- [ ] Unit test: atomic write (crash mid-write doesn't leave partial file).
- [ ] Integration test: graph with `data_files` read + `write_data_file` write round-trips.
- [ ] Lint: `yamlgraph graph lint` accepts graphs using the built-in tool.
- [ ] Documentation: add to `reference/graph-yaml.md` under tools section.

## Use Cases Enabled

1. **Novel generator wiki memory** — Character bible, world facts, style guide persisted between chapters.
2. **Diary index** — Replace custom `write_index` tool with built-in.
3. **Any incremental pipeline** — Research agent accumulates findings across multiple runs.
4. **Schema-driven extraction** — Output schemas that evolve (new fields discovered) written back for next run.

## Related

- `data_files` (existing read primitive in `data_loader.py`)
- `diary_index` demo (FR-254, uses custom write tool)
- Wiki Memory concept (LangChain blog, June 2026): agent-maintained persistent knowledge as files
- FR-618: Lazy reference variables (related state management)
