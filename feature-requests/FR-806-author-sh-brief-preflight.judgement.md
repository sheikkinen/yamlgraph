# Judgement: FR-806 author.sh Brief Pre-Flight: Premise and Budget Checks

**Prior art:** FR-806-author-sh-brief-preflight.md is the judged FR itself (verdict target, not precedent). FR-801-provider-readiness-preflight checks provider/environment readiness at run time — a different boundary (execution environment) from this FR's brief-content pre-flight at the authoring-route entry; no overlap in surface or mechanism, both may coexist.

**Verdict:** APPROVED WITH REVISIONS - the entry-boundary pre-flight is justified, but authority activates only after the budget trigger, premise extraction boundary, command-safety contract, and traceability artifact are folded into the FR.

**Reviewed against:** `feature-requests/FR-806-author-sh-brief-preflight.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md`; `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; `feature-requests/FR-790-api-discovery-schema-extract-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `feature-requests/FR-792-multi-step-investigation-template.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`.

## What is sound

The problem is real and evidenced. FR-789 records a full authoring run that died at the report gate because the brief's `python3 -m http.server` premise could not serve `/api/*` fixture routes (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:100-108`). FR-791 records a separate full authoring run that authored artifacts and passed lint but hit the copilot CLI hard 900s timeout during live full-pipeline smokes, again with report-gate rejection (`feature-requests/FR-791-api-discovery-orchestrator.md:122-128`). The FR-791 diary generalizes the same failure class as "briefs now carry BUDGETS as well as premises" and asks for `author.sh` pre-flight checks before burning a 15-minute run (`docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md:20-31`, `docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md:48-54`).

The proposed location is architecturally aligned. Repo doctrine already defines `scripts/author.sh <task-brief.md>` as the sole graph-authoring route and the sentinel/report artifact as the mechanical proof boundary (`.github/copilot-instructions.md:15`, `feature-requests/FR-767-graph-authoring-sole-route.md:77-82`). Checking the brief before spawning that route is an entry-boundary normalization, matching `the_one_law` (`.github/copilot-instructions.md:50-52`) and `two_strike_split` (`.github/copilot-instructions.md:115-116`). Strategic classification: framework tooling primitive for the authoring route, not pattern documentation, because the same route-level failure class has at least three cited events and manual diligence already failed once per session (`feature-requests/FR-806-author-sh-brief-preflight.md:32-40`, `docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md:48-54`).

The scope is mostly minimal: deterministic path/command existence checks and an advisory budget warning, with no LLM in the pre-flight (`feature-requests/FR-806-author-sh-brief-preflight.md:64-83`). The planned shell-level proof that a doomed brief exits before the backend spawns is the right acceptance shape (`feature-requests/FR-806-author-sh-brief-preflight.md:80-83`).

## Required revisions

### R-1: Align the budget warning with the FR-791 incident

Revise the budget heuristic and AC-02 so the reproduced FR-791 class warns for two live full-pipeline smokes, not only for `3+` live graph runs. The current FR says to warn above a default threshold of 2 and AC-02 requires `3+` live `graph run` smokes (`feature-requests/FR-806-author-sh-brief-preflight.md:71-74`, `feature-requests/FR-806-author-sh-brief-preflight.md:88`), but the cited failure was two full-pipeline live smokes plus authoring hitting the 900s ceiling (`feature-requests/FR-791-api-discovery-orchestrator.md:122-128`; `docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md:20-31`). Fold in a mechanically testable distinction: two or more live full-pipeline smokes warn; three or more narrower live graph-run smokes may also warn if retained.

### R-2: Narrow premise-path failures to asserted existing inputs

Revise premise extraction and AC-01 so pre-flight fails only for workspace paths that the brief asserts as existing inputs, fixtures, fixture servers, or validation prerequisites. Do not fail merely because a brief names an output path or governed graph/prompt artifact that the authoring run is supposed to create. The current AC says any brief referencing a nonexistent workspace path exits 64 (`feature-requests/FR-806-author-sh-brief-preflight.md:87`), while the route's normal purpose is to create governed graph artifacts through `scripts/author.sh` under the sentinel (`.github/copilot-instructions.md:15`, `feature-requests/FR-767-graph-authoring-sole-route.md:77-82`). Add a negative acceptance witness: a clean brief naming a not-yet-created output graph/prompt path passes pre-flight when that path is not an asserted prerequisite.

### R-3: Specify command parsing as static inspection, never execution

