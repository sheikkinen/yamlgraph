# Feature Request: FR-1159 Ship the Map Memo as `yamlgraph.contrib.map_memo`

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Requested:** 2026-11-13
**First consumer / first event:** the new provider-cheap demo
`examples/demos/map_memo` (in scope). It declares the memo tools inline as
`module: yamlgraph.contrib.map_memo`, which is the route an installed
user takes, since `examples*` is not in the wheel. Its second run over an
unchanged corpus makes zero worker calls. The two existing consumers,
`meta_map` and `person_profile_census`, keep working through the
`examples/shared` manifests, which are repointed at the contrib module.
**Research:** in-body dispositioned alternatives table (§ Alternatives Considered).
**Prior art:**
[FR-1158](FR-1158-cached-map-node.md) proposed a core `cached_map` node
type and was REJECTED. Its judgement classified persistent per-item reuse
as contrib/example on the evidence: two consumers plus a demo. The
operator accepted that classification on 2026-11-13. This FR is the
contrib shape, and it adds no node type, compiler, or state change.
[FR-1116](FR-1116-map-memo-file-corpus.md) wrote the memo and rejected a
framework-owned `memo:` key "for now". This FR keeps that rejection: no
key, no compiler change. Only the module's home moves.
[FR-1120](FR-1120-census-map-memo.md) added opaque `versions`. That
moves along unchanged.
[FR-755](FR-755-utils-fsm-ownership-ruling.md) defines the contrib tier:
a supported repeating pattern that is not core framework API. The memo
fits, with three graphs, two existing plus this demo.

## Summary

Move `examples/shared/map_memo.py` to `yamlgraph/contrib/map_memo.py`
with `git mv` and no behaviour change. Repoint the two `examples/shared`
manifests from `path: map_memo.py` to `module: yamlgraph.contrib.map_memo`.
Update the tests' imports. Leave no shim at the old path. Add a small
demo that uses the contrib module the way an installed user would.

## Value Statement

Anyone who installs `yamlgraph` can memoize a map over a file corpus.
Today the helper exists only in a source checkout.

## Problem

`pyproject.toml` excludes `examples*` from the distribution, so
`map_memo_split` and `map_memo_merge` are unreachable for installed users.
Each new consumer outside this repository would copy the file, which
would make it the sixth reinvention (FR-1116 cites five).

## Ideal Result

`from yamlgraph.contrib.map_memo import map_memo_split, map_memo_merge`
works in an installed wheel. Every existing memo consumer and test
passes unchanged in behaviour. A demo shows the inline tool declaration.

## Planned Operations

```yaml
probes:
  - "done: PythonRuntime supports `module:` (yamlgraph/tools/manifest.py:33)"
  - "done: map_memo.py imports only stdlib, pydantic, yamlgraph.models (contrib layer-legal)"
branches:
  - "any FR-1116/FR-1120/FR-1113 test changes behaviour → stop; move is wrong"
  - "judge round cap → re-file shorter FR"
delegations:
  - "judge.sh: 1 run"
  - "author.sh: 1 run (examples/demos/map_memo)"
waits:
  - "judge"
  - "CI"
commands:
  - python -m pytest tests/unit/test_fr1116_map_memo.py tests/unit/test_fr1120_map_memo_versions.py tests/unit/test_fr1113_meta_map.py tests/unit/test_fr1120_census_memo_graph.py tests/unit/test_fr1159_map_memo_contrib.py -q --no-cov
  - python scripts/req_coverage.py --strict
  - lint-imports
  - "clean CI-mirror container fast suite on the committed HEAD (FR-1157 recipe)"
  - yamlgraph graph lint examples/demos/map_memo/graph.yaml
  - "live smoke: run the demo twice, ≤ 10 provider calls total (operator-approved 2026-11-13)"
```

## Proposed Solution

1. `git mv examples/shared/map_memo.py yamlgraph/contrib/map_memo.py`.
   The content is unchanged, apart from the module docstring naming its
   new home. `yamlgraph/contrib/__init__.py` lists the module in its
   docstring and does **not** re-export it, so `import yamlgraph.contrib`
   stays free of sqlite.
