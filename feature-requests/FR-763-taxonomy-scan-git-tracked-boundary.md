# Feature Request: FR-763 Example taxonomy scanner must scope discovery to git-tracked files

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced (2026-07-27)
**Effort:** 0.5 days
**Requested:** 2026-07-27
**Prior art:** The prior-art gate matched FR-759
(`otel-observability-boundary`) on the shared nouns *scan/boundary* —
not substantive: FR-759 governs the OTel per-node export boundary, a
different subsystem. This FR is a direct child of FR-762 (CAP-213, the
example dependency taxonomy generator it fixes) and shares surface with
FR-760/FR-761 only as cited context. No prior FR — approved or
rejected — has proposed scoping example-root discovery to the
git-tracked tree; the territory is new.
**First consumer / first event:** any developer with local generator
outputs (e.g. `examples/yamlgraph_gen/outputs/*`) running
`python scripts/example_taxonomy_scan.py --check` — it fails falsely
today (observed 2026-07-27 on a dirty merged main: `--check` reported
the committed taxonomy stale with 86 phantom insertions, every one a
gitignored `examples/yamlgraph_gen/outputs/*` directory). There is no
committed `example-taxonomy-check` pre-commit hook today (R-1); this FR
does not add one — a new enforcement hook is separate human-reviewed
scope.

## Summary

`scripts/example_taxonomy_scan.py` discovers example roots by walking
the raw filesystem under `examples/`. It therefore counts **gitignored**
directories as example roots: `examples/yamlgraph_gen/outputs/*` are
generator test outputs, explicitly gitignored, yet each contains a
`graph.yaml` and is admitted as a root. On any machine with local
generator outputs, `example_taxonomy_scan.py --check` reports the
committed `examples/dependency-taxonomy.yaml` as stale; CI stays green
only because clean checkouts lack those directories.

## Value Statement

Developers stop getting false `example-taxonomy-check` hook failures
caused by their own local, gitignored artifacts, and the committed
taxonomy becomes a deterministic function of the repository content
rather than of whoever's machine last regenerated it.

## Problem

The taxonomy's contract (FR-762) is "one row per example root *in the
repository*." The implementation's boundary is the filesystem, not the
git-tracked set — a `workspace_is_not_boundary` defect. Consequences:

1. **False-stale failures:** `--check` fails locally whenever gitignored
   directories under `examples/` contain graph YAML, entry points, or
   qualifying READMEs. Observed drift on 2026-07-27: 86 insertions, all
   under `examples/yamlgraph_gen/outputs/` (agent-test, debug-test,
   ext-test, interrupt-test, map-debug*, …), every one gitignored
   (`git check-ignore` confirms).
2. **Poisoned regeneration:** a developer who "fixes" the failure by
   running the generator commits phantom rows for directories that do
   not exist in the repository. The committed artifact then fails
   `--check` in CI and on every other machine.