Revise the command-premise contract so pre-flight statically identifies the executable for validation-section commands without executing any brief-controlled command text. The FR currently says to scan fenced/inline commands and run `command -v` on the first token, with venv-aware handling for `yamlgraph` (`feature-requests/FR-806-author-sh-brief-preflight.md:68-70`), but "first token" is underspecified for environment assignments, `python -m ...`, relative scripts, and quoted commands. Fold in tests proving: missing executable exits 64 before backend spawn; valid `python -m` and `./relative-script` forms resolve; shell substitutions or command bodies are not executed during pre-flight. This keeps instruction/brief text treated as untrusted external input (`.github/copilot-instructions.md:63`) and avoids silent success-shaped fallbacks (`.github/copilot-instructions.md:218`).

### R-4: Add the traceability capability and exact doc surface

Add the concrete capability/requirement artifact this tooling change will satisfy, then bind tests to that `REQ-YG-XXX`. The FR requires req markers (`feature-requests/FR-806-author-sh-brief-preflight.md:91`) but does not name the CAP/REQ artifact required by ADR-001 for new capabilities (`.github/copilot-instructions.md:173-176`). Also replace the broad docs criterion with the exact graph-authoring doc files that will be edited so enforcement cannot sprawl across unrelated doctrine (`feature-requests/FR-806-author-sh-brief-preflight.md:92`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/author.sh` pre-flight invocation, `--no-preflight` handling, exit-64 path, and preservation of existing sentinel/report-gate behavior |
| D-2 | A small pre-flight helper under `scripts/` if needed for testable extraction/checking logic |
| D-3 | Unit tests and one shell-level route test proving extractor/checker behavior and backend-not-spawned failure |
| D-4 | One new or updated `capabilities/CAP-XXX-*.yaml` requirement artifact for this authoring-route pre-flight |
| D-5 | Exact `.github/skills/graph-authoring/` brief-writing documentation named in the revised FR |
| D-6 | FR-806 updates folding in this judgement and recording implementation status/decisions |

Not authorized: LLM-based brief review; execution of validation commands during pre-flight; hard failure on budget warnings by default; changes to sentinel arming or report-gate verification beyond preserving them; changes to judge/review routes; auto-commit, PR creation/update, merge, CI-running, inbox polling, or worktree management; governed graph/prompt artifact authoring under this FR; a broad natural-language parser for every possible prose premise.

## Revised acceptance criteria

- [ ] AC-01: A brief with a validation prerequisite path asserted as an existing input/fixture/server, where that path is absent, exits 64 before the copilot CLI/backend is spawned and quotes the violated line.
- [ ] AC-02: A brief naming a not-yet-created output graph/prompt path, without asserting it as an existing prerequisite, passes pre-flight.
- [ ] AC-03: A validation-section command whose executable cannot be resolved exits 64 before backend spawn and quotes the violated line.
- [ ] AC-04: Command checking is static: tests prove pre-flight resolves valid executable forms including `python -m ...` and `./relative-script`, and does not execute shell substitutions or command bodies from the brief.
- [ ] AC-05: A brief reproducing the FR-791 class with two live full-pipeline `yamlgraph graph run` smokes prints a 900s-ceiling warning and still proceeds.
- [ ] AC-06: A clean brief passes pre-flight with all mechanically checked premises marked pass and no behavior change to sentinel arming, report-gate verification, or existing route exit semantics.
- [ ] AC-07: `--no-preflight` skips only the pre-flight; report-gate verification remains mandatory.
- [ ] AC-08: Pre-flight logic is unit-tested with `@pytest.mark.req("<new REQ-YG-XXX>")`; the new/updated CAP file supplies that requirement; no LLM call exists in the pre-flight path.
- [ ] AC-09: `.github/skills/graph-authoring/` documentation named in the revised FR teaches the checked premise forms, the budget warning trigger, and the `--no-preflight` boundary.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review is mandatory before merge because this changes authoring-route enforcement infrastructure and agent-facing doctrine; enforcement-infrastructure changes are adversarial input under judge doctrine (`.github/skills/judge-fr/doctrine.md:96-103`, `feature-requests/FR-767-graph-authoring-sole-route.judgement.md:81-90`). | GATE |
| C-2 | The sentinel and report gate remain mandatory. `--no-preflight` must not bypass sentinel arming, governed-artifact write protections, or `tmp/draft-authoring-report.md` verification. | GATE |
| C-3 | Pre-flight may inspect command text and resolve executables; it must not execute validation commands from the brief. | GATE |
| C-4 | Failures must be limited to mechanically violated premises. Ambiguous prose should produce no failure unless the revised FR defines a deterministic extraction rule for it. | GATE |
| C-5 | Budget findings remain advisory warnings by default. Do not add a hard budget-fail mode, backend timeout override, or validation-resume automation under this FR. | GATE |
| C-6 | Scope stays at launch-time pre-flight for `scripts/author.sh`; do not generalize into a reusable natural-language premise engine or alter graph-authoring artifacts themselves. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-806, the enforcer may implement the deterministic `scripts/author.sh` brief pre-flight, its tests, its requirement traceability artifact, and the named graph-authoring brief documentation within the frozen surfaces above.
