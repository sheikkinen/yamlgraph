# Judgement: FR-765 Graph Authoring Workflow Skill

**Verdict:** APPROVED WITH REVISIONS — the workflow-skill direction is sound as pattern documentation, but authority activates only after the FR makes the CAP-158 extension explicit, upgrades tests from presence checks to substance checks, and removes ambiguity between artifact-closed delegation and the judge/review routes.

**Prior art:** The gate's sole hit is `FR-765-graph-authoring-workflow-skill.md` itself (nouns *authoring/workflow/skill*) — self-referential, this judgement's own subject, not independent prior art. The substantive prior art is dispositioned in the FR and reviewed against below: FR-446 (CAP-158 skill promotion, which this FR extends rather than duplicates), the `author-graph`/`author-prompt` syntax-reference skills (distinct responsibility: syntax reference vs. end-to-end workflow), and the retired `examples/yamlgraph_gen` generator (the failed one-shot abstraction this FR replaces with workflow discipline). No prior FR, approved or rejected, has proposed a graph-authoring workflow skill.

**Reviewed against:** `feature-requests/FR-765-graph-authoring-workflow-skill.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-446-copilot-skill-promotion.md`; `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md`; `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.judgement.md`; `docs/diary/diary-2026-07-27-taxonomy-git-tracked-boundary.md`; `capabilities/CAP-158-copilot-skill-promotion.yaml`; `ARCHITECTURE.md`; `tests/unit/test_fr446_copilot_skills.py`; `.github/skills/author-graph/SKILL.md`; `.github/skills/author-prompt/SKILL.md`; `.github/skills/feature-request/SKILL.md`; `examples/yamlgraph_gen/README.md`; `examples/yamlgraph_gen/graph.yaml`; `examples/yamlgraph_gen/prompts/assemble_graph.yaml`; `examples/yamlgraph_gen/docs/linter-reflection.md`; `examples/yamlgraph_gen/run_generator.py`; `.gitignore`; git-tracked file listing for `examples/yamlgraph_gen/`.

## What is sound

The problem is real and correctly scoped to workflow discipline rather than a runtime primitive. The existing generator advertises natural-language graph generation, prompt generation, validation, linting, and optional execution in one surface (`examples/yamlgraph_gen/README.md:1-10`, `examples/yamlgraph_gen/README.md:48-83`). Its graph actually spans classification, interrupt clarification, snippet loading, multiple LLM generation nodes, file writing, validation, linting, and an LLM report (`examples/yamlgraph_gen/graph.yaml:63-200`). That supports FR-765's claim that the failed abstraction is a one-shot generation model, not graph authoring as a capability (`feature-requests/FR-765-graph-authoring-workflow-skill.md:31-45`).

The proposed new skill has a distinct responsibility. `author-graph` is a graph YAML syntax reference (`.github/skills/author-graph/SKILL.md:7-10`), and `author-prompt` is a prompt YAML syntax reference (`.github/skills/author-prompt/SKILL.md:7-10`). FR-446 deliberately split those two concerns because graph authoring and prompt authoring have distinct triggers (`feature-requests/FR-446-copilot-skill-promotion.md:13-20`). FR-765's proposed table makes the third concern explicit: end-to-end graph creation workflow, not syntax reference duplication (`feature-requests/FR-765-graph-authoring-workflow-skill.md:76-83`).

The boundary evidence is credible and aligned with repo doctrine. FR-763 documents ignored `examples/yamlgraph_gen/outputs/*` directories becoming phantom example roots on dirty machines while clean CI stayed green (`feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:16-23`, `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md:28-35`), and the diary records the same `workspace_is_not_boundary` failure as 86 phantom insertions from ignored generator outputs (`docs/diary/diary-2026-07-27-taxonomy-git-tracked-boundary.md:13-20`). Repo doctrine names that trap directly (`.github/copilot-instructions.md:84-86`). A skill that steers repeated graph creation away from unvalidated, locally polluted generated outputs is therefore strategically justified.

