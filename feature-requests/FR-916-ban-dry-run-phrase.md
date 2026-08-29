# Feature Request: FR-916 Ban "dry-run" as a hedge phrase

**Status:** Proposed
**Date:** 2026-08-29
**Author:** agent session (operator-directed)

**Prior art:** FR-438 (reasoning-pattern sentinel, Phase 1 keyword registry), FR-439 (rename), FR-124 (diary import CLI — the sole legitimate `--dry-run` in core, must be dispositioned), FR-862 (deviant-daily — 36 dry-run occurrences, densest single-FR usage), FR-903 (alternatives table proposed a dry-run mode — the triggering recurrence). Existing bans: "backward compatibility" (`forbid-terms` pre-commit hook over `yamlgraph/**/*.py`) and the 5-phrase reasoning-sentinel registry (`.github/hooks/scripts/reasoning-patterns.json`).

## Summary

Add "dry-run" (and variants `dry_run`, `dry run`) to the banned-phrase enforcement, in both channels where phrase bans live: the `forbid-terms` pre-commit hook (code scope) and the reasoning-pattern sentinel registry (agent-reasoning scope). Disposition the one legitimate core consumer (`yamlgraph diary import --dry-run`) so the code gate can be armed without an exemption shim.

## Value Statement

For the operator and every agent session in this repo, who keep receiving dry-run modes as hedges — a simulation flag instead of an execution guarded by tests and git reversibility — this ban makes the hedge mechanically expensive, the same way "backward compatibility" made refactor-reluctance expensive. The alternative (advisory doctrine text) is already refuted by recurrence: FR-862 (36 occurrences), FR-903 (agent proposed a dry-run alternative), and a steady drip across scripts.

## Problem

"Dry-run" is the execution-side twin of "backward compatibility": it signals reluctance to do the thing. A dry-run mode is a second code path that must be built, tested, and maintained, yet by construction never exercises the real boundary — it is a `mock_escape_hatch` wearing a CLI flag (Scripture: a mock E2E is a unit test with extra steps; Commandment 6: no hedging with silent fallbacks). The repo's actual safety rails are TDD witnesses, git reversibility, and worktree isolation — not previews.

Current status (measured 2026-08-29, tracked files):

| Scope | Occurrences | Files | Notes |
|---|---|---|---|
| `yamlgraph/**/*.py` (forbid-terms hook scope) | 17 | 3 | ALL one feature: `diary import --dry-run` (FR-124): `cli/__init__.py:333-335`, `cli/diary_commands.py`, `diary/importer.py` |
| Repo-wide `dry-run` | 254 | 112 | mostly FRs/judgements (historical record) |
| Repo-wide `dry_run` | 147 | 39 | tests, scripts, examples |
| Repo-wide `dry run` (prose) | 34 | 19 | docs, FR prose |
| Top single files | FR-862 (36), FR-124 (22), `set_fly_secrets.sh` (13), `test_diary_commands.py` + `test_copilot_session_gc.py` (12 each) | | |

Key finding: the core debt is small and coherent — one CLI flag and its plumbing. The long tail lives in `scripts/` (out of hook scope) and in immutable historical FRs.

## Ideal Result

An agent that reaches for "let me add a dry-run mode" is stopped at the reasoning boundary before code exists; a `--dry-run` flag cannot enter `yamlgraph/` without tripping pre-commit; the diary importer's preview behavior either survives under an honest name or is retired if it has no consumer.

## Proposed Solution

