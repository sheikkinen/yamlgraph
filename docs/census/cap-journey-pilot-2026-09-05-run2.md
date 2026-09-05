# CAP Journey Census Ledger

- rows: 30  judged: 28  row_failed: 2  abstained: 0
- model: claude-haiku-4-5  git_sha: a3945008  prompt: judge_cap.v1
- canary misses: 7 — CAP-131: journeys ['serve_embed'] miss ['run_operate']; CAP-203: journeys ['author_graph'] miss ['census_classify']; CAP-203: disposition keep != extend; CAP-203: extend_to None not in ['audit_comply', 'census_classify']; CAP-11: consumer_cited 'examples/demos/map/graph.yaml' misses ['corpus_census', 'diary_census', 'person_profile_census', 'repo_census']; CAP-108: disposition keep != extend; CAP-108: extend_to None not in ['audit_comply']

## Journey × CAP matrix

| journey | CAPs | keep | extend | retire | contested |
|---|---:|---:|---:|---:|---:|
| author_graph | 8 | 7 | 0 | 0 | 1 |
| run_operate | 5 | 4 | 0 | 0 | 1 |
| debug_observe | 0 | 0 | 0 | 0 | 0 |
| integrate | 3 | 2 | 0 | 0 | 0 |
| serve_embed | 4 | 2 | 0 | 0 | 0 |
| census_classify | 0 | 0 | 0 | 0 | 0 |
| govern_process | 3 | 3 | 0 | 0 | 0 |
| audit_comply | 0 | 0 | 0 | 0 | 0 |
| conversational_app | 2 | 0 | 0 | 0 | 2 |
| none_internal | 5 | 5 | 0 | 0 | 0 |

off-catalog labels: none

## Disposition table

| CAP | name | disposition | effective | extend_to | consumer_cited | anchor violations |
|---|---|---|---|---|---|---|
| CAP-142 | Skill Export Portable Packaging | already_retired | already_retired | - | - | - |
| CAP-81 | A2A Protocol Server | already_retired | already_retired | - | yamlgraph/discovery.py | - |
| CAP-150 | Philosopher's Book Demo | keep | contested | - | examples/demos/philosopher_book/graph.yaml | keep without a consumer from the mechanical list |
| CAP-153 | Built-in Questionnaire Gap Utilities | keep | contested | - | yamlgraph/tools/python_tool.py | keep without a consumer from the mechanical list |
| CAP-158 | Copilot Skill Promotion | keep | contested | - | .github/skills/graph-authoring/adapters/graph.yaml | keep without a consumer from the mechanical list |
| CAP-102 | Complete Worktree Teardown Self-Heal | keep | keep | - | yamlgraph/utils/worktree_helpers.py | - |
| CAP-108 | Changelog REQ Cross-Validation Gate | keep | keep | - | scripts/check_changelog_req.py | - |
| CAP-11 | Subgraph & Map | keep | keep | - | examples/demos/map/graph.yaml | - |
| CAP-12 | Utilities | keep | keep | - | .chaplain/actions/audit_action.py | - |
| CAP-126 | Test Speed Optimization | keep | keep | - | .github/workflows/workflow.yml | - |
| CAP-131 | Anthropic Prompt Caching Support | keep | keep | - | examples/demos/prompt-caching/graph.yaml | - |
| CAP-14 | Graph-Level Streaming | keep | keep | - | yamlgraph/cli/graph_commands.py | - |
| CAP-178 | Novel Fandom Prose and Close Loop | keep | keep | - | examples/novel_fandom/close.yaml | - |
| CAP-184 | Novel Fandom Duplicate Entity Prevention | keep | keep | - | examples/novel_fandom/nodes/persist_genesis.py | - |
| CAP-198 | Persistent Bridge Loop | keep | keep | - | yamlgraph/node_factory/__init__.py | - |
| CAP-201 | Pre-emptive Module Splits | keep | keep | - | yamlgraph/executor_async.py | - |
| CAP-203 | ICPC-2 RFE Classifier Example | keep | keep | - | examples/icpc-2-rfe/graph.yaml | - |
| CAP-209 | Root Package Seams | keep | keep | - | yamlgraph/compile/__init__.py | - |
| CAP-219 | Book-Summary Vision Fallback | keep | keep | - | examples/demos/book-summary/tools.py | - |
| CAP-226 | API Discovery Page-Analysis Step | keep | keep | - | examples/api-discovery/steps/page_analysis.tool.yaml | - |
| CAP-232 | API Discovery Browser-Sniff Step | keep | keep | - | examples/api-discovery/steps/browser_sniff.tool.yaml | - |
| CAP-238 | API Discovery Orchestrator v2 — Recon an | keep | keep | - | examples/api-discovery/tools/fetch_page.tool.yaml | - |
| CAP-42 | Inquisitor Worktree Gate | keep | keep | - | .chaplain/inquisitor.sh | - |
| CAP-77 | Image Generation Pipeline | keep | keep | - | yamlgraph/compile/map_compiler.py | - |
| CAP-78 | .fi Domain Crawl Demo | keep | keep | - | examples/demos/fi_domain_crawl/graph.yaml | - |
| CAP-79 | Demo Proof Gate | keep | keep | - | scripts/check_demo_proof.sh | - |
| CAP-84 | Import-Linter Architectural Boundary Enf | keep | keep | - | .github/workflows/commitlint.yml | - |
| CAP-87 | Ruff C901 Cognitive Complexity Gate | keep | keep | - | pyproject.toml | - |