The implementation approach is feasible with existing repo surfaces. Skills already use frontmatter with `name`, `description`, and `argument-hint` (`.github/skills/feature-request/SKILL.md:1-5`), CAP-158 already governs skill promotion (`capabilities/CAP-158-copilot-skill-promotion.yaml:1-5`), and the current FR-446 tests already provide the promotion-test surface to extend (`tests/unit/test_fr446_copilot_skills.py:9-36`). FR-765 also keeps the right non-goals: no `examples/yamlgraph_gen` revival, no mobile/web trigger, no judge/review doctrine changes, no new graph-generation primitive, and no remote auto-run surface (`feature-requests/FR-765-graph-authoring-workflow-skill.md:127-133`).

Strategic classification: **Pattern documentation / workflow skill extension**, not a framework primitive. The existing graph, prompt, lint, and skill abstractions are sufficient; this FR should package the authoring procedure and validation contract around them.

## Required revisions

### R-1: Make CAP-158 extension unconditional

Replace AC-07's conditional wording with a binding requirement: this FR extends CAP-158 / REQ-YG-423 with `graph-authoring`. CAP-158 currently names exactly six Tier 1 skills and lists only their six modules (`capabilities/CAP-158-copilot-skill-promotion.yaml:15-30`), and the generated architecture text repeats the same six-skill contract (`ARCHITECTURE.md:2044-2052`). The promotion test also hard-codes the same six-skill list (`tests/unit/test_fr446_copilot_skills.py:11-18`). Leaving this conditional would let the new skill exist outside the registry and make requirement coverage dishonest.

Fold into the FR: update `capabilities/CAP-158-copilot-skill-promotion.yaml`, regenerate the CAP-158 section of `ARCHITECTURE.md` through the existing capability aggregation workflow, and update `tests/unit/test_fr446_copilot_skills.py` to include `graph-authoring` under `@pytest.mark.req("REQ-YG-423")`.

### R-2: Upgrade tests from presence to substance

AC-06 currently requires only existence and non-empty files (`feature-requests/FR-765-graph-authoring-workflow-skill.md:153-156`), matching the weak current test shape of "file exists" plus `len(content) > 100` (`tests/unit/test_fr446_copilot_skills.py:25-36`). Repo doctrine explicitly identifies this as `gate_checks_shape_not_substance` and prescribes `substance_over_presence` (`.github/copilot-instructions.md:86-108`).

Fold into the FR: the promotion tests must parse `SKILL.md` frontmatter and assert `name: graph-authoring`, a non-empty `description` containing a "Use when:" trigger, and a non-empty `argument-hint`; assert `SKILL.md` references `author-graph`, `author-prompt`, and `doctrine.md`; and assert `doctrine.md` contains the required workflow contract headings: input closure, precedent search, artifact report, local validation, escalation rules, and anti-patterns.

### R-3: Disambiguate delegation from judge/review execution routes

The proposed workflow says substantial work should use a "judge-fr-style delegation contract" (`feature-requests/FR-765-graph-authoring-workflow-skill.md:95-98`). That is directionally sound as input-closure discipline, but the phrase is unsafe because judge doctrine treats route identity as a hard boundary: a judge execution must not launch another judge, adapter, graph, or command that invokes judgement (`.github/skills/judge-fr/doctrine.md:26-32`). FR-765 already says the new skill must not modify or weaken canonical judge/review routes (`feature-requests/FR-765-graph-authoring-workflow-skill.md:108-113`, `feature-requests/FR-765-graph-authoring-workflow-skill.md:129-132`).

