# Judgement: FR-854 Subagent-Call Classification Graph (Retrospective Measurement)

**Prior art:** FR-854-subagent-call-classification-graph.md is the FR
under judgement (self-match). FR-853 is the dispositioned companion (see
FR body). FR-588 (llm-scored prompt abstraction span), FR-767 (authoring
sole route), FR-546 (opencode backend): keyword-overlap only on generic
nouns (subagent/call/classification); none occupies this FR's territory.
NOTE (post-judgement): the governing prior art —
`docs/2026-07-29-research-subagent-promotion.md`, which already ran this
census — was NOT in this judgement's input set; its disposition and the
resulting authority suspension are recorded in the FR's Prior Art
Disposition section.

**Verdict:** APPROVED WITH REVISIONS — the measurement-first direction is sound, but authority is withheld until the FR folds in raw-sample evidence, a precise corpus/extraction contract, graph-registry reconciliation, and authoring input closure.

**Reviewed against:** `feature-requests/FR-854-subagent-call-classification-graph.md`; `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md`; `.github/skills/session-introspection/SKILL.md`; `scripts/vscode/README.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/FR-853-agent-instrument-registry.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/adapters/README.md`.

## What is sound

The problem is real and timely: the FR names a first consumer and first event (`feature-requests/FR-854-subagent-call-classification-graph.md:8-11`), and the cited diary shows the agent repeatedly reaching for terminal loops, subagents, and scripts instead of yamlgraph for N parallel LLM calls (`docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md:11-25`, `49-55`). FR-853 independently records the same gap and explicitly defers live interception as a separate concern (`feature-requests/FR-853-agent-instrument-registry.md:25-40`, `84-85`).

The scope is directionally minimal: measuring historical base rate before building live redirect machinery directly answers the stated risk that a PreToolUse classifier would tax every subagent call without evidence (`feature-requests/FR-854-subagent-call-classification-graph.md:27-33`, `93-98`). That aligns with the project doctrine requiring measurement/metric tooling to read raw records before trusting aggregates (`.github/copilot-instructions.md:232`) and with the `read_raw_output_first` cure (`.github/copilot-instructions.md:115`, `128`).

The proposed extract -> map-classify -> reconcile -> report shape has a strong in-repo precedent in FR-851: LLM fan-out via a map graph, typed output, deterministic reconciliation, raw-response evidence, and no silent drops (`feature-requests/FR-851-requirement-witness-audit.md:28-31`, `132-148`, `204-206`). The cited session-introspection substrate is also plausible: the repo already documents session stores, chronicle data, chat session logs, and read-only spike scripts in `scripts/vscode/` (`.github/skills/session-introspection/SKILL.md:8-23`; `scripts/vscode/README.md:73-83`, `144-153`).

## Required revisions

### R-1: Complete the raw-output read before authority

Replace the placeholder Raw Output Read section (`feature-requests/FR-854-subagent-call-classification-graph.md:38-46`) with a real table of at least 10 raw records read end-to-end before enforcement. Each row must include source store, session id or stable redacted id, timestamp or turn index, source stratum (`subagent-call` or `llm-loop-candidate`), raw dump path under `tmp/fr854-raw-samples/`, and one concrete surprising detail. This is a GATE because the judge doctrine says measurement/metric-tooling FRs require evidenced raw-output reads before authority, not during enforcement (`.github/copilot-instructions.md:232`).

### R-2: Freeze the corpus and extraction selectors

Define exactly what is being extracted. The FR currently says "past subagent prompts / LLM-loop invocations" and names `sessions`/`turns` plus `scripts/vscode/` precedent (`feature-requests/FR-854-subagent-call-classification-graph.md:61-64`), but the cited store map distinguishes chat sessions, transcripts, chronicle DB, debug logs, and resources (`scripts/vscode/README.md:73-83`). Fold in a deterministic extraction contract: source files or DB path family, selectors for `runSubagent` calls, selectors for terminal LLM-loop candidates, date/window defaults, maximum sample limits, redaction policy, and the machine-readable extracted-record schema. If `llm-loop-candidate` cannot be defined mechanically from committed precedent plus raw samples, remove it from this FR and leave it for a follow-up.

### R-3: Keep one base rate per source stratum

The title and first consumer are about subagent-call redirection, while the summary also includes terminal LLM loops (`feature-requests/FR-854-subagent-call-classification-graph.md:15-17`, `27-33`). Do not publish one blended "graph-shaped fraction" across both populations. The report must partition distributions by source stratum before ranking, and any redirect conclusion may cite only the `subagent-call` stratum unless a later FR separately justifies loop interception.

### R-4: Freeze the graph-registry and classifier reconciliation boundary

Define the allowed set used for `graph-shaped-existing`: committed graph ids/paths and descriptions from a deterministic registry source. The FR requires the report to name matched existing graphs (`feature-requests/FR-854-subagent-call-classification-graph.md:65-74`, `88-89`) but does not yet say how hallucinated graph names are rejected. Fold in the FR-851-style invariant for graph ids: returned existing-graph matches must be a subset of the extracted registry, duplicates keep first with audit trail, hallucinated graph ids are rejected or downgraded to `graph-shaped-novel`, and audited plus unaudited records must equal inputs (`feature-requests/FR-851-requirement-witness-audit.md:132-139`).

### R-5: Close the authoring input artifact

