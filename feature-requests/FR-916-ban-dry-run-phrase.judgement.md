# Judgement: FR-916 Ban "dry-run" as a hedge phrase

**Prior art:** FR-438/FR-439 (sentinel mechanism and neutral-wording precedent), FR-124 (diary import --dry-run, dispositioned: retire), FR-862/FR-903 (operator rulings treating preview modes as ceremony), forbid-terms hook (backward-compatibility ban precedent).

**Verdict:** APPROVED - FR-916 now contains substantive research, freezes the diary-import disposition, reuses existing enforcement mechanisms, and has mechanically testable acceptance criteria; authority is granted within the frozen scope below.

**Reviewed against:** `feature-requests/FR-916-ban-dry-run-phrase.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.pre-commit-config.yaml`; `.github/hooks/scripts/reasoning-patterns.json`; `.github/hooks/scripts/reasoning-pattern-check.sh`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/checks/common.sh`; `.github/hooks/scripts/checks/fr-checks.sh`; `.github/hooks/tests/test_reasoning_pattern_check.py`; `.github/hooks/tests/test_fr_checks.py`; `feature-requests/FR-124-diary-import-cli.md`; `feature-requests/FR-438-thoughtcrime-hook.md`; `feature-requests/FR-439-tone-down-enforcement-terminology.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.md`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/diary_commands.py`; `yamlgraph/diary/importer.py`; `tests/unit/test_diary_commands.py`; `tests/unit/test_diary_importer.py`.

## What is sound

The research gate is satisfied. FR-916 has a `**Research:**` field pointing to an in-body record (`feature-requests/FR-916-ban-dry-run-phrase.md:7`), a direct `is_this_a_graph` answer (`feature-requests/FR-916-ban-dry-run-phrase.md:35-37`), six dispositioned solution classes (`feature-requests/FR-916-ban-dry-run-phrase.md:39-48`), and precedent lines that preserve conflicting prior art before resolving it (`feature-requests/FR-916-ban-dry-run-phrase.md:50-55`). That meets the local judge requirement for substance: alternatives, precedent, disagreement, and graph-fit answer (`.github/skills/judge-fr/doctrine.md:118-128`).

The problem is real and scoped to existing mechanisms. The current code-scope debt is identified as 17 matches in three core files (`feature-requests/FR-916-ban-dry-run-phrase.md:23-33`), and those matches are the diary import flag and its plumbing (`yamlgraph/cli/__init__.py:333-335`, `yamlgraph/cli/diary_commands.py:19-50`, `yamlgraph/diary/importer.py:38-185`). The existing code ban is already a local pre-commit hook over `yamlgraph/**/*.py` (`.pre-commit-config.yaml:170-175`), the reasoning-pattern registry already carries `pattern`/`variants`/`doctrine`/`scripture_ref` entries (`.github/hooks/scripts/reasoning-patterns.json:1-33`), the scanner already flattens primary phrases and variants (`.github/hooks/scripts/reasoning-pattern-check.sh:71-80`) and arms `.reasoning-flag-<session_id>` (`.github/hooks/scripts/reasoning-pattern-check.sh:122-155`), and the pre-command guard already consumes that sentinel exactly once (`.github/hooks/scripts/pre-command-guard.sh:101-110`).

The FR preserves single responsibility. It bans one hedge phrase across the three boundaries where it can enter future work: code before commit, reasoning before follow-on tool use, and FR prose at write time (`feature-requests/FR-916-ban-dry-run-phrase.md:61-68`). The diary-import removal is not an unrelated feature deletion; it is the necessary disposition of the sole core consumer so the code gate can be armed without a permanent exemption (`feature-requests/FR-916-ban-dry-run-phrase.md:13`, `feature-requests/FR-916-ban-dry-run-phrase.md:70`).

The contrary precedent is handled honestly. FR-124 deliberately approved `yamlgraph diary import --dry-run` (`feature-requests/FR-124-diary-import-cli.md:13-36`, `feature-requests/FR-124-diary-import-cli.md:282-292`), while later FRs record the operator's shift toward deletion rather than redesign: FR-862 voided `dry_run`/`force` as paternalistic (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:11-22`), and FR-903 retired `--dry-run` instead of adding an explicit route (`feature-requests/FR-903-digest-archive-then-email-ordering.md:121-143`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:258`). FR-916's chosen retirement follows that later ruling (`feature-requests/FR-916-ban-dry-run-phrase.md:70`).

Strategic classification: **framework/process enforcement primitive implemented by existing hook primitives**. The use cases exceed a single feature request (FR-124, FR-862, FR-903, current core occurrences), advisory doctrine alone is explicitly rejected by recurrence (`feature-requests/FR-916-ban-dry-run-phrase.md:43`), and the chosen solution avoids a new classifier or graph where literal deterministic matching is sufficient (`feature-requests/FR-916-ban-dry-run-phrase.md:46-48`).

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.pre-commit-config.yaml` `forbid-terms` hook, preserving the existing `yamlgraph/**/*.py` scope |
| D-2 | `.github/hooks/scripts/reasoning-patterns.json` |
| D-3 | `.github/hooks/scripts/checks/fr-checks.sh` and only the minimal support in `.github/hooks/scripts/checks/common.sh` needed to reuse existing parsed hook context |
| D-4 | `.github/hooks/tests/test_reasoning_pattern_check.py` and `.github/hooks/tests/test_fr_checks.py` |
| D-5 | `.github/copilot-instructions.md` Conventions |
| D-6 | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/diary_commands.py`, `yamlgraph/diary/importer.py` |
| D-7 | `tests/unit/test_diary_commands.py`, `tests/unit/test_diary_importer.py` |
| D-8 | `feature-requests/FR-916-ban-dry-run-phrase.md` implementation/status notes and the final committed judgement artifact |
| D-9 | One `changelog/unreleased/` fragment for FR-916 |
| D-10 | One new `docs/diary/` reflection entry for the enforcement change |

