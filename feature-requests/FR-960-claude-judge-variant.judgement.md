<!-- Folded 2026-09-02 from tmp/draft-judgement.md rendered by the sole-route judge (scripts/judge.sh, Copilot CLI, gpt-5.6-sol, session c03cb3ef-473f-40dd-b190-4586602bd06d, run 01a06327-89b5-7ecb-a80d-827963c65f61, log tmp/judge-fr960.log). Wrapper verified the artifact 2026-09-02 17:30Z; copied to tmp/draft-judgement-fr960.md in the same command to survive the fixed-name clobber (FR-960 §Problem 2). Body below verbatim. Judged in a session other than the author's. -->

# Judgement: FR-960 Claude judge variant — second backend in the sole-route judge adapter

**Verdict:** APPROVED WITH REVISIONS — the opt-in second judge is a coherent contrib/internal enforcement adoption, but authority activates only after FR-959 is Implemented and R-1 through R-6 are folded into the FR.

**Reviewed against:** `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.md`; `feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.judgement.md`; `feature-requests/FR-959-claude-cli-backend-primitive.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/SKILL.md`; `.github/skills/judge-fr/adapters/README.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/prompts/judge.yaml`; `scripts/judge.sh`; `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/adapters/README.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/development-process.md`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`; `capabilities/CAP-44-judge-split-verdict.yaml`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `feature-requests/FR-758.judgement.md`; `tests/unit/test_fr758_judge_review_wrappers.py`; repository searches for `REQ-YG-642`, FR-960 capability coverage, committed FR-960 authoring briefs, condition-expression precedent, and existing judge-wrapper tests. The local `tmp/judge-fr958.log`, `tmp/judge-fr955-957.log`, `tmp/.judge.lock/holder`, future FR-959 evidence, and future FR-960 witness were not consumed because they are not committed artifacts available to this judgement.

## What is sound

The problem is real and bounded. The current wrapper deletes one fixed artifact before every run (`scripts/judge.sh:9,41`), while the proposed backend-and-FR-derived name directly prevents the witnessed cross-FR and cross-backend clobber without weakening the existing lock or artifact verification contract (`FR-960:35-42,117-127`). Backend validation before lock acquisition is an appropriate fail-closed boundary (`FR-960:117-125,177-182`).

The graph change preserves one wrapper, one graph, one prompt, and state-conditioned routing rather than introducing a second execution route (`FR-960:56-113`). Conditional inequality/equality expressions are established YAMLGraph syntax, and both backend nodes point to the same `judge` prompt. Restricting the Claude node's availability and approval sets separately to `Read, Glob, Grep, Write`, with no Bash, MCP, Edit, or broad permission bypass, correctly folds FR-958 R-2 and C-3 (`FR-960:89-115,170-176`; `FR-958 judgement:49-58,177-179`).

The proposal is a single responsibility: opt-in adoption of the FR-959 backend by the sole-route judge, including the wrapper and evidence needed to operate that adoption. The generic runtime, payer preflight, other governance adapters, automated scoring, and additional backends remain excluded (`FR-960:229-241`). Strategically this is a **contrib/internal enforcement adoption**, not a framework primitive: it has one named operator workflow and consumes the backend abstraction defined by FR-959.

The research field is substantive. The in-body table carries six material alternatives, concrete precedent, preserved dissent, and an explicit `is_this_a_graph` disposition (`FR-960:211-227`). The live witness, kill criterion, four-tool argv assertion, unknown-backend shell case, unchanged-doctrine assertion, and artifact coexistence case are appropriate direct witnesses (`FR-960:166-208`).

## Required revisions

### R-1: Make FR-959 a hard precondition for all enforcement

Replace the current allowance that "offline criteria may proceed on a branch" (`FR-960:163-165`) with a gate that no FR-960 graph, prompt, wrapper, test, documentation, traceability, or witness implementation begins until FR-959 is Implemented on main, its committed auth probe and live witness exist, and its kill criterion has not fired. Until then, `backend: claude` and its flags are not an available repository contract; graph compilation or argv tests would fail because of the dependency rather than because FR-960 is RED. Update the status, dependency language, acceptance criteria, and authority statement consistently.

### R-2: Cite the committed graph-authoring brief

Add `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` as an explicit deliverable and cite it from FR-960 before authoring begins. The brief must name `.github/skills/judge-fr/adapters/graph.yaml` and `.github/skills/judge-fr/adapters/prompts/judge.yaml` as the artifact boundary, the existing judge adapter as precedent, the exact expected edits, lint command, narrow mocked smoke, and report contract. Graph-authoring doctrine requires an FR-bound brief to be committed and cited by its governing FR (`.github/skills/graph-authoring/doctrine.md:17-29`; `.github/skills/graph-authoring/SKILL.md:39-48`); FR-960 currently names only an unspecified task brief (`FR-960:69-72`).

### R-3: Name the artifact contract honestly

Replace every "per-run artifact" claim with **per-backend-per-FR artifact**, including the Summary, state comment, README plan, witness schema, REQ-YG-642, acceptance criteria, and Out of Scope (`FR-960:25-30,73-76,117-132,152-158,177-182,237-240`). The frozen filename `draft-judgement-<backend>-<fr-slug>.md` intentionally overwrites an earlier rerun of the same backend on the same FR (`FR-960:121-123,220-221`), so it is not per-run. Add a shell assertion that a same-backend/same-FR rerun removes and replaces only its own deterministic artifact while the other backend's artifact survives.

### R-4: Complete the ADR-001 traceability spine

Fold REQ-YG-642 into the existing `capabilities/CAP-211-sole-route-judge-review.yaml`, adding FR-960 to that capability's provenance and naming the judge graph, prompt, wrapper, wrapper tests, and graph-routing tests as requirement modules. Add the generated CAP-211/REQ-YG-642 entry to `ARCHITECTURE.md`; specify requirement-tagged tests; require `python scripts/req_coverage.py --strict`; add a `changelog/unreleased/` fragment carrying `req: REQ-YG-642`; and name the required FR-960 diary entry. FR-960 currently declares a provisional requirement but authorizes none of these traceability surfaces (`FR-960:150-159`), while CAP-211 already owns the sole-route wrapper and adapter contract (`capabilities/CAP-211-sole-route-judge-review.yaml:1-53`).

### R-5: Freeze routing and wrapper tests, not only static shape

Name the test surfaces and add direct path assertions. Extend `tests/unit/test_fr758_judge_review_wrappers.py` or create `tests/unit/test_fr960_claude_judge_variant.py`, marked `process`, with every new test tagged `@pytest.mark.req("REQ-YG-642")`. Stub `YAMLGRAPH_BIN` and assert exact argument vectors for unset, `copilot`, `claude`, and invalid `JUDGE_BACKEND`; assert invalid input exits 64 before creating the lock; assert exact artifact deletion/replacement and verdict verification; and require no real judge launch from pytest or CI. Add a graph test that compiles the adapter and proves `backend=copilot` visits only `judge`, `backend=claude` visits only `judge_claude`, and both carry the same prompt plus the requested artifact path. Merely counting two copilot nodes and linting (`FR-960:166-182`) does not prove that the selection path is correct.

### R-6: Define an auditable disagreement unit and human decisions

Replace "every finding" with a witness protocol that inventories each draft's verdict and every substantive claim in `What is sound`, each R-* revision, and each C-* condition under stable witness-local IDs. For every inventoried item, record `matched`, `contradicted`, or `backend-only`, cite the source draft section and its file:line evidence, and include an explicit `no backend-only or contradicted items` sentinel when there are no disagreement rows. Revise the Ideal Result so convergence is valid evidence rather than contradicting its assertion that the drafts must disagree (`FR-960:60-65,143-145,206-208`).

The witness must carry two separate signed decisions by a human other than the enforcer: (1) the enforcement-infrastructure diff and route invariants are accepted, and (2) the repository spend owner accepts use of FR-959's residual Claude subscription payer boundary for judge execution. Each signature records name and date and must exist before the Claude route is treated as operational or FR-960 becomes Implemented. This makes the semantic completeness and spend decisions explicit rather than absorbing them into one combined signature (`FR-960:187-190`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-960-claude-judge-variant.md`, folded with R-1 through R-6 |
| D-2 | `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` |
| D-3 | `.github/skills/judge-fr/adapters/graph.yaml` and `.github/skills/judge-fr/adapters/prompts/judge.yaml`, authored only through `scripts/author.sh` |
| D-4 | `scripts/judge.sh` |
| D-5 | `.github/skills/judge-fr/adapters/README.md` and `.github/skills/judge-fr/SKILL.md` |
| D-6 | `tests/unit/test_fr758_judge_review_wrappers.py` and/or `tests/unit/test_fr960_claude_judge_variant.py` |
| D-7 | `capabilities/CAP-211-sole-route-judge-review.yaml` and generated `ARCHITECTURE.md` traceability for REQ-YG-642 |
| D-8 | `feature-requests/evidence/FR-960-claude-judge-witness.md` |
| D-9 | `changelog/unreleased/<fr-960-slug>.md` and one FR-960 entry under `docs/diary/` |