## Value

value_unstated: 0 / 28

| CAP | for whom | pain | versus |
|---|---|---|---|
| CAP-102 | none_internal | Developers no longer encounter ModuleNotFoundError after worktree teardown because the ins | manual diagnosis and repair of broken editable installs afte |
| CAP-108 | govern_process | Maintainers prevent silent traceability drift by validating changelog req: front-matter re | Manual review or no validation gate, allowing cross-wired fr |
| CAP-11 | run_operate | Enables parallel fan-out and nested subgraph execution for scalable workflow orchestration | Manual sequential node execution or external orchestration f |
| CAP-12 | none_internal | Eliminates duplication of logging, templating, JSON extraction, and environment handling a | Reimplementing these utilities in each action or graph modul |
| CAP-126 | none_internal | Developers experience slow test feedback during rapid iteration, with test suite taking ~7 | Running full test suite without selective filtering, forcing |
| CAP-131 | serve_embed | Reduces token costs by 3x for stable context prefixes through Anthropic prompt caching. | Raw Anthropic API without declarative cache control in YAML. |
| CAP-14 | run_operate | CLI users must write Python to access streaming instead of using the YAML-first paradigm w | raw Python scripts or writing custom code to call run_graph_ |
| CAP-142 | serve_embed | Graph authors can publish reusable, agent-discoverable skill bundles directly from YAMLGra | runtime-only interoperability via MCP or A2A server setup |
| CAP-150 | conversational_app | Demonstrates how to build a multi-turn LLM pipeline that uses tool-based search and file I | Raw LangGraph or manual prompt orchestration without integra |
| CAP-153 | run_operate | Schema-driven questionnaire loops can now reuse deterministic gap detection and extraction | Manual gap detection and extraction normalization in each qu |
| CAP-158 | author_graph | Graph authoring reference docs are invisible unless manually read; promoting them to Copil | Manual reading of reference/graph-yaml.md or relying on gene |
| CAP-178 | author_graph | Authors can now close the loop by drafting prose that deterministically updates the dynami | Manual canon updates or prose that drifts from the underlyin |
| CAP-184 | author_graph | Prevents orphan IDs and parallel-invention duplicates from corrupting the novel_fandom kno | Manual post-hoc deduplication or accepting corrupted entity  |
| CAP-198 | run_operate | Eliminates per-call thread churn and fresh-loop SDK reconnects, reducing latency and preve | Per-invocation daemon-thread + asyncio.run() topology with f |
| CAP-201 | none_internal | Preemptive module splits relieve size-gate pressure before unplanned splits occur under de | Unplanned split under deadline pressure when the next featur |
| CAP-203 | author_graph | Clinical teams can author a transparent, reproducible YAMLGraph-based ICPC-2 RFE classifie | manual free-text encounter coding or vendor black-box classi |
| CAP-209 | author_graph | Removes implicit module clusters by enforcing package boundaries via import-linter contrac | Flat 27-module root structure with no enforced seams between |
| CAP-219 | serve_embed | Scanned PDF documents without extractable text can now be summarized via vision fallback i | The prior default behavior (FR-774) which raised ValueError  |
| CAP-226 | integrate | Distinguishing portal pages hosting APIs from plain websites by inspecting HTML source for | Manual inspection or browser-sniff on all HTML responses wit |
| CAP-232 | integrate | Developers can now discover APIs hidden behind client-side rendering in SPAs without manua | Manual page inspection or static analysis that fails on Java |
| CAP-238 | author_graph | Eliminates wrong not_found verdicts by exhausting the orchestrator's own step inventory be | manually re-running recon or browser-sniff as standalone gra |
| CAP-42 | run_operate | Eliminates wasteful Inquisitor audits and API calls on intermediate commits during enforce | Running full audit and propose phases on every worktree comm |
| CAP-77 | author_graph | Graph authors no longer need to manually glue together fragmented image workflow pieces; t | manually chaining batch_image_prompts, file I/O, and zimage- |
| CAP-78 | author_graph | Graph authors lack a reusable crawl-and-summarise pattern combining HTTP tool nodes, map-b | raw LangGraph or custom scripts without structured YAMLGraph |
| CAP-79 | govern_process | Demos ship with syntax errors and broken imports because no gate verifies demos were actua | Manual review or skipping demo execution enforcement entirel |
| CAP-81 | integrate | Graphs can now be exposed as A2A agents without Python glue code, enabling interoperabilit | Raw LangGraph or manual FastAPI/MCP wiring to expose graphs  |
| CAP-84 | govern_process | Architectural layer violations are caught at pre-commit and CI instead of silently degradi | Convention-only enforcement with no mechanical gate, allowin |
| CAP-87 | none_internal | Cognitive complexity violations are caught at commit time instead of in code review or pro | Discovering complexity-driven refactor debt in code review o |