Fold into the FR: replace "judge-fr-style delegation" with "artifact-closed delegation brief" and require the skill to state that graph-authoring delegation is not FR judgement, must not invoke `judge-fr`, `review-pr`, their adapters, or any judgement/review graph, and may escalate to Chaplain only by submitting a proposal and stopping direct edits for that concern.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/graph-authoring/SKILL.md`: short discoverable wrapper with valid skill frontmatter, trigger guidance, composition references, and pointer to local doctrine. |
| D-2 | `.github/skills/graph-authoring/doctrine.md`: stable workflow contract covering input closure, precedent search, artifact boundary/report, local validation, escalation, and anti-patterns. |
| D-3 | `tests/unit/test_fr446_copilot_skills.py`: CAP-158 promotion tests extended to `graph-authoring` with frontmatter and substance assertions. |
| D-4 | `capabilities/CAP-158-copilot-skill-promotion.yaml`: REQ-YG-423 updated from six skills to include `graph-authoring`. |
| D-5 | `ARCHITECTURE.md`: regenerated CAP-158 capability text only. |
| D-6 | `feature-requests/FR-765-graph-authoring-workflow-skill.md`: revised per R-1 through R-3 and updated with implementation status/decisions after enforcement. |
| D-7 | `changelog/unreleased/`: one changelog fragment for the skill addition. |
| D-8 | `docs/diary/`: one metacognitive reflection entry for the enforcement if submitted as a feat/fix FR PR. |

Not authorized: changes to `examples/yamlgraph_gen/`, generated output directories, mobile/web trigger channels, `judge-fr` doctrine, `review-pr` doctrine, judge/review adapters, hooks, CI workflows, branch protection, a new graph-generation runtime primitive, remote create-and-run behavior, or broad changes to existing `author-graph` / `author-prompt` syntax content.

## Revised acceptance criteria

- [ ] AC-01: `.github/skills/graph-authoring/SKILL.md` exists with valid YAML frontmatter: `name: graph-authoring`, a non-empty `description` containing "Use when:", and a non-empty `argument-hint`.
- [ ] AC-02: `.github/skills/graph-authoring/doctrine.md` exists and defines the graph-authoring workflow contract: input closure, precedent search, artifact boundary/report, local validation, escalation rules, and anti-patterns.
- [ ] AC-03: `SKILL.md` explicitly composes with `author-graph` and `author-prompt` as syntax/reference skills and does not duplicate their graph-node or prompt-schema reference material beyond brief trigger guidance.
- [ ] AC-04: The skill or doctrine explicitly rejects the one-shot `examples/yamlgraph_gen` path as the default for repeated graph authoring and cites the `workspace_is_not_boundary` / FR-763 precedent.
- [ ] AC-05: The workflow requires `yamlgraph graph lint <graph.yaml>` and the narrowest meaningful smoke/demo command when credentials and dependencies permit; blocked validation must record the exact blocked command and reason, not claim success.
- [ ] AC-06: The workflow uses "artifact-closed delegation brief" language and explicitly states it is not FR judgement/review and must not invoke `judge-fr`, `review-pr`, their adapters, or any judgement/review graph.
- [ ] AC-07: `tests/unit/test_fr446_copilot_skills.py` includes `graph-authoring` under `@pytest.mark.req("REQ-YG-423")` and asserts frontmatter validity, non-empty substantive content, required doctrine headings, and composition references to `author-graph` and `author-prompt`.
- [ ] AC-08: `capabilities/CAP-158-copilot-skill-promotion.yaml` updates REQ-YG-423 to include `graph-authoring`, and `ARCHITECTURE.md` is regenerated so the CAP-158 text and module list match the capability file.
- [ ] AC-09: A changelog fragment exists in `changelog/unreleased/` with a valid requirement reference to REQ-YG-423.
- [ ] AC-10: The FR is updated with implementation status, decisions, and any deviations from this judgement after enforcement.
- [ ] AC-11: A diary reflection is added if the resulting PR type triggers the repo diary gate.
- [ ] AC-12: No changes are made to `examples/yamlgraph_gen/`, generated output directories, mobile/web trigger channels, judge/review doctrine or adapters, hooks, CI workflows, branch protection, or graph-generation runtime primitives under this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Treat this as a pattern-documentation/workflow-skill change. Do not implement a new YAMLGraph runtime primitive, generator framework, mobile/web trigger, or remote create-and-run path. | GATE |
| C-2 | Do not modify `judge-fr`, `review-pr`, their doctrines, adapters, or execution routes. Any enforcement-infrastructure change requires separate human-reviewed authority. | GATE |
| C-3 | Keep CAP-158, ARCHITECTURE, and the skill promotion tests synchronized in the same change; a new skill without registry and requirement coverage is not complete. | GATE |
| C-4 | Tests must check substance, not just presence. A non-empty `SKILL.md` or `doctrine.md` alone does not satisfy AC-07. | GATE |
| C-5 | Validation claims in the skill's report contract must be command-backed or explicitly blocked with the exact command and reason. No success-shaped fallback for unavailable credentials or dependencies. | GATE |
| C-6 | Do not commit or rely on ignored/generated `examples/yamlgraph_gen/outputs/*` artifacts. Precedent search and examples must use committed repository artifacts. | GATE |
| C-7 | Graph-authoring delegation may use a closed artifact brief for a worker, but it must not use verdict vocabulary, judge/review skills, judge/review adapters, or judgement/review graphs. | GATE |

Authority granted: after R-1 through R-3 are folded into the FR, the enforcer may add the `graph-authoring` skill package, update CAP-158/REQ-YG-423 and its generated architecture text, extend the promotion tests, add the changelog and required reflection, and update FR-765 within the frozen surfaces above.

---

# Round 2 Judgement (2026-07-29): Executable Adapter Amendment

# Judgement: FR-765 Graph Authoring Workflow Skill

**Verdict:** APPROVED WITH REVISIONS — the executable adapter direction is sound, but authority activates only after the FR narrows the re-entry guard so validation commands remain legal, defines the operator/report contract mechanically, and synchronizes tests plus CAP-158 with the new adapter surface.

**Reviewed against:** `feature-requests/FR-765-graph-authoring-workflow-skill.md`; `feature-requests/FR-765-graph-authoring-workflow-skill.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/author-graph/SKILL.md`; `.github/skills/author-prompt/SKILL.md`; `.github/skills/judge-fr/adapters/README.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/prompts/judge.yaml`; `scripts/judge.sh`; `reference/graph-yaml.md`; `capabilities/CAP-158-copilot-skill-promotion.yaml`; `ARCHITECTURE.md`; `tests/unit/test_fr446_copilot_skills.py`; `feature-requests/FR-446-copilot-skill-promotion.md`; `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.md`; `feature-requests/FR-763-taxonomy-scan-git-tracked-boundary.judgement.md`; `docs/diary/diary-2026-07-27-taxonomy-git-tracked-boundary.md`; `examples/yamlgraph_gen/README.md`; `examples/yamlgraph_gen/graph.yaml`; `examples/yamlgraph_gen/docs/linter-reflection.md`; `examples/yamlgraph_gen/run_generator.py`; `.gitignore`.

## What is sound

The amendment correctly identifies the missing part of round 1: the delivered `graph-authoring` skill is currently a discovery wrapper plus doctrine (`.github/skills/graph-authoring/SKILL.md:7-19`, `.github/skills/graph-authoring/doctrine.md:1-7`), while the ideal result asks for an executable route analogous to `scripts/judge.sh` launching a thin adapter graph (`feature-requests/FR-765-graph-authoring-workflow-skill.md:56-66`). That is a real gap, not a new runtime primitive.

The proposed adapter shape fits existing YAMLGraph capability. Copilot nodes support `backend: cli`, `cli_flags`, `allow_all_paths`, `allow_all_tools`, model override, and timeout (`reference/graph-yaml.md:465-512`), and the judge adapter already demonstrates the exact thin graph shape: a single `type: copilot` node with `backend: cli`, both load-bearing flags, a prompt pointer, and timeout (`.github/skills/judge-fr/adapters/graph.yaml:18-32`). The judge prompt is also a valid precedent for a zero-duplication pointer prompt with a re-entry guard (`.github/skills/judge-fr/adapters/prompts/judge.yaml:1-18`).

The operator-wrapper precedent is concrete. `scripts/judge.sh` validates its argument, blocks recursive judge invocation with a lineage sentinel, launches the adapter graph, and treats `tmp/draft-judgement.md` as the proof artifact rather than trusting the graph exit code (`scripts/judge.sh:16-22`, `scripts/judge.sh:54-60`). The adjacent adapter README makes the operational rules explicit: use the wrapper, keep output advisory, require `allow_all_paths` and `allow_all_tools`, and verify by artifact existence instead of exit code (`.github/skills/judge-fr/adapters/README.md:5-30`).

Round 1 remains strategically sound. `author-graph` and `author-prompt` are syntax-reference skills (`.github/skills/author-graph/SKILL.md:7-10`, `.github/skills/author-prompt/SKILL.md:7-10`), while `graph-authoring` is the process contract around complete graph creation (`.github/skills/graph-authoring/SKILL.md:21-28`). The stale `examples/yamlgraph_gen` surface really is a one-shot generator spanning classification, clarification, snippet selection, graph assembly, prompt/tool generation, file writes, validation, linting, and reporting (`examples/yamlgraph_gen/README.md:48-83`, `examples/yamlgraph_gen/graph.yaml:63-200`), and the FR-763 diary documents why ignored generated outputs are unsafe discovery inputs (`docs/diary/diary-2026-07-27-taxonomy-git-tracked-boundary.md:13-20`).

Strategic classification: **workflow-skill execution route**, not framework primitive. Existing YAMLGraph copilot nodes, prompts, shell wrappers, skill files, and requirement registry surfaces are sufficient; the FR should add a thin authoring adapter and operator contract around them.

## Required revisions

### R-1: Narrow the authoring re-entry guard so validation remains legal

Replace the broad "must never re-invoke the skill/adapter/yamlgraph" wording in AC-14 (`feature-requests/FR-765-graph-authoring-workflow-skill.md:219-223`) and the proposed-solution guard (`feature-requests/FR-765-graph-authoring-workflow-skill.md:90-92`) with a precise recursion ban: the launched authoring agent must not invoke the `graph-authoring` skill, `scripts/author.sh`, `.github/skills/graph-authoring/adapters/graph.yaml`, or any command that launches that adapter route again.

Do not ban ordinary YAMLGraph validation. The FR and existing doctrine both require `yamlgraph graph lint <graph.yaml>` plus the narrowest meaningful smoke command (`feature-requests/FR-765-graph-authoring-workflow-skill.md:130-132`, `.github/skills/graph-authoring/doctrine.md:50-63`), and repo quickstart doctrine names those same validation commands for graph development (`.github/copilot-instructions.md:7-13`). A guard that forbids all `yamlgraph` commands contradicts the core acceptance criteria.

### R-2: Define the operator input and artifact-report contract mechanically

Fold a closed invocation contract into the FR: `scripts/author.sh <task-brief.md>` is the sole operator command; the wrapper validates that the task brief exists; the adapter graph state includes `task_path: str`; the pointer prompt instructs the launched agent to read that task brief plus committed repo artifacts and explicit user-provided files only. Any target directory or desired artifact name must be stated inside the task brief, not inferred from hidden chat narrative.

Define `tmp/draft-authoring-report.md` as a parseable artifact contract, not just prose. It must contain these required headings: `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`. Under `Artifacts`, it must list at least one repo-relative authored or modified path. `scripts/author.sh` must fail unless the report is non-empty and at least one listed artifact path exists; it must never treat the adapter graph's exit code as proof of success. This mirrors the judge wrapper's artifact proof (`scripts/judge.sh:58-60`) while adapting it to authoring's multi-file output.

### R-3: Synchronize CAP-158 and generated architecture with the executable route

Round 1 updated CAP-158 and `ARCHITECTURE.md` to describe seven Tier 1 skills and the graph-authoring doctrine (`capabilities/CAP-158-copilot-skill-promotion.yaml:16-35`, `ARCHITECTURE.md:2044-2052`). The amendment changes the governed surface from documentation-only skill to executable skill route, but AC-13 through AC-18 do not require the capability registry or generated architecture text to reflect that new route (`feature-requests/FR-765-graph-authoring-workflow-skill.md:213-236`).

Fold a binding criterion requiring CAP-158 / REQ-YG-423 and regenerated `ARCHITECTURE.md` to name the executable graph-authoring adapter route and its key modules: `.github/skills/graph-authoring/SKILL.md`, `.github/skills/graph-authoring/doctrine.md`, `.github/skills/graph-authoring/adapters/README.md`, `.github/skills/graph-authoring/adapters/graph.yaml`, `.github/skills/graph-authoring/adapters/prompts/author.yaml`, and `scripts/author.sh`.

### R-4: Upgrade adapter tests from existence to substance

AC-18 currently asks the tests to prove that the graph lints, the prompt is a pointer, and the wrapper exists and is executable (`feature-requests/FR-765-graph-authoring-workflow-skill.md:234-236`). That is not enough for the amended route. Repo doctrine calls out the `gate_checks_shape_not_substance` trap and requires `substance_over_presence` (`.github/copilot-instructions.md:85-108`), and round 1 explicitly upgraded skill tests for the same reason (`tests/unit/test_fr446_copilot_skills.py:1-7`, `tests/unit/test_fr446_copilot_skills.py:83-132`).

Fold into AC-18: tests must assert the adapter graph has exactly one copilot node with `backend: cli`, `allow_all_paths: true`, `allow_all_tools: true`, a pinned model, and timeout sized for authoring loops; the prompt is a thin pointer to `../doctrine.md`, contains the narrowed re-entry guard from R-1, and does not duplicate doctrine headings; `scripts/author.sh` is executable, documents/implements `scripts/author.sh <task-brief.md>`, and contains artifact-report existence checks for `tmp/draft-authoring-report.md`; the README documents the sole command, flags, artifact proof rule, and no auto-commit/PR/merge boundary.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/graph-authoring/SKILL.md`: existing discovery wrapper updated only to point to the adapter route and preserve composition with `author-graph` / `author-prompt`. |
| D-2 | `.github/skills/graph-authoring/doctrine.md`: existing workflow doctrine updated only for the executable route, task-brief input closure, narrowed re-entry guard, and report contract. |
| D-3 | `.github/skills/graph-authoring/adapters/README.md`: operational instructions, sole command, load-bearing flags, artifact proof rule, advisory-output boundary. |
| D-4 | `.github/skills/graph-authoring/adapters/graph.yaml`: single-node copilot adapter graph. |
| D-5 | `.github/skills/graph-authoring/adapters/prompts/author.yaml`: thin pointer prompt with narrowed re-entry guard. |
| D-6 | `scripts/author.sh`: operator wrapper for the authoring adapter. |
| D-7 | `tests/unit/test_fr446_copilot_skills.py`: REQ-YG-423 tests extended to the adapter, prompt, wrapper, README, and registry surface. |
| D-8 | `capabilities/CAP-158-copilot-skill-promotion.yaml`: REQ-YG-423 updated to include the executable graph-authoring route. |
| D-9 | `ARCHITECTURE.md`: regenerated CAP-158 capability text only. |
| D-10 | `feature-requests/FR-765-graph-authoring-workflow-skill.md`: revised per R-1 through R-4 and updated with implementation status/decisions after enforcement. |
| D-11 | `changelog/unreleased/`: one changelog fragment if the enforcement changes user-visible behavior beyond the existing round-1 fragment. |
| D-12 | `docs/diary/`: one metacognitive reflection entry if the resulting PR type triggers the repo diary gate. |

Not authorized: changes to `examples/yamlgraph_gen/`, generated output directories, mobile/web trigger channels, `judge-fr` doctrine, `review-pr` doctrine, judge/review adapters, hooks, CI workflows, branch protection, YAMLGraph runtime primitives, graph-generation framework primitives, auto-commit behavior, PR creation, merge behavior, inbox polling, worktree management, or remote create-and-run behavior.

## Revised acceptance criteria

- [ ] AC-01: Round 1 criteria AC-01 through AC-12 remain satisfied and are not regressed by the adapter amendment.
- [ ] AC-02: `.github/skills/graph-authoring/adapters/graph.yaml` exists, passes `yamlgraph graph lint`, and defines a YAMLGraph graph with exactly one `type: copilot` node using `backend: cli`, `allow_all_paths: true`, `allow_all_tools: true`, a pinned model, a prompt named `author`, `state_key`, and timeout sized for lint/smoke repair loops.
- [ ] AC-03: The adapter graph state includes `task_path: str` and passes that path to the prompt; no hidden chat narrative is required to execute the route.
- [ ] AC-04: `.github/skills/graph-authoring/adapters/prompts/author.yaml` is a thin pointer prompt: it instructs the launched agent to read `.github/skills/graph-authoring/doctrine.md` and the task brief, follow the doctrine, write `tmp/draft-authoring-report.md`, and duplicates no doctrine content.
- [ ] AC-05: The author prompt contains the narrowed re-entry guard: the launched agent is the authoring execution and must not invoke the `graph-authoring` skill, `scripts/author.sh`, `.github/skills/graph-authoring/adapters/graph.yaml`, or any command that launches that adapter route again; ordinary `yamlgraph graph lint <target graph>` and narrow smoke commands against authored target graphs remain required.
- [ ] AC-06: `scripts/author.sh <task-brief.md>` exists, is executable, validates that the task brief exists, launches `.github/skills/graph-authoring/adapters/graph.yaml` with `task_path`, and treats `tmp/draft-authoring-report.md` plus listed artifact paths as the proof of authoring.
- [ ] AC-07: `scripts/author.sh` verifies success by artifact existence, not adapter exit code: `tmp/draft-authoring-report.md` must be non-empty, contain `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` headings, and list at least one repo-relative artifact path that exists.
- [ ] AC-08: `.github/skills/graph-authoring/adapters/README.md` documents the sole invocation command `scripts/author.sh <task-brief.md>`, the load-bearing CLI flags, the artifact-existence verification rule, and the prohibition on auto-commit, PR creation, merge, inbox polling, CI, and worktree-management actions.
- [ ] AC-09: `SKILL.md` and `doctrine.md` name the adapter as the execution route for delegated authoring while keeping `doctrine.md` non-invocable and avoiding duplicated graph/prompt syntax reference material.
- [ ] AC-10: `tests/unit/test_fr446_copilot_skills.py` remains tagged with `@pytest.mark.req("REQ-YG-423")` and asserts adapter substance: graph shape/flags, prompt pointer/no-duplication/narrowed guard, executable wrapper with artifact checks, README command/flag/prohibition content, and CAP-158 module synchronization.
- [ ] AC-11: `capabilities/CAP-158-copilot-skill-promotion.yaml` updates REQ-YG-423 to include the executable graph-authoring route and key modules, and `ARCHITECTURE.md` is regenerated so the CAP-158 text matches the capability file.
- [ ] AC-12: The FR is updated with implementation status, decisions, and any deviations from this judgement after enforcement.
- [ ] AC-13: No changes are made to `examples/yamlgraph_gen/`, generated output directories, mobile/web trigger channels, judge/review doctrine or adapters, hooks, CI workflows, branch protection, YAMLGraph runtime primitives, or graph-generation framework primitives under this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | The authoring re-entry guard must prohibit only recursive launch of the graph-authoring route; it must not prohibit `yamlgraph graph lint` or narrow smoke commands against authored target graphs. | GATE |
| C-2 | Keep this a workflow-skill execution route over existing copilot-node capability. Do not add a YAMLGraph runtime primitive, generator framework, mobile/web trigger, or remote create-and-run path. | GATE |
| C-3 | Do not modify `judge-fr`, `review-pr`, their doctrines, adapters, or execution routes. Any enforcement-infrastructure change requires separate human-reviewed authority. | GATE |
| C-4 | The adapter graph and prompt must be thin pointers to doctrine, not a second copy of authoring doctrine or graph/prompt syntax references. | GATE |
| C-5 | Artifact proof is mandatory: the wrapper must verify `tmp/draft-authoring-report.md` and at least one listed artifact path; adapter exit code alone is never sufficient. | GATE |
| C-6 | Tests must check substance, not just file presence or executability, and CAP-158 / `ARCHITECTURE.md` must stay synchronized with the executable route. | GATE |
| C-7 | Output is advisory and uncommitted. The adapter and wrapper must never auto-commit, open or update PRs, poll inboxes, manage worktrees, run CI, or merge. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may add the graph-authoring adapter graph, pointer prompt, adapter README, and `scripts/author.sh`; update the graph-authoring skill/doctrine, CAP-158, generated architecture text, tests, changelog/diary artifacts as required; and update FR-765 within the frozen surfaces above.
