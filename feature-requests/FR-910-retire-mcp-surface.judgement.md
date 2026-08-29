# Judgement: FR-910 Retire the MCP server surface

**Prior art:** gate hits are this change's own sibling artifacts (FR-910 FR, FR-909 A2A-retirement FR and judgement, committed together); external precedent (FR-717, FR-355, FR-465/466, FR-470, CAP-19/CAP-136) is dispositioned in the FR's own Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS - the retirement direction is evidenced and strategically sound, but authority activates only after the FR folds in the missing live surfaces and replaces the over-broad `mcp` grep gate with server-specific acceptance criteria.

**Reviewed against:** `feature-requests/FR-910-retire-mcp-surface.md`; `docs/research-agentic-sdlc-providers-2026-08-29.md` section 4.4; `feature-requests/FR-466-cap-retirement-support.md`; `capabilities/CAP-163-cap-retirement-support.yaml`; `feature-requests/FR-470-dm-web-ui-v2-synopsis-review.md`; `capabilities/CAP-169-dungeon-master-web-ui.yaml`; `feature-requests/FR-909-retire-a2a-surface.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `capabilities/CAP-19-mcp-server-interface.yaml`; `capabilities/CAP-136-per-graph-typed-mcp-tools.yaml`; `pyproject.toml`; `constraints/dev-py312.txt`; `.vscode/mcp.json`; `.vscode/settings.json`; `reference/README.md`; `reference/a2a-server.md`; `docs/concurrency-safety.md`; `tests/unit/test_fr375_typescript_node_demo_red.py`; `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py`; `tests/unit/test_concurrency_safety_doc.py`; `tests/unit/test_fr717_seams.py`; `tests/unit/test_discovery.py`; `tests/unit/test_invoke_graph.py`; repository search output over FR-cited MCP server symbols in `yamlgraph/`, `tests/`, `reference/`, `.vscode/`, `CLAUDE.md`, `.github/copilot-instructions.md`, and selected live docs.

## What is sound

The problem is real and evidenced. The FR names a first consumer and first event: maintainers and CI stop carrying a broken tool surface from this PR onward (`feature-requests/FR-910-retire-mcp-surface.md:8-11`). It cites a committed research record (`feature-requests/FR-910-retire-mcp-surface.md:12-13`) whose MCP section says the operator confirmed no MCP consumer, the registration failed for about six weeks, stale cached tools hid the failure, and the unconsumed-surface witness predated the breakage (`docs/research-agentic-sdlc-providers-2026-08-29.md:237-256`). The alternatives table disposes the obvious keep/probation/build-for-agents objections rather than hand-waving them (`feature-requests/FR-910-retire-mcp-surface.md:86-93`).

Scope and single responsibility are mostly clear: retire one transport surface, its registration, dependency, tests, docs, and two capability claims (`feature-requests/FR-910-retire-mcp-surface.md:17-19`), while explicitly keeping `yamlgraph/discovery.py` and other exporters (`feature-requests/FR-910-retire-mcp-surface.md:73-74`). That aligns with repo doctrine: `growth_as_default` says mature systems improve by pruning phantom capability claims, not adding implementations (`.github/copilot-instructions.md:94`), and `does_the_tool_fit_or_merely_exist` requires fit to a named recurring task rather than a generic affordance (`.github/copilot-instructions.md:130`).

The implementation is feasible. The MCP dependency is isolated as a `mcp` extra in `pyproject.toml:116-118`, the live server capability claims are in CAP-19 and CAP-136 (`capabilities/CAP-19-mcp-server-interface.yaml:1-27`; `capabilities/CAP-136-per-graph-typed-mcp-tools.yaml:1-54`), and the CAP retirement mechanism already exists: FR-466 defines `status: retired` as first-class lifecycle support (`feature-requests/FR-466-cap-retirement-support.md:11-15`), CAP-163 records that mechanism (`capabilities/CAP-163-cap-retirement-support.yaml:3-6`), and CAP-169 shows the concrete retired-file format (`capabilities/CAP-169-dungeon-master-web-ui.yaml:1-8`).

Strategic classification: this is a justified retirement of a former framework primitive, not a new primitive. The old surface has zero current use cases in this repo while the existing CLI-adapter route satisfies the agent-facing use case (`docs/research-agentic-sdlc-providers-2026-08-29.md:242-256`). Per the judge rubric, the correct classification is effectively "Reject the stale surface": the problem is real, and the solution reduces complexity rather than creating it (`.github/skills/judge-fr/doctrine.md:51-57`).

## Required revisions

### R-1: Replace the broad `mcp` grep acceptance criterion with a server-specific denylist

Revise the acceptance criterion at `feature-requests/FR-910-retire-mcp-surface.md:79`. `grep -riE '\bmcp\b' yamlgraph/ tests/` is not a valid gate because it catches unrelated or historical uses, including a watcher2 PR-title fixture string (`tests/unit/test_fr358_watcher2_primary_pr_title_selection.py:87-95`) and a TypeScript demo docs assertion about protocol alternatives (`tests/unit/test_fr375_typescript_node_demo_red.py:42-54`). It also risks matching ignored `__pycache__` files unless exclusions are spelled out.

Replace it with a server-surface denylist over live surfaces only:

```bash
rg -n 'yamlgraph\.export\.mcp|yamlgraph/export/mcp\.py|yamlgraph\.mcp_server|mcp_server\.py|yamlgraph_list_graphs|yamlgraph_run_graph|mcp_yamlgraph_' \
  yamlgraph tests reference README.md CLAUDE.md .github/copilot-instructions.md .vscode docs/concurrency-safety.md docs/dependency-rationale.yaml \
  --glob '!**/__pycache__/**'