Not authorized: retroactive cleanup of historical FRs, judgements, changelog history, or diary entries; widening the pre-commit code gate beyond `yamlgraph/**/*.py`; adding a new LLM classifier, daemon, graph, or hook framework; adding a permanent exemption list for `dry-run`; renaming diary import `--dry-run` into `--preview`, `--plan`, or equivalent; changing judge/review doctrine; changing unrelated scripts, examples, or workflow flags that happen to contain dry-run language.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-916-ban-dry-run-phrase.md` retains a `**Research:**` field pointing to the in-body research record, and that record contains the dispositioned alternatives, precedent lines, preserved disagreement, and `is_this_a_graph` answer cited above.
- [ ] AC-02: A targeted pre-commit-hook witness proves `forbid-terms` fails for `dry-run`, `dry_run`, and `dry run` in `yamlgraph/**/*.py`, while preserving the existing `TODO`, `FIXME`, and `backward compati(bility)?` detections and passing after the witness text is removed.
- [ ] AC-03: `.github/hooks/scripts/reasoning-patterns.json` contains exactly one dry-run phrase entry with primary pattern `dry-run`, variants `dry_run` and `dry run`, non-empty doctrine text tied to Commandment 6 / `mock_escape_hatch`, and a non-empty `scripture_ref`.
- [ ] AC-04: `.github/hooks/tests/test_reasoning_pattern_check.py` proves the primary phrase and both variants arm a `.reasoning-flag-<session_id>` sentinel from the latest assistant message.
- [ ] AC-05: `.github/hooks/tests/test_reasoning_pattern_check.py` proves the existing pre-command guard consumes the dry-run sentinel exactly once and the denial text includes the literal prompt `Are you sure?`.
- [ ] AC-06: `.github/hooks/scripts/checks/fr-checks.sh` detects `dry-run`, `dry_run`, and `dry run` on `feature-requests/*.md` edit/create/apply-patch writes when the FR body lacks `preview-justified:`.
- [ ] AC-07: `.github/hooks/tests/test_fr_checks.py` proves an FR-write hit without `preview-justified:` arms the session-scoped sentinel, an FR with `preview-justified:` followed by a one-line rationale does not arm it, and a clean FR does not arm it.
- [ ] AC-08: The diary import dry-run surface is retired completely: no parser flag, no command-handler branch, no importer `dry_run` parameter, no preview output, and no help text or docstring advertising the mode.
- [ ] AC-09: Diary importer and command tests are updated so live import behavior remains covered without any dry-run fixture or assertion.
- [ ] AC-10: `git grep -icE 'dry[-_ ]run|dry run' -- 'yamlgraph/**/*.py'` returns zero matches after the diary-import retirement.
- [ ] AC-11: `.github/copilot-instructions.md` Conventions records the dry-run phrase ban and states that any genuine preview must use an honest name and a `preview-justified:` rationale in the governing FR.
- [ ] AC-12: `changelog/unreleased/` contains one FR-916 fragment with valid front matter.
- [ ] AC-13: The enforcement diff includes one `docs/diary/` reflection entry with a `Seed:` line; this is a new record, not retroactive diary prose surgery.
- [ ] AC-14: The targeted hook tests and diary-import tests pass in one or more existing test invocations that cover the modified surfaces.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | The implementation must reuse the existing reasoning sentinel path (`.reasoning-flag-<session_id>`) and pre-command consumption semantics; a new sentinel type, daemon, graph, or classifier is outside scope. | GATE |
| C-2 | Historical records remain immutable: do not rewrite old FRs, judgements, changelog entries, diary entries, scripts, examples, or docs merely to remove dry-run prose. | GATE |
| C-3 | Because this changes enforcement infrastructure and doctrine, the final hook-denial wording, `preview-justified:` escape semantics, and `.github/copilot-instructions.md` text require explicit human review before merge (`.github/skills/judge-fr/doctrine.md:94-103`). | GATE |
| C-4 | The diary-import disposition is retirement only. Do not introduce a replacement preview flag, alias, compatibility shim, or exemption. | GATE |
| C-5 | The FR-write escape is local to the edited FR body and must require the literal `preview-justified:` marker with a one-line rationale; no global allowlist or hidden bypass is authorized. | GATE |
| C-6 | If implementation discovers a committed non-test automation consumer of `yamlgraph diary import --dry-run`, stop and return to FR revision instead of silently preserving or renaming the flag. | GATE |

Authority granted: implement FR-916 exactly as the dry-run phrase ban, FR-write one-shot sentinel, doctrine note, diary-import dry-run retirement, and associated tests/artifacts described above.
