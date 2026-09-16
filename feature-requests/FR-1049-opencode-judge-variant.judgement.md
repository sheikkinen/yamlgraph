# Judgement: FR-1049 opencode judge variant — third backend in the sole-route judge adapter

**Prior art:** `FR-1049-opencode-judge-variant.md` — the FR this judgement
renders (its own subject; not a competing proposal). `FR-960-claude-judge-variant.judgement.md`
— the structural template (the Claude-judge analogue; this judgement repeats
its verdict shape for a different backend). `FR-1048-opencode-cli-backend.md`
and `FR-1048.research.md` — the backend and its research record that this FR
consumes (precondition, not a duplicate). `FR-546-opencode-copilot-backend.md`
— the superseded server/SDK route, excluded by this judgement's frozen scope.
None is a duplicate: this file freezes the scope and gates for the opencode
judge, which no prior judgement covers.

**Verdict:** APPROVED — the named provider-key-only consumer, implemented FR-1048 backend, minimal third-node route, exact human-selected model pin, fail-loud permission boundary, and mechanically witnessed enforcement gates now form a clear and testable contrib/example change; scope is frozen and authority is granted subject to the gates below.

**Reviewed against:** `feature-requests/FR-1049-opencode-judge-variant.md`; `feature-requests/evidence/FR-1049-opencode-judge-write-probe.md`; `feature-requests/FR-1048-opencode-cli-backend.md`; `feature-requests/evidence/FR-1048-opencode-cli-probe.md`; `feature-requests/evidence/FR-1048-opencode-backend-witness.md`; `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/evidence/FR-960-claude-judge-witness.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/SKILL.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/README.md`; `scripts/judge.sh`; `yamlgraph/routing.py`; `yamlgraph/models/schemas.py`; `yamlgraph/node_factory/copilot_node.py`; `yamlgraph/node_factory/copilot_runtime_opencode.py`; `tests/unit/test_fr960_claude_judge_variant.py`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `ramp/manifest.yaml`.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The proposal is the smallest route-level consumption of the already implemented backend: one graph node, three explicit routing conditions, one wrapper enum extension, directly coupled documentation/tests/traceability, and a live witness (`FR-1049:132-272`). Runtime/backend expansion, new permission flags, review/author/research migration, default changes, and the superseded server route are explicitly excluded (`FR-1049:369-403`). |
| Consistency | Summary, ideal result, target YAML, constraints, and acceptance criteria all select `backend: opencode`, preserve the default, and pin `deepseek/deepseek-v4-pro` (`FR-1049:62-82, 117-184, 278-347, 369-385`). The formerly open spend decision is now named and dated by the spend owner, and the same exact model appears across the target and criteria (`FR-1049:425-439, 454-461`). |
| Measurability | The acceptance criteria specify exact commands, paths, exit codes, argv order, forbidden flags, hashes, verdict grammar, route visits, mirror behavior, requirement tags, and witness fields (`FR-1049:278-347`). No success criterion depends only on aspirational prose. |
| Feasibility | FR-1048 is recorded Implemented with a passing live witness (`FR-1048:5-8`). The backend already has a strict two-field flag model (`yamlgraph/models/schemas.py:182-204`), compile-time validation/model resolution (`yamlgraph/node_factory/copilot_node.py:250-275`), exact `opencode run <prompt> --format json --model <provider/model>` construction (`yamlgraph/node_factory/copilot_runtime_opencode.py:210-216`), and fail-loud execution (`yamlgraph/node_factory/copilot_runtime_opencode.py:329-381`). The pinned CLI exposes the selected model and `--auto` boundary (`FR-1048-opencode-cli-probe:133-160`), while the dedicated probe demonstrates a workspace-local headless `write` completing without a permission flag and records its limits (`FR-1049-opencode-judge-write-probe:16-84`). |
| Architecture alignment | The change extends the existing FR-960 one-graph/two-node route rather than adding another route (`FR-960:70-167`; `.github/skills/judge-fr/adapters/graph.yaml:19-65`). It preserves the wrapper's closed-set validation and per-backend artifact seam (`scripts/judge.sh:23-33`) and obeys the graph-authoring route for the governed YAML (`FR-1049:132-139`; `.github/copilot-instructions.md:208-213`). |
| Single responsibility | Every authorized deliverable serves one concern: admitting the implemented opencode backend to the judge route and proving that route. Review, author, research, server/SDK, permission mapping, result-shape, and default-backend changes remain separate (`FR-1049:353-403`). No split is warranted. |
| Strategic classification | **Contrib/example.** There is one concrete provider-key-only operator and one first event (`FR-1049:8-15`), while the required backend and judge abstractions already exist (`FR-1048:74-84`; `FR-960:70-74`). The proposal fills a gap in those abstractions; it does not establish three independent use cases for a new framework primitive. |
| Testability | Direct failing tests follow from the wrapper and graph seams: backend selection, pre-lock rejection, artifact isolation/replacement, route exclusivity, shared prompt/variable propagation, and exact opencode argv (`FR-1049:243-256, 295-315`). The existing FR-960 tests demonstrate both seams without a live judge (`tests/unit/test_fr960_claude_judge_variant.py:99-315`); live behavior is separately gated and witnessed (`FR-1049:321-347`). |

