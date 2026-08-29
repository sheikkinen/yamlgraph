# Judgement: FR-912 Retire the skill/agent export surface

**Prior art:** gate hits are this change's own sibling artifacts (FR-912 FR, FR-913 bench-retirement FR and judgement, committed together) and the FR-909/910 retirement arc; external precedent (FR-348/350/351, FR-446/CAP-158, FR-466/CAP-163, CAP-169, FR-717) is dispositioned in the FR's Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS - the retirement is strategically sound and feasible, but authority activates only after the FR fixes its evidence trail, completes the live documentation/import-linter sweep, and strengthens the residual-reference gates.

**Reviewed against:** `feature-requests/FR-912-retire-skill-export-surface.md`; cited research `docs/research-agentic-sdlc-providers-2026-08-29.md` section 4.4; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `CLAUDE.md`; precedents `feature-requests/FR-348-skill-export-portable-skills-packaging.md`, `feature-requests/FR-350-agent-export-tool-scoped-personas.md`, `feature-requests/FR-351-agent-export-agent-md.md`, `feature-requests/FR-446-copilot-skill-promotion.md`, `feature-requests/FR-765-graph-authoring-workflow-skill.md`, `feature-requests/FR-466-cap-retirement-support.md`, `capabilities/CAP-163-cap-retirement-support.yaml`, `capabilities/CAP-169-dungeon-master-web-ui.yaml`, `feature-requests/FR-909-retire-a2a-surface.md`, `feature-requests/FR-909-retire-a2a-surface.judgement.md`, `feature-requests/FR-910-retire-mcp-surface.md`, `feature-requests/FR-910-retire-mcp-surface.judgement.md`; current cited/live surfaces `capabilities/CAP-142-skill-export.yaml`, `capabilities/CAP-143-agent-md-export-tool-scoped-personas.yaml`, `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/export/__init__.py`, `yamlgraph/export/mcp.py`, `yamlgraph/cli/skill_commands.py`, `yamlgraph/cli/__init__.py`, `.importlinter`, `reference/skills-export.md`, `reference/cli.md`, `reference/README.md`, `reference/module-map.md`, `ARCHITECTURE.md`, `tests/unit/test_fr348_skill_export_red.py`, `tests/unit/test_fr350_agent_export_red.py`, `tests/unit/test_fr351_agent_export_red.py`, `tests/unit/test_fr446_copilot_skills.py`; tracked-source searches over FR-cited skill-export symbols in `.github/skills/`, `yamlgraph/`, `tests/`, `reference/`, `ARCHITECTURE.md`, and `README.md`.

## What is sound

The problem is credible and the proposed direction matches repository doctrine. FR-912 names a concrete first consumer and event: maintainers and CI stop carrying three RED test files and two zero-production capability claims from this PR onward (`feature-requests/FR-912-retire-skill-export-surface.md:8-11`). Its target surface is also concrete: delete the `skill` CLI group, `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, skill-export docs/tests, and retire CAP-142/CAP-143 (`feature-requests/FR-912-retire-skill-export-surface.md:17-24`, `feature-requests/FR-912-retire-skill-export-surface.md:58-92`). That is a bounded retirement, not a new feature.

The retirement mechanism is established. FR-466 created `status: retired` so retired CAP files stay as historical records while their REQs stop blocking strict coverage (`feature-requests/FR-466-cap-retirement-support.md:11-15`, `feature-requests/FR-466-cap-retirement-support.md:118-127`), and CAP-163 records the same behavior in the registry (`capabilities/CAP-163-cap-retirement-support.yaml:3-17`). CAP-142 and CAP-143 are exactly the active claims this FR should retire: they point at `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, `reference/skills-export.md`, and the FR-348/350 tests (`capabilities/CAP-142-skill-export.yaml:1-80`, `capabilities/CAP-143-agent-md-export-tool-scoped-personas.yaml:1-68`).

The architectural shape is feasible. The skill-export implementation is isolated in two export modules plus one CLI dispatch module (`yamlgraph/export/skill.py:1-313`, `yamlgraph/export/skill_writer.py:1-111`, `yamlgraph/cli/skill_commands.py:1-28`), and the parser wiring is localized to one import plus one subparser block (`yamlgraph/cli/__init__.py:16`, `yamlgraph/cli/__init__.py:298-320`). Deleting the three original acceptance test files and replacing them with a parser-rejection witness is testable directly from the FR (`feature-requests/FR-912-retire-skill-export-surface.md:100-108`).

