# Feature Request: Retire the MCP server surface (export/mcp.py, mcp.json, CAP-19, CAP-136)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded 2026-08-29)
**Effort:** 0.5 days
**Requested:** 2026-08-29
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops carrying
a tool surface whose registration was broken for six weeks without a single
failure report.
**Research:** [docs/research-agentic-sdlc-providers-2026-08-29.md](../docs/research-agentic-sdlc-providers-2026-08-29.md) §4.4
(committed alongside this FR) + in-body dispositioned alternatives table below.
**Prior art:** FR-465/FR-466 (CAP retirement mechanism — followed, not duplicated); FR-470 (retired-CAP file format — followed); FR-717 PR2 (moved the server to export/mcp.py and orphaned the registration — the breakage this FR's evidence rests on); FR-355 (MCP schema validation gate — its test retires with the surface); CAP-19/CAP-136 (the claims being retired); sibling FR-909 (A2A retirement — separate surface, separate FR per judgement C-4).

## Summary

Delete yamlgraph's MCP server surface — `yamlgraph/export/mcp.py`,
`.vscode/mcp.json`, the `mcp` extra, MCP tests and reference doc — and
retire CAP-19 and CAP-136 per the FR-465/466 retirement precedent.

## Value Statement

Maintainers shed a ~370-line server, its typed-tool test suite, the `mcp`
dependency, and two capability claims whose consumer class never
materialized — while the agent-facing thesis remains served by the
transport that demonstrably won (CLI adapters).

## Problem

No one speaks MCP to yamlgraph (operator-confirmed 2026-08-29). The
mechanical evidence: `.vscode/mcp.json` pointed at `yamlgraph/mcp_server.py`,
deleted by FR-717 PR2 on 2026-07-18; the launch command failed with ENOENT
for ~6 weeks while ~130 `mcp_yamlgraph_*` tools in agent sessions were
served from stale editor cache — not one invocation can have succeeded, and
nobody noticed. Decisively, the `builders_never_call` diary witness
(2026-07-17, graphs found unconsumed) **predates the breakage**: the surface
was unconsumed even while it worked. Agents consume graphs daily through the
route that won — CLI wrapped in adapter scripts (`author.sh`, `judge.sh`,
`review.sh`). MCP duplicated that surface for editor-attached dynamic tool
selection, a consumer class that never appeared here.

## Ideal Result

No MCP server code, registration, dependency, or capability claim remains;
the Scripture's `is_this_a_graph` cure points agents at `yamlgraph graph
list` (CLI) only; CAP-19/CAP-136 read `status: retired` citing this FR;
suite and `req_coverage.py --strict` green. Resurrection requires a named
external MCP host actually wired to yamlgraph, dispositioning this FR first.

## Proposed Solution

1. **Code**: delete `yamlgraph/export/mcp.py` (no wiring in
   `export/__init__.py` — verified); update the `mcp_server.py` mention in
   `yamlgraph/discovery.py`'s docstring.
2. **Registration**: delete `.vscode/mcp.json` AND remove the
   `.vscode/settings.json` entries that authorize it
   (`chat.mcp.serverSampling` etc.) so no stale registration state remains
   (R-2). (The launch path was fixed 2026-08-29 during evaluation; the fix
   becomes moot.)
3. **Tests**: delete `tests/unit/test_mcp_server.py`,
   `tests/unit/test_mcp_typed_tools.py`, and
   `tests/unit/test_fr355_mcp_schema_validation_gate_red.py`; update
   MCP-dependent residual tests rather than leaving import-error failures
   (R-2): `tests/unit/test_fr853_task_shapes_index.py`,
   `tests/unit/test_discovery.py`, `tests/unit/test_invoke_graph.py`,
   `tests/unit/test_fr717_seams.py`, and
   `tests/unit/test_concurrency_safety_doc.py`.
4. **Packaging**: remove the `mcp` extra (`pyproject.toml` line ~116);
   verify mechanically that `constraints/dev-py312.txt` has no `^mcp==`
   pin — regenerate only if that check fails (R-4; inspected file has no
   pin).
5. **Docs & doctrine**: delete `reference/mcp-server.md`; remove live
   MCP-server claims and links from `reference/README.md`,
   `reference/a2a-server.md` (if it survives FR-909), `CLAUDE.md`,
   `reference/getting-started.md`, `docs/concurrency-safety.md` (and its
   witness test), `docs/dependency-rationale.yaml`, and the Scripture's
   `is_this_a_graph` entry (CLI route only). **The
   `.github/copilot-instructions.md` edit is enforcement-infrastructure
   work: isolated in its own commit and explicitly human-approved before
   merge (R-3, binding).**
6. **Registry**: CAP-19, CAP-136 → `status: retired`, description prefixed
   `RETIRED by FR-910`.
7. **Changelog**: fragment `type: removal`.

Kept: `yamlgraph/discovery.py` and every other exporter in
`yamlgraph/export/` (CLI-consumed).

## Acceptance Criteria

Revised per judgement (R-1 replaced the over-broad `\bmcp\b` grep, which
matched unrelated fixtures in `test_fr358_*` and `test_fr375_*`):

- [ ] AC-01: `test ! -e yamlgraph/export/mcp.py && test ! -e .vscode/mcp.json && test ! -e reference/mcp-server.md`
- [ ] AC-02: `.vscode/settings.json` is absent or contains no `.vscode/mcp.json` / `chat.mcp.serverSampling` entries for yamlgraph
- [ ] AC-03: the server-surface denylist returns zero matches on live surfaces (excluding `feature-requests/`, `docs/diary/`, `docs/memento/`, archives, changelog fragments, judgements):
  `rg -n 'yamlgraph\.export\.mcp|yamlgraph/export/mcp\.py|yamlgraph\.mcp_server|mcp_server\.py|yamlgraph_list_graphs|yamlgraph_run_graph|mcp_yamlgraph_' yamlgraph tests reference README.md CLAUDE.md .github/copilot-instructions.md .vscode docs/concurrency-safety.md docs/dependency-rationale.yaml --glob '!**/__pycache__/**'`
- [ ] AC-04: `pyproject.toml` contains no `mcp = [` extra and `rg -n '^mcp==' constraints/dev-py312.txt` returns no matches
- [ ] AC-05: CAP-19 and CAP-136 both contain `status: retired` and `RETIRED by FR-910`, historical requirements preserved in the files
- [ ] AC-06: the three MCP-only test files are deleted; residual tests no longer import `yamlgraph.export.mcp` or assert `yamlgraph/export/mcp.py` exists
- [ ] AC-07: `.github/copilot-instructions.md` `is_this_a_graph` names `yamlgraph graph list` only, not MCP tools
- [ ] AC-08: `reference/README.md`, `reference/a2a-server.md`, `docs/concurrency-safety.md`, `docs/dependency-rationale.yaml`, `CLAUDE.md`, `reference/getting-started.md`, and `yamlgraph/discovery.py` contain no live MCP-server claim or broken link to `reference/mcp-server.md`
- [ ] AC-09: `python scripts/req_coverage.py --strict` passes
- [ ] AC-10: full unit suite, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass
- [ ] AC-11: changelog fragment in `changelog/unreleased/` with `type: removal`
- [ ] AC-12: this FR records implementation status and folded revisions before enforcement is considered complete

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep + fix registration (this session's initial verdict) | OVERTURNED by operator consumer record — and `builders_never_call` predates the breakage, so the working surface was already unconsumed |
| Probation (fix now, retire if unused in 30 days) | REFUTED — `detection_without_enforcement`; the 6-week dead period *was* the probation, result: zero demand |
| Keep because "build for agents first" | REFUTED — the thesis is served by CLI adapters, consumed daily; thesis without a consumer is `growth_as_default` with a mission statement |
| Retire (chosen) | Cheap, reversible, precedented (FR-465/466); resurrection condition named |

## Related

- Evidence: docs/research-agentic-sdlc-providers-2026-08-29.md §4.4
- Breakage origin: FR-717 PR2 (export package seam, 2026-07-18)
- Precedent: FR-465/FR-466, FR-470, CAP-163; sibling FR-909 (A2A retirement)
- Diary witness: 2026-07-17 `builders_never_call`

## Judgement (2026-08-29)

**Verdict:** APPROVED WITH REVISIONS — full judgement:
[FR-910-retire-mcp-surface.judgement.md](FR-910-retire-mcp-surface.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | `\bmcp\b` grep over-broad (matches unrelated fixtures, pycache) | Replaced with server-surface denylist, AC-03 |
| R-2 | Missing live surfaces: `.vscode/settings.json`, `reference/README.md` link, `reference/a2a-server.md` MCP section, `docs/concurrency-safety.md` + witness test, `test_mcp_server.py`, four residual MCP-importing tests | Folded into Proposed Solution items 2, 3, 5 and AC-02/AC-06/AC-08 |
| R-3 | Scripture edit is enforcement-infrastructure | Isolated commit + explicit human approval before merge (item 5, C-2) |
| R-4 | Constraints regen unnecessary unless a pin exists | Mechanical `^mcp==` check; regenerate only on failure (item 4, AC-04) |

**Conditions:** C-1–C-5 per judgement — notably C-2 (doctrine edit human-approved), C-3 (discovery.py preserved), C-4 (A2A owned by FR-909), C-5 (deleted-import failures are not success evidence).

**Scope frozen:** deliverables D-1–D-8 per judgement.

## Implementation Status (2026-08-29)

**Enforced** on branch `feat/fr910-retire-mcp`, stacked on
`feat/fr909-retire-a2a` (the two retirements share doc surfaces; C-4 is
honoured — separate FRs, separate commits, separate PRs). RED witness
committed first (`test(mcp): FR-910 RED witness…`).

- D-1: deleted `yamlgraph/export/mcp.py`.
- D-2: deleted the untracked `.vscode/mcp.json` and the MCP-only
  `.vscode/settings.json` (both are gitignored, so they leave no diff);
  removed the dead `!.vscode/mcp.json` negation from `.gitignore`.
- D-3: removed the `mcp` extra from `pyproject.toml`; `constraints/dev-py312.txt`
  carries no `^mcp==` pin, so no regen (R-4).
- D-4: CAP-19 and CAP-136 carry `status: retired` + `RETIRED by FR-910`.
- D-5: deleted `test_mcp_server.py`, `test_mcp_typed_tools.py`,
  `test_fr355_mcp_schema_validation_gate_red.py`; updated
  `test_discovery.py`, `test_invoke_graph.py`, `test_fr717_seams.py`,
  `test_fr853_task_shapes_index.py`, `test_concurrency_safety_doc.py`.
- D-6: deleted `reference/mcp-server.md`; removed live claims from
  `reference/README.md`, `CLAUDE.md`, `docs/concurrency-safety.md`,
  `docs/dependency-rationale.yaml`, `yamlgraph/discovery.py`,
  `yamlgraph/export/__init__.py`, `yamlgraph/compile/graph_loader.py`.
- D-7: `changelog/unreleased/fr-910-retire-mcp-surface.md` (`type: removal`).
- D-8: this section.

**Doctrine edit (C-2):** `.github/copilot-instructions.md` `is_this_a_graph`
now names `yamlgraph graph list` only. It is **isolated in its own commit**
and requires explicit human approval before merge.

### Finding: C-3's premise does not hold

C-3 preserves `yamlgraph/discovery.py` "because it is CLI-consumed". It is
not. After the MCP server is deleted, `discover_graphs()` and
`DEFAULT_GRAPH_PATTERNS` have **zero production consumers** — `yamlgraph
graph list` does not use them; only tests import them. `vulture` flags both
as dead code.

C-3 is a GATE, so this FR does **not** delete the module. Both names were
added to `vulture_whitelist.py` with the reason recorded. **Disposition of
`yamlgraph/discovery.py` (retire, or wire a real consumer) belongs to a
follow-up FR.**

### Out of scope, flagged

`examples/demos/mastra-integration/` demonstrates a TypeScript client
discovering typed MCP tools. It is not in D-1–D-8 and is not touched here;
it is now a demo of a retired surface and needs its own disposition.

**Verification:** full unit suite 6197 passed / 97 skipped / 1 xfailed;
`req_coverage.py --strict`, `validate_capabilities.py`,
`dependency_rationale.py --strict`, `lint-imports`, and `vulture` all pass.
