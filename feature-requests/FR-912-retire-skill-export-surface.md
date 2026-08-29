# Feature Request: Retire the skill/agent export surface (CLI `skill`, export/skill*, CAPs 142/143)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Draft — awaiting judgement
**Effort:** 0.5–1 day
**Requested:** 2026-08-29
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops running
three RED test files for formats no one has ever consumed and stops
asserting two capability claims with a zero-artifact production record.
**Research:** consumer-record sweep 2026-08-29 (method of
[docs/research-agentic-sdlc-providers-2026-08-29.md](../docs/research-agentic-sdlc-providers-2026-08-29.md) §4.4)
+ in-body evidence and dispositioned alternatives below.
**Prior art:** FR-348/FR-350/FR-351 (the surface being retired — spec survives in those FRs and git history); FR-446/CAP-158 (hand-authored `.github/skills` promotion — NOT this surface; explicitly kept); FR-765 (graph-authoring skill — hand-written, proving the export tool was bypassed even for the flagship skill); FR-465/FR-466 + FR-470/CAP-163 (retirement mechanism and format — followed); FR-717 (created the export package seam this FR helps empty); siblings FR-909/FR-910 (A2A/MCP retirements — same evidence class, separate surfaces).

## Summary

Delete the `yamlgraph skill export` surface — `yamlgraph/export/skill.py`,
`yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, the
`skill` CLI subcommand, its three RED test files, and
`reference/skills-export.md` — and retire CAP-142 and CAP-143 per the
FR-465/466 precedent. When FR-910 has also landed, `yamlgraph/export/` is
empty: this FR owns the final package deletion and the `.importlinter`
export-seam cleanup.

## Value Statement

Maintainers shed ~3 modules, 3 dead test files, a CLI subcommand, and two
phantom capability claims. The export-seam import-linter contract (FR-717)
retires with its last member, simplifying the layer map.

## Problem

`yamlgraph skill export` (FR-348) generates portable skill packages in four
formats (`skill-md`, `copilot`, `cursor`, `agent-md` — FR-350/351 added the
agent formats). Its production record after ~4 months: **zero committed
artifacts**. Every file in `.github/skills/` is hand-authored — no generated
marker exists anywhere in the tracked tree; no script, CI job, hook, or
chaplain pipeline invokes `yamlgraph skill`; the flagship graph-authoring
skill (FR-765) was written by hand *while this tool existed to generate it*.
Consumers of `yamlgraph.export.skill` are exactly: its own CLI dispatch and
its own RED tests. This is the identical failure mode that convicted MCP
(FR-910): an agent-interop export surface whose transport lost to
hand-authored artifacts and CLI adapters (`builders_never_call`,
`growth_as_default`).

## Ideal Result

`git grep` finds no live skill-export implementation; the `skill`
subcommand is gone from the CLI; CAP-142/CAP-143 read `status: retired`
citing this FR; once FR-910 is merged, `yamlgraph/export/` no longer exists
and `.importlinter` carries no export-seam contract; the full suite and
`req_coverage.py --strict` are green; the format specs survive in
FR-348/350/351 so resurrection is a disposition of this FR, not
archaeology.

## Proposed Solution

Mechanical deletion plus registry retirement:

1. **Code**: delete `yamlgraph/export/skill.py`,
   `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`;
   remove the `cmd_skill_dispatch` import (`yamlgraph/cli/__init__.py:16`)
   and the `skill` subparser block (~lines 291–320).
2. **Export package endgame** (sequenced on FR-910): if `export/mcp.py` is
   already deleted when this FR enforces, also delete
   `yamlgraph/export/__init__.py` and the package directory, remove
   `yamlgraph.export` from the `.importlinter` layer listing and delete the
   `export-seam` contract (`.importlinter:46–58`, plus the
   `compile never imports export` clause's export mention). If FR-910 has
   not merged, leave `__init__.py` + `mcp.py` untouched and record the
   deferral in this FR — the package deletion then belongs to whichever FR
   lands second.
3. **Tests**: delete `tests/unit/test_fr348_skill_export_red.py`,
   `test_fr350_agent_export_red.py`, `test_fr351_agent_export_red.py`; add
   a narrow FR-912 witness test asserting the top-level CLI parser rejects
   `skill` as an unknown subcommand. `tests/unit/test_fr446_copilot_skills.py`
   is explicitly KEPT — it tests hand-authored `.github/skills` substance
   (CAP-158), not this surface.
4. **Docs**: delete `reference/skills-export.md`; remove the `skill`
   subcommand from the usage line and command table in `reference/cli.md`
   (lines 8, 15, §240–269); remove active CAP-142/143 rows from
   `ARCHITECTURE.md`; regenerate `reference/module-map.md`.
5. **Registry**: CAP-142, CAP-143 → `status: retired`, description
   prefixed `RETIRED by FR-912` (files stay, per CAP-163).
6. **Changelog**: fragment `type: removal`.

Kept: `.github/skills/**` (hand-authored, governed by CAP-158/FR-446);
`docs/plan-skills-export.md`, `docs/plan-yamlgraph-skills.md`, all diary
entries and frozen changelog fragments (historical record); no `pyproject`
change — the surface has no optional extra.

**Boundary:** this FR does NOT touch MCP (`export/mcp.py` — FR-910), A2A
(FR-909), `.github/skills` content, the skill-promotion tests (FR-446), or
`yamlgraph/discovery.py`.

## Acceptance Criteria

- [ ] AC-01: `git ls-files 'yamlgraph/export/skill*' 'yamlgraph/cli/skill_commands.py'` prints nothing, and `git grep -nE 'skill_commands|export\.skill|cmd_skill_dispatch|SkillExport' -- yamlgraph` prints no live references
- [ ] AC-02: a new FR-912 witness test asserts the CLI rejects `skill` as an unknown subcommand; `yamlgraph/cli/__init__.py` has no skill import or subparser
- [ ] AC-03: `git ls-files 'tests/unit/test_fr348*' 'tests/unit/test_fr350*' 'tests/unit/test_fr351*'` prints nothing; `tests/unit/test_fr446_copilot_skills.py` still exists and passes
- [ ] AC-04: `reference/skills-export.md` deleted; `reference/cli.md` and `ARCHITECTURE.md` contain no live skill-export advertising; `reference/module-map.md` regenerated
- [ ] AC-05: export-package endgame per step 2 — either the package and export-seam contract are gone (FR-910 merged first) or the deferral is recorded in this FR with the remaining owner named
- [ ] AC-06: CAP-142/CAP-143 carry `status: retired` + `RETIRED by FR-912`; `scripts/validate_capabilities.py` passes
- [ ] AC-07: `python scripts/req_coverage.py --strict`, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass
- [ ] AC-08: full unit suite passes with the witness test present
- [ ] AC-09: changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-912

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep as-is | REFUTED — zero artifacts produced in 4 months; even the flagship skill was hand-written past it |
| Keep one format, retire the rest | REFUTED — no format has a consumer; `partial_remediation` |
| Wire it into chaplain/CI to create a consumer | REFUTED — `would_you_use_this` demands a named consumer with a real trigger, not a manufactured one |
| Wait for agent-skill market convergence | REFUTED — resurrection from FR-348/350/351 specs is cheap and explicit (`constraint_over_code`) |

## Related

- Origin: FR-348 (skill export), FR-350/FR-351 (agent formats)
- Precedent: FR-465/FR-466, FR-470, CAP-163; siblings FR-909, FR-910
- Kept sibling surface: FR-446/CAP-158 (hand-authored skill promotion)
