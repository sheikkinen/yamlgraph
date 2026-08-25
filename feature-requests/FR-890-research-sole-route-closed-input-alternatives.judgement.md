# Judgement: FR-890 Research Sole Route - Closed-Input Alternatives Before Authority

**Prior art:** dispositioned in the FR (innovation_matrix + web-research + research-agent graphs; CAP-113 dead chaplain step; FR-737/738 past-half; FR-888 post-mortem; FR-889 exemplar; FR-780 search toolbelt).

**Verdict:** APPROVED WITH REVISIONS - the problem is real and the graph-shaped direction is sound, but authority activates only after the FR resolves its own gate-scope contradiction, pins the activation boundary, and makes the research artifact/substance checks mechanically enforceable.

**Reviewed against:** `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `.github/skills/feature-request/SKILL.md`; `scripts/judge.sh`; `scripts/author.sh`; `.github/skills/judge-fr/adapters/README.md`; `.github/skills/graph-authoring/adapters/README.md`; `docs/analysis-fr888-post-mortem-2026-08-25.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md`; `feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md`; `feature-requests/FR-738-prior-art-disposition-gate.md`; `feature-requests/FR-780-research-agent-toolbelt-conversion.md`; `capabilities/CAP-113-chaplain-research-step.yaml`; `examples/demos/innovation_matrix/graph.yaml`; `examples/demos/map/graph.yaml`; `examples/demos/session-shapes/graph.yaml`; `examples/demos/web-research/graph.yaml`; `examples/demos/research-agent/graph.yaml`; `examples/shared/websearch.py`; `pyproject.toml`.

## What is sound

The need is evidenced, not speculative. FR-888's post-mortem records a high-cost planning miss: a 601-line hook, 16 commits, five review rounds, fourteen defect classes, and no gate catching the bloat (`docs/analysis-fr888-post-mortem-2026-08-25.md:12-20`), with the core tool-space failure named as parsing shell instead of moving enforcement to the OS boundary (`docs/analysis-fr888-post-mortem-2026-08-25.md:52-64`). FR-889 then shows the exact missing alternative surfaced as an operator-supplied tool-space table, selecting OS permissions over the regex grammar (`feature-requests/FR-889-os-enforced-main-write-lock.md:61-73`). That is sufficient evidence that loaded-context planning missed a cheaper solution class.

The proposal fits existing architecture. The Scripture says the moment a plan contains "for each item, ask the model" or parallel fan-out, map is the native shape and subagents are the fallback (`.github/copilot-instructions.md:133`); the existing map demo describes exactly that task shape (`examples/demos/map/graph.yaml:4-7`), and FR-884 already used a pinned-model map classifier plus deterministic reduce for session task-shape analysis (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:139-147`, `examples/demos/session-shapes/graph.yaml:43-64`). The proposed route is therefore a contrib/example plus process gate, not an invented framework primitive.

Prior art is dispositioned enough to proceed after revision. FR-737 and FR-738 establish that retrieval alone is not authority: prior art must be dispositioned by the judge, and shape-only gates are floors while substance stays with judgement (`feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md:86-91`, `feature-requests/FR-738-prior-art-disposition-gate.md:71-76`). FR-780 and the web-research demo provide feasible tool surfaces for grounded research (`feature-requests/FR-780-research-agent-toolbelt-conversion.md:13-25`, `examples/demos/web-research/graph.yaml:10-23`), and `ddgs` is already declared in the `websearch` extra (`pyproject.toml:62-64`).

The wrapper/sole-route pattern is also precedented. `scripts/judge.sh` and `scripts/author.sh` already implement lock, lineage sentinel, and artifact-not-exit-code contracts (`scripts/judge.sh:19-22`, `scripts/judge.sh:58-62`, `scripts/author.sh:40-43`, `scripts/author.sh:92-111`). Reusing that shape for `scripts/research.sh` is feasible and aligned.

## Required revisions

### R-1: Resolve the research-gate scope contradiction and freeze activation