The strategic classification is **Reject / retire stale surface**. The old surface began as a framework primitive in FR-348/350/351, but its own successor evidence shows the winning path for real agent workflow is hand-authored skills plus explicit adapter scripts: FR-446 created `.github/skills/*/SKILL.md` by manual curation (`feature-requests/FR-446-copilot-skill-promotion.md:40-118`), and FR-765 delivered the graph-authoring workflow through `.github/skills/graph-authoring/...` and `scripts/author.sh` rather than through `yamlgraph skill export` (`feature-requests/FR-765-graph-authoring-workflow-skill.md:60-111`, `feature-requests/FR-765-graph-authoring-workflow-skill.md:227-270`). That aligns with `growth_as_default`: mature systems improve by retiring phantom claims, not preserving unused interfaces (`.github/copilot-instructions.md:94`), and with `would_you_use_this`: a surface without a named recurring trigger should not remain active (`.github/copilot-instructions.md:125`).

## Required revisions

### R-1: Replace the borrowed research citation with a skill-export-specific consumer record

Amend the Research/Problem section so the evidence for retiring **skill export** is first-class and mechanically reproducible. The current research citation points to a committed section about MCP and A2A only (`feature-requests/FR-912-retire-skill-export-surface.md:12-15`; `docs/research-agentic-sdlc-providers-2026-08-29.md:237-272`). That section is valid sibling-method precedent, but it does not itself establish the skill-export consumer record.

Fold in either a committed research subsection or an in-FR evidence block containing the exact commands and results that prove:

- no tracked generated skill/agent artifacts exist under `.github/skills/` from `yamlgraph skill export`;
- no live automation, chaplain script, CI job, hook, or adapter invokes `yamlgraph skill`;
- references to `yamlgraph.export.skill`, `export_skill`, `PackageSkill`, `SkillPackage`, `SkillFormat`, `write_skill_package`, and `write_agent_md_file` are confined to the implementation, CLI dispatch, docs, CAPs, and the three self-tests being deleted;
- FR-446/CAP-158 and FR-765 remain the consumed hand-authored skill surfaces, not consumers of the export tool.

This revision satisfies the judge doctrine's research-evidence gate for newly created FRs (`.github/skills/judge-fr/doctrine.md:118-128`) without making the enforcer rediscover the author's private search.

### R-2: Correct the retirement-format prior-art citation

Amend the Prior art and Related lines to stop saying `FR-470/CAP-163` is the retirement mechanism/format. `FR-470` resolves to `feature-requests/FR-470-dm-web-ui-v2-synopsis-review.md`, a Dungeon Master Web UI request, not the CAP-retirement mechanism (`feature-requests/FR-470-dm-web-ui-v2-synopsis-review.md:1-14`). If the intended point is "retired-file format precedent", cite `capabilities/CAP-169-dungeon-master-web-ui.yaml:1-8` as the concrete example and `FR-466` / `CAP-163` as the mechanism (`capabilities/CAP-163-cap-retirement-support.yaml:3-17`). If a separate FR number is intended, name the exact file.

### R-3: Add `reference/README.md` to the documentation deletion/update scope

Fold `reference/README.md` into Proposed Solution step 4 and AC-04. The current FR deletes `reference/skills-export.md` and updates `reference/cli.md` plus `ARCHITECTURE.md` (`feature-requests/FR-912-retire-skill-export-surface.md:79-82`, `feature-requests/FR-912-retire-skill-export-surface.md:103`), but `reference/README.md` still links to the soon-deleted skill export guide (`reference/README.md:54`) and both CAP files name it as part of the capability surface (`capabilities/CAP-142-skill-export.yaml:7-16`, `capabilities/CAP-143-agent-md-export-tool-scoped-personas.yaml:7-16`). Leaving that link would make the docs deletion incomplete.

### R-4: Strengthen the residual-reference acceptance gates