3. **Four review rounds missed it** (PR #464) because review worktrees
   were always clean checkouts — the defect only manifests where
   ignored artifacts exist.

This is the diary's one law: normalize at the boundary where external
data enters. The external data here is the filesystem; the boundary
where it should be normalized is root discovery.

## Ideal Result

The taxonomy is a pure function of the git-tracked tree: regenerating
it on any machine — dirty, clean, CI — produces byte-identical output,
and `--check` failures always mean the repository changed, never that
the machine did.

## Proposed Solution

Filter discovery to git-tracked paths at the boundary — in the
directory walk, before classification:

- Obtain the tracked set once via `git ls-files -z -- examples/`
  (or equivalently prune with `git check-ignore --stdin` for
  directories); cache it for the run.
- A directory qualifies as an example-root *candidate* only if it
  contains at least one tracked file; root markers (graph YAML,
  entry point, fenced README usage command) are evaluated against
  tracked files only.
- Fallback: if `git` is unavailable (e.g. an exported archive), warn
  and fall back to the current filesystem walk — `--check` is a repo
  hook, so the fallback path never gates.

No taxonomy schema change; `examples/dependency-taxonomy.yaml` content
for a clean checkout is unchanged.

## Acceptance Criteria

(Adopted from the judgement's revised acceptance criteria.)

- [ ] AC-01: In a git work tree, root discovery obtains the tracked path
      set under `examples/` once via git and never treats ignored or
      untracked files as discovery input.
- [ ] AC-02: Root markers are evaluated against tracked files only: an
      ignored or untracked `graph.yaml`, Python main entrypoint, or
      README usage command cannot create a taxonomy row even when the
      directory contains other filesystem artifacts.
- [ ] AC-03: A tmp git repo regression proves a gitignored directory
      under `examples/yamlgraph_gen/outputs/` containing `graph.yaml`
      produces no taxonomy row.
- [ ] AC-04: `example_taxonomy_scan.py --check` (or the checked code path
      with monkeypatched module constants) passes in a fixture checkout
      that contains the ignored output directory from AC-03 and a
      matching committed `examples/dependency-taxonomy.yaml`.
- [ ] AC-05: Regeneration in a checkout with ignored generator outputs is
      byte-identical to regeneration from the same tracked tree without
      those outputs.
- [ ] AC-06: An untracked-but-not-ignored example root does not create a
      taxonomy row; after that same file is `git add`ed, it is eligible
      for discovery and taxonomy drift becomes visible.
- [ ] AC-07: Outside a git work tree, the scanner emits a warning and
      preserves the current filesystem-walk behavior so exported archives
      and existing non-git fixture tests remain usable.
- [ ] AC-08: CAP-213 / REQ-YG-571 is updated to state the git-tracked
      discovery boundary, and every new or changed test is tagged with
      `@pytest.mark.req("REQ-YG-571")`.
- [ ] AC-09: No changes are made to `scripts/direct_import_scan.py`,
      `PENDING_GAPS`, pre-commit hooks, CI workflows, or taxonomy schema
      under this FR.
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`.

## Frozen scope (from judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/example_taxonomy_scan.py`: root discovery + marker evaluation normalize candidates to git-tracked files before classification. |
| D-2 | `tests/unit/test_example_taxonomy_scan.py`: tmp git repo regression for ignored/untracked roots + fallback outside a work tree. |
| D-3 | `capabilities/CAP-213-example-dependency-taxonomy.yaml`: REQ-YG-571 updated to include the tracked-tree boundary. |
| D-4 | `ARCHITECTURE.md`: regenerated capability text only if required by the existing aggregation workflow. |
| D-5 | this FR: implementation status/decisions after enforcement. |
| D-6 | `changelog/unreleased/`: one changelog fragment. |

Enforcement conditions (GATE): C-1 normalize at discovery, not
post-classification, and never hard-code the `yamlgraph_gen/outputs`
name; C-2 use git as the source of truth (no `.gitignore` reimpl);
C-3 fall back only when git is unavailable / not a work tree —
unexpected git errors inside a work tree fail loudly; C-4 no
enforcement infrastructure changes; C-5 no `direct_import_scan.py`
changes; C-6 `examples/dependency-taxonomy.yaml` stays byte-identical
for the current tracked tree.

## Alternatives Considered

- **Extend the walker's noise-dir prune list with `outputs/`:** treats
  one symptom; the next gitignored artifact (checkpoints, exports,
  scratch graphs) recreates the bug. Rejected — `downstream_fix`.
- **Add the ignored dirs to `--check`'s exclusions only:** leaves
  regeneration poisoned (consequence 2). Rejected.
- **Respect `.gitignore` by parsing it in Python:** reimplements git's
  matching semantics (negations, nested ignore files) — the fourth
  special case would demand a proper parser anyway. Git itself is the
  parser; ask it. Rejected.

## Related

- FR-762 (example dependency taxonomy) — the governing capability,
  CAP-213 / REQ-YG-571.
- `docs/diary/diary-2026-07-27-sixteen-not-approveds-forensic.md` —
  the forensic that surfaced this defect.
- Scripture traps: `workspace_is_not_boundary`, `downstream_fix`.

> R-2 (judgement): the FR-760 `PENDING_GAPS` cleanup in
> `scripts/direct_import_scan.py` is orthogonal to this boundary defect
> and is explicitly OUT OF SCOPE here; split into its own FR if desired.

## Implementation Status (Enforced 2026-07-27)

Delivered within the frozen scope; git status shows only D-1..D-6 surfaces
touched (no `direct_import_scan.py`, hooks, or CI — AC-09/C-5 held).

- **D-1** `scripts/example_taxonomy_scan.py`: added `_git_tracked_files()`
  (single `git ls-files -z` per run, `rev-parse --is-inside-work-tree`
  guard) and `_is_tracked()`. Threaded a `tracked` set through
  `discover_roots` → `_is_example_root`/`_has_graph_yaml`/
  `_has_main_entrypoint`/`_has_readme_usage_command` and through
  `classify_root` → `_root_imports`/`_local_module_names`/
  `_yaml_tool_module_paths`/`_readme_cli_surface_paths`. `build_taxonomy`
  resolves the tracked set once and shares it. Normalization is at
  discovery/marker evaluation, not post-classification (C-1); git is the
  sole `.gitignore` authority (C-2); unexpected git failure inside a work
  tree raises `RuntimeError`, only "not a work tree"/"git unavailable"
  warns and falls back (C-3, AC-07).
- **D-2** `tests/unit/test_example_taxonomy_scan.py`: 5 new tmp-git-repo
  regressions — ignored dir (AC-01/03), untracked→added (AC-06), tracked
  non-marker + untracked marker (AC-02), dirty==clean byte-identical
  (AC-04/05), fallback warning outside a work tree (AC-07). All 33 module
  tests pass.
- **D-3** `capabilities/CAP-213`: REQ-YG-571 states the git-tracked
  boundary (AC-08).
- **D-4** `ARCHITECTURE.md`: regenerated via `aggregate_capabilities.py`
  (cap-architecture-sync gate).
- **D-6** `changelog/unreleased/fr763-taxonomy-git-tracked-boundary.md`
  (AC-10, `type: fix`, `req: REQ-YG-571`).

Verification on the reporting (dirty) machine: `example_taxonomy_scan.py
--check` now passes (135 roots) and `git diff examples/dependency-taxonomy.yaml`
is empty — byte-identical committed taxonomy (C-6, AC-05). ruff, strict
req-coverage, capability validation, and the changelog-req gate all green.

### Review round 1 (PR #466 P1) — fixed 2026-07-27

The reviewer proved a residual filesystem leak: `_local_module_names`
derived directory-based local-module names from `root.rglob("*")` and the
ancestor sibling scan filtered untracked *files* only — so an untracked
directory named like a third-party package (e.g. `examples/real/requests/`)
flipped a tracked root from externally-provisioned to extra-backed.

Fix (RED 047b2f5c, GREEN e8f8a36a): a directory contributes a local-module
name only when it has at least one tracked descendant (derived from the
tracked set's ancestor directories); applied to both the subtree walk and
the ancestor sibling scan. Two regressions added (reviewer's probe as
blueprint): unit-level name exclusion and end-to-end classification
invariance under an untracked directory. 35 module tests pass; `--check`
green at 135 roots.
