# Feature Request: Retire the A2A surface (server, client, CLI, demo, CAPs 81/101/103/104/105)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded 2026-08-29)
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops
installing grpcio/protobuf/starlette, stops running ~1,500 dead test lines,
and stops asserting five capability claims nothing consumes.
**Research:** [docs/research-agentic-sdlc-providers-2026-08-29.md](../docs/research-agentic-sdlc-providers-2026-08-29.md) §4.4
(committed alongside this FR) + in-body dispositioned alternatives table below.
**Prior art:** FR-465/FR-466 (CAP retirement mechanism — followed, not duplicated); FR-470 (retired-CAP file format — followed); FR-253 (moved a2a_call to contrib — this FR completes that arc by retiring the contrib client too); FR-761/FR-762 (a2a extra dependency-honesty — their ownership comments are resolved by deletion); sibling FR-910 (MCP retirement — separate surface, separate FR per judgement C-2/C-4).

## Summary

Delete yamlgraph's A2A protocol surface — server, contrib client, CLI
subcommand, demo, optional extra — and retire CAP-81, CAP-101, CAP-103,
CAP-104, CAP-105 per the FR-465/466 retirement precedent.

## Value Statement

Maintainers shed ~1,600 code lines, ~1,500 test lines, three heavy optional
dependencies, and five phantom capability claims that have had zero
consumers for four months.

## Problem

No one speaks A2A to yamlgraph (operator-confirmed 2026-08-29; in-repo
evidence concurs). `send_a2a_message` is referenced only by its own CAPs,
tests, and demo; `examples/demos/a2a_call/` is the sole graph using it; no
chaplain script, example, or external system (outcaller, ninchat_voice)
calls the server or client. Last functional commit: FR-253 (2026-04-19) —
everything since is mechanical carrying cost (CI gates, seam refactors,
dependency-honesty fixes). None of the seven providers surveyed in the
research doc speak A2A. Unconsumed capability claims are the
`growth_as_default` failure mode the FR-465/466 arc exists to cure.

## Ideal Result

`grep -ri a2a yamlgraph/ tests/` returns nothing; `pip install -e ".[dev]"`
paths carry no grpcio/protobuf/starlette; the five CAP files read
`status: retired` with this FR cited; the full suite and
`req_coverage.py --strict` are green; the spec survives in the FRs and git
history so resurrection is a disposition of this FR, not archaeology.

## Proposed Solution

Mechanical deletion plus registry retirement:

1. **Code**: delete `yamlgraph/a2a/` (server.py, message.py, __init__.py),
   `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py`;
   remove only their imports and subparser wiring from
   `yamlgraph/cli/__init__.py` (line 12, ~347–401).
2. **Tests**: delete `tests/unit/test_a2a_server.py`,
   `test_a2a_server_docs.py`, `test_a2a_message.py`,
   `test_a2a_contrib_client.py`, and `test_a2a_commands.py` (R-1); add a
   narrow FR-909 witness test asserting the CLI rejects `a2a` as an unknown
   subcommand and no live A2A references remain (R-2).
3. **Demos**: delete `examples/demos/a2a_call/` **and
   `examples/demos/a2a_server/`** (R-1); remove A2A rows from
   `examples/dependency-taxonomy.yaml` and `examples/README.md`.
4. **Packaging**: remove the `a2a` extra, `a2a-sdk`, A2A-owned `grpcio`
   and `protobuf` from `pyproject.toml`; `starlette` is removed only from
   A2A ownership — it stays where a retained extra (e.g. `openai-proxy`)
   requires it (R-3). Update CI install commands in `.github/workflows/`
   and `CLAUDE.md`; regenerate `constraints/dev-py312.txt` per FR-761.
5. **Docs** (mechanically explicit per R-1): delete
   `reference/a2a-server.md`; remove live A2A sections/links from
   `examples/README.md`, `reference/README.md`, `reference/cli.md`,
   `README.md`/`reference/getting-started.md`, and the active A2A
   capability rows in `ARCHITECTURE.md`.
6. **Registry**: CAP-81, CAP-101, CAP-103, CAP-104, CAP-105 →
   `status: retired`, description prefixed `RETIRED by FR-909` (CAP files
   stay, per CAP-163 retirement support).
