# FR-1049 run — copilot judge draft (raw, advisory)

**Prior art:** `FR-1049-opencode-judge-witness.md` — the witness that cites this
raw draft; this file is the draft itself, committed so the witness's claim
inventory is independently auditable (review P1). `FR-960-run-A-copilot-draft-FR-961.md`
— the Copilot-judge raw-draft analogue (same role, prior FR). None is a
duplicate: this is the raw Copilot judge output on FR-1049, which no other file
contains.

**Verdict:** APPROVED — the request names a real provider-key-only consumer, reuses the implemented FR-1048 backend through the existing sole-route pattern, freezes an exact human-selected model and fail-loud permission boundary, and supplies mechanically checkable offline and live gates; this draft becomes implementation authority only after human review and promotion.

**Reviewed against:** `feature-requests/FR-1049-opencode-judge-variant.md`; `feature-requests/evidence/FR-1049-opencode-judge-write-probe.md`; `feature-requests/FR-1048-opencode-cli-backend.md`; `feature-requests/evidence/FR-1048-opencode-cli-probe.md`; `feature-requests/evidence/FR-1048-opencode-backend-witness.md`; `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/FR-1049-opencode-judge-variant.judgement.md` (round-history evidence only, not inherited authority); `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `scripts/judge.sh`; `yamlgraph/routing.py`.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The smallest useful change is exactly the proposed one: consume the existing opencode backend in the existing judge graph, make the prior Copilot catch-all explicit, admit one closed-set wrapper value, and prove the route. Runtime/schema/result changes, permission mapping, other sole-route wrappers, default changes, and FR-546's server route are excluded (`FR-1049:56-82, 118-219, 373-403`). |
| Consistency | Summary, target graph, wrapper plan, constraints, and acceptance criteria consistently use `backend: opencode`, preserve Copilot as default, and pin `deepseek/deepseek-v4-pro`. The formerly open payer decision is now recorded with chooser and date, and the comparison-host entitlement requirement is distinguished from the provider-key-only consumer (`FR-1049:56-82, 145-187, 280-347, 373-390, 438-461`). |
| Measurability | The criteria specify commands, paths, exact argv, forbidden flags, route visits, exit codes, hashes, mirror equality, requirement tags, witness fields, two signatures, and an explicit kill result. Each criterion can be checked by an assertion, file inspection, or recorded live command (`FR-1049:280-347, 364-371`). |
| Feasibility | FR-1048 is recorded Implemented with a live nonce-resumption witness (`FR-1048:5-10`; `FR-1048-opencode-backend-witness:13-50`). Its contract already limits opencode flags to `model` and `resume`, requires an explicit `provider/model`, and freezes prompt-first JSONL argv (`FR-1048:150-189, 191-250, 268-292`). The dedicated FR-1049 probe records a completed workspace-local `write` without `--auto` and clearly limits that evidence to one host, model, version, and in-workspace path (`FR-1049-opencode-judge-write-probe:16-84`). |
| Architecture alignment | The proposal follows FR-960's one-wrapper, one-graph, shared-prompt, conditional-backend-node pattern rather than creating another route (`FR-960:60-167`). The explicit equality edges also match the router's first-match behavior and remove the third-value misroute (`FR-1049:87-101, 190-207`; `yamlgraph/routing.py:91-115`). |
| Single responsibility | All authorized deliverables serve one concern: admitting and witnessing opencode as a judge backend. Review, author, research, server/SDK, permission-schema, result-shape, default-backend, and fourth-backend work remain separate (`FR-1049:373-403`). A split would duplicate one route-level change rather than isolate orthogonal work. |
| Strategic classification | **Contrib/example.** One named consumer has one concrete first event, while both the copilot-node backend abstraction and judge-route abstraction already exist (`FR-1049:11-17, 56-82`; `FR-1048:13-20`; `FR-960:8-10`). This fills a gap in those abstractions; it does not establish three independent use cases for a framework primitive. |
| Testability | Direct failing tests follow from the criteria: unknown backend rejected before lock, exact graph variables, artifact isolation/replacement, mutually exclusive node visits, shared prompt/path propagation, exact opencode argv, and forbidden arguments. Live file-writing and cross-backend comparison are deliberately separated from offline pytest and guarded by the kill criterion (`FR-1049:243-256, 280-347, 364-371`). |

The prospective research gate is substantive rather than shape-only: five alternatives preserve opposing cases and explicit dispositions, prior FR-960/FR-1048/FR-546 territory is distinguished, and the FR answers `is_this_a_graph` directly (`FR-1049:29-54, 350-362`). The risky ambient-permission assumption is not promoted into a universal contract: the FR states that `--auto` exists but remains unmapped, limits the claim to the probed default configuration and workspace-local write, requires failure through the artifact contract, and rejects scope-widening rescue if the live witness fails (`FR-1049:20-28, 62-75, 364-371`).

## Required revisions

None. The prior human-decision gap is folded mechanically: spend owner Sami Heikkinen selected `deepseek/deepseek-v4-pro` on 2026-09-16, and the same exact value is used by the target node, argv criterion, requirement, constraints, and live witness contract (`FR-1049:157-158, 252-256, 274-278, 300-304, 375-381, 438-446`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md` — committed graph-authoring brief naming the artifact boundary, precedent, exact edits, lint, narrow mocked smoke, and report contract. |
| D-2 | `.github/skills/judge-fr/adapters/graph.yaml` — add only `judge_opencode`, change the Copilot condition to `backend == "copilot"`, retain explicit Claude routing, add explicit opencode routing, and connect the new node to `END`. |
| D-3 | `scripts/judge.sh` — add `opencode` to the closed backend set and usage/error text while preserving the default, lock, round sentinel, re-entry guard, executor resolution, and artifact contract. |
| D-4 | `.github/skills/judge-fr/adapters/README.md`, `.github/skills/judge-fr/SKILL.md`, and `ramp/assets/tier2/github/skills/judge-fr/SKILL.md` — document the third backend, exact ambient-permission limitation, payer link, routing condition, and required byte mirror. |
| D-5 | `tests/unit/test_fr1049_opencode_judge_variant.py` — offline wrapper and mocked graph-routing witnesses, all tagged `REQ-YG-682`. |
| D-6 | `capabilities/CAP-211-sole-route-judge-review.yaml`, generated `ARCHITECTURE.md`, and `changelog/unreleased/fr-1049-opencode-judge-variant.md` — FR-1049/REQ-YG-682 traceability only. |
| D-7 | `feature-requests/evidence/FR-1049-opencode-judge-witness.md` — authoring proof, one opencode run and one default Copilot run on the same comparison host, claim inventory, limitations, and two separate human approvals. |
| D-8 | `feature-requests/FR-1049-opencode-judge-variant.md` and one `docs/diary/` entry — implementation status, decisions/deviations, and Distill record with a Seed. |

