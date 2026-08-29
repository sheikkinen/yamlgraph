# Feature Request: FR-916 Ban "dry-run" as a hedge phrase

**Status:** Judged — APPROVED (2026-08-29, second judgement; first REJECTED, R-1..R-4 folded)
**Date:** 2026-08-29
**Author:** agent session (operator-directed)

**Research:** in-body — see § Research Record below (dispositioned alternatives table, precedent lines, `is_this_a_graph` answer).

**Prior art:** FR-438 (reasoning-pattern sentinel, Phase 1 keyword registry), FR-439 (rename), FR-124 (diary import CLI — the sole legitimate `--dry-run` in core, dispositioned below: retire), FR-862 (deviant-daily — 36 dry-run occurrences, densest single-FR usage), FR-903 (alternatives table proposed a dry-run mode — the triggering recurrence). Existing bans: "backward compatibility" (`forbid-terms` pre-commit hook over `yamlgraph/**/*.py`) and the 5-phrase reasoning-sentinel registry (`.github/hooks/scripts/reasoning-patterns.json`).

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

## Research Record

`is_this_a_graph`: No — this is deterministic keyword enforcement at three existing boundaries (pre-commit grep, sentinel registry, PostToolUse scanner); no LLM stage, no fan-out, no graph.

**Alternatives dispositioned:**

| # | Solution class | Disposition |
|---|---|---|
| A1 | Advisory doctrine text only (Conventions line, no gates) | REJECTED — refuted by recurrence: FR-862 shipped 36 uses, FR-903's judge proposed a dry-run mode today despite existing doctrine; `detection_without_enforcement` |
| A2 | Reasoning sentinel entry only | REJECTED as sole gate — sentinel scans only the latest assistant message and is one-shot; "backward compatibility" precedent shows the pre-commit gate is what holds |
| A3 | Pre-commit code gate only | REJECTED as sole gate — fires after code exists; the cheapest kill is at FR-authoring time (spec_kill) |
| A4 | Three-gate layered ban (code + reasoning + FR-write) with escape marker | **CHOSEN** — each gate covers the other's blind window; reuses three existing mechanisms, zero new infrastructure |
| A5 | LLM classifier for hedge-intent (graph/daemon) | REJECTED — keyword match suffices for a literal phrase; a classifier is `growth_as_default` |
| A6 | Permanent noqa-style exemption for `diary import --dry-run` | REJECTED — a day-one permanent exemption makes the ban advisory |

**Precedent lines (disagreement preserved):**
- FR-124 introduced `diary import --dry-run` with accepted non-mutating-import tests (FR-124:13-36, 282-292) — the flag was a deliberate design, not an accident.
- FR-862 originally designed `dry_run` as a no-publication path (FR-862:194-214); the operator later voided `dry_run`/`force` as paternalistic ceremony (FR-862:11-18). The contrary precedent is real: dry-run was once considered good design here.
- FR-903's judge proposed routing a `--dry-run` flag; the operator overruled to deletion — "a dry-run flag is hedging" (FR-903:121-143, 258).
- FR-438/FR-439: the sentinel mechanism and its neutral-wording precedent (FR-439:61-65, 95-99).
- Resolution of the disagreement: the 2024-era design consensus (FR-124, early FR-862) predates the repo's TDD-witness + worktree-isolation safety rails; with those rails in place, the operator's 2026 rulings (FR-862 voiding, FR-903 overrule) consistently treat preview modes as ceremony. This FR codifies the later ruling.

## Ideal Result

An agent that reaches for "let me add a dry-run mode" is stopped at the reasoning boundary before code exists; a `--dry-run` flag cannot enter `yamlgraph/` without tripping pre-commit; the diary importer's preview behavior either survives under an honest name or is retired if it has no consumer.

## Proposed Solution