7. **Changelog**: fragment `type: removal`.

Kept: `yamlgraph/discovery.py` (consumed by the CLI; its stale A2A wording
is updated, not deleted).

**Boundary (R-4):** this FR does NOT retire MCP, shared graph invocation,
`yamlgraph/discovery.py`, `yamlgraph/export/`, or any non-A2A
protocol/export surface — MCP retirement is sibling FR-910.

## Acceptance Criteria

Revised per judgement (R-2 replaced the impossible zero-A2A-in-tests grep):

- [ ] AC-01: `git ls-files 'yamlgraph/a2a/*' 'yamlgraph/cli/a2a_commands.py' 'yamlgraph/contrib/a2a_client.py'` prints no files, and `git grep -niE '\ba2a\b|send_a2a_message|create_a2a_app|parse_a2a_message' -- yamlgraph` prints no live implementation/import references
- [ ] AC-02: a new FR-909 witness test asserts the top-level CLI parser rejects `a2a` as an unknown subcommand; `yamlgraph/cli/__init__.py` has no `cmd_a2a_dispatch` import and no `a2a` subparser
- [ ] AC-03: `git ls-files 'tests/unit/test_a2a*.py'` prints no obsolete A2A test files; the only permitted A2A mention under `tests/` is the FR-909 retirement witness test
- [ ] AC-04: `examples/demos/a2a_call/`, `examples/demos/a2a_server/`, and `reference/a2a-server.md` are deleted; `examples/dependency-taxonomy.yaml`, `examples/README.md`, `reference/README.md`, `reference/cli.md`, README/getting-started docs, and `ARCHITECTURE.md` contain no live A2A advertising or active A2A requirement claims
- [ ] AC-05: `pyproject.toml` has no `a2a` extra, no `a2a-sdk`, no A2A-owned `grpcio`/`protobuf`; retained `starlette` declarations are justified by non-A2A extras only
- [ ] AC-06: `.github/workflows/workflow.yml`, `CLAUDE.md`, and `constraints/dev-py312.txt` updated so install commands do not request the removed `a2a` extra or A2A-only distributions
- [ ] AC-07: CAP-81/101/103/104/105 each carry `status: retired` + `RETIRED by FR-909`; retired CAPs remain valid under `scripts/validate_capabilities.py`
- [ ] AC-08: `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py`, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass
- [ ] AC-09: full unit suite passes with obsolete A2A tests deleted and the witness test present
- [ ] AC-10: changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-909

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep as-is | REFUTED — zero consumers for 4 months; pure carrying cost (research doc §4.4) |
| Keep server, retire client (or inverse) | REFUTED — neither half has a consumer; partial retirement is `partial_remediation` |
| Archive to `contrib/` unclaimed | REFUTED — `constraint_over_code`: git history is the archive; an unclaimed module is a shim |
| Wait for A2A market adoption | REFUTED — `would_you_use_this` requires a named consumer *now*; resurrection path is cheap and explicit |

## Related

- Evidence: docs/research-agentic-sdlc-providers-2026-08-29.md §4.4
- Precedent: FR-465/FR-466 (CAP retirement arc), FR-470 (CAP-169 retirement format), CAP-163 (retirement support)
- History: FR-253 (a2a_call → contrib client), FR-761/FR-762 (dependency honesty for a2a extra)

## Judgement (2026-08-29)

