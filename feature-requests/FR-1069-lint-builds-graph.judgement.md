# Judgement: FR-1069 Lint builds graph

**Prior art:** `FR-1069-lint-builds-graph.md` is the FR this judgement governs; its own prior-art line dispositions FR-842. FR-854 (Withdrawn), FR-875 and FR-1048 match only on "lint" and "graph"; they concern subagent classification, memory curation and an opencode backend.

**Verdict:** SPLIT — opt-in compile validation and repairing the safety-guards demo are independent concerns, with a human trust-boundary decision still open.

**Reviewed against:** `feature-requests/FR-1069-lint-builds-graph.md`; `docs/issues-2026-09-24.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The safety-guards edge compiles unsuccessfully despite clean lint (plan section 2 D10 and appendix), which is a focused missing check. FR-842 validates config rather than the compiled edge shape (FR-1069:14-19). FR-1069:51-57 correctly flags that compiling imports graph-declared Python and may execute module-level code; treating lint as a trusted-code operation requires a deliberate contract. Classification: correction to existing lint behavior and separate contrib/example repair, not a new framework primitive.

## Required revisions

### R-1: File separate compile-check and demo-repair FRs

Keep linter/CLI check and compiler parity tests in one successor, and safety-guards wiring plus authoring proof in another. The demo remains broken even if lint detects it; it can be fixed without changing lint (FR-1069:58-65). Neither successor gains authority from this SPLIT verdict.

### R-2: Resolve the trust boundary with a human decision

Ask the human: **May the ordinary `graph lint` command import and execute graph-declared Python, or must compilation be opt-in (`--build`) on trusted graphs?** FR-1069:43-57 says both "final check at end of lint_graph" and "behind `--build` on CLI". If opt-in, retract "lint passes implies graph builds" as the unconditional Ideal Result (FR-1069:34-44); make the promise `lint --build` instead. Do not claim importing arbitrary graph modules is side-effect-free; CLAUDE.md says only YAML config is trusted.

### R-3: Re-file each successor with independent evidence

The current three rejected tactics (FR-1069:72-77) do not meet the prospective research gate. Each successor needs four to six solution classes, precedent, dissent and `is_this_a_graph` with a committed reference. A repo-wide compile test must name fixture/module-import behavior and define what happens when optional dependencies or private graph fixtures are unavailable; "repair or list as defect" does not make the test green (FR-1069:58-68).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Researched compile-validation FR, with a human-approved trust contract |
| D-2 | Researched safety-guards demo-repair FR |
| D-3 | FR-1069 split disposition |

Not authorized: new default lint imports, `--build` flag, repo-wide compile test, or edits to safety-guards graph under FR-1069.

## Revised acceptance criteria

- [ ] AC-01: Two independently researched and judged successor FRs exist.
- [ ] AC-02: Human chooses default versus opt-in importing; the lint successor states the resulting promise and has a fixture proving the import boundary.
- [ ] AC-03: The lint successor's RED fixture reports the safety-guards edge failure with the original exception text; its census records each tracked graph's compile outcome and optional-dependency policy.
- [ ] AC-04: The demo successor proves corrected edge flow through the graph-authoring route, including revise-loop execution count.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not change lint's code-execution trust boundary before the human decision. | GATE |
| C-2 | Graph and prompt repair uses the sole governed authoring route, not direct file edits. | GATE |
| C-3 | No production or demo implementation under this split parent. | GATE |

Authority granted: none under FR-1069; both successors must re-enter judgement.