The research gate is substantive: the FR preserves five materially different alternatives, dissent, dispositions, precedent, and an explicit `is_this_a_graph` answer (`FR-1049:349-359`). The enforcement-infrastructure risk is not normalized away: two human approvals remain a hard operational gate (`FR-1049:227-240, 340-343`), matching the repository's adversarial-input rule.

## Required revisions

None. The round-2 payer/model revision is folded mechanically: `deepseek/deepseek-v4-pro` is selected by Sami Heikkinen as spend owner on 2026-09-16 and is used consistently throughout the frozen plan (`FR-1049:425-439, 454-461`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md` — committed graph-authoring brief with the boundary, precedent, exact edits, lint, narrow mocked smoke, and report contract. |
| D-2 | `.github/skills/judge-fr/adapters/graph.yaml` — add only `judge_opencode`, replace the Copilot catch-all with `backend == "copilot"`, add explicit Claude/opencode conditions, and connect the new node to `END`. |
| D-3 | `scripts/judge.sh` — admit `opencode` in the closed backend set and usage/error text while preserving lock, sentinel, executor, artifact, and default behavior. |
| D-4 | `.github/skills/judge-fr/adapters/README.md`, `.github/skills/judge-fr/SKILL.md`, and `ramp/assets/tier2/github/skills/judge-fr/SKILL.md` — document and mirror the third backend, permission limitation, payer link, and explicit routing. |
| D-5 | `tests/unit/test_fr1049_opencode_judge_variant.py` — offline wrapper and mocked graph-routing witnesses, all tagged `REQ-YG-682`; existing judge wrapper/model-pin tests remain green. |
| D-6 | `capabilities/CAP-211-sole-route-judge-review.yaml`, generated `ARCHITECTURE.md`, and `changelog/unreleased/fr-1049-opencode-judge-variant.md` — REQ-YG-682 traceability only. |
| D-7 | `feature-requests/evidence/FR-1049-opencode-judge-witness.md` — authoring proof, two live runs on one comparison host, claim inventory, limitations, and two human approvals. |
| D-8 | `feature-requests/FR-1049-opencode-judge-variant.md` and one `docs/diary/` entry — implementation status/decisions/deviations and Distill record with a Seed. |

Not authorized: edits to `yamlgraph` backend/runtime/model/result code; `OpenCodeCliFlags`; any `--auto`, tool, agent, shell, resume, or permission flag; `adapters/prompts/judge.yaml`; judge doctrine or judgement template; Copilot/Claude node configuration other than the Copilot routing condition; the default backend; `scripts/review.sh`, `scripts/author.sh`, or `scripts/research.sh`; the FR-546 server/SDK route; a fourth backend; real judge execution from pytest or CI; automatic folding, committing, PR activity, polling, merging, or any expansion of the advisory artifact boundary. `ramp/assets/tier2/scripts/judge.sh` remains outside this FR.

## Revised acceptance criteria

- [ ] AC-01: Before D-1 through D-8 begin, FR-1048 remains Implemented on main, its committed probe and live witness exist, and its kill criterion has not fired.
- [ ] AC-02: The committed authoring brief names the sole graph artifact, FR-960 precedent, exact node/edge edits, lint command, narrow mocked smoke, and authoring-report contract.
- [ ] AC-03: `scripts/author.sh feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md` produces a non-empty local `tmp/draft-authoring-report.md`; the committed witness records its digest, required-section quotations, lint/smoke results, graph commit SHA, and limitations without claiming the report is committed.
- [ ] AC-04: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml` reports zero errors; REQ-YG-682 tests prove `copilot` visits only `judge`, `claude` only `judge_claude`, and `opencode` only `judge_opencode`, with the same `judge` prompt and requested `artifact_path`.
- [ ] AC-05: The Copilot and Claude node definitions and `adapters/prompts/judge.yaml` remain byte-identical; the only existing-edge change is `backend != "claude"` to `backend == "copilot"`.
- [ ] AC-06: The opencode node is `backend: opencode`, pins exactly `deepseek/deepseek-v4-pro`, and captures argv exactly as `["opencode", "run", <one prompt element>, "--format", "json", "--model", "deepseek/deepseek-v4-pro"]`, with no tool, approval, `--auto`, `--agent`, permission, resume, or shell argument.
- [ ] AC-07: Stubbed wrapper tests prove unset and explicit `copilot`, `claude`, and `opencode` selection; exact `backend` and `artifact_path` graph variables; and exit 64 before lock creation or executor launch for every unknown backend.
- [ ] AC-08: Wrapper tests prove `tmp/draft-judgement-opencode-<fr-slug>.md`; replacement of only the same-backend/same-FR artifact; and preservation of other-backend and other-FR drafts.
- [ ] AC-09: Adapter README, live SKILL, and byte-mirrored ramp SKILL describe the third backend and its precise ambient-permission limitation; `doctrine.md`, `judgement.template.md`, and `adapters/prompts/judge.yaml` have empty diffs.
- [ ] AC-10: CAP-211 contains REQ-YG-682 with FR-1049 provenance and the new graph/test modules; `ARCHITECTURE.md` is regenerated; every new test carries `@pytest.mark.req("REQ-YG-682")`; the changelog fragment carries `req: REQ-YG-682`; and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: On one comparison witness host with opencode 1.18.31, the selected model's provider key, and a working Copilot entitlement, `JUDGE_BACKEND=opencode scripts/judge.sh <FR>` writes a non-empty opencode draft with a `**Verdict:**` line; the witness records target path/commit, version, exact model argv, timestamps, artifact path/hash, verdict, and effective permission/config limitation.
- [ ] AC-12: The default Copilot run on the same host and target FR writes its own non-empty draft; both backend artifacts remain and have distinct hashes or explicitly recorded equality.
- [ ] AC-13: The witness inventories every substantive claim from both drafts under stable `CP-n`/`OC-n` IDs with source locations, evidence citations, and `matched`, `contradicted`, or `backend-only` dispositions; convergence uses the literal `no backend-only or contradicted items` sentinel.
- [ ] AC-14: Before the opencode route becomes operational or the FR is marked Implemented, the witness contains two separate dated approvals by humans other than the enforcer: acceptance of the enforcement-infrastructure diff/route invariants, and spend-owner acceptance of the FR-1048 provider-key payer boundary for judge execution.
- [ ] AC-15: The diary entry contains a Seed, all REQ-YG-682 tests and existing judge wrapper/model-pin tests pass, and pytest/CI never launches a real judge.
- [ ] AC-16: If the AC-11 run does not produce the required artifact and verdict under the frozen default-permission contract, the FR is rejected with the log attached; enforcement does not add `--auto`, invent a permission flag, fall back to Copilot/Claude, substitute a model, or weaken the artifact contract.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Treat `deepseek/deepseek-v4-pro` as the frozen H-1 human spend decision. Any model change or fallback returns to planning; enforcement does not substitute one. | GATE |
| C-2 | Confirm the FR-1048 implementation, committed probe, live witness, pinned 1.18.31 contract, and untriggered kill criterion before implementation. | GATE |
| C-3 | Make the governed graph edit only through the committed `scripts/author.sh` brief and preserve the local authoring report through its digest/quoted sections in the witness. | GATE |
| C-4 | Keep the opencode node to the single `model` flag. No runtime/schema/result change and no tool, approval, `--auto`, agent, resume, permission, or shell surface is permitted. | GATE |
| C-5 | Preserve the sole route: one wrapper, one graph, one prompt, explicit mutually exclusive backend edges, closed-set validation before the lock, unchanged default, and unchanged round/artifact/re-entry contracts. | GATE |
| C-6 | Keep all automated tests offline. A real judge may run only for the two explicitly recorded live witness runs. | GATE |
| C-7 | Apply the kill criterion literally if the opencode live run cannot write a valid verdict artifact under the frozen contract; do not rescue it by widening scope or silently falling back. | GATE |
| C-8 | Because this changes enforcement infrastructure and incurs provider spend, obtain and record both human approvals before operationalization or Implemented status. | GATE |
| C-9 | Keep `adapters/prompts/judge.yaml`, `.github/skills/judge-fr/doctrine.md`, and `.github/skills/judge-fr/judgement.template.md` unchanged, and preserve byte equality for the ramp SKILL mirror. | GATE |
| C-10 | Update the FR with implementation status, decisions, and deviations; complete REQ-YG-682 traceability, changelog, and Distill artifacts before marking Implemented. | GATE |

Authority granted: implement only D-1 through D-8 as frozen above, using `deepseek/deepseek-v4-pro`, and make the opencode judge route operational only after AC-01 through AC-16 and C-1 through C-10 are satisfied.
