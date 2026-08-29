# Judgement: FR-915 Retire the Mastra integration demo

**Prior art:** the top gate hit is this judgement's own subject FR (`FR-915-retire-mastra-integration-demo.md`), not independent precedent. `FR-291-per-graph-typed-mcp-tools.md` is the FR that *created* this demo and is dispositioned in the FR's Prior art line and throughout this judgement — it is the thing being retired, not a competing proposal. The remaining hits (`FR-876-minimal-llm-training-demo`, `FR-881-image-pipeline-v3-local-model-generator`) are noun collisions on "demo"/"integration" over unrelated surfaces (LLM training, image pipeline) with no bearing on MCP client demos. External retirement precedent (FR-909, FR-910, FR-465/466, FR-470/CAP-169, CAP-163) is dispositioned in the FR's Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS - the demo-retirement direction is sound, but authority activates only after the FR corrects its FR-910 sequencing/current-state claims and makes the remaining research and test criteria mechanically foldable.

**Reviewed against:** `feature-requests/FR-915-retire-mastra-integration-demo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `examples/demos/mastra-integration/mastra-app/src/index.ts`; `examples/demos/mastra-integration/demo-output.log`; `examples/demos/typescript-node/` directory listing; `examples/README.md`; `examples/dependency-taxonomy.yaml`; `tests/unit/test_fr375_typescript_node_demo_red.py`; `reference/cli.md`; `docs/research-mastra.md`; `feature-requests/FR-910-retire-mcp-surface.md`; `feature-requests/FR-910-retire-mcp-surface.judgement.md`; `feature-requests/FR-291-per-graph-typed-mcp-tools.md`; `feature-requests/FR-375-graph-run-json-stdout-typescript-node-integration.md`; `capabilities/CAP-79-demo-proof-gate.yaml`; `capabilities/CAP-136-per-graph-typed-mcp-tools.yaml`; `capabilities/CAP-163-cap-retirement-support.yaml`; `capabilities/CAP-169-dungeon-master-web-ui.yaml`; repository search output over FR-cited Mastra/MCP symbols in `examples/`, `yamlgraph/`, `reference/`, `tests/`, `.vscode/`, and `pyproject.toml`.

## What is sound

The problem is real. The Mastra demo declares itself an MCP typed-tool integration (`examples/demos/mastra-integration/mastra-app/src/index.ts:1-11`) and resolves `yamlgraph/mcp_server.py` as its server entry point (`examples/demos/mastra-integration/mastra-app/src/index.ts:21-23`), while that path is absent in the current tree. Its committed proof log is stale local-machine evidence, beginning with `Project root: /Users/sami.j.p.heikkinen/src/yamlgraph` rather than this checkout (`examples/demos/mastra-integration/demo-output.log:1-2`). The demo is also still advertised as a live Mastra/MCP integration in `examples/README.md:111` and is still present in the dependency taxonomy at `examples/dependency-taxonomy.yaml:301-305`.

The proposed scope is mostly minimal and single-responsibility: delete one obsolete demo directory, remove its examples advertising, regenerate the examples taxonomy, adjust the residual FR-375 documentation test, and add a removal changelog (`feature-requests/FR-915-retire-mastra-integration-demo.md:67-83`). The FR explicitly keeps the historical Mastra research record and the surviving TypeScript subprocess demo (`feature-requests/FR-915-retire-mastra-integration-demo.md:85-92`), which avoids the archive-sweep failure mode. That aligns with the repo doctrine that mature systems improve by pruning phantom claims (`.github/copilot-instructions.md:94`) and that demos prove abstractions worth having (`.github/copilot-instructions.md:154`).

The architectural classification is correct after revision: this is not a new framework primitive. It is retirement of an obsolete contrib/example surface whose remaining useful TypeScript integration use case is already covered by the FR-375 `typescript-node` demo (`feature-requests/FR-375-graph-run-json-stdout-typescript-node-integration.md:1-14`; `examples/README.md:131`). The alternatives table is substantive and dispositioned: it rejects rewriting against `graph run --json` because FR-375 already covers that transport, rejects keeping a non-runnable reference, rejects external MCP repointing, and rejects folding the work into already-frozen sibling FRs (`feature-requests/FR-915-retire-mastra-integration-demo.md:106-115`).

Most acceptance criteria are mechanically checkable: tracked demo deletion, zero Mastra matches under `examples/`, README row/guidance checks, idempotent taxonomy regeneration, demo gate, unit/registry checks, changelog presence, and `docs/research-mastra.md` no-diff are all commandable (`feature-requests/FR-915-retire-mastra-integration-demo.md:94-104`). CAP-79 supports the demo-proof-gate concern at the merge boundary (`capabilities/CAP-79-demo-proof-gate.yaml:1-24`).

## Required revisions

### R-1: Correct the FR-910 dependency and current-state claims

Revise the Summary, Problem evidence, Prior art, and acceptance criteria so FR-915 is explicitly sequenced after FR-910 enforcement rather than asserting that FR-910's implementation has already landed in this worktree. The current committed artifacts contradict the FR as written: FR-915 says FR-910 "retired the MCP server" and that CAP-136 already carries `status: retired` / `RETIRED by FR-910` (`feature-requests/FR-915-retire-mastra-integration-demo.md:17-20`, `29-31`, `41-53`), but this tree still contains `yamlgraph/export/mcp.py` as the MCP server (`yamlgraph/export/mcp.py:1-19`) and CAP-136 has no `status: retired` field while still listing `yamlgraph/export/mcp.py` and MCP requirements (`capabilities/CAP-136-per-graph-typed-mcp-tools.yaml:1-54`).

Fold this exact gate into the FR: "FR-915 enforcement is authorized only on a base where FR-910's MCP retirement acceptance criteria AC-01 and AC-05 are already true; FR-915 must not implement FR-910's `yamlgraph/`, packaging, reference, or CAP changes." FR-910 is judged and revisions are folded (`feature-requests/FR-910-retire-mcp-surface.md:5`), but its own scope and acceptance criteria still describe future enforcement (`feature-requests/FR-910-retire-mcp-surface.md:18-20`, `94-105`; `feature-requests/FR-910-retire-mcp-surface.judgement.md:60-84`). FR-915 may depend on that result; it may not silently absorb it.

### R-2: Add the required `is_this_a_graph` research answer

Fold an explicit research line into the FR, for example: "`is_this_a_graph`: No. This is retirement of an obsolete demo artifact, not authoring of a replacement graph; the surviving TypeScript integration is the existing `examples/demos/typescript-node/` subprocess demo." The local judge doctrine requires research substance to include genuine alternatives, precedent lines, disagreement preserved, and the `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-128`). FR-915 has a useful in-body alternatives table (`feature-requests/FR-915-retire-mastra-integration-demo.md:106-115`), but it currently lacks the explicit graph-fit answer.

### R-3: Make the FR-375 residual-test acceptance criterion exact

Replace AC-05 with a mechanically checkable criterion that names the command and the required assertions. The current text requires the test to pass "without asserting any MCP term" and to be mutation-checked (`feature-requests/FR-915-retire-mastra-integration-demo.md:100`), while the current test asserts MCP in both `reference/cli.md` and `examples/README.md` (`tests/unit/test_fr375_typescript_node_demo_red.py:42-54`). Fold this replacement:

"`pytest tests/unit/test_fr375_typescript_node_demo_red.py::test_ac09_docs_include_json_mode_and_typescript_demo_guidance -q --no-cov` passes; the test source contains no assertion for the string `mcp`; it still asserts `--json`, `stdout`, and `subprocess` in `reference/cli.md`, and `typescript-node`, `--json`, and `subprocess` in `examples/README.md`."

This preserves the FR-375 subprocess documentation witness without making the enforcer perform an underspecified manual mutation exercise.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete all tracked files under `examples/demos/mastra-integration/`, including `README.md`, `demo.sh`, `demo-output.log`, `graph.yaml`, `prompts/greet.yaml`, `tools.py`, and the `mastra-app/` Node project. |
| D-2 | Remove the `mastra-integration` row from `examples/README.md` and rewrite the TypeScript integration guidance there so it names `demos/typescript-node/`, `graph run --json`, and subprocess request/response without offering MCP as a TypeScript alternative. |
| D-3 | Regenerate `examples/dependency-taxonomy.yaml` with `python scripts/example_taxonomy_scan.py` so no `mastra-integration` path remains. |
| D-4 | Update `tests/unit/test_fr375_typescript_node_demo_red.py` so its documentation test no longer asserts any MCP term and still protects the `typescript-node` / `--json` / subprocess guidance. |
| D-5 | Add a changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-915. |
| D-6 | Update `feature-requests/FR-915-retire-mastra-integration-demo.md` with folded revisions, implementation status, decisions, and any deviations. |

Not authorized: implementing any FR-910 surface retirement in this FR; touching `yamlgraph/`, `pyproject.toml`, `.vscode/`, `capabilities/CAP-19*`, `capabilities/CAP-136*`, or `reference/mcp-server.md`; deleting or modifying `docs/research-mastra.md`; deleting or weakening `examples/demos/typescript-node/`; deleting any other demo; sweeping historical diary, memento, archived research, feature-request, or judgement records merely because they mention Mastra or MCP.

## Revised acceptance criteria

- [ ] AC-01: FR-910 dependency gate is satisfied before enforcement: `test ! -e yamlgraph/export/mcp.py` passes, and `rg -n 'status: retired|RETIRED by FR-910' capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` shows both retirement markers. If either check fails, stop; FR-915 may not perform those changes itself.
- [ ] AC-02: `git ls-files 'examples/demos/mastra-integration/*'` prints no files.
- [ ] AC-03: `rg -ri 'mastra' examples/` returns no matches.
- [ ] AC-04: `examples/README.md` has no `mastra-integration` row, and its TypeScript-integration guidance names `demos/typescript-node/`, `graph run --json`, and subprocess request/response without offering MCP as an alternative.
- [ ] AC-05: `examples/dependency-taxonomy.yaml` contains no `mastra-integration` path, and `python scripts/example_taxonomy_scan.py` followed by `git diff --exit-code examples/dependency-taxonomy.yaml` proves the taxonomy is idempotent.
- [ ] AC-06: `pytest tests/unit/test_fr375_typescript_node_demo_red.py::test_ac09_docs_include_json_mode_and_typescript_demo_guidance -q --no-cov` passes; the test source contains no assertion for `mcp`; it still asserts `--json`, `stdout`, and `subprocess` in `reference/cli.md`, and `typescript-node`, `--json`, and `subprocess` in `examples/README.md`.
- [ ] AC-07: `./scripts/check_demo_proof.sh` passes, and no `examples/demos/mastra-integration/demo-output.log` remains in the tree.
- [ ] AC-08: full unit suite passes; `python scripts/req_coverage.py --strict` and `python scripts/validate_capabilities.py` pass.
- [ ] AC-09: a changelog fragment exists under `changelog/unreleased/` with `type: removal` and text naming FR-915.
- [ ] AC-10: `git diff --exit-code docs/research-mastra.md` passes.
- [ ] AC-11: `git diff --name-only` for this FR contains no paths under `yamlgraph/`, `.vscode/`, `capabilities/`, or `examples/demos/typescript-node/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-3 are folded into `feature-requests/FR-915-retire-mastra-integration-demo.md`. | GATE |
| C-2 | FR-915 must be enforced only after FR-910's MCP retirement is present in the base; if MCP server code or CAP-136 active status remains, stop rather than implementing FR-910 under this FR. | GATE |
| C-3 | Deleting the Mastra demo must delete its stale `demo-output.log`; keeping the proof artifact while removing or disabling code would recreate the `gate_checks_shape_not_substance` defect (`.github/copilot-instructions.md:88`). | GATE |
| C-4 | `docs/research-mastra.md` is a retained historical record and must remain byte-for-byte untouched. | GATE |
| C-5 | `examples/demos/typescript-node/` is the surviving TypeScript integration witness and must remain untouched except for external documentation that points to it. | GATE |

Authority granted: after the required revisions are folded and the FR-910 dependency gate is satisfied, the enforcer may retire only the Mastra integration demo and its examples-level advertising/taxonomy/test witnesses described above.
