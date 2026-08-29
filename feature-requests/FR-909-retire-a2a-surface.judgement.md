# Judgement: FR-909 Retire the A2A surface

**Prior art:** gate hits are this change's own sibling artifacts (FR-909 FR, FR-910 MCP-retirement FR and judgement, committed together); external precedent (FR-253, FR-465/466, FR-470, FR-761/762) is dispositioned in the FR's own Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS — the retirement is evidenced, strategically correct, and feasible, but authority activates only after the FR fixes two missing live A2A surfaces and replaces the impossible "no A2A in tests" grep criterion with a witness-compatible one.

**Reviewed against:** `feature-requests/FR-909-retire-a2a-surface.md`; cited evidence `docs/research-agentic-sdlc-providers-2026-08-29.md` §4.4; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `feature-requests/TEMPLATE.md`; precedent `feature-requests/FR-466-cap-retirement-support.md`, `capabilities/CAP-163-cap-retirement-support.yaml`, `feature-requests/FR-253-a2a-consumer-to-contrib.md`, `feature-requests/FR-761-reproducible-dependency-governance.md`, `feature-requests/FR-761-reproducible-dependency-governance.judgement.md`, `feature-requests/FR-762-example-dependency-taxonomy.md`, `feature-requests/FR-762-example-dependency-taxonomy.judgement.md`, `feature-requests/FR-470-dm-web-ui-v2-synopsis-review.md`; current cited surfaces `capabilities/CAP-81-a2a-server.yaml`, `capabilities/CAP-101-a2a-call-node.yaml`, `capabilities/CAP-103-a2a-sdk-v1-compatibility.yaml`, `capabilities/CAP-104-a2a-server-reference-docs.yaml`, `capabilities/CAP-105-a2a-consumer-phase2.yaml`, `ARCHITECTURE.md`, `pyproject.toml`, `.github/workflows/workflow.yml`, `CLAUDE.md`, `examples/dependency-taxonomy.yaml`, `examples/README.md`, `reference/README.md`, `reference/cli.md`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/a2a_commands.py`, `yamlgraph/a2a/server.py`, `yamlgraph/a2a/message.py`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/discovery.py`, `tests/unit/test_a2a_server.py`, `tests/unit/test_a2a_server_docs.py`, `tests/unit/test_a2a_message.py`, `tests/unit/test_a2a_contrib_client.py`, `tests/unit/test_a2a_commands.py`, and tracked-file searches over `yamlgraph/`, `tests/`, `examples/`, `reference/`, docs, workflows, and packaging manifests.

## What is sound

The problem is real and evidenced. FR-909 names a concrete first consumer and event: maintainers and CI stop installing A2A dependencies, stop running dead tests, and stop asserting unused capabilities at merge time (`feature-requests/FR-909-retire-a2a-surface.md:8-13`). The cited research independently records "A2A — RETIRE", with zero consumers, only self-tests/demo references, four months of carrying cost after FR-253, and no surveyed provider workflow speaking A2A (`docs/research-agentic-sdlc-providers-2026-08-29.md:258-267`).

The strategic classification is **Reject / retire surface**, not a framework primitive, contrib/example, or pattern-doc increment. The current CAPs assert active server, client, SDK compatibility, reference-doc, and consumer-streaming requirements (`capabilities/CAP-81-a2a-server.yaml:1-57`, `capabilities/CAP-101-a2a-call-node.yaml:1-25`, `capabilities/CAP-103-a2a-sdk-v1-compatibility.yaml:1-37`, `capabilities/CAP-104-a2a-server-reference-docs.yaml:1-24`, `capabilities/CAP-105-a2a-consumer-phase2.yaml:1-52`), while the doctrine explicitly treats unconsumed capability accretion as `growth_as_default` and names CAP retirement as the cure (`.github/copilot-instructions.md:94`, `.github/copilot-instructions.md:125`, `.github/copilot-instructions.md:162`).

The architecture and feasibility are sound. A2A is isolated enough to delete surgically: the CLI imports and wires the A2A subparser in one place (`yamlgraph/cli/__init__.py:12`, `yamlgraph/cli/__init__.py:347-401`), the protocol server/client live in named leaf modules (`yamlgraph/a2a/server.py:1-51`, `yamlgraph/a2a/message.py:1-29`, `yamlgraph/contrib/a2a_client.py:1-21`), and CAP-163/FR-466 already provide the registry retirement mechanism that excludes retired REQs from strict coverage while preserving historical records (`feature-requests/FR-466-cap-retirement-support.md:9-15`, `feature-requests/FR-466-cap-retirement-support.md:118-127`, `capabilities/CAP-163-cap-retirement-support.yaml:1-24`).