Fold the FR to one rule: after FR-890 enforcement lands, every newly created FR that seeks plan authority must carry a committed `**Research:**` reference or receive no authority. Remove the narrower "solution-bearing FRs" wording from the Summary (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:35-37`) or explicitly mark it superseded by the operator amendment that says "any plan" (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:133-140`).

Also add a transition clause: the new rule is prospective from the commit that updates the FR template and judge doctrine; it does not retro-gate already judged or completed FRs, and this FR is the bootstrap case judged under the current doctrine. Without that boundary, the FR is self-invalidating because the current template has no `**Research:**` field (`feature-requests/TEMPLATE.md:1-12`) and FR-890 itself has no such header.

### R-2: Make the problem-brief closure preflight exact

Replace "rejects briefs containing solution-shaped sections" (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:80-84`) with a mechanical contract: required headings/fields, allowed free-text sections, forbidden headings, and forbidden candidate-list markers. The closed enum in lines 123-132 is sound; the FR must say whether the preflight is a stdlib script, a Python tool in the graph, or wrapper code, and the tests must include both a rejected draft-solution brief and an accepted incident/constraint-only brief.

The closure must not rely on an LLM deciding whether the brief is contaminated. This is enforcement infrastructure and must be deterministic.

### R-3: Strengthen the `tmp/draft-alternatives.md` artifact contract

AC-05 currently accepts a non-empty file with table markers (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:158-160`), which repeats the `gate_checks_shape_not_substance` failure mode. Fold a concrete artifact schema into the FR: at minimum candidate, planner/persona, class, verdict, precedent citation, `is_this_a_graph` answer, and effort/risk columns; 4-6 distinct solution classes; one row per persona output unless explicitly marked duplicate; disagreement preserved as separate rows; no empty/stub citation cells; no "Error:" web-search output counted as an external citation.

The wrapper may check presence and table shape; the judge clause checks substance. Both must be named, not blurred.

### R-4: Make the web-grounded witness fail closed

The reused `search_web` tool is feasible but returns error strings for missing `ddgs`, empty queries, or runtime search failures (`examples/shared/websearch.py:46-75`). AC-03 must require the exemplar to contain at least one real URL-bearing external citation from the librarian row, and tests or smoke verification must fail if the row contains `Error:`, `No results found`, or no URL. The route may depend on the existing `websearch` extra (`pyproject.toml:62-64`), but it must not silently accept an ungrounded librarian row as research evidence.

### R-5: Keep the judge-doctrine change narrow and human-reviewed

