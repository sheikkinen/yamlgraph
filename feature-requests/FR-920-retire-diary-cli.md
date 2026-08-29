# Feature Request: Retire the `yamlgraph diary` CLI surface (FR-124 wrapper, CAP-46)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (revisions R-1..R-4 folded 2026-08-30; [judgement](FR-920-retire-diary-cli.judgement.md))
**Effort:** 0.5 day
**Requested:** 2026-08-30
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops running a
204-line test file for a CLI wrapper no automation has ever invoked and
retires a capability claim with a zero-consumer production record.
**Research:** first-class in-FR consumer record (§Evidence below, R-1),
gathered 2026-08-30 at origin/main 8ec9cb41 in this worktree
(`name_the_tree_the_evidence_came_from`).
**Prior art:** FR-124 (created the surface being retired — the importer
extraction is kept, the CLI wrapper is convicted; spec survives in FR-124
and git history); FR-134 (diary folder refactor — `scripts/diary_rotate.py`
became the pre-commit thin wrapper, which is the live path and is kept);
FR-916 (APPROVED, frozen scope includes deleting `diary import --dry-run`
and the `dry_run` branches in `diary/importer.py` — this FR subsumes those
deletions, see §FR-916 Interaction); FR-466/CAP-163 (retirement mechanism —
followed) with CAP-169 as the retired-file format example; siblings
FR-909/FR-910/FR-912/FR-913/FR-915 (same evidence class: surfaces with zero
committed consumers).

preview-justified: this FR's `dry-run` mentions name the flag and code
branches being deleted — use, not hedge.

## Evidence (R-1)

Consumer-record sweep, 2026-08-30, mechanically reproducible:

- **Two entry points, one library.** `yamlgraph.diary.importer` (247 lines)
  has exactly two callers: `scripts/diary_rotate.py` (live) and
  `yamlgraph/cli/diary_commands.py` (dead). Verified:
  `rg -n 'from yamlgraph.diary' --type py` → those two files plus tests.
- **The live path never touches the CLI.** launchd agents
  (`com.yamlgraph.git-report`, `com.yamlgraph.diary-digest`,
  `com.yamlgraph.file-hook` — all loaded, exit 0; outputs in
  `~/scheduled-yamlgraphs/outputs/git_report` fresh as of 2026-08-29) feed
  the pre-commit hook `diary-rotate` (`.pre-commit-config.yaml:39-44`,
  `always_run: true`), which runs `scripts/diary_rotate.py`, which imports
  the library directly.
- **No committed automation invokes the CLI** (transcript repaired per
  R-3, two separate claims):
  (a) `rg -l 'yamlgraph diary' scripts/ .github/ .chaplain/` → zero
  matches — no chaplain script, CI job, hook, or adapter runs
  `yamlgraph diary`;
  (b) `rg -l 'yamlgraph diary' capabilities/ reference/` →
  `capabilities/CAP-46-diary-import-cli.yaml` (self-description, retired
  by this FR) and `reference/cli.md` (documentation of the command, not an
  invocation — updated by this FR per R-1).
- **`dry_run` is CLI-only plumbing.** The `dry_run` parameters and branches
  in `yamlgraph/diary/importer.py` (lines 38, 71, 84, 123, 157, 185) are
  reachable only from the CLI wrapper; `diary_rotate.py` calls with
  defaults. FR-916's judgement already convicted the flag on the same
  evidence.
- **Confined blast radius.** `rg -l 'diary_commands|cmd_diary_dispatch'` →
  exactly `yamlgraph/cli/__init__.py`, `yamlgraph/cli/diary_commands.py`,
  `tests/unit/test_diary_commands.py`. Documentation surfaces (corrected
  per R-1): `reference/cli.md` lists `diary` in its synopsis and command
  table (lines 8, 16), and `ARCHITECTURE.md`'s generated capability
  sections advertise CAP-46/REQ-YG-122 as active — both are updated by
  this FR (R-2).

## Summary

Delete the `yamlgraph diary` CLI subcommand — `yamlgraph/cli/diary_commands.py`
(64 lines), the `diary` subparser block in `yamlgraph/cli/__init__.py`, the
`dry_run` parameters/branches in `yamlgraph/diary/importer.py`, and
`tests/unit/test_diary_commands.py` (204 lines) — and retire CAP-46
(REQ-YG-122) per the FR-465/466 precedent. The importer library,
`scripts/diary_rotate.py`, the `diary-rotate` pre-commit hook, and their
tests (`test_diary_importer.py`, `test_diary_rotate.py`) are explicitly
kept: they are the live path.

## Value Statement

Maintainers shed a dead CLI subcommand, ~150 lines of code and plumbing, a
204-line test file, and a phantom capability claim. The diary import
feature keeps exactly one entry point — the one that has actually run every
commit since FR-134.

## Problem

FR-124 extracted diary import logic from `scripts/diary_rotate.py` into
`yamlgraph.diary.importer` and added a CLI wrapper (`yamlgraph diary import
[--dry-run] [--source]`) alongside. The extraction succeeded — the
pre-commit hook has consumed the library on every commit since. The wrapper
never gained a caller: after ~6 months, zero committed automation invokes
`yamlgraph diary`, and the only repo-wide mention of the command outside
its own implementation is CAP-46 describing itself. This is the identical
failure mode that convicted the skill export (FR-912) and MCP (FR-910)
surfaces: a duplicate entry point kept "for humans" that no human or agent
ever used (`builders_never_call`, `growth_as_default`).

## Ideal Result