```

The revised criterion must require zero matches, except inside `feature-requests/`, `docs/diary/`, `docs/memento/`, archived research/context records, changelog fragments, and the judgement itself.

### R-2: Add the missing live surfaces to the Proposed Solution and acceptance criteria

Fold these exact surfaces into the FR before enforcement:

- Remove `.vscode/settings.json` entries that authorize `.vscode/mcp.json`; deleting only `.vscode/mcp.json` leaves stale MCP registration state (`.vscode/settings.json:2-8`; `.vscode/mcp.json:1-8`).
- Update `reference/README.md` so it no longer links to the deleted `reference/mcp-server.md` (`reference/README.md:45-53`).
- Update `reference/a2a-server.md` if it remains after FR-909, because it currently describes the MCP server and links to the soon-deleted MCP reference (`reference/a2a-server.md:415-449`).
- Update or remove the MCP section in `docs/concurrency-safety.md` and its witness test; it currently cites `yamlgraph/export/mcp.py` lines as live evidence (`docs/concurrency-safety.md:121-136`; `tests/unit/test_concurrency_safety_doc.py:18-35`).
- Delete `tests/unit/test_mcp_server.py`, `tests/unit/test_mcp_typed_tools.py`, and `tests/unit/test_fr355_mcp_schema_validation_gate_red.py`.
- Update MCP-dependent residual tests rather than leaving them to fail for import errors: `tests/unit/test_fr853_task_shapes_index.py`, `tests/unit/test_discovery.py:33-40`, `tests/unit/test_invoke_graph.py:108-121`, and `tests/unit/test_fr717_seams.py:15-21`.

This revision cures consistency and testability defects under the judge rubric: tests must fail because the server exists when it should not, not because deleted imports were left behind (`.github/skills/judge-fr/doctrine.md:41-61`).

### R-3: Make the doctrine edit a named human-review gate

The FR correctly says the Scripture's `is_this_a_graph` entry should point only to the CLI route (`feature-requests/FR-910-retire-mcp-surface.md:44-48`, `63-68`; current text at `.github/copilot-instructions.md:133`), but doctrine changes are enforcement-infrastructure changes. Fold an explicit condition into the FR: the `.github/copilot-instructions.md` edit must be reviewed as its own commit or explicitly human-approved before merge. This is not optional; the judge doctrine requires adversarial review for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:94-103`).

### R-4: Clarify dependency artifact handling