The proposed doctrine edit is enforcement infrastructure (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:133-143`), so the FR must pin the exact doctrine surfaces to change and require human review before the doctrine edit is treated as binding. The clause may add a research-evidence requirement and a substance check; it must not alter `scripts/judge.sh` output shape beyond the existing draft artifact contract, and it must not authorize any new judge invocation path.

### R-6: Define the research artifact's committed lifecycle

The persistent artifact amendment is correct (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:105-121`), but the FR must specify who promotes `tmp/draft-alternatives.md` to `feature-requests/FR-XXX.research.md`, what minimum headings/metadata it carries, and how dangling links are detected. The feature-request skill is stale relative to current template/process expectations (`.github/skills/feature-request/SKILL.md:21-54`), so its update must be included as a named deliverable, not only mentioned in AC-08.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/research-route/graph.yaml`, prompts, local nodes/tools, and `demo-output.log`, authored through `scripts/author.sh` |
| D-2 | `scripts/research.sh` wrapper with lock, lineage sentinel, problem-brief preflight, and artifact verification |
| D-3 | Problem-brief fixtures for accepted closed-input briefs and rejected solution-contaminated briefs |
| D-4 | Tests for artifact schema, disagreement preservation, librarian URL citation, and wrapper artifact verification |
| D-5 | `feature-requests/TEMPLATE.md` research-reference field and lifecycle text |
| D-6 | `.github/skills/feature-request/SKILL.md` update matching the template and lifecycle |
| D-7 | `.github/skills/judge-fr/doctrine.md` research-evidence clause, human-reviewed before binding |
| D-8 | Fixture judgement proving an FR without a committed research reference receives no authority after activation |
| D-9 | FR-888 exemplar problem brief and resulting committed/summarized witness of whether OS permissions surfaced |
| D-10 | Changelog fragment and diary reflection |

Not authorized: reviving the chaplain FSM runtime; auto-running research on FR creation; adding a pre-commit/CI denial gate for the research field; changing the judge/review/author invocation routes; adding semantic search infrastructure; implementing any alternative proposed by the research route; changing branch protection, release flow, or PR merge policy.

## Revised acceptance criteria

- [ ] AC-01: `examples/demos/research-route/` is authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` lists the graph/prompt artifacts and records graph lint plus a synthetic-brief smoke; all LLM nodes explicitly pin a cheap model.
- [ ] AC-02: A deterministic problem-brief preflight rejects a fixture brief containing forbidden solution/candidate sections and accepts a fixture containing only problem statement, classification enum value, constraints, and witnessed incidents.
- [ ] AC-03: The route runs five orthogonal personas: OS/infra primitivist, data/process planner, YAMLGraph-native planner, subtractionist, and web-grounded librarian.
- [ ] AC-04: The YAMLGraph-native planner records the `is_this_a_graph` answer and consults available graph `Task shapes:` descriptions; the exemplar or test output names the matching graph shape or says none.
- [ ] AC-05: The librarian row uses the reused `search_web` tool and carries at least one URL-bearing external citation; `Error:`, `No results found`, or empty URL output fails the exemplar.
- [ ] AC-06: The reducer writes `tmp/draft-alternatives.md` with the required columns: candidate, planner/persona, class, verdict, precedent citation, `is_this_a_graph`, effort/risk; the artifact has 4-6 distinct solution classes and no empty required cells.
- [ ] AC-07: Conflicting planner outputs are preserved as separate rows; a fixture with conflicting verdicts does not collapse them by vote or summary.
- [ ] AC-08: `scripts/research.sh <problem-brief.md>` serializes runs, exports a lineage sentinel, invokes only the research graph, and verifies the artifact by schema/shape rather than graph exit code.
- [ ] AC-09: The FR-888 pre-solution problem brief is run through the route; the FR records whether the OS-permissions class surfaced without operator help, with the resulting artifact or summarized table cited.
- [ ] AC-10: `feature-requests/TEMPLATE.md` adds a mandatory `**Research:** [FR-XXX.research.md](FR-XXX.research.md)` field and documents the committed sibling artifact convention plus allowed equivalent committed records.
- [ ] AC-11: `.github/skills/feature-request/SKILL.md` is updated to match the research-reference lifecycle and no longer presents a template that omits first-consumer or research evidence.
- [ ] AC-12: `.github/skills/judge-fr/doctrine.md` gains a prospective research-evidence clause: after FR-890 activation, newly created FRs without a non-dangling committed research reference receive no authority; already judged/completed FRs and this bootstrap FR are not retro-gated.
- [ ] AC-13: A fixture FR lacking `**Research:**` is judged through the sole route and the draft judgement grants no authority with a named missing-research finding; the existing judge output artifact shape remains unchanged.
- [ ] AC-14: Human review of the judge-doctrine edit is recorded before the doctrine change is treated as binding.
- [ ] AC-15: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-6 are folded into FR-890. | GATE |
| C-2 | Governed graph/prompt edits must go through `scripts/author.sh`; repair the authoring route if it fails rather than writing governed graph artifacts manually. | GATE |
| C-3 | The research route must not pass the author's draft solution or candidate list into persona prompts. | GATE |
| C-4 | The web-grounded persona must fail closed on search errors; an error string is not a citation. | GATE |
| C-5 | The judge-doctrine edit requires human review and must preserve the sole judge route and existing output artifact contract. | GATE |
| C-6 | No hook/CI/pre-commit denial gate for missing `**Research:**` is authorized by this FR; the Judge clause is the demand gate. | GATE |
| C-7 | The implementation must not auto-run research on FR creation or revive `.chaplain/` runtime behavior. | GATE |

Authority granted: after the required revisions are folded, implement the research sole route, its wrapper, committed research artifact lifecycle, template/feature-request documentation, and prospective judge-doctrine demand gate exactly within the frozen scope above.