1. **Code gate** — extend the `forbid-terms` hook regex in `.pre-commit-config.yaml` from `TODO|FIXME|backward compati(bility)?` to also match `dry[-_ ]?run` (case-insensitive where the grep permits). Scope stays `yamlgraph/**/*.py`.
2. **Reasoning gate** — add a `dry-run` entry to `.github/hooks/scripts/reasoning-patterns.json` with variants `dry_run`, `dry run`, doctrine text pointing at Commandment 6 / `mock_escape_hatch`, scripture_ref `copilot-instructions.md § Conventions`.
3. **FR-write gate (the "Are you sure?" hook)** — extend `.github/hooks/scripts/checks/fr-checks.sh` (PostToolUse, already scans `feature-requests/*.md` writes) to detect `dry[-_ ]run` in a newly written or edited FR and arm the existing one-shot sentinel (same arm/consume mechanism as `reasoning-pattern-check.sh` → `pre-command-guard.sh`). The denial message is neutral and descriptive (FR-439 wording precedent) and MUST contain the literal prompt `Are you sure?`:
   > *"Are you sure? A dry-run mode duplicates an execution path that is already guarded by tests and git reversibility. This denial is one-shot — if the FR genuinely needs a preview mode, name it honestly and justify it with a `preview-justified:` line in the FR body."*

   Escape marker (same pattern as the fsm gate's `escapes` list in fr-checks.sh): the literal string `preview-justified:` followed by a one-line rationale in the FR body suppresses the gate — a justified preview is a design decision, an unjustified dry-run is a hedge. Historical FRs are untouched: the gate fires only on writes, not on the existing record. Final denial wording and hook semantics require human review before the enforcement PR merges (C-3).
4. **Doctrine** — add one Conventions line to `.github/copilot-instructions.md`: the phrase "dry-run" is forbidden; execution is guarded by tests and reversibility, not simulation modes. If a preview is genuinely required, justify it explicitly in an FR under an honest name (`--plan`, `--diff`, `--preview`) with a `preview-justified:` line.
5. **Disposition of `diary import --dry-run` (FR-124) — FROZEN: retire.** Delete the flag (`cli/__init__.py:333-335`), the `dry_run` parameter and branches in `diary/importer.py`, the plumbing and preview output in `cli/diary_commands.py`, and the corresponding tests in `tests/unit/test_diary_commands.py` / `tests/unit/test_diary_importer.py`. Evidence: no committed script or automation invokes `yamlgraph diary import --dry-run` (repo grep — the only invocations are help text and the feature's own tests); the operator's rulings in FR-862 (voided as ceremony) and FR-903 (overruled routing to deletion) both chose retirement over rename for the same construct. The enforcer makes no choice here.
6. **Out of scope** — historical FRs/judgements, `docs/diary/`, `changelog/` are the immutable record; the ban is not retroactive prose surgery. `scripts/` and `examples/` stay outside the code gate (same scope as the existing bans) but fall under the reasoning and FR-write gates for future sessions.

## Acceptance Criteria

(Judge's revised set, adopted verbatim.)

- [ ] AC-01: FR-916 contains a `**Research:**` field pointing to a committed research artifact or an in-body equivalent that satisfies R-1.
- [ ] AC-02: `.pre-commit-config.yaml` `forbid-terms` fails on each banned variant in a `yamlgraph/**/*.py` fixture or temporary tracked-file witness and passes after removal.
- [ ] AC-03: `.github/hooks/scripts/reasoning-patterns.json` contains one entry with primary pattern, variants `dry_run` and `dry run`, doctrine text, and scripture reference.
- [ ] AC-04: `.github/hooks/tests/test_reasoning_pattern_check.py` proves the new primary phrase and variants arm a session-scoped sentinel.
- [ ] AC-05: `.github/hooks/tests/test_reasoning_pattern_check.py` proves the pre-command guard consumes that sentinel exactly once.
- [ ] AC-06: `.github/hooks/scripts/checks/fr-checks.sh` detects the banned phrase on `feature-requests/*.md` writes without `preview-justified:`.
- [ ] AC-07: `.github/hooks/tests/test_fr_checks.py` covers FR-write deny, `preview-justified:` escape, and clean FR cases.
- [ ] AC-08: The diary-import disposition chosen in the FR (retire) is implemented consistently in CLI parser, command handler, importer, help text, and tests.
- [ ] AC-09: `git grep -icE 'dry[-_ ]run' -- 'yamlgraph/**/*.py'` returns zero matches after the diary-import disposition is complete.
- [ ] AC-10: `.github/copilot-instructions.md` Conventions records the ban and the honest preview-name escape hatch.
- [ ] AC-11: `changelog/unreleased/` contains a fragment for FR-916.
- [ ] AC-12: Targeted hook tests and diary-import tests pass.

## Alternatives Considered

See § Research Record (A1–A6, dispositioned).

## Related

- FR-124 (diary import CLI), FR-438/FR-439 (sentinel), `forbid-terms` hook (`.pre-commit-config.yaml:170-177`), Scripture: Commandment 6, traps `mock_escape_hatch`, process `detection_without_enforcement`.

preview-justified: this FR defines the ban — its mentions are use, not hedge.