Replace AC-01 and AC-04 with live-surface denylist checks that include all exported API names and docs indexes. The current AC-01 only searches `yamlgraph/` for `skill_commands|export\.skill|cmd_skill_dispatch|SkillExport` (`feature-requests/FR-912-retire-skill-export-surface.md:100`), but the live implementation also exposes `PackageSkill`, `SkillPackage`, `SkillFormat`, `export_skill`, `write_skill_package`, and `write_agent_md_file` (`yamlgraph/export/skill.py:36-56`, `yamlgraph/export/skill.py:292-313`, `yamlgraph/export/skill_writer.py:12-111`). A partial delete could leave those names in tests or docs while still passing the current `yamlgraph/`-only grep.

Use a criterion shaped like:

```bash
git grep -nE 'skill_commands|yamlgraph\.export\.skill|yamlgraph/export/skill|cmd_skill_dispatch|PackageSkill|SkillPackage|SkillFormat|export_skill|write_skill_package|write_agent_md_file|yamlgraph skill export|skills-export\.md|agent-md|skill-md' -- yamlgraph tests reference README.md ARCHITECTURE.md
```

The revised criterion must require zero live-surface matches after deleting obsolete self-tests and docs, with explicit exclusions only for the new FR-912 witness test, historical records (`feature-requests/**`, `docs/diary/**`, archived changelog fragments), and the judgement itself. If `agent-md` or `skill-md` has a surviving non-export meaning, name that exception explicitly in the FR before enforcement.

### R-5: Make `.importlinter` package-endgame cleanup exhaustive when FR-910 has already removed MCP

Amend Proposed Solution step 2 and AC-05 so the conditional export-package deletion removes **every** live `.importlinter` mention of `yamlgraph.export`, not only the layer listing, `export-seam`, and the `compile never imports export` clause. The current file also lists `yamlgraph.export` under the `fsm-contrib-ownership` source modules (`.importlinter:13`, `.importlinter:46-63`, `.importlinter:86`). If FR-912 enforces after FR-910 and deletes `yamlgraph/export/`, any remaining `yamlgraph.export` contract entry is stale gate configuration.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, and `yamlgraph/cli/skill_commands.py`; remove only their imports and `skill` subparser wiring from `yamlgraph/cli/__init__.py`. |
| D-2 | Delete obsolete skill-export tests `tests/unit/test_fr348_skill_export_red.py`, `tests/unit/test_fr350_agent_export_red.py`, and `tests/unit/test_fr351_agent_export_red.py`; add one narrow FR-912 witness test for top-level CLI rejection and residual-reference absence. |
| D-3 | Delete `reference/skills-export.md`; remove live skill-export rows, links, command sections, and active requirement claims from `reference/cli.md`, `reference/README.md`, `ARCHITECTURE.md`, and `reference/module-map.md`. |
| D-4 | Retire `capabilities/CAP-142-skill-export.yaml` and `capabilities/CAP-143-agent-md-export-tool-scoped-personas.yaml` with `status: retired` and description prefix `RETIRED by FR-912`, preserving the files and historical requirements. |
| D-5 | Conditional package endgame: if `yamlgraph/export/mcp.py` is already gone at enforcement time, delete `yamlgraph/export/__init__.py` and remove all live `.importlinter` references to `yamlgraph.export`; otherwise leave the package and export-seam intact and record the deferral in FR-912. |
| D-6 | Add a changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-912. |
| D-7 | Update `feature-requests/FR-912-retire-skill-export-surface.md` with implementation status, folded revisions, sequencing decision, and any deviations before enforcement is considered complete. |

Not authorized: deleting or modifying `.github/skills/**`; weakening CAP-158 / REQ-YG-423 or `tests/unit/test_fr446_copilot_skills.py`; retiring MCP (`yamlgraph/export/mcp.py`) or A2A surfaces under this FR; changing `yamlgraph/discovery.py`; changing `scripts/author.sh`, `scripts/judge.sh`, `scripts/review.sh`, or any judge/review/author doctrine or adapter; creating, copying, or materially modifying `graph.yaml` or `prompts/*.yaml`; deleting historical records in `feature-requests/`, `docs/diary/`, `.chaplain/done/`, frozen changelog directories, or other archives merely because they mention skill export.

## Revised acceptance criteria

