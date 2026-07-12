# Feature Request: FR-717 Root-Package Seams — a2a/, export/, compile/

**Priority:** MEDIUM
**Type:** Enhancement (refactor — package structure; move-only)
**Status:** Judged (2026-07-12) — scope frozen with F1 naming note; authority granted; PR 3 sequenced after FR-715/716
**Effort:** 1–2 days (three independent PRs, one per sub-package)
**Requested:** 2026-07-12
**Spawned by:** docs/2026-07-12-review-refactoring.md P2.2 (27 flat root modules, 6,097 lines, no seams inside Layer 2)
**Related:** `.importlinter` (three-layer contract — gains three intra-layer seams), `reference/module-map.md` (regenerates), FR-713 F9 (one concern per PR — precedent for split delivery)

## Summary

Layer 2 is architecturally enforced against Layers 1/3 but internally a
flat bag of 27 modules. Three sub-packages already exist in the names —
move them under their seams, one PR each.

## Value Statement

Import-linter can only guard seams that exist as packages; today a2a
internals, export tooling, and the compile pipeline can reach into each
other freely. Naming the seams turns three implicit clusters into three
contracts — and shrinks the root listing every reader scans first.

## Proposed Solution (move-only; no logic changes)

| PR | New package | Moves | Lines |
|---|---|---|---|
| 1 | `yamlgraph/a2a/` | a2a_server.py, a2a_message.py | 613 |
| 2 | `yamlgraph/export/` | skill_export.py, skill_export_writer.py, mcp_server.py | 815 |
| 3 | `yamlgraph/compile/` | graph_loader.py, node_compiler.py, edge_compiler.py, map_compiler.py, pipeline_template.py, verify_insert.py | ~1,800 |

- Public names re-exported from `yamlgraph/__init__` where they already
  are; deep-import call sites (tests, examples, projects/) updated in
  the same PR — no aliasing left behind (no shims, Commandment 8).
- `.importlinter`: add three `independence`/`layers` contracts (e.g.
  compile must not import export; a2a must not import compile
  internals). The contract additions are the point, not the mkdir.
- `reference/module-map.md` regenerated; grep for stale paths in docs.

## Constraints

- PR 3 (compile/) touches the hottest imports — it lands LAST, after
  FR-715/FR-716 settle, so churn does not stack (mixed_commits_erode_
  auditability, applied at PR granularity).
- Move-only discipline: `git log --follow` must show 100% similarity
  renames; any behavior diff in the PR is scope violation.

## Acceptance Criteria

- [ ] AC-01 Per PR: full unit suite green UNMODIFIED except import-path
      mechanical updates (pure-move witness)
- [ ] AC-02 `.importlinter` gains ≥1 new contract per sub-package;
      `lint-imports` green; a deliberate cross-seam import in a scratch
      file fails it (gate witnessed)
- [ ] AC-03 Root `yamlgraph/*.py` module count ≤ 16 after PR 3
- [ ] AC-04 No `from yamlgraph.a2a_server import ...`-style stale paths
      anywhere in repo (docs included)
- [ ] Changelog fragment per PR; diary once at arc end

## Judgement (2026-07-12)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | `yamlgraph.compile` shadows the `compile` builtin as an attribute name — harmless for `from yamlgraph.compile import x` but `from yamlgraph import compile` would shadow the builtin at the importer's site | Keep `compile/` (the domain word is right); forbid re-exporting the package itself from `yamlgraph/__init__` — only its members (`load_and_compile` already re-exported, verified) |
| F2 | Move-only claim needs a mechanical witness, not reviewer discipline | AC-01 amended: `git diff --find-renames --summary` output pasted into each PR description; any non-rename line in yamlgraph/ fails review |

## Alternatives Considered

- One big PR — rejected: F9 lesson; unattributable failure.
- Also extract `executor*` into `runtime/` — deferred: FR-713's
  out-of-scope note pins the async-first promotion as the next substrate
  change; moving executor files now would force that FR to re-move them.
- Leave flat, rely on discipline — rejected:
  `architecture_as_diagram` trap; a seam that exists only in a review
  document is violated under the next deadline.