The FR is mostly single-responsibility: retire one unconsumed protocol surface. Its packaging, docs, tests, CAP registry, and changelog work are not separate features; they are the required cleanup blast radius of that deletion. The cited dependency-governance precedent supports touching constraints and install commands when optional dependency ownership changes (`feature-requests/FR-761-reproducible-dependency-governance.md:8-16`; `feature-requests/FR-761-reproducible-dependency-governance.judgement.md:106-112`), and the example taxonomy precedent supports removing A2A example classifications when the examples disappear (`feature-requests/FR-762-example-dependency-taxonomy.judgement.md:9-11`, `feature-requests/FR-762-example-dependency-taxonomy.md:252-255`).

## Required revisions

### R-1: Add every live A2A surface to the deletion and documentation sweep

Amend the Proposed Solution and Acceptance Criteria to explicitly include `examples/demos/a2a_server/`, `tests/unit/test_a2a_commands.py`, `examples/README.md`, `reference/README.md`, `reference/cli.md`, and the A2A entries in `ARCHITECTURE.md`. The current FR names `examples/demos/a2a_call/` but not the live server demo (`feature-requests/FR-909-retire-a2a-surface.md:58-59`, `examples/dependency-taxonomy.yaml:100-109`, `examples/README.md:108-109`), and it lists four A2A test files while `tests/unit/test_a2a_commands.py` also directly tests the A2A CLI (`feature-requests/FR-909-retire-a2a-surface.md:55-57`, `tests/unit/test_a2a_commands.py:1-17`). The docs sweep is currently broad prose (`feature-requests/FR-909-retire-a2a-surface.md:64-65`); make it mechanically explicit because the active CLI/reference indexes still advertise A2A (`reference/README.md:51-54`, `reference/cli.md:8-17`, `reference/cli.md:183-235`), and `ARCHITECTURE.md` still lists CAP-81/101/103/104/105 as active capability rows (`ARCHITECTURE.md:406-429`, `ARCHITECTURE.md:1309-1324`, `ARCHITECTURE.md:1508-1559`).

### R-2: Replace the impossible zero-A2A-in-tests criterion

Replace `grep -riE '\ba2a\b' yamlgraph/ tests/ returns no matches` with a tracked-source absence check that excludes the new FR-909 witness test, plus a separate positive assertion that the witness test exists. The current AC-01 and AC-02 conflict: a test proving `yamlgraph a2a` is rejected must mention `a2a`, so the grep over all `tests/` cannot return zero matches (`feature-requests/FR-909-retire-a2a-surface.md:76-77`; `.github/skills/judge-fr/doctrine.md:43-44`, `.github/skills/judge-fr/doctrine.md:58-61`). The enforcer needs a check shaped like "no live A2A implementation/import/docs references remain" rather than "the historical string never appears in any test."

### R-3: Clarify dependency removal without deleting unrelated dependency ownership

Amend the dependency acceptance criterion to say `a2a-sdk`, `grpcio`, `protobuf`, and the `a2a` extra are removed, and `starlette` is removed only from A2A ownership comments/paths if another retained extra still requires it. FR-909 says maintainer install paths stop carrying `grpcio/protobuf/starlette` (`feature-requests/FR-909-retire-a2a-surface.md:8-11`, `feature-requests/FR-909-retire-a2a-surface.md:41-43`), but `pyproject.toml` currently also declares `starlette` under the retained `openai-proxy` extra (`pyproject.toml:119-125`, `pyproject.toml:142-145`). Deleting that unrelated declaration would violate scope; leaving it without clarifying the FR would make the acceptance criterion misleading.

### R-4: Freeze resurrection and adjacent-retirement boundaries