Not authorized: any FR-959 runtime, schema, linter, authentication, settings, or payer implementation; changes to judge doctrine or the judgement template; a second graph or wrapper route; changes to the default backend or `gpt-5.6-sol` pin; Claude access to Bash, Edit, MCP, unrestricted tools, or a permission bypass; a third backend; review/author/research adapter migration; automated disagreement scoring or comparison graphs; usage-limit waiting/rerouting; API-key, cloud-provider, or Copilot payer fallback; CI judge execution; auto-folding, committing, commenting, opening/updating PRs, polling, merging, or any other expansion of the advisory output boundary.

## Revised acceptance criteria

- [ ] AC-01: FR-959 is Implemented on main, its committed auth probe and live witness exist, and its kill criterion has not fired before any D-2 through D-9 enforcement begins.
- [ ] AC-02: `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` is committed, cited by FR-960, and names the artifact boundary, precedent, expected edits, lint, narrow smoke, and report contract required by R-2.
- [ ] AC-03: `scripts/author.sh feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` produces a non-empty local `tmp/draft-authoring-report.md` with the required headings; the persistent witness records its digest, quoted required sections, lint and smoke commands/results, graph commit SHA, and limitations without claiming the report is committed.
- [ ] AC-04: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml` reports 0 errors; a REQ-YG-642 test proves `copilot` selects only `judge`, `claude` selects only `judge_claude`, and both receive the same `judge` prompt and requested artifact path.
- [ ] AC-05: The unchanged Copilot node retains `backend: cli`, `model: gpt-5.6-sol`, `allow_all_paths: true`, and `allow_all_tools: true`; only its `artifact_path` variable and routing edge differ from the committed pre-FR-960 graph.
- [ ] AC-06: The Claude node's captured exact argv contains the FR-959-supported availability restriction and narrow approval for exactly `Read,Glob,Grep,Write`, contains `--max-turns 40`, and contains no `--dangerously-skip-permissions`, `Bash`, `Edit`, or `mcp__` name.
- [ ] AC-07: Stubbed wrapper tests prove unset and `copilot` select the Copilot branch, `claude` selects the Claude branch, any other value exits 64 before lock creation, and the exact `--var backend=...` and `--var artifact_path=...` arguments are passed.
- [ ] AC-08: Wrapper tests prove the deterministic path is `tmp/draft-judgement-<backend>-<fr-slug>.md`; a run removes/replaces only that path; the other backend and other-FR artifacts survive; and a same-backend/same-FR rerun intentionally replaces its earlier artifact.
- [ ] AC-09: The prompt contains `{{ artifact_path }}` and no literal `tmp/draft-judgement.md`; `.github/skills/judge-fr/doctrine.md` and `.github/skills/judge-fr/judgement.template.md` are unchanged.
- [ ] AC-10: README and SKILL documentation state that two backend nodes remain one sole route, document backend validation and the per-backend-per-FR overwrite contract, list the Claude node's four-tool boundary and no-bypass rule, and link rather than duplicate FR-959's residual payer boundary.
- [ ] AC-11: CAP-211 contains REQ-YG-642 and FR-960 provenance; `ARCHITECTURE.md` contains the generated requirement; every new test is tagged `@pytest.mark.req("REQ-YG-642")`; the FR-960 changelog fragment carries `req: REQ-YG-642`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: On one committed target FR and one host, the Claude run with subscription login and no `ANTHROPIC_API_KEY` writes its backend-and-FR artifact with a verdict line; the witness records target FR path and commit SHA, backend, CLI version, auth mode, start/end timestamps, artifact path/hash, and verdict.
- [ ] AC-13: On the same host, exporting `ANTHROPIC_API_KEY=sk-invalid-on-purpose` does not change AC-12's successful subscription-authenticated result; if it does, FR-959's kill criterion fires and FR-960 receives no operational authority.
- [ ] AC-14: A default-backend run against the same target FR writes the Copilot artifact, and both backend artifacts exist with distinct hashes or an explicit recorded equality.
- [ ] AC-15: The witness inventories both drafts under R-6's protocol; every item has a source location, evidence citation, and `matched`, `contradicted`, or `backend-only` disposition; convergence uses the explicit sentinel instead of an empty-table success claim.
- [ ] AC-16: A human other than the enforcer signs separate dated acceptance lines for the enforcement-infrastructure diff/route invariants and for the residual Claude subscription payer boundary before the Claude route is operational or FR-960 is marked Implemented.
- [ ] AC-17: The required FR-960 diary entry exists and records a Seed; all targeted REQ-YG-642 tests and existing judge-wrapper/model-pin tests pass without launching a real judge from pytest or CI.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-960 before implementation authority activates. | GATE |
| C-2 | FR-959 must be Implemented on main with its committed auth evidence and an untriggered kill criterion before FR-960 enforcement begins. | GATE |
| C-3 | Author the graph and prompt only through the committed FR-960 brief and `scripts/author.sh`; retain the local report as advisory evidence and persist its digest/quoted proof in the witness. | GATE |
| C-4 | Preserve one wrapper, one graph, one prompt, the default Copilot backend/model, the OS lock, recursion sentinel, and artifact-not-exit-code contract. | GATE |
| C-5 | The Claude judge may have only the four reviewed tools with separate availability restriction and approval; no Bash, Edit, MCP, broad bypass, or payer fallback is permitted. | GATE |
| C-6 | Real Claude/Copilot judge runs are manual witness steps only; pytest and CI must use stubs/mocks and must never launch the judge graph. | GATE |
| C-7 | A human other than the enforcer must approve the enforcement-infrastructure diff and route invariants before operational use. | GATE |
| C-8 | The repository spend owner must explicitly accept FR-959's residual Claude subscription payer boundary for judge execution; absent that decision, the Claude route remains disabled. | GATE |
| C-9 | Preserve the advisory boundary: neither backend may auto-fold, commit, comment, open/update PRs, poll, run CI, or merge. | GATE |
| C-10 | If the subscription-authenticated live run fails or a different payer rescues it, the kill criterion fires and FR-960 is not Implemented. | GATE |

Authority granted: after R-1 through R-6 are folded and C-2 is satisfied, enforcement may add the opt-in Claude node inside the existing sole-route judge graph, deterministic per-backend-per-FR artifacts, bounded wrapper selection, traceability/tests/docs, and the committed dual-run witness described above; operational Claude use remains gated by C-7 and C-8.