**Verdict:** APPROVED WITH REVISIONS — full judgement:
[FR-909-retire-a2a-surface.judgement.md](FR-909-retire-a2a-surface.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Two live A2A surfaces missing (`examples/demos/a2a_server/`, `tests/unit/test_a2a_commands.py`) + docs sweep too vague | Folded into Proposed Solution items 2, 3, 5 and AC-03/AC-04 |
| R-2 | "No A2A in tests" grep impossible (witness test must mention a2a) | Replaced with AC-01–AC-03 witness-compatible checks |
| R-3 | `starlette` also owned by retained `openai-proxy` extra | Folded into item 4 and AC-05: remove A2A ownership only |
| R-4 | Adjacent-retirement boundary implicit | Explicit boundary paragraph added: no MCP/export/discovery changes |

**Conditions:** C-1–C-7 per judgement — notably C-2 (no MCP work under this FR), C-5 (CI/constraints edits need human review), C-6 (stop and amend if a real consumer surfaces), C-7 (deletion only; no graph authoring).

**Scope frozen:** deliverables D-1–D-6 per judgement.

## Implementation Status (2026-08-29)

**Enforced** on branch `feat/fr909-retire-a2a`. RED witness committed first
(`test(a2a): FR-909 RED witness…`), then the deletion sweep.

- D-1: deleted `yamlgraph/a2a/`, `yamlgraph/contrib/a2a_client.py`,
  `yamlgraph/cli/a2a_commands.py`; removed the import and subparser block
  from `yamlgraph/cli/__init__.py`.
- D-2: deleted the five obsolete A2A test modules; added
  `tests/unit/test_fr909_a2a_retirement.py` (9 witnesses, `REQ-YG-032`,
  `pytestmark = pytest.mark.process` because it asserts `examples/` paths).
- D-3: deleted both demos and `reference/a2a-server.md`; removed A2A rows
  from `examples/README.md`, `reference/README.md`, and the whole
  `## yamlgraph a2a` section from `reference/cli.md`;
  `examples/dependency-taxonomy.yaml` and `reference/module-map.md`
  regenerated.
- D-4: removed the `a2a` extra from `pyproject.toml`; removed the extra
  from `.github/workflows/workflow.yml` (both jobs), `CLAUDE.md`, and the
  `constraints/dev-py312.txt` header.
- D-5: CAP-81/101/103/104/105 carry `status: retired` +
  `RETIRED by FR-909`.
- D-6: `changelog/unreleased/fr-909-retire-a2a-surface.md` (`type: removal`).

**Deviations (all consequences of the deletion, none expanding scope):**

1. **REQ-YG-206 relocated to CAP-111.** CAP-81 hosted the *shared graph
   discovery* requirement, which survives the retirement (C-3 keeps
   `discovery.py`) and is tagged by nine live tests. Retiring CAP-81 whole
   would have made it a phantom REQ and broken `req_coverage.py --strict`.
   Duplicate REQ IDs are rejected by `validate_capabilities.py`, so the
   requirement moved rather than being copied; the historical fragment
   `changelog/0.4.64/FR-208-a2a-graph-support.md` was repointed to
   `REQ-YG-207..213` to keep the changelog↔CAP cross-check honest.
2. **`.importlinter`**: removed the `a2a-seam` contract and every
   `yamlgraph.a2a` layer/forbidden-module entry — the contract referenced a
   module that no longer exists and `lint-imports` failed hard on it.
   `tests/unit/test_fr717_seams.py` updated accordingly.
3. **Residual test updates** (C-5 class, not deleted-import failures):
   `test_fr375_typescript_node_demo_red.py` no longer asserts A2A guidance
   in the CLI/examples docs; `test_example_taxonomy_scan.py`'s real-tree
   regression now pins `examples/openai_proxy` instead of the deleted A2A
   demos.
4. **`constraints/dev-py312.txt`**: rather than a wholesale regen (which
   would have churned every unrelated pin against today's resolver), the
   ten A2A-attributable distributions were derived by diffing two clean
   Python 3.12 installs — with and without the `a2a` extra — and removed:
   `a2a-sdk`, `aiologic`, `culsans`, `google-api-core`,
   `googleapis-common-protos`, `grpcio`, `json-rpc`, `proto-plus`,
   `protobuf`, `sse-starlette`.

**Verification:** full unit suite 6234 passed / 97 skipped / 1 xfailed;
`req_coverage.py --strict`, `validate_capabilities.py`,
`validate_id_registry.py`, `check_changelog_req.py`,
`dependency_rationale.py --strict`, `direct_import_scan.py --strict`, and
`lint-imports` all pass.

**C-5 discharged (2026-08-29):** the operator reviewed and approved the
CI-workflow (`.github/workflows/workflow.yml`, both install commands) and
dependency-constraint (`constraints/dev-py312.txt`, ten a2a-attributable
pins removed by two-environment diff) edits. All GATE conditions C-1–C-7
are satisfied; the PR is unblocked for merge.