Not authorized: changes to `yamlgraph` backend/runtime/schema/result code; `OpenCodeCliFlags`; any `--auto`, tool, approval, agent, shell, resume, or permission mapping; `.github/skills/judge-fr/adapters/prompts/judge.yaml`; judge doctrine or judgement template; Copilot or Claude node configuration other than the Copilot edge condition; the default backend; `scripts/review.sh`, `scripts/author.sh`, or `scripts/research.sh`; FR-546's server/SDK route; a fourth backend; real judge execution in pytest or CI; automatic folding, committing, PR activity, polling, merging, or any expansion of the advisory artifact boundary. `ramp/assets/tier2/scripts/judge.sh` remains outside this FR.

## Revised acceptance criteria

- [ ] AC-01: Before D-1 through D-8 begin, FR-1048 remains Implemented on main, its committed probe and live witness exist, and its kill criterion has not fired.
- [ ] AC-02: The committed authoring brief names `.github/skills/judge-fr/adapters/graph.yaml` as the sole governed artifact, FR-960 as precedent, the exact node/edge edits, lint command, narrow mocked smoke, and authoring-report contract.
- [ ] AC-03: `scripts/author.sh feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md` produces a non-empty local `tmp/draft-authoring-report.md`; D-7 records its digest, required-section quotations, lint/smoke results, graph commit SHA, and limitations without claiming that report is committed.
- [ ] AC-04: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml` reports zero errors; REQ-YG-682 tests prove `copilot` visits only `judge`, `claude` only `judge_claude`, and `opencode` only `judge_opencode`, with all three using the same `judge` prompt and requested `artifact_path`.
- [ ] AC-05: The Copilot and Claude node definitions and `.github/skills/judge-fr/adapters/prompts/judge.yaml` remain byte-identical; the only existing-edge change is `backend != "claude"` to `backend == "copilot"`.
- [ ] AC-06: The opencode node uses `backend: opencode`, pins exactly `deepseek/deepseek-v4-pro`, and produces exactly `["opencode", "run", <one prompt element>, "--format", "json", "--model", "deepseek/deepseek-v4-pro"]`, with no tool, approval, `--auto`, `--agent`, permission, resume, or shell argument.
- [ ] AC-07: Stubbed wrapper tests prove unset and explicit `copilot`, `claude`, and `opencode` selection; exact `backend` and `artifact_path` graph variables; and exit 64 before lock creation or executor launch for every unknown backend.
- [ ] AC-08: Wrapper tests prove `tmp/draft-judgement-opencode-<fr-slug>.md`, replacement of only the same-backend/same-FR artifact, and preservation of other-backend and other-FR drafts.
- [ ] AC-09: The adapter README, live SKILL, and byte-mirrored ramp SKILL describe the third backend and precise ambient-permission limitation; `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and `.github/skills/judge-fr/adapters/prompts/judge.yaml` have empty diffs.
- [ ] AC-10: CAP-211 contains REQ-YG-682 with FR-1049 provenance and the new graph/test modules; `ARCHITECTURE.md` is regenerated; every new test has `@pytest.mark.req("REQ-YG-682")`; the changelog fragment has `req: REQ-YG-682`; and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: On one comparison witness host with opencode 1.18.31, the selected model's provider key, and a working Copilot entitlement, `JUDGE_BACKEND=opencode scripts/judge.sh <FR>` writes a non-empty opencode draft containing a `**Verdict:**` line; D-7 records target path/commit, backend, version, exact model argv, timestamps, artifact path/hash, verdict, and effective permission/config limitation.
- [ ] AC-12: The default Copilot run on the same host and target FR writes its own non-empty draft; both backend artifacts remain and have distinct hashes or explicitly recorded equality.
- [ ] AC-13: D-7 inventories every substantive claim from both drafts under stable `CP-n`/`OC-n` IDs with source locations, evidence citations, and `matched`, `contradicted`, or `backend-only` dispositions; convergence uses the literal `no backend-only or contradicted items` sentinel.
- [ ] AC-14: Before the opencode route becomes operational or the FR is marked Implemented, D-7 contains two separate dated approvals by humans other than the enforcer: acceptance of the enforcement-infrastructure diff/route invariants, and spend-owner acceptance of the FR-1048 provider-key payer boundary for judge execution.
- [ ] AC-15: D-8 includes a diary entry with a Seed; all REQ-YG-682 tests and existing judge-wrapper/model-pin tests pass; pytest and CI never launch a real judge.
- [ ] AC-16: If AC-11 does not produce the required artifact and verdict under the frozen default-permission contract, the FR is rejected with the log attached; enforcement does not add `--auto`, invent a permission flag, fall back to Copilot/Claude, substitute a model, or weaken the artifact contract.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Treat `deepseek/deepseek-v4-pro` as the frozen H-1 human spend decision. Any model change or fallback returns to planning; enforcement must not substitute one. | GATE |
| C-2 | Confirm FR-1048's implementation, committed probe, live witness, pinned 1.18.31 contract, and untriggered kill criterion before implementation. | GATE |
| C-3 | Make the governed graph edit only through the committed `scripts/author.sh` brief and preserve the local authoring report through its digest and quoted required sections in D-7. | GATE |
| C-4 | Keep the opencode node to the single `model` flag. No runtime/schema/result change and no tool, approval, `--auto`, agent, resume, permission, or shell surface is permitted. | GATE |
| C-5 | Preserve the sole route: one wrapper, one graph, one prompt, explicit mutually exclusive backend edges, closed-set validation before the lock, unchanged default, and unchanged round/artifact/re-entry contracts. | GATE |
| C-6 | Keep all automated tests offline. Real judge execution is limited to the two expressly recorded live witness runs. | GATE |
| C-7 | Apply the kill criterion literally if the opencode live run cannot write a valid verdict artifact under the frozen contract; do not rescue it by widening scope or silently falling back. | GATE |
| C-8 | Because this changes enforcement infrastructure and incurs provider spend, record both required human approvals before operationalization or Implemented status. | GATE |
| C-9 | Keep the judge prompt, doctrine, and judgement template unchanged, and preserve byte equality for the ramp SKILL mirror. | GATE |
| C-10 | Update the FR with implementation status, decisions, and deviations; complete REQ-YG-682 traceability, changelog, witness, and Distill artifacts before marking Implemented. | GATE |

Authority granted: after human review and promotion of this draft, implement only D-1 through D-8 as frozen above using `deepseek/deepseek-v4-pro`, and make the opencode judge route operational only after AC-01 through AC-16 and C-1 through C-10 are satisfied.