`yamlgraph diary` exits with argparse's unknown-command error; `git grep
diary_commands` finds nothing; `yamlgraph/diary/importer.py` has no
`dry_run` parameter; CAP-46 reads `status: retired` citing this FR; the
pre-commit `diary-rotate` hook still imports every pending scheduled entry
on the next commit; the full suite and `req_coverage.py --strict` are
green; resurrection is a disposition of this FR, not archaeology.

## FR-916 Interaction

FR-916 (APPROVED) froze the retirement of `diary import --dry-run`: the
flag in `cli/__init__.py`, the `dry_run` plumbing in `diary_commands.py`,
the `dry_run` branches in `importer.py`, and their tests. This FR is a
strict superset on the diary axis: whole-subcommand deletion subsumes
flag deletion. Enforcement ordering is commutative — whichever lands first,
the other's diary deletions become already-satisfied no-ops. FR-916's three
phrase gates (forbid-terms regex, reasoning sentinel, FR-write gate) are a
separate axis, untouched by this FR.

## Proposed Solution

Mechanical deletion plus registry retirement:

1. **Code**: delete `yamlgraph/cli/diary_commands.py`; remove the
   `cmd_diary_dispatch` import and the `diary` subparser block from
   `yamlgraph/cli/__init__.py`; remove the `dry_run` parameters and
   conditional branches from `yamlgraph/diary/importer.py` (unconditional
   write path remains, as `diary_rotate.py` exercises it).
2. **Tests**: delete `tests/unit/test_diary_commands.py`; keep
   `test_diary_importer.py` and `test_diary_rotate.py` (they test the live
   path); adjust any importer tests that pass `dry_run=` explicitly.
3. **Registry**: CAP-46 → `status: retired`, description prefixed
   `RETIRED by FR-920` (CAP-163 mechanism, CAP-169 format); REQ-YG-122
   leaves the active requirement set; `req_coverage.py --strict` green.
4. **Witness (TDD)**: RED test asserting `yamlgraph diary import` is
   rejected by the CLI and `import_scheduled_entries` has no `dry_run`
   parameter; commit RED (`SKIP=pytest`) and GREEN separately.
5. **Documentation (R-1, R-2)**: remove the `diary` rows from
   `reference/cli.md` synopsis and command table; run
   `python scripts/aggregate_capabilities.py` so `ARCHITECTURE.md`'s
   generated capability sections stop presenting CAP-46 as active (the
   resulting `ARCHITECTURE.md` diff is in scope).
6. **Changelog**: `removal` fragment in `changelog/unreleased/`.
7. **Enforcement artifacts (R-4)**: FR-920 status/decision notes, the
   final `FR-920-retire-diary-cli.judgement.md`, and one `docs/diary/`
   reflection entry with a `Seed:` line ship in the implementation diff.

## Alternatives (dispositioned)

| # | Alternative | Disposition |
|---|-------------|-------------|
| A1 | Keep the CLI, document it better | REJECTED — 6 months of zero consumers with the command fully documented in its own CAP; documentation was never the gap (FR-912 precedent) |
| A2 | Retire only `--dry-run`, keep `diary import` | REJECTED — that is FR-916's already-frozen subset; it leaves a one-flag wrapper whose only distinction from `diary_rotate.py` is `--source`, which also has zero consumers |
| A3 | Retire `scripts/diary_rotate.py` instead, route the hook through the CLI | REJECTED — inverts the evidence: the script is the consumed path (every commit), the CLI is the unconsumed one; churning the live path to save the dead one |
| A4 | Delete the whole `yamlgraph/diary/` package | REJECTED — the importer has a live consumer (pre-commit hook) and fresh launchd-fed inputs; this is not a phantom surface |
| A5 | Whole-subcommand retirement, importer and hook kept (chosen) | CHOSEN — deletes exactly the zero-consumer surface, keeps the every-commit path byte-identical in behavior |

**is_this_a_graph:** No — mechanical deletion with no LLM stage, no fan-out,
no routing; the graph list offers nothing for a code-removal task.

## Acceptance Criteria

Judge's revised criteria adopted verbatim:

- AC-01: A RED witness first proves
  `create_parser().parse_args(["diary", "import"])` or equivalent CLI
  invocation exits non-zero because `diary` is no longer a valid top-level
  command; the GREEN change makes that witness pass.
- AC-02: `yamlgraph/cli/diary_commands.py` and
  `tests/unit/test_diary_commands.py` do not exist, and
  `rg -n 'diary_commands|cmd_diary_dispatch' yamlgraph tests scripts
  reference capabilities ARCHITECTURE.md` returns no active
  implementation/test/docs references except immutable historical FR or
  judgement prose.
- AC-03: `import_scheduled_entries` and `import_git_reports` have no
  `dry_run` parameter; `rg -n 'dry_run' yamlgraph/diary
  tests/unit/test_diary_importer.py` returns zero matches.
- AC-04: The `diary-rotate` pre-commit hook entry is unchanged and
  `python scripts/diary_rotate.py` runs green.
- AC-05: FR-916's phrase gates, sentinel, and FR-write gate are untouched.
- AC-06: CAP-46 has `status: retired` and a description beginning
  `RETIRED by FR-920`; `python scripts/validate_capabilities.py` and
  `python scripts/req_coverage.py --strict` pass.
- AC-07: `python scripts/aggregate_capabilities.py` has been run, and
  `ARCHITECTURE.md` no longer presents CAP-46 as an active CLI capability.
- AC-08: `reference/cli.md` no longer lists `diary` in the command
  synopsis or command table.
- AC-09: Full unit suite, `ruff check yamlgraph/`, and `lint-imports` pass.
- AC-10: `changelog/unreleased/` contains one `removal` fragment for
  FR-920.
- AC-11: The implementation diff includes FR-920 status/decision notes,
  the final judgement artifact, and one diary reflection entry with
  `Seed:`.