2. Both `examples/shared/map_memo_*.tool.yaml` change
   `runtime.path: map_memo.py` to `runtime.module: yamlgraph.contrib.map_memo`.
   No graph changes.
3. Tests import `yamlgraph.contrib.map_memo`. The manifest-resolution
   witness asserts that the module resolves instead of the file path. The
   `copytree(examples/shared)` fixture in `test_fr1120_census_memo_graph.py`
   keeps working, because the module is importable.
4. Update docs: `examples/shared/README.md` points to the contrib module and
   shows the inline declaration:

   ```yaml
   tools:
     map_memo_split:
       type: python
       module: yamlgraph.contrib.map_memo
       function: map_memo_split
   ```

   CAP-289 and CAP-292 do not change. A new capability, **CAP-302 /
   REQ-YG-726** ("map memo ships in the distribution as contrib"), owns the
   relocation witnesses.
5. Demo: `examples/demos/map_memo/`, authored through `scripts/author.sh`.
   Three small text notes are summarized by a subgraph worker (python
   read → llm). The pipeline is `memo_split → summarize (map, min_success: 0) → memo_merge`.
   Tools are declared inline via `module:`. The store lives at
   `outputs/map_memo_demo/memo.sqlite`.

## Acceptance Criteria

- [ ] AC-01: `yamlgraph/contrib/map_memo.py` exists, and
  `examples/shared/map_memo.py` does not. Nothing in the repository imports
  `examples.shared.map_memo`. `git log --follow` shows the move.
- [ ] AC-02: Both shared manifests load through FR-768 and resolve
  `yamlgraph.contrib.map_memo` functions. The FR-1116 manifest witness is
  updated accordingly.
- [ ] AC-03: The FR-1116, FR-1120, FR-1113, and FR-1120-census tests pass.
  Their assertion bodies are unchanged; only import or path lines change.
- [ ] AC-04: A witness tagged REQ-YG-726 builds the wheel file list, or
  inspects `setuptools` package discovery, and asserts that
  `yamlgraph/contrib/map_memo.py` is included.
- [ ] AC-05: `import yamlgraph.contrib` does not import `sqlite3`-backed
  memo code (no eager re-export).
- [ ] AC-06: A provider-free test of `examples/demos/map_memo` (patched
  `execute_prompt` with a call counter) runs the graph twice in one
  `tmp_path` store. Run 1 makes 3 calls, and run 2 makes 0 and reports
  `reused_ok == 3`. Editing one note makes run 3 call exactly once.
- [ ] AC-07: The demo is authored via `scripts/author.sh` with an honest
  report. `yamlgraph graph lint` is clean. The live smoke (operator-approved
  2026-11-13, ≤ 10 provider calls) shows run 2 with zero worker calls.
- [ ] AC-08: `lint-imports`, `req_coverage --strict`, ruff, and the clean
  CI-mirror suite pass. There is a changelog fragment of type `feat`, and
  a diary entry with a **Seed:**.

## Alternatives Considered

| Option | Disposition |
|--------|-------------|
| Core `cached_map` node type (FR-1158) | Rejected by judgement; operator accepted contrib classification. |
| Core node-type plugin hook, then contrib node | Deferred: two FRs of core surface for one consumer pattern. |
| Copy (not move) into contrib | Rejected: two sources of truth; Commandment 8 forbids shims. |
| Ship the `.tool.yaml` manifests inside the package | Rejected for now: graphs reference manifests by relative path, which does not reach site-packages; the inline `module:` declaration is the installed route. |
| Leave example-local | Rejected: installed users cannot reach it (Problem). |
| is_this_a_graph | The memo is deterministic I/O (FR-1116); the demo is the graph-shaped deliverable. |

## Related

- `examples/shared/map_memo.py`, `examples/shared/map_memo_*.tool.yaml`
- `yamlgraph/tools/manifest.py` (`PythonRuntime.module`)
- `capabilities/CAP-289-map-memo-file-corpus.yaml`
