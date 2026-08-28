# Judgement: FR-901 Map the skills layer into the development-process overview

**Verdict:** APPROVED WITH REVISIONS — the documentation gap is real and the proposed surface is minimal, but authority activates only after the FR folds in the explicit research/graph-dispatch answer and repairs the contradictory file-scope acceptance criterion.

**Reviewed against:** `feature-requests/FR-901-skills-layer-in-process-overview.md`; cited evidence `docs/development-process.md`, `.github/hooks/README.md`, `docs/process.md`, `docs/sheikkinen-process.md`, `reference/skills-export.md`, `docs/plan-yamlgraph-skills.md`, `docs/plan-skills-export.md`, `.github/agents/code-analysis.agent.md`, `.github/skills/*/SKILL.md`, `.github/skills/graph-authoring/doctrine.md`, `.github/skills/judge-fr/doctrine.md`, `.github/skills/review-pr/doctrine.md`, `.github/skills/graph-authoring/adapters/README.md`, `.github/skills/judge-fr/adapters/README.md`, `.github/skills/review-pr/adapters/README.md`; repo doctrine `.github/copilot-instructions.md`, `CLAUDE.md`, `ARCHITECTURE.md`; judge contract `.github/skills/judge-fr/doctrine.md`; judgement template `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The FR identifies a real orientation defect with concrete evidence: `docs/development-process.md` currently presents the doctrine subgraph with Scripture, CLAUDE.md, reference docs, and ARCHITECTURE.md only (`docs/development-process.md:30-35`), and Ring 1 names generic pre-command/post-edit/audit hooks without the FR-767 authoring guard (`docs/development-process.md:238-242`). The target document already claims to be the relationship overview for doctrine-governed automation (`docs/development-process.md:16-19`), so adding the missing skills vertex there conforms to the existing overview rather than creating a second map.

The inventory claim is materially correct. The filesystem contains exactly nine skill directories: `chaplain-ops`, `check-langsmith-trace`, `feature-request`, `graph-authoring`, `judge-fr`, `release-version`, `review-pr`, `run-code-analysis`, and `session-introspection`; only `graph-authoring`, `judge-fr`, and `review-pr` have both `doctrine.md` and `adapters/`. The FR's summary and problem statement match that split (`feature-requests/FR-901-skills-layer-in-process-overview.md:55-59`). The cited hook documentation confirms the FR-767 edge: the pre-command guard blocks unsentineled writes to governed graph artifacts and allows sentineled adapter executions (`.github/hooks/README.md:74-80`), with sentinel lifecycle and denial route documented at `.github/hooks/README.md:97-107`.

The proposed change is strategically classified as **Pattern documentation**. It adds no framework primitive, runtime behavior, hook behavior, or graph artifact; it updates a process map so future readers can discover an already-existing doctrine layer. That classification aligns with the FR's narrow proposed edits to `docs/development-process.md` only (`feature-requests/FR-901-skills-layer-in-process-overview.md:70-86`) and its rejection of a standalone map or generator (`feature-requests/FR-901-skills-layer-in-process-overview.md:103-108`).

## Required revisions

### R-1: Add the explicit `is_this_a_graph` research answer

Fold one sentence into the FR's `**Research:**` field or Alternatives section: `is_this_a_graph: No — the deliverable is a deterministic documentation edit to docs/development-process.md, not a multi-stage LLM pipeline or graph artifact; graph-authoring is not triggered because no graph.yaml or prompts/*.yaml artifact is created or materially modified.` This satisfies the local research-evidence rule requiring the Judge to see the graph-dispatch answer, not infer it (`.github/skills/judge-fr/doctrine.md:118-128`).

### R-2: Repair AC-04 so it does not prohibit the target edit

Replace AC-04 with: `AC-04: Implementation modifies only docs/development-process.md, plus required process artifacts in feature-requests/, changelog/unreleased/ if the selected submit path requires it, and docs/diary/; no graph YAML, prompt YAML, hook, script, capability, or skill source files are modified.` The current wording says "no other files modified" while the FR authorizes edits to `docs/development-process.md` (`feature-requests/FR-901-skills-layer-in-process-overview.md:72-86`, `feature-requests/FR-901-skills-layer-in-process-overview.md:96-97`), creating an avoidable enforcement ambiguity.

### R-3: Make AC-02 require names, not only a collapsed count

Replace AC-02 with: `AC-02: Section 2 contains a skill-to-doctrine-to-adapter-to-enforcement table that names graph-authoring, judge-fr, and review-pr individually; names all six operational skills in a collapsed row; and includes one .github/agents/code-analysis.agent.md row.` The current AC says "all 9 skills accounted for" but permits one collapsed row for six skills (`feature-requests/FR-901-skills-layer-in-process-overview.md:92-94`); naming the six prevents a count-only compliance artifact and preserves AC-05's "no skill invented, no route misattributed" intent (`feature-requests/FR-901-skills-layer-in-process-overview.md:98-99`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/development-process.md` §1 big-picture Mermaid doctrine subgraph: add the skills node and an edge/placement that shows it constrains the development pipeline. |
| D-2 | `docs/development-process.md` §2 Doctrine Layer: add the federated-doctrine paragraph and the skills/agent mapping table. |
| D-3 | `docs/development-process.md` §5 Ring 1: add the FR-767 graph-authoring sole-route guard entry or bullet, citing `.github/hooks/README.md` for hook-side detail. |
| D-4 | Process artifacts only as required by the repository workflow: the folded FR, judgement artifact, optional changelog fragment if the submit path requires it, and diary reflection. |

Not authorized: changes to `.github/skills/**`, `.github/agents/**`, `.github/hooks/**`, `scripts/**`, `yamlgraph/**`, `tests/**`, `capabilities/**`, `graphs/**`, `.chaplain/graphs/**`, `examples/**/graph.yaml`, or `examples/**/prompts/*.yaml`; adding a generator for the skills table; changing any adapter, hook, pre-commit, CI, or branch-protection behavior; updating framework-user documentation such as `reference/getting-started.md`; authoring or modifying graph artifacts.

## Revised acceptance criteria

- [ ] AC-01: `docs/development-process.md` §1 DOCTRINE subgraph contains a `.github/skills/` node and the Mermaid fenced block remains syntactically parseable.
- [ ] AC-02: `docs/development-process.md` §2 contains a skill-to-doctrine-to-adapter-to-enforcement table that names `graph-authoring`, `judge-fr`, and `review-pr` individually; names `chaplain-ops`, `check-langsmith-trace`, `feature-request`, `release-version`, `run-code-analysis`, and `session-introspection` in one operational-skills row; and includes one `.github/agents/code-analysis.agent.md` row.
- [ ] AC-03: `docs/development-process.md` §5 Ring 1 names the FR-767 graph-authoring sole-route guard and states that sentineled adapter executions are allowed while unsentineled writes to governed graph artifacts are denied.
- [ ] AC-04: Implementation modifies only `docs/development-process.md`, plus required process artifacts in `feature-requests/`, `changelog/unreleased/` if the selected submit path requires it, and `docs/diary/`; no graph YAML, prompt YAML, hook, script, capability, or skill source files are modified.
- [ ] AC-05: Every route/enforcement claim in the new prose is traceable to the existing cited artifacts: `scripts/author.sh` and FR-767 sentinel guard for `graph-authoring`; `scripts/judge.sh`, lock/lineage sentinel, and draft judgement artifact for `judge-fr`; `scripts/review.sh`, lock/lineage sentinel, and draft review artifact for `review-pr`; no route is attributed to the six operational skills.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into the FR before implementation authority activates. | GATE |
| C-2 | Treat this as documentation-only pattern work; do not alter enforcement infrastructure or runtime behavior. | GATE |
| C-3 | Do not invoke graph-authoring, judge-fr, review-pr, their adapters, `yamlgraph graph run`, or any route that authors or reviews graph artifacts while enforcing this FR. | GATE |
| C-4 | If any implementation step touches enforcement-class files (`.github/hooks/**`, `.github/skills/**`, `.github/agents/**`, `scripts/**`, `yamlgraph/**`, `tests/**`, `capabilities/**`) stop; that is outside this FR and needs a separate judged request. | GATE |

Authority granted: after R-1 through R-3 are folded, the enforcer may update only `docs/development-process.md` to map the existing skills and agent layer into the process overview, with required process artifacts as described above.

**Prior art:** dispositioned in the FR body (skills-export docs are the graph-export product, keyword overlap only).