Keep the `mcp` extra removal, but make the constraints rule mechanical: remove `pyproject.toml`'s `mcp` extra (`pyproject.toml:116-118`) and run a check that `constraints/dev-py312.txt` contains no `^mcp==` pin. Do not require regenerating `constraints/dev-py312.txt` unless that check fails; the inspected file has no `mcp` pin.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `yamlgraph/export/mcp.py`. |
| D-2 | Delete `.vscode/mcp.json` and remove `.vscode/settings.json` entries that reference it. |
| D-3 | Remove the `mcp` optional extra from `pyproject.toml`; verify `constraints/dev-py312.txt` has no MCP pin. |
| D-4 | Retire `capabilities/CAP-19-mcp-server-interface.yaml` and `capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` with `status: retired` and a `RETIRED by FR-910` description prefix while preserving the files as historical records. |
| D-5 | Delete MCP-server-only tests and update remaining tests that assert MCP server existence or import `yamlgraph.export.mcp`. |
| D-6 | Delete `reference/mcp-server.md`; remove live links and server claims from `reference/README.md`, `reference/a2a-server.md`, `CLAUDE.md`, `reference/getting-started.md`, `.github/copilot-instructions.md`, `yamlgraph/discovery.py`, `docs/concurrency-safety.md`, and `docs/dependency-rationale.yaml` where they refer to the live MCP server. |
| D-7 | Add a changelog fragment with `type: removal`. |
| D-8 | Update `feature-requests/FR-910-retire-mcp-surface.md` with implementation status, folded revisions, and any deviations. |

Not authorized: deleting or weakening `yamlgraph/discovery.py`; deleting other exporters; changing CLI graph-list behavior, `author.sh`, `judge.sh`, or `review.sh`; retiring A2A under this FR rather than FR-909; sweeping historical diary, memento, archived research, or context records merely because they mention MCP; changing judge/review/author routing doctrine beyond the single `is_this_a_graph` MCP-tool reference named in this FR.

## Revised acceptance criteria

- [ ] AC-01: `test ! -e yamlgraph/export/mcp.py && test ! -e .vscode/mcp.json && test ! -e reference/mcp-server.md`.
- [ ] AC-02: `.vscode/settings.json` is absent or contains no `.vscode/mcp.json` / `chat.mcp.serverSampling` entries for yamlgraph.
- [ ] AC-03: the server-surface denylist command from R-1 returns zero matches in live surfaces, excluding only historical archives, changelog fragments, feature-request records, and judgement artifacts.
- [ ] AC-04: `pyproject.toml` contains no `mcp = [` extra and `rg -n '^mcp==' constraints/dev-py312.txt` returns no matches.
- [ ] AC-05: `capabilities/CAP-19-mcp-server-interface.yaml` and `capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` both contain `status: retired` and `RETIRED by FR-910`, and their historical requirements remain in the files.
- [ ] AC-06: `tests/unit/test_mcp_server.py`, `tests/unit/test_mcp_typed_tools.py`, and `tests/unit/test_fr355_mcp_schema_validation_gate_red.py` are deleted; residual tests no longer import `yamlgraph.export.mcp` or assert `yamlgraph/export/mcp.py` exists.
- [ ] AC-07: `.github/copilot-instructions.md` `is_this_a_graph` names `yamlgraph graph list` only, not MCP tools.
- [ ] AC-08: `reference/README.md`, `reference/a2a-server.md`, `docs/concurrency-safety.md`, `docs/dependency-rationale.yaml`, `CLAUDE.md`, `reference/getting-started.md`, and `yamlgraph/discovery.py` contain no live MCP-server claim or broken link to `reference/mcp-server.md`.
- [ ] AC-09: `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: full unit suite, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass after the dependency and import-surface deletion.
- [ ] AC-11: a changelog fragment exists in `changelog/unreleased/` with `type: removal`.
- [ ] AC-12: the FR records implementation status and the folded revisions before enforcement is considered complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-4 are folded into `feature-requests/FR-910-retire-mcp-surface.md`. | GATE |
| C-2 | The `.github/copilot-instructions.md` edit is enforcement-infrastructure work and must be isolated for human review or explicitly human-approved before merge. | GATE |
| C-3 | Do not delete `yamlgraph/discovery.py`; the cited research says shared discovery stays because it is CLI-consumed (`docs/research-agentic-sdlc-providers-2026-08-29.md:269-272`). | GATE |
| C-4 | Do not combine A2A retirement with this FR; sibling FR-909 owns A2A (`feature-requests/FR-909-retire-a2a-surface.md:15-19`, `64-69`). | GATE |
| C-5 | Deleted-import test failures are not acceptable evidence of success; tests must be updated or deleted so failures map to the revised acceptance criteria. | GATE |

Authority granted: after the required revisions are folded and gates are acknowledged, the enforcer may retire only the YAMLGraph MCP server surface, registration, dependency, live docs/tests, and CAP-19/CAP-136 claims described above.