- [ ] AC-01: `git ls-files 'yamlgraph/export/skill*' 'yamlgraph/cli/skill_commands.py'` prints no files, and `yamlgraph/cli/__init__.py` has no `cmd_skill_dispatch` import, no `skill` subparser, and no `skill-md|copilot|cursor|agent-md` export-format choice list.
- [ ] AC-02: A new FR-912 witness test asserts the top-level CLI parser rejects `skill` as an unknown subcommand and records `@pytest.mark.req` coverage appropriate to the retained/non-retired requirement it exercises; obsolete FR-348/350/351 tests are not kept as skipped tests.
- [ ] AC-03: `git ls-files 'tests/unit/test_fr348*' 'tests/unit/test_fr350*' 'tests/unit/test_fr351*'` prints no obsolete skill-export test files; `tests/unit/test_fr446_copilot_skills.py` still exists and passes.
- [ ] AC-04: `reference/skills-export.md` is deleted; `reference/cli.md`, `reference/README.md`, `ARCHITECTURE.md`, and `reference/module-map.md` contain no live skill-export advertising, active CAP-142/CAP-143 rows, or broken `skills-export.md` link.
- [ ] AC-05: A live-surface denylist search over `yamlgraph tests reference README.md ARCHITECTURE.md` for `skill_commands|yamlgraph\.export\.skill|yamlgraph/export/skill|cmd_skill_dispatch|PackageSkill|SkillPackage|SkillFormat|export_skill|write_skill_package|write_agent_md_file|yamlgraph skill export|skills-export\.md|agent-md|skill-md` returns zero matches except the FR-912 witness test and explicitly named non-live historical exceptions.
- [ ] AC-06: Export-package endgame is satisfied according to enforcement order: if `yamlgraph/export/mcp.py` exists, `yamlgraph/export/__init__.py` and `.importlinter` export-seam entries remain and FR-912 records that FR-910 is the remaining owner; if `yamlgraph/export/mcp.py` is already gone, `yamlgraph/export/__init__.py` is deleted and all live `.importlinter` mentions of `yamlgraph.export` are removed.
- [ ] AC-07: `capabilities/CAP-142-skill-export.yaml` and `capabilities/CAP-143-agent-md-export-tool-scoped-personas.yaml` both contain `status: retired`, a description prefixed `RETIRED by FR-912`, and preserved historical requirements; `python scripts/validate_capabilities.py` passes.
- [ ] AC-08: `python scripts/req_coverage.py --strict`, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass.
- [ ] AC-09: The full unit suite passes with the witness test present and deleted-import failures resolved rather than treated as success.
- [ ] AC-10: A changelog fragment under `changelog/unreleased/` exists with `type: removal` and names FR-912.
- [ ] AC-11: FR-912 contains the folded R-1 through R-5 revisions, implementation status, and the actual FR-910 sequencing decision.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-5 are folded into `feature-requests/FR-912-retire-skill-export-surface.md`. | GATE |
| C-2 | If a tracked search finds a real skill-export consumer outside the implementation, CLI dispatch, docs, CAP files, and obsolete self-tests, stop and amend the FR rather than silently deleting or preserving it. | GATE |
| C-3 | Do not delete or rewrite `.github/skills/**`, CAP-158 / REQ-YG-423, or `tests/unit/test_fr446_copilot_skills.py`; FR-912 retires the generator, not the hand-authored skill corpus. | GATE |
| C-4 | Do not retire MCP or A2A under this FR. MCP remains owned by FR-910 and A2A by FR-909, regardless of enforcement order. | GATE |
| C-5 | Only perform the `yamlgraph/export/` package deletion and `.importlinter` export cleanup when `yamlgraph/export/mcp.py` is already absent; otherwise record the explicit deferral in FR-912. | GATE |
| C-6 | Deleted-import test failures are not acceptable evidence of success; tests must be updated or deleted so failures map to the revised acceptance criteria. | GATE |
| C-7 | This FR authorizes deletion/retirement only. It does not authorize creating, copying, or materially modifying any `graph.yaml` or `prompts/*.yaml` artifact. | GATE |

Authority granted: after the required revisions are folded and the gates are acknowledged, the enforcer may retire only the YAMLGraph skill/agent export surface, its direct tests/docs, CAP-142/CAP-143 claims, and the conditional empty `yamlgraph/export` package seam described above.