1. **Code gate** — extend the `forbid-terms` hook regex in `.pre-commit-config.yaml` from `TODO|FIXME|backward compati(bility)?` to also match `dry[-_ ]?run` (case-insensitive where the grep permits). Scope stays `yamlgraph/**/*.py`.
2. **Reasoning gate** — add a `dry-run` entry to `.github/hooks/scripts/reasoning-patterns.json` with variants `dry_run`, `dry run`, doctrine text pointing at Commandment 6 / `mock_escape_hatch`, scripture_ref `copilot-instructions.md § Conventions`.
3. **FR-write gate (the "Are you sure?" hook)** — extend `.github/hooks/scripts/checks/fr-checks.sh` (PostToolUse, already scans `feature-requests/*.md` writes) to detect `dry[-_ ]run` in a newly written or edited FR and arm the existing one-shot sentinel (same arm/consume mechanism as `reasoning-pattern-check.sh` → `pre-command-guard.sh`). The denial message is deliberately sarcastic:
   > *"Are you sure? A dry-run is a rehearsal for software that already has an undo button. You built the tests; you have git; the worktree is disposable. What exactly are you afraid of executing? (This denial is one-shot — if the FR genuinely needs a preview mode, name it honestly and justify it in the FR body.)"*

   Escape marker (same pattern as the fsm gate's `escapes` list in fr-checks.sh): the literal string `preview-justified:` followed by a one-line rationale in the FR body suppresses the gate — a justified preview is a design decision, an unjustified dry-run is a hedge. Historical FRs are untouched: the gate fires only on writes, not on the existing record.
4. **Doctrine** — add one Conventions line to `.github/copilot-instructions.md`: the phrase "dry-run" is forbidden; execution is guarded by tests and reversibility, not simulation modes. If a preview is genuinely required, justify it explicitly in an FR under an honest name (`--plan`, `--diff`, `--preview`) with a `preview-justified:` line.
5. **Disposition of `diary import --dry-run` (FR-124)** — decide before arming the code gate:
   - (a) **rename** to `--preview` (mechanical: flag, dest, importer kwarg, 3 core files + 2 test files), or
   - (b) **retire** the flag if the diary importer has no preview consumer (check: any script/automation passing `--dry-run` to `yamlgraph diary import`).
   Evidence gathered so far: only automation trace is interactive CLI usage; no script in the repo invokes `diary import --dry-run`.
6. **Out of scope** — historical FRs/judgements, `docs/diary/`, `changelog/` are the immutable record; the ban is not retroactive prose surgery. `scripts/` and `examples/` stay outside the code gate (same scope as the existing bans) but fall under the reasoning and FR-write gates for future sessions.

## Acceptance Criteria

- [ ] AC-01: `forbid-terms` hook fails on a `yamlgraph/` Python file containing `dry-run`, `dry_run`, or `dry run` (witness: hook run against a fixture change).
- [ ] AC-02: `reasoning-patterns.json` contains the new entry; sentinel test suite (`.github/hooks/tests/`) covers the new phrase and variants.
- [ ] AC-02b: FR-write gate — a write to `feature-requests/*.md` containing `dry-run` (no `preview-justified:` marker) arms the one-shot sentinel; the denial text contains "Are you sure?"; a write WITH the marker passes clean; hook test suite covers deny, escape, and one-shot-consume paths.
- [ ] AC-03: `git grep -icE 'dry[-_ ]run' -- 'yamlgraph/**/*.py'` returns zero matches (disposition of FR-124 flag complete).
- [ ] AC-04: `yamlgraph diary import` help text and tests updated to the chosen disposition; full unit suite green.
- [ ] AC-05: `.github/copilot-instructions.md` Conventions section carries the ban with the honest-name escape hatch.
- [ ] AC-06: Changelog fragment in `changelog/unreleased/`.

## Alternatives Considered

- **Reasoning gate only, no code gate**: cheaper, but "backward compatibility" precedent shows the code gate is what holds — sentinel scans only the latest assistant message and is one-shot.
- **Ban in prose/FRs too**: rejected — retroactive prose surgery on the historical record violates the record's immutability; the prior-art gate already forces new FRs through review where the reasoning sentinel fires.
- **Exempt `diary import --dry-run` via noqa-style confession**: rejected — a permanent exemption on day one makes the ban advisory (detection_without_enforcement).

## Related

- FR-124 (diary import CLI), FR-438/FR-439 (sentinel), `forbid-terms` hook (`.pre-commit-config.yaml:170-177`), Scripture: Commandment 6, traps `mock_escape_hatch`, process `detection_without_enforcement`.

preview-justified: this FR defines the ban — its mentions are use, not hedge.
