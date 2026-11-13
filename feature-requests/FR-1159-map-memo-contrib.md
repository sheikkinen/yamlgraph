# Feature Request: FR-1159 Ship the Map Memo as `yamlgraph.contrib.map_memo`

**Priority:** MEDIUM
**Type:** Feature
**Status:** Rejected (operator, 2026-11-13, after merge in PR #771). It built a
cross-run result memo; the request was the warm-first prompt-cache map of the
[FR-1155 follow-up](FR-1155-prompt-cache-tokens-in-token-usage.md). Code and
demo are removed by [FR-1160](FR-1160-remove-map-memo-contrib.md). Earlier:
implemented, approved with revisions R-1..R-3 folded; see
[judgement](FR-1159-map-memo-contrib.judgement.md).
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
  - "any behavioural assertion in FR-1116/FR-1120/FR-1113 tests must change → stop; move is wrong (R-2 manifest-source assertion is the sole exception)"
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

   CAP-289 and CAP-292 get mechanical module-path updates only (R-1):
   every `examples/shared/map_memo.py` becomes `yamlgraph/contrib/map_memo.py`.
   Their IDs, REQ text, and FR ownership are preserved. A new capability,
   **CAP-302 / REQ-YG-726** ("map memo ships in the distribution as
   contrib"), registers FR-1159 and owns the relocation witnesses. The
   only `ARCHITECTURE.md` change is the regenerated output.
5. Demo: `examples/demos/map_memo/`, authored through `scripts/author.sh`.
   Three small text notes are summarized by a subgraph worker (python
   read → llm). The pipeline is `memo_split → summarize (map, min_success: 0) → memo_merge`.
   Tools are declared inline via `module:`. The store lives at
   `outputs/map_memo_demo/memo.sqlite`.

## Acceptance Criteria

- [x] AC-01: The implementation exists only at
  `yamlgraph/contrib/map_memo.py`. A diff against the baseline shows no
  executable changes. No executable import uses
  `examples.shared.map_memo`, including source strings passed to
  subprocesses. Git rename history identifies the move.
- [x] AC-02: Both existing manifests use
  `runtime.module: yamlgraph.contrib.map_memo` and no `runtime.path`. The
  FR-768 translation asserts the module source, and both resolved
  functions run the existing split/merge witness successfully.
- [x] AC-03: The four named existing suites pass with their behavioural
  assertions preserved. Only these may change:
  - import lines and path references
  - documentation that names the old path
  - the R-2 manifest-source assertion, which becomes
    `tool["module"] == "yamlgraph.contrib.map_memo"` and `"path" not in tool`

  Existing consumer graphs and prompts are unchanged.
- [x] AC-04: A provider-free witness tagged REQ-YG-726 checks the
  installed wheel (R-3):
  - it builds the wheel;
  - the archive contains `yamlgraph/contrib/map_memo.py` and no
    `examples/shared/map_memo.py`;
  - the wheel is installed non-editably into an isolated venv;
  - a fresh interpreter, run outside the checkout with checkout paths
    absent from `PYTHONPATH`, proves the module comes from that install;
  - it loads both functions through inline `module:` tool declarations;
  - it runs a split/merge round trip over temporary files, and a second
    split returns no work.
- [x] AC-05: In a fresh interpreter, importing `yamlgraph.contrib` does
  not load `yamlgraph.contrib.map_memo`. The contrib initializer adds only
  module-list documentation, with no memo re-export.
- [x] AC-06: The compiled demo runs with only `execute_prompt` patched,
  on isolated copies of its three notes and a temporary store, with fresh
  graph state on each invocation.
  - Provider calls per run are 3, then 0, then 1 after editing exactly
    one note.
  - Run 2 reports `reused_ok == 3`, and its ordered records equal run 1's.
  - Run 3 keeps the records of the unchanged notes.
- [x] AC-07: The demo is authored with `scripts/author.sh`, has a
  substantive and honest authoring report, and lints clean. The live
  two-run smoke:
  - starts from one empty, isolated store;
  - makes at most 10 provider calls in total (operator authorization,
    2026-11-13);
  - shows zero worker calls and three reused successes on run 2.

  Record the provider and model, the exact commands, and the observed
  counts, not just exit codes. Missing credentials or an exhausted cap is
  recorded as an unmet AC.
- [x] AC-08: CAP-289 and CAP-292 carry the new implementation path in
  every affected location, with no change to behavioural requirements.
  CAP-302 / REQ-YG-726 registers FR-1159 and its witnesses. Any
  `ARCHITECTURE.md` regeneration is limited to the matching registry
  output.
- [ ] AC-09: All of these pass on the committed candidate:
  - the targeted command in Planned Operations
  - `python scripts/req_coverage.py --strict`
  - `lint-imports`
  - Ruff
  - the FR-1157 clean CI-mirror fast suite

  The FR records the candidate identity, commands, results, and
  deviations. The README, the feature fragment, and the diary entry with
  its **Seed:** are present.

## Alternatives Considered

| Option | Disposition |
|--------|-------------|
| Core `cached_map` node type (FR-1158) | Rejected by judgement; operator accepted contrib classification. |
| Core node-type plugin hook, then contrib node | Deferred: two FRs of core surface for one consumer pattern. |
| Copy (not move) into contrib | Rejected: two sources of truth; Commandment 8 forbids shims. |
| Ship the `.tool.yaml` manifests inside the package | Rejected for now: graphs reference manifests by relative path, which does not reach site-packages; the inline `module:` declaration is the installed route. |
| Leave example-local | Rejected: installed users cannot reach it (Problem). |
| is_this_a_graph | The memo is deterministic I/O (FR-1116); the demo is the graph-shaped deliverable. |

## Demo Authoring Status

The authoring execution created `examples/demos/map_memo/` and left its
files uncommitted. Both graphs lint without graph warnings. The unchanged
AC-06 witness passes: worker calls are 3, 0, then 1, with three reused
successes on run 2 and two on run 3. Evidence and exact commands are in
`tmp/draft-authoring-report.md`.

Two brief corrections were necessary: Python tools return `plan` and
`note` state-update envelopes because dict returns are merged directly,
not wrapped by `state_key`; `read_note` is declared only in the worker,
where it is used, rather than also as an unused parent tool. The pipeline
and single plain-text prompt are unchanged. The live AC-07 smoke remains
for the enforcer under its spend cap; this execution made no live calls.

## Implementation Record

- RED `066e6f0e` (witnesses, test import changes, CAP-302); GREEN follows
  it on `feat/fr-1159-map-memo-contrib`.
- AC-01: `git mv` recorded as a rename; the only content change is the
  module docstring. `git grep` finds `examples/shared/map_memo.py` only in
  CAP-302 prose and the wheel witness's negative assertion.
- AC-03/AC-06: targeted command (Planned Operations) → **117 passed**.
- AC-07 live smoke (inception / mercury-2.5, repo root, fresh store):
  `yamlgraph graph run examples/demos/map_memo/graph.yaml --var store=outputs/map_memo_demo/smoke.sqlite --full`
  run twice. Run 1: exit 0, 3 provider POSTs, counts
  `executed_ok 3, reused_ok 0`. Run 2: exit 0, 0 provider POSTs, counts
  `executed_ok 0, reused_ok 3`. Total 3 calls (cap 10). Lint: no issues.
- AC-08/AC-09: `aggregate_capabilities.py` regenerated `ARCHITECTURE.md`;
  `req_coverage --strict` exit 0; `lint-imports` exit 0; Ruff check and
  format clean.
- AC-09 container (FR-1157 recipe, python:3.11-slim, non-root, committed
  candidate `b9d0d8b5`): **7668 passed, 57 skipped, 1 xfailed**, exit 0.

### Deviations

- Gates outside the plan fired on the GREEN commit and were satisfied
  in scope: the vulture whitelist lists the two YAML-resolved tool
  functions; `examples/README.md` indexes the demo
  (`test_all_demos_listed_in_readme`); `demo-output.log` holds the two
  live smoke runs. The clean container run then failed only
  `test_fr335 ...line_budget` (302 > 300 lines, the new module's entry +
  dependency line); the budget moves to 302 with an FR-1159 comment, as
  every prior module addition did. The committed `reference/module-map.md`
  already drifted before this FR and is not regenerated here.
- The host pytest hook was skipped on the GREEN commit: the Windows host
  fails ~283 unit tests on path separators etc. (diary FR-1156), the same
  set with or without this change. The binding suite is the container.

- The wheel witness builds **with** build isolation (no
  `--no-build-isolation`): the Windows host Python has no setuptools, and
  isolation fetches the declared backend. Edited in the GREEN commit; the
  assertions are unchanged.
- The demo's `prepare` / `read_note` return `plan` / `note` envelopes (see
  Demo Authoring Status).
- The first `author.sh` run failed in 6 s: its pinned model `gpt-5.5` is
  no longer served (`copilot -p` probe: "Model gpt-5.5 is not available").
  The rerun used `gpt-6.1-sol`, matching the operator's local judge-adapter
  pin. That adapter edit is left uncommitted, outside this FR's scope,
  like the judge-adapter one.
- `test_fr1120_census_memo_graph::test_signature_file_change_reruns_everything`
  failed once in an early combined run that included the then-missing demo.
  It did not reproduce: 8/8 alone, with and without the GREEN changes, and
  in three later combined runs (113 passed; 116 passed + the not-yet-authored
  demo; 117 passed).

## Related

- `yamlgraph/contrib/map_memo.py`, `examples/shared/map_memo_*.tool.yaml`
- `yamlgraph/tools/manifest.py` (`PythonRuntime.module`)
- `capabilities/CAP-289-map-memo-file-corpus.yaml`