## Blast by journey

### author_graph

```mermaid
graph LR
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m216786[".chaplain/actions/git_commit_action.py"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m706200[".chaplain/graphs/fr_triage/graph.yaml"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m118575[".chaplain/graphs/fr_triage/tools.py"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m768774[".chaplain/graphs/philosopher/prompts/challenge.yaml"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m601842[".chaplain/graphs/watcher-plan/prompts/judge.yaml"]
  CAP-178["CAP-178 Novel Fandom Prose and Close"] --> m285340[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-178["CAP-178 Novel Fandom Prose and Close"] --> m377900[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-178["CAP-178 Novel Fandom Prose and Close"] --> m30804[".chaplain/lib/diary.py"]
  CAP-178["CAP-178 Novel Fandom Prose and Close"] --> m291623[".chaplain/philosopher.sh"]
  CAP-178["CAP-178 Novel Fandom Prose and Close"] --> m720592[".github/hooks/scripts/memory-advisory.sh"]
  CAP-209["CAP-209 Root Package Seams"] --> m619394["examples/beautify/run.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m905891["examples/beautify/tests/test_beautify.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m56944["examples/book_reviewer/tests/test_review.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m305727["examples/book_translator/tests/test_book_translator.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m184117["examples/booking/run_booking.py"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m285340[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m377900[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m30804[".chaplain/lib/diary.py"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m291623[".chaplain/philosopher.sh"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m720592[".github/hooks/scripts/memory-advisory.sh"]
```

### run_operate

```mermaid
graph LR
  CAP-11["CAP-11 Subgraph & Map"] --> m980754["examples/abstraction_span/graph.yaml"]
  CAP-11["CAP-11 Subgraph & Map"] --> m297679["examples/batch_image_prompts/graph.yaml"]
  CAP-11["CAP-11 Subgraph & Map"] --> m86175["examples/book_reviewer/graph.yaml"]
  CAP-11["CAP-11 Subgraph & Map"] --> m339835["examples/book_translator/graph.yaml"]
  CAP-11["CAP-11 Subgraph & Map"] --> m14714["examples/codegen/impl-agent.yaml"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m55214["examples/booking/api/app.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m121197["examples/booking/main.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m383854["examples/demos/hello/demo_cache.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m246305["examples/discord_bot/bot.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m512589["examples/ebook/prompts/chapter/wizard.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m465703[".chaplain/inquisitor.sh"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m53999[".chaplain/lib/watcher/project_contract.py"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m192856[".pre-commit-config.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m694077["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m14447["examples/demos/judge/prompts/judge.yaml"]
  CAP-198["CAP-198 Persistent Bridge Loop"] --> m7965["examples/demos/image-that-speaks/graph.yaml"]
  CAP-198["CAP-198 Persistent Bridge Loop"] --> m139268["examples/demos/race/graph.yaml"]
  CAP-198["CAP-198 Persistent Bridge Loop"] --> m468378["scripts/fr711_conn_witness.py"]
  CAP-198["CAP-198 Persistent Bridge Loop"] --> m1679["yamlgraph/node_factory/__init__.py"]
  CAP-198["CAP-198 Persistent Bridge Loop"] --> m947143["yamlgraph/node_factory/llm_nodes.py"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m886673[".chaplain/actions/audit_action.py"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m902499[".chaplain/config/watcher-dispatcher.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m696162["examples/ebook/graph-ch04.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m133046["examples/ebook/graph.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m533164["examples/ebook/nodes/writing.py"]
```