Add one explicit sentence to the FR: this FR does not retire MCP, shared graph invocation, `yamlgraph/discovery.py`, or any non-A2A protocol/export surface. The cited research section discusses MCP retirement immediately before A2A (`docs/research-agentic-sdlc-providers-2026-08-29.md:242-256`), and `yamlgraph/discovery.py` still has shared-protocol wording (`yamlgraph/discovery.py:1-6`) while `ARCHITECTURE.md` records root-package seams that include `yamlgraph.a2a` among broader package boundaries (`ARCHITECTURE.md:2640-2648`). The FR already intends to keep discovery (`feature-requests/FR-909-retire-a2a-surface.md:71-72`); make the non-authorized boundary explicit so enforcement does not expand into MCP/export or shared invocation cleanup.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete A2A implementation modules: `yamlgraph/a2a/`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py`; remove only their imports/subparser wiring from `yamlgraph/cli/__init__.py`. |
| D-2 | Delete obsolete A2A tests: `tests/unit/test_a2a_server.py`, `tests/unit/test_a2a_server_docs.py`, `tests/unit/test_a2a_message.py`, `tests/unit/test_a2a_contrib_client.py`, `tests/unit/test_a2a_commands.py`; add a narrow FR-909 regression test for CLI rejection and live-reference absence. |
| D-3 | Delete A2A demos/docs: `examples/demos/a2a_call/`, `examples/demos/a2a_server/`, `reference/a2a-server.md`; remove live A2A rows/links/CLI sections from `examples/dependency-taxonomy.yaml`, `examples/README.md`, `reference/README.md`, `reference/cli.md`, README/getting-started references, and A2A active claims in `ARCHITECTURE.md`. |
| D-4 | Remove the `a2a` optional extra and A2A-owned dependency declarations from `pyproject.toml`; update `.github/workflows/workflow.yml`, `CLAUDE.md`, and `constraints/dev-py312.txt` so install commands no longer request `a2a`. |
| D-5 | Retire `capabilities/CAP-81-a2a-server.yaml`, `capabilities/CAP-101-a2a-call-node.yaml`, `capabilities/CAP-103-a2a-sdk-v1-compatibility.yaml`, `capabilities/CAP-104-a2a-server-reference-docs.yaml`, and `capabilities/CAP-105-a2a-consumer-phase2.yaml` with `status: retired` and `RETIRED by FR-909` descriptions. |
| D-6 | Add one changelog fragment with `type: removal`. |

Not authorized: MCP retirement; deletion of `yamlgraph/discovery.py`; changes to `yamlgraph/export/`, skill export, MCP adapter scripts, shared graph invocation semantics, LangGraph execution semantics, non-A2A demos, non-A2A dependency extras, or any replacement graph/prompt authoring. If a surviving graph or prompt must be materially changed rather than deleted, that is a separate graph-authoring-governed task.

## Revised acceptance criteria

- [ ] AC-01: `git ls-files 'yamlgraph/a2a/*' 'yamlgraph/cli/a2a_commands.py' 'yamlgraph/contrib/a2a_client.py'` prints no files, and `git grep -niE '\ba2a\b|send_a2a_message|create_a2a_app|parse_a2a_message' -- yamlgraph` prints no live implementation/import references.
- [ ] AC-02: A new FR-909 witness test asserts the top-level CLI parser rejects `a2a` as an unknown subcommand; `yamlgraph/cli/__init__.py` has no `cmd_a2a_dispatch` import and no `a2a` subparser.
- [ ] AC-03: `git ls-files 'tests/unit/test_a2a*.py'` prints no obsolete A2A test files; the only permitted A2A mention under `tests/` is the new FR-909 retirement witness test.
- [ ] AC-04: `examples/demos/a2a_call/`, `examples/demos/a2a_server/`, and `reference/a2a-server.md` are deleted; `examples/dependency-taxonomy.yaml`, `examples/README.md`, `reference/README.md`, `reference/cli.md`, README/getting-started docs, and `ARCHITECTURE.md` contain no live A2A advertising or active A2A requirement claims.
- [ ] AC-05: `pyproject.toml` has no `a2a` optional extra and no `a2a-sdk`, A2A-owned `grpcio`, or A2A-owned `protobuf` declaration; retained `starlette` declarations are justified by non-A2A extras only.
- [ ] AC-06: `.github/workflows/workflow.yml`, `CLAUDE.md`, and `constraints/dev-py312.txt` are regenerated/updated so install commands and pinned dependency artifacts do not request the removed `a2a` extra or A2A-only distributions.
- [ ] AC-07: CAP-81, CAP-101, CAP-103, CAP-104, and CAP-105 each carry `status: retired` and a description prefixed `RETIRED by FR-909`; retired CAPs remain valid under `scripts/validate_capabilities.py`.
- [ ] AC-08: `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py`, `lint-imports`, and `python scripts/direct_import_scan.py --strict` pass.
- [ ] AC-09: The full unit suite passes with the obsolete A2A tests deleted and the FR-909 witness test present.
- [ ] AC-10: A changelog fragment under `changelog/unreleased/` exists with `type: removal` and names FR-909.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-4 are folded into `feature-requests/FR-909-retire-a2a-surface.md`. | GATE |
| C-2 | Do not retire or modify MCP/export surfaces under this FR, even though the cited research also says MCP should retire. | GATE |
| C-3 | Preserve `yamlgraph/discovery.py` except for removing stale A2A wording; if its live CLI/MCP behavior changes, stop and amend the FR. | GATE |
| C-4 | Do not remove `starlette` from retained non-A2A extras such as `openai-proxy`; remove only A2A-owned dependency claims and pins. | GATE |
| C-5 | CI workflow, dependency-constraint, and enforcement-gate edits require human review because judge doctrine treats enforcement-infrastructure changes as adversarial input. | GATE |
| C-6 | If a tracked search finds a real A2A consumer outside the named tests, demos, docs, CAPs, and implementation modules, stop and amend the FR rather than silently deleting or preserving it. | GATE |
| C-7 | This FR authorizes deletion of A2A graph artifacts only. It does not authorize creating, adapting, or materially rewriting any surviving `graph.yaml` or `prompts/*.yaml`. | GATE |

Authority granted: after the required revisions are folded, enforce one mechanical retirement of the unconsumed A2A protocol surface and its direct tests, docs, dependencies, demos, and CAP claims.
