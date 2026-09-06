# FR-1013 R-1 inventory at BASE `36591389` — per-file dispositions

Raw match list: `fr1013-inventory-at-base-36591389.txt` (2586 lines, 261 files). Command: see FR-1013 § Inventory at BASE. One disposition per file applies to every match in that file.

| File | Matches | Disposition |
|---|---|---|
| `.github/copilot-instructions.md` | 4 | **edit** — edit — :205 heading `## Sermon of the Chaplain` → `## Sermon`; :177 drop "chaplain pipeline, " from the sources clause. :52 (`audit` boundary) and :162 (`inquisitor_auto_escalation` seed) are Knowledge Graph entries — unchanged |
| `.github/skills/graph-authoring/SKILL.md` | 1 | **edit** — edit — :3 description drops "deciding whether graph work belongs in Chaplain instead" |
| `.github/skills/graph-authoring/doctrine.md` | 2 | **edit** — edit — :58 "escalate to Chaplain instead" and :128 "Enforce via Chaplain." → file an FR (`proposals/` → judge); live doctrine naming a retired route (found at BASE, not in the planning table) |
| `.github/skills/judge-fr/doctrine.md` | 2 | **edit** — edit — :135 → `docs/archive/chaplain.md`; :133 kept (true history) |
| `docs/context/chaplain-system.md` | 58 | **edit** — edit — `git mv` → `docs/archive/chaplain-system.md`; linked from `docs/archive/chaplain.md` |
| `docs/development-process.md` | 28 | **edit** — every active-process passage (round-3 R-3 / review #627 P2): topology mermaid, § 3, § 3.1 (measurement sentence byte-identical; the rest past-tense history or deleted), intro :6, § 2.1 row :113, § 5 bullet :286, § 6 mermaid + bullets :312–320, § 7 row :330. Exact residual lines (7): listed in `tests/unit/test_fr1013_doctrine_sweep.py::RESIDUAL` |
| `examples/README.md` | 3 | **edit** — edit — :57 row deleted; :74 note → `graphs/`; :171 witnesses line deleted |
| `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` | 2 | **edit** — edit — `cp` byte-for-byte from the canonical after editing (mirror_exact, R-2) |
| `reference/audit-index.md` | 8 | **edit** — edit — :65–71 six rows deleted, Philosopher → `graphs/philosopher/graph.yaml`, one `Chaplain (archived)` row → `docs/archive/chaplain.md`; :57 Inquisitor-audits row kept (the diary entries exist) |
| `reference/command-book.md` | 1 | **edit** — edit — :76 "Sermon of the Chaplain" → "Sermon" (follows the heading rename) |
| `reference/graph-yaml.md` | 2 | **edit** — edit — :610 comment dropped; :1469 example → `graphs/fr_triage` |
| `reference/onepager-development-process.md` | 9 | **edit** — edit — :11 column, :26 heading, :31 inbox path, :45 submission route, :90 hook row, :126, :138 flow step, :146, :154 sources |
| `reference/patterns/fsm-as-conductor.md` | 8 | **edit** — edit — :169–170, :235 link targets → `docs/archive/chaplain-system.md`; the Chaplain remains a case study in the pattern (historical) |
| `.github/hooks/README.md` | 2 | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| `.github/hooks/scripts/pre-command-guard.sh` | 1 | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| `.github/skills/feature-request/SKILL.md` | 1 | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| `.github/skills/judge-fr/MANIFEST.yaml` | 4 | keep — lineage/provenance metadata (MANIFEST, adapter header) |
| `.github/skills/judge-fr/adapters/graph.yaml` | 1 | keep — lineage/provenance metadata (MANIFEST, adapter header) |
| `.github/skills/outsider-view/fixtures/EXPECTATIONS.md` | 1 | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| `.github/workflows/workflow.yml` | 1 | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| `ARCHITECTURE.md` | 105 | keep — generated file; changes only as `scripts/aggregate_capabilities.py` output of the CAP-264 edit (D-6): exact delta (1 row replaced, 1 REQ-YG-668 row added) frozen in the witness's `DELTA` |
| `CHANGELOG.md` | 92 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `capabilities/CAP-106-github-issues-remote-inbox.yaml` | 5 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-109-harden-remote-inbox.yaml` | 5 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-113-chaplain-research-step.yaml` | 10 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-114-automated-post-merge-finalization.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-116-acceptance-tests-before-enforce.yaml` | 13 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-124-watcher2-pr-reuse.yaml` | 2 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-125-pipeline-script-retirement.yaml` | 12 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-128-chaplain-documentation.yaml` | 9 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-130-watcher2-finalize-optimization.yaml` | 3 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-132-watcher2-ci-resilience.yaml` | 6 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-133-watcher2-ci-remediation-crash-fix.yaml` | 3 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-134-watcher2-changelog-auto-generation.yaml` | 7 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-135-watcher2-forensic-failure-diary.yaml` | 8 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-137-watcher-fsm-startup-script.yaml` | 3 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-138-watcher-pipeline-fsm-simplification.yaml` | 8 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-140-watcher2-validate-split-fix-gate.yaml` | 11 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-142-skill-export.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-152-watcher2-dispatcher-audit-cadence.yaml` | 11 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-158-copilot-skill-promotion.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-16-linter-cross-reference.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-165-watcher2-baseline-dead-code-removal.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-193-watcher-wrapper-json-envelope.yaml` | 4 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-259-declared-text-encoding.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-264-chaplain-runtime-retired.yaml` | 30 | **edit** (D-6, round 3) — REQ-YG-668 added, FR-1013 in `fr`, doc surfaces + witness in `modules`; exact added lines frozen in the witness's `DELTA` |
| `capabilities/CAP-31-chaplain-diary-append.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-36-inquisitor-auto-propose.yaml` | 8 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-39-inquisitor-commit-delta-gate.yaml` | 7 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-42-inquisitor-worktree-gate.yaml` | 7 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-44-judge-split-verdict.yaml` | 2 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-55-chaplain-inbox-documentation.yaml` | 5 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-64-concurrency-safety-map.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-67-philosopher-daemon.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-72-knowledge-graph-mass-graduation-fr193.yaml` | 1 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-74-fsm-scripture-claude-md.yaml` | 2 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `capabilities/CAP-75-portable-chaplain.yaml` | 2 | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| `docs/2026-06-28-research.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-07-12-review-refactoring.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-07-18-fr-atlas.md` | 76 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-07-19-fr-atlas.md` | 76 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-07-28-research-safe-mobile-web-graph-access.md` | 10 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-07-29-research-subagent-promotion.md` | 4 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-08-18-velocity-report.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-08-21-plan-architecture-claims-pipeline.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-09-02-brainstorm-business-use-cases.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-09-05-research-pi-agent-runtime.md` | 3 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/2026-09-05-research-plan-cap-journey-census.md` | 5 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/FR-884-raw-read-log.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/FR-884-session-task-shapes.md` | 3 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/case-study-earlier-spikes.md` | 1 | keep — historical prose |
| `docs/case-study-research-spike-outsider.md` | 1 | keep — historical prose |
| `docs/census/cap-journey-pilot-2026-09-05-run1.md` | 50 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/cap-journey-pilot-2026-09-05-run2.md` | 54 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/cap-journey-pilot-2026-09-05-run3.md` | 55 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/chaplain-test-disposition.brief.REJECTED.md` | 6 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/chaplain-test-disposition.generic.md` | 77 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/chaplain-test-disposition.human-read.md` | 131 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/census/chaplain-test-disposition.md` | 98 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `docs/cmm-assessment.md` | 4 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/concurrency-safety.md` | 11 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/confessions.md` | 1 | keep — historical prose. Main drift after BASE: PR #628 (`b71d0083`, CONF-462…465 for FR-1012's noqa lines) added 4 matching `**File**:` lines before this PR; that exact delta is frozen in the witness's `DELTA` — the only post-BASE main change inside the census scope |
| `docs/constitution-diff.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/contexts/extending-watcher-fsm.md` | 25 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-19.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-20.md` | 16 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-21.md` | 8 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-22.md` | 4 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-23.md` | 65 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-24.md` | 23 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-02-26.md` | 99 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-03-02.md` | 98 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-03-04.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/diary-2026-03-06.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/feature-request-methodology.md` | 1 | keep — historical prose |
| `docs/letter-to-the-philosopher.md` | 5 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/mercury-census/findings.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/node-type-census-2026-08.md` | 7 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/origin-story.md` | 18 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-chat-initiated-outbound-calls.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-converge-map-mercury-reduce.md` | 6 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-defensive-position-governed-pipeline.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-dogfood-chaplain.md` | 11 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-github-chaplain-arbitrary-repo.md` | 21 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-planner-topics-2026-07-18.md` | 4 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-process-mining.md` | 4 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-repo-split.md` | 8 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-research-langgraph-1.2-feature-gaps.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-research-session-isolation.md` | 5 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-token-cost-mitigation.md` | 16 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-watcher-fsm.md` | 97 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-web-toolkit.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/plan-yamlgraph-skills.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/recaps/2026-W34.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/recaps/2026-W35.md` | 1 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/refactoring-watcher-pipeline-v2.md` | 29 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/refactoring-watcher-pipeline-v3.md` | 21 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/refactoring-watcher-pipeline.md` | 8 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/reflections-2026-03-05.md` | 1 | keep — historical prose |
| `docs/scripture-provenance.md` | 1 | keep — historical prose |
| `docs/sheikkinen-process.md` | 2 | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| `docs/spikes/outsider-reader-2026-09-05/EXPECTATIONS.md` | 1 | keep — historical prose |
| `examples/2026-07-01-plan-cleanup.md` | 14 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/agent-sdk-planner/README.md` | 2 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/agent-sdk-planner/plan.py` | 1 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/bugfix/README.md` | 2 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/cap_journey_census/extract.py` | 4 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/demos/cap_journey_census/journeys.yaml` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml` | 4 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml` | 4 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `examples/demos/corpus_census/adapters/chaplain_adapters.py` | 14 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `examples/demos/corpus_census/adapters/chaplain_rubric.md` | 6 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `examples/demos/corpus_census/adapters/diary_recurrence.py` | 5 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/demos/diary_index/prompts/extract_entry.yaml` | 1 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/file-hook/README.md` | 2 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/forensic-failure-diary/README.md` | 6 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/forensic-failure-diary/graph.yaml` | 1 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/forensic-failure-diary/prompts/analyze_failure.yaml` | 1 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/demos/philosopher_book/edited-chapters/ch-03-partial_remediation.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-05-false_duplicate.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-06-plausible_wrong_answer.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-07-framework_costume.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-08-working_system_inertia.md` | 8 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-09-architecture_as_diagram.md` | 3 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-10-gate_checks_shape_not_substance.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-11-audit_as_ritual.md` | 9 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-13-quick_confidence.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-16-instruction_boundary_uncrossed.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-18-model_as_trusted_peer.md` | 4 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/ch-19-infrastructure_self_exempt.md` | 11 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/edited-chapters/editorial-report.md` | 13 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/appendix-01-doctrine-accumulation.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/book.md` | 46 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-03-partial_remediation.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-05-false_duplicate.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-06-plausible_wrong_answer.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-07-framework_costume.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-08-working_system_inertia.md` | 8 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-09-architecture_as_diagram.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-10-gate_checks_shape_not_substance.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-11-audit_as_ritual.md` | 9 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-13-quick_confidence.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-16-instruction_boundary_uncrossed.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-18-model_as_trusted_peer.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-19-infrastructure_self_exempt.md` | 11 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/ch-22-letter-to-the-philosopher.md` | 5 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/book.md` | 46 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-03-partial_remediation.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-05-false_duplicate.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-06-plausible_wrong_answer.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-07-framework_costume.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-08-working_system_inertia.md` | 8 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-09-architecture_as_diagram.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-10-gate_checks_shape_not_substance.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-11-audit_as_ritual.md` | 9 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-13-quick_confidence.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-16-instruction_boundary_uncrossed.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-18-model_as_trusted_peer.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-19-infrastructure_self_exempt.md` | 11 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/final/demo-run/_input_snapshot/ch-22-letter-to-the-philosopher.md` | 5 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-01-downstream_fix.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-03-partial_remediation.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-04-regex_fourth_exclusion.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-05-false_duplicate.md` | 4 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-06-plausible_wrong_answer.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-07-framework_costume.md` | 3 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-08-working_system_inertia.md` | 11 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-09-architecture_as_diagram.md` | 3 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-10-gate_checks_shape_not_substance.md` | 3 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-11-audit_as_ritual.md` | 12 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-13-quick_confidence.md` | 1 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-16-instruction_boundary_uncrossed.md` | 5 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-18-model_as_trusted_peer.md` | 4 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/philosopher_book/philosopher-book/chapters/ch-19-infrastructure_self_exempt.md` | 13 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/demos/planner/README.md` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/demos/planner/demo.sh` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/demos/research-route/nodes/research_tools.py` | 4 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `examples/ebook/README.md` | 5 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/graph-ch03.yaml` | 4 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/graph-ch04.yaml` | 4 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/graph.yaml` | 32 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/nodes/writing.py` | 10 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/chapter/chaplain_pipeline.yaml` | 6 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/chapter/doctrine.yaml` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/chapter/inquisitor.yaml` | 10 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/chapter/introduction.yaml` | 3 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/chapter/traceability.yaml` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/prompts/judge_draft.yaml` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/ebook/run-chapters.sh` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `examples/novel_fandom/story/thread_waivers.yaml` | 3 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/plot_modeller/docs/plan-roundtrip-phased.md` | 1 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `examples/shared/diary.py` | 3 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `graphs/philosopher/README.md` | 1 | keep — FR-1011 relocated graph; comments record provenance |
| `graphs/philosopher/diary.py` | 3 | keep — FR-1011 relocated graph; comments record provenance |
| `graphs/philosopher/graph.yaml` | 1 | keep — FR-1011 relocated graph; comments record provenance |
| `graphs/philosopher/prompts/challenge.yaml` | 1 | keep — FR-1011 relocated graph; comments record provenance |
| `graphs/philosopher/tools.py` | 1 | keep — FR-1011 relocated graph; comments record provenance |
| `prompts/chaplain-audit.md` | 2 | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| `reference/fr-knowledge-graph.yaml` | 3 | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| `scripts/chaplain_archive.sh` | 33 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `scripts/chaplain_census.py` | 22 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `scripts/chaplain_postmerge_witness.sh` | 14 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `scripts/fix_bare.sh` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/migrate_capabilities.py` | 6 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/migrate_diary_to_folder.py` | 2 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/pipeline_summary.py` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/vscode/MAP.md` | 3 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/vscode/now.py` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `scripts/worktree.sh` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `tests/conftest.py` | 2 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `tests/unit/test_automated_post_merge_finalization.py` | 3 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_chaplain_graph_compile.py` | 6 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_concurrency_safety_doc.py` | 2 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_diary_digest.py` | 6 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_diary_index.py` | 4 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_ebook_writing.py` | 15 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr026_chaplain_fixes.py` | 2 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr1011_relocation.py` | 19 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `tests/unit/test_fr1012_chaplain_archive.py` | 24 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `tests/unit/test_fr1012_chaplain_census.py` | 34 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `tests/unit/test_fr1012_chaplain_postmerge_witness.py` | 13 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `tests/unit/test_fr1012_chaplain_removed.py` | 18 | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| `tests/unit/test_fr372_gitignore_boundary_guard.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr382_chaplain_prompt_caching_scope_red.py` | 2 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr392_fsm_on_launch_hook_red.py` | 2 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr419_action_config_schema_boundary.py` | 9 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr446_copilot_skills.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr693_event_revision.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr748_fr_atlas.py` | 2 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr754_id_registry_package_boundary.py` | 5 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr896_precedent_traceability.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fr942_instruction_diet.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_fsm_claude_md_doctrine.py` | 3 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_knowledge_graph_fr193.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_migrate_diary.py` | 7 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_philosopher.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_python_node_graph_integration.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_python_nodes.py` | 6 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `tests/unit/test_ramp_installer.py` | 1 | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| `yamlgraph/utils/fsm/action.py` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| `yamlgraph/utils/worktree_helpers.py` | 1 | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