### integrate

```mermaid
graph LR
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m285340[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m377900[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m30804[".chaplain/lib/diary.py"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m291623[".chaplain/philosopher.sh"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m720592[".github/hooks/scripts/memory-advisory.sh"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m285340[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m377900[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m30804[".chaplain/lib/diary.py"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m291623[".chaplain/philosopher.sh"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m720592[".github/hooks/scripts/memory-advisory.sh"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m334903["scripts/direct_import_scan.py"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m81370["scripts/example_taxonomy_scan.py"]
```

### serve_embed

```mermaid
graph LR
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m56944["examples/book_reviewer/tests/test_review.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m55214["examples/booking/api/app.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m121197["examples/booking/main.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m977337["examples/codegen/tests/test_dependency_tools.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m359580["examples/codegen/tests/test_plan_discovery_prompt.py"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m285340[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m377900[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m30804[".chaplain/lib/diary.py"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m291623[".chaplain/philosopher.sh"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m720592[".github/hooks/scripts/memory-advisory.sh"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m334903["scripts/direct_import_scan.py"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m81370["scripts/example_taxonomy_scan.py"]
```

### govern_process

```mermaid
graph LR
  CAP-108["CAP-108 Changelog REQ Cross-Validati"] --> m43514["scripts/migrate_capabilities.py"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m465703[".chaplain/inquisitor.sh"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m558077[".github/hooks/tests/test_fr902_retired.py"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m996814[".github/hooks/tests/test_size_gate.py"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m694077["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m407635["examples/dungeon_master/tests/test_module_size.py"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m601842[".chaplain/graphs/watcher-plan/prompts/judge.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m633048[".chaplain/graphs/watcher-plan/prompts/plan.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m916109[".chaplain/graphs/watcher-plan/prompts/summarize.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m30804[".chaplain/lib/diary.py"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m840596[".github/hooks/scripts/checks/fr-checks.sh"]
```

### conversational_app

```mermaid
graph LR
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m465703[".chaplain/inquisitor.sh"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m53999[".chaplain/lib/watcher/project_contract.py"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m192856[".pre-commit-config.yaml"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m694077["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m14447["examples/demos/judge/prompts/judge.yaml"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m216786[".chaplain/actions/git_commit_action.py"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m706200[".chaplain/graphs/fr_triage/graph.yaml"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m118575[".chaplain/graphs/fr_triage/tools.py"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m768774[".chaplain/graphs/philosopher/prompts/challenge.yaml"]
  CAP-158["CAP-158 Copilot Skill Promotion"] --> m601842[".chaplain/graphs/watcher-plan/prompts/judge.yaml"]
```

### none_internal

```mermaid
graph LR
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m308707[".chaplain/lib/worktree.py"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m42153["examples/bugfix/graph.yaml"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m43514["scripts/migrate_capabilities.py"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m950889["scripts/worktree.sh"]
  CAP-12["CAP-12 Utilities"] --> m886673[".chaplain/actions/audit_action.py"]
  CAP-12["CAP-12 Utilities"] --> m442830[".chaplain/actions/bash_context_action.py"]
  CAP-12["CAP-12 Utilities"] --> m414229[".chaplain/actions/changelog_gen_action.py"]
  CAP-12["CAP-12 Utilities"] --> m274949[".chaplain/actions/failure_cleanup_action.py"]
  CAP-12["CAP-12 Utilities"] --> m216786[".chaplain/actions/git_commit_action.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m465703[".chaplain/inquisitor.sh"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m558077[".github/hooks/tests/test_fr902_retired.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m996814[".github/hooks/tests/test_size_gate.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m521060[".github/workflows/workflow.yml"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m192856[".pre-commit-config.yaml"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m55214["examples/booking/api/app.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m121197["examples/booking/main.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m383854["examples/demos/hello/demo_cache.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m246305["examples/discord_bot/bot.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m2581["examples/fastapi_interview.py"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m521060[".github/workflows/workflow.yml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m192856[".pre-commit-config.yaml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m794201["examples/demos/ramp_doctrine/nodes/doctrine_tools.py"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m572722["examples/dependency-taxonomy.yaml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m223141["scripts/check_changelog_release_sync.py"]
```

## Failed / abstained rows

| CAP | status | reason |
|---|---|---|
| CAP-221 | row_failed | journey 'example_only' neither in catalog nor off_catalog:<label> |
| CAP-233 | row_failed | journey 'example_only' neither in catalog nor off_catalog:<label> |