The FR correctly requires `scripts/author.sh` (`feature-requests/FR-854-subagent-call-classification-graph.md:59`, `83`), but graph-authoring doctrine also requires FR-bound task briefs to live under `feature-requests/authoring-briefs/` and be cited by the governing FR (`.github/skills/graph-authoring/doctrine.md:19-30`; `.github/skills/graph-authoring/adapters/README.md:12-18`). Add the exact committed task-brief path, expected artifact boundary, precedent-search target, and authoring report checks. The report must be `tmp/draft-authoring-report.md` with `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`, and listed paths must exist (`.github/skills/graph-authoring/doctrine.md:60-74`).

### R-6: Make evidence and tests mechanically checkable

The current ACs name broad categories only (`feature-requests/FR-854-subagent-call-classification-graph.md:83-91`). Replace them with criteria that can fail directly: fixture-based extractor tests for both strata, redaction tests, registry reconciliation tests, no-silent-drop tests, report-rendering tests that prove separate distributions per stratum, and graph lint/smoke validation recorded in the authoring report. The durable evidence file must include tree SHA, extractor command, source window, raw-sample citation table, model/provider, class distribution by stratum, registry reconciliation summary, and unclassified count. Bulk raw prompts stay in `tmp/`; committed evidence should cite only the minimum snippets needed for review.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR with completed raw-output read table and frozen extraction/classification contract |
| D-2 | Committed authoring brief, e.g. `feature-requests/authoring-briefs/fr-854-subagent-census-brief.md` |
| D-3 | Authored graph artifact under `examples/demos/subagent_census/` via `scripts/author.sh` |
| D-4 | Graph-local or narrowly scoped deterministic extraction, registry, reconciliation, and report tooling |
| D-5 | Unit tests for extraction fixtures, redaction, registry matching, reconciliation, and report rendering |
| D-6 | Durable evidence report at `feature-requests/evidence/FR-854-subagent-call-classification-graph.md` |
| D-7 | Changelog fragment and required ADR-001 test markers if tests are added |

Not authorized: live interception or redirect of subagent invocations; PreToolUse hooks; on-the-fly graph generation; changes to judge/review/authoring doctrine; CI or pre-commit changes; new yamlgraph node types; provider factory changes; MCP server changes; scheduled automation; committing bulk raw session transcripts or prompt dumps.

## Revised acceptance criteria

- [ ] AC-01: FR Raw Output Read section contains at least 10 real raw-record rows with source store, stable id, timestamp/turn, stratum, tmp dump path, and surprising detail.
- [ ] AC-02: FR cites the committed authoring brief path under `feature-requests/authoring-briefs/` and that brief names target directory, expected files, precedent graph(s), and validation expectations.
- [ ] AC-03: Extractor contract is deterministic: source store(s), selectors, date/window default, max records, redaction policy, and extracted-record schema are documented and covered by tests.
- [ ] AC-04: If both `subagent-call` and `llm-loop-candidate` are retained, reports and evidence keep separate distributions and rankings; no blended base rate is used for redirect conclusions.
- [ ] AC-05: Classification schema is typed and limited to `graph-shaped-existing`, `graph-shaped-novel`, `genuinely-agentic`, and `unclassified`, with `source_stratum`, rationale, and optional `matched_graph_id`.
- [ ] AC-06: Existing-graph matches reconcile against a deterministic committed graph registry; hallucinated ids are rejected or downgraded, and no matched graph id appears outside the registry.
- [ ] AC-07: Reconciliation invariant holds for extracted records: every extracted record is classified or listed unclassified; audited plus unaudited equals inputs; no silent drops.
- [ ] AC-08: Graph and prompts are authored solely via `scripts/author.sh <task-brief.md>`; `tmp/draft-authoring-report.md` exists, is non-empty, has required headings, lists repo-relative authored paths, and records lint plus smoke outcome or exact blocked validation reason.
- [ ] AC-09: Tests cover extractor fixtures, redaction, registry reconciliation, duplicate/missing/hallucinated classifier outputs, report rendering, and separate source-stratum aggregation; all new tests carry valid `@pytest.mark.req(...)` markers.
- [ ] AC-10: Evidence file includes tree SHA, extractor command, source window, record counts, model/provider, class distribution by stratum, graph-registry reconciliation summary, unclassified records, and at least 10 raw-sample citations with concrete details.
- [ ] AC-11: The report names matched existing graphs only for `graph-shaped-existing`; `graph-shaped-novel` names task shape without pretending a committed graph exists.
- [ ] AC-12: No live redirect, interception hook, doctrine change, CI change, MCP change, or new node/provider primitive is introduced.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 are folded into the FR before implementation begins; until then authority is withheld. | GATE |
| C-2 | Raw samples must be read before aggregate classification/reporting is trusted; mocked or fixture-only evidence cannot satisfy the real-run ACs. | GATE |
| C-3 | Graph artifacts are created only through `scripts/author.sh <committed-task-brief.md>` and verified by the authoring report artifact, not by adapter exit code. | GATE |
| C-4 | Raw prompt/session dumps remain under `tmp/`; committed evidence contains only review-minimal citations and redacted identifiers where needed. | GATE |
| C-5 | Any change to live agent routing, hooks, CI, doctrine, MCP registration, node types, or provider/runtime primitives requires a separate FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may build a self-contained retrospective measurement graph and evidence report for classifying historical agent-work records; it may not redirect live subagent calls or change enforcement infrastructure.
