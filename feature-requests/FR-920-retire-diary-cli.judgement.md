# Judgement: FR-920 Retire the `yamlgraph diary` CLI surface (FR-124 wrapper, CAP-46)

**Verdict:** APPROVED WITH REVISIONS — the retirement is sound and evidence-backed, but authority activates only after the FR folds the stale CLI-reference evidence, generated capability-documentation scope, and enforcement artifact list into the frozen plan.

**Reviewed against:** `feature-requests/FR-920-retire-diary-cli.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-916-ban-dry-run-phrase.md`; `feature-requests/FR-916-ban-dry-run-phrase.judgement.md`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/diary_commands.py`; `yamlgraph/diary/importer.py`; `scripts/diary_rotate.py`; `.pre-commit-config.yaml`; `reference/cli.md`; `capabilities/CAP-46-diary-import-cli.yaml`; `capabilities/CAP-163-cap-retirement-support.yaml`; `capabilities/CAP-169-dungeon-master-web-ui.yaml`; `scripts/req_coverage.py`; `scripts/validate_capabilities.py`; `scripts/aggregate_capabilities.py`; `ARCHITECTURE.md`; `tests/unit/test_diary_commands.py`; `tests/unit/test_diary_importer.py`; `tests/unit/test_diary_rotate.py`.

**Prior art:** dispositioned in the FR's own prior-art record (FR-124, FR-134, FR-916, FR-466/CAP-163, FR-909/910/912/913/915) — verified against the cited artifacts above; no undispositioned precedent found, including rejected FRs in the diary or CLI-retirement territory.

## What is sound

The problem is real: FR-920 names the first consumer/event and frames the change as capability pruning, which matches the local `growth_as_default` doctrine that "the capability registry becomes honest by retiring phantom claims" (`feature-requests/FR-920-retire-diary-cli.md:7-10`, `.github/copilot-instructions.md:94`) and the FR template's consumer test (`feature-requests/TEMPLATE.md:7-10`). The proposal also includes an in-FR research record and prior-art disposition, satisfying the local research gate in substance rather than merely by field presence (`feature-requests/FR-920-retire-diary-cli.md:12-21`, `.github/skills/judge-fr/doctrine.md:118-128`).

The scope target is coherent: the current parser imports and registers `cmd_diary_dispatch` as a `diary` subcommand (`yamlgraph/cli/__init__.py:12`, `yamlgraph/cli/__init__.py:322-344`), and the command handler exists only as a wrapper around the shared importer (`yamlgraph/cli/diary_commands.py:12-63`). The live pre-commit path imports the library directly (`scripts/diary_rotate.py:24`, `scripts/diary_rotate.py:50-51`) and the hook executes that script, not the CLI (`.pre-commit-config.yaml:39-42`). Keeping the importer while deleting the Layer-1 wrapper therefore preserves the consumed side-effect path.

The dry-run subset is already dispositioned by FR-916. FR-916 freezes retirement of the diary dry-run parser flag, command handler branch, importer parameter, and tests (`feature-requests/FR-916-ban-dry-run-phrase.md:70`, `feature-requests/FR-916-ban-dry-run-phrase.judgement.md:51-53`), while FR-920 explicitly states it is a strict superset on the diary axis (`feature-requests/FR-920-retire-diary-cli.md:99-106`). That avoids conflicting implementation authority as long as FR-920 keeps FR-916's phrase-gate axis out of scope.

The capability-retirement mechanism exists and is feasible: retired CAP files are accepted with only `id`, `name`, and `status` required (`scripts/validate_capabilities.py:80-92`), and `req_coverage.py` excludes retired CAPs from `ALL_REQS` (`scripts/req_coverage.py:48-93`). CAP-169 demonstrates the cited "status: retired" plus `RETIRED by FR-...` description format (`capabilities/CAP-169-dungeon-master-web-ui.yaml:1-7`), while CAP-46 currently still asserts the active CLI requirement (`capabilities/CAP-46-diary-import-cli.yaml:1-23`).

Strategic classification: **capability retirement / pattern-documentation cleanup**, not a framework primitive. The existing importer plus `scripts/diary_rotate.py` path suffices for the only evidenced consumer; the FR removes an unconsumed duplicate presentation surface rather than adding a new abstraction.

## Required revisions

### R-1: Correct the CLI-reference evidence and include documentation deletion

Replace the false claim that `reference/cli.md` does not document the subcommand. The file currently lists `diary` in the top-level CLI synopsis and command table (`reference/cli.md:8`, `reference/cli.md:16`), contradicting FR-920's confined-blast-radius statement (`feature-requests/FR-920-retire-diary-cli.md:54-57`). Fold `reference/cli.md` into the proposed solution, deliverables, and acceptance criteria so the deleted CLI surface does not leave stale user documentation.

### R-2: Add generated capability documentation to the registry-retirement scope

State that `ARCHITECTURE.md`'s generated capability sections are regenerated after CAP-46 changes. The current generated registry still advertises CAP-46 and REQ-YG-122 as active CLI behavior (`ARCHITECTURE.md:377`, `ARCHITECTURE.md:1015-1023`), and `scripts/aggregate_capabilities.py` is the repo mechanism that rewrites those sections from `capabilities/CAP-*.yaml` (`scripts/aggregate_capabilities.py:1-10`, `scripts/aggregate_capabilities.py:117-137`). Add `python scripts/aggregate_capabilities.py` or an equivalent explicit generated-doc check to acceptance criteria, and allow the resulting `ARCHITECTURE.md` diff.

### R-3: Repair the consumer-record command transcript

Make the evidence commands exactly reproducible. FR-920 says `rg -l 'yamlgraph diary' scripts/ .github/ .chaplain/ reference/` produced `capabilities/CAP-46-diary-import-cli.yaml`, but that path is outside the listed search roots (`feature-requests/FR-920-retire-diary-cli.md:44-48`). Replace this with either the exact repo-wide command that includes `capabilities/`, or split it into two claims: committed automation search roots have no invocation, while capability/reference files are documentation-only and are being updated or retired.

### R-4: Freeze all required enforcement artifacts

Add the missing implementation artifacts to the frozen scope: `feature-requests/FR-920-retire-diary-cli.md` status/implementation notes, the final `feature-requests/FR-920-retire-diary-cli.judgement.md`, and one `docs/diary/` reflection entry. Repo doctrine requires FR implementation status/decision updates and a metacognitive diary entry for completed task lists (`.github/copilot-instructions.md:33-34`, `.github/copilot-instructions.md:215-218`); leaving them out conflicts with FR-920's AC-08 "No file outside the enumerated scope" gate (`feature-requests/FR-920-retire-diary-cli.md:158-159`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/cli/__init__.py` diary parser/import removal |
| D-2 | Delete `yamlgraph/cli/diary_commands.py` |
| D-3 | `yamlgraph/diary/importer.py` removal of `dry_run` parameters, branches, and docstring references to the retired CLI |
| D-4 | Delete `tests/unit/test_diary_commands.py`; update `tests/unit/test_diary_importer.py` only where `dry_run=` assertions or REQ-YG-122 markers must be removed/replaced |
| D-5 | Preserve `scripts/diary_rotate.py` behavior and `.pre-commit-config.yaml` `diary-rotate` hook entry byte-for-byte |
| D-6 | `capabilities/CAP-46-diary-import-cli.yaml` retired via CAP-163 mechanism |
| D-7 | Generated capability documentation in `ARCHITECTURE.md` after `scripts/aggregate_capabilities.py` |
| D-8 | `reference/cli.md` removal of the top-level `diary` command documentation |
| D-9 | One `changelog/unreleased/` removal fragment for FR-920 |
| D-10 | `feature-requests/FR-920-retire-diary-cli.md` implementation/status notes and final `feature-requests/FR-920-retire-diary-cli.judgement.md` |
| D-11 | One new `docs/diary/` reflection entry with a `Seed:` line |

