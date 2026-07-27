# Feature Request: FR-763 Example taxonomy scanner must scope discovery to git-tracked files

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-27
**First consumer / first event:** any developer with local generator
outputs (e.g. `examples/yamlgraph_gen/outputs/*`) running the
`example-taxonomy-check` pre-commit hook — it fails falsely today
(observed 2026-07-27 on a clean merged main: `--check` reported the
committed taxonomy stale with 86 phantom insertions).

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

- [ ] AC-01: Root discovery considers only git-tracked files; a
      gitignored directory containing a `graph.yaml` produces no
      taxonomy row.
- [ ] AC-02: `example_taxonomy_scan.py --check` passes on a checkout
      that contains gitignored `examples/yamlgraph_gen/outputs/*`
      directories with graph YAML in them (regression test uses a tmp
      git repo fixture with an ignored dir).
- [ ] AC-03: Regenerated taxonomy on such a checkout is byte-identical
      to regeneration on a clean checkout.
- [ ] AC-04: Untracked-but-not-ignored files do not create roots either
      (discovery is tracked-set-scoped, not merely ignore-aware), so a
      half-added example fails visibly at `git add` time, not silently
      in taxonomy drift.
- [ ] AC-05: Graceful fallback with a warning when not running inside a
      git work tree.
- [ ] AC-06: Tests tagged `@pytest.mark.req(...)` under the CAP-213
      requirement; changelog fragment added.

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
- Cleanup rider (same surface, mechanical): remove the moot FR-760
  `PENDING_GAPS` entries from `scripts/direct_import_scan.py` —
  langchain-core is now a declared core dependency, and the entry's own
  comment says it "dies with FR-760."