Not authorized: deleting `yamlgraph/diary/` as a package; changing `scripts/diary_rotate.py` behavior; changing the `diary-rotate` hook command, stages, or `always_run` setting; touching FR-916's phrase gates, reasoning sentinel, FR-write gate, or doctrine changes; adding a replacement `diary` alias, preview flag, dry-run/plan mode, compatibility shim, or wrapper script; broad cleanup of unrelated dry-run mentions in historical FRs, changelog, examples, scripts, docs, or tests outside the surfaces above.

## Revised acceptance criteria

- [ ] AC-01: A RED witness first proves `create_parser().parse_args(["diary", "import"])` or equivalent CLI invocation exits non-zero because `diary` is no longer a valid top-level command; the GREEN change makes that witness pass.
- [ ] AC-02: `yamlgraph/cli/diary_commands.py` and `tests/unit/test_diary_commands.py` do not exist, and `rg -n 'diary_commands|cmd_diary_dispatch' yamlgraph tests scripts reference capabilities ARCHITECTURE.md` returns no active implementation/test/docs references except immutable historical FR or judgement prose.
- [ ] AC-03: `import_scheduled_entries` and `import_git_reports` have no `dry_run` parameter; `rg -n 'dry_run' yamlgraph/diary tests/unit/test_diary_importer.py` returns zero matches.
- [ ] AC-04: `scripts/diary_rotate.py` still imports `import_scheduled_entries` and `import_git_reports` directly and calls both without extra flags; `.pre-commit-config.yaml` `diary-rotate` hook entry is byte-identical to the pre-FR state.
- [ ] AC-05: `python scripts/diary_rotate.py` exits 0 in the existing environment.
- [ ] AC-06: CAP-46 has `status: retired` and a description beginning `RETIRED by FR-920`; `python scripts/validate_capabilities.py` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-07: `python scripts/aggregate_capabilities.py` has been run, and `ARCHITECTURE.md` no longer presents CAP-46 as an active CLI capability.
- [ ] AC-08: `reference/cli.md` no longer lists `diary` in the command synopsis or command table.
- [ ] AC-09: Full unit suite, `ruff check yamlgraph/`, and `lint-imports` pass.
- [ ] AC-10: `changelog/unreleased/` contains one `removal` fragment for FR-920.
- [ ] AC-11: The implementation diff includes FR-920 status/decision notes, the final judgement artifact, and one diary reflection entry with `Seed:`.
- [ ] AC-12: No file outside the frozen deliverables is modified, except generated `docs/fr-board.md` if the repo tooling updates it.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-4 are folded into FR-920. | GATE |
| C-2 | If enforcement discovers any committed non-test automation invoking `yamlgraph diary`, stop and return to FR revision instead of preserving, renaming, or shimming the CLI. | GATE |
| C-3 | The live diary import path is `scripts/diary_rotate.py` plus `yamlgraph.diary.importer`; do not route the hook through the CLI or change source-file mutation semantics. | GATE |
| C-4 | FR-920 may retire the diary CLI and its CAP claim only; FR-916 phrase-gate implementation remains separate authority. | GATE |
| C-5 | Do not add an alias, replacement wrapper, preview mode, or compatibility layer for the retired command. | GATE |

Authority granted after revisions: delete the `yamlgraph diary` CLI surface, remove its CLI-only dry-run importer plumbing, retire CAP-46, update the corresponding docs/generated registry/test/changelog/FR/diary artifacts, and preserve the direct `scripts/diary_rotate.py` importer path.
