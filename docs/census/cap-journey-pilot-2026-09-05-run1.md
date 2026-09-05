# CAP Journey Census Ledger

- rows: 30  judged: 25  row_failed: 5  abstained: 0
- model: claude-haiku-4-5  git_sha: a3945008  prompt: judge_cap.v1
- canary misses: 5 — CAP-131: consumer_cited 'examples/demos/prompt-caching/graph.yaml' misses ['llm_factory', 'executor_base', 'prompts']; CAP-203: row_failed (evidence_span is not a substring of the CAP yaml or FR head); CAP-11: journeys ['author_graph'] miss ['run_operate', 'census_classify']; CAP-11: consumer_cited 'yamlgraph/compile/node_compiler.py' misses ['corpus_census', 'diary_census', 'person_profile_census', 'repo_census']; CAP-108: row_failed (evidence_span is not a substring of the CAP yaml or FR head)

## Journey × CAP matrix

| journey | CAPs | keep | extend | retire | contested |
|---|---:|---:|---:|---:|---:|
| author_graph | 6 | 5 | 0 | 0 | 1 |
| run_operate | 4 | 4 | 0 | 0 | 0 |
| debug_observe | 1 | 1 | 0 | 0 | 0 |
| integrate | 5 | 4 | 0 | 0 | 0 |
| serve_embed | 3 | 1 | 0 | 0 | 0 |
| census_classify | 0 | 0 | 0 | 0 | 0 |
| govern_process | 2 | 2 | 0 | 0 | 0 |
| audit_comply | 0 | 0 | 0 | 0 | 0 |
| conversational_app | 0 | 0 | 0 | 0 | 0 |
| none_internal | 5 | 5 | 0 | 0 | 0 |

off-catalog labels: none

## Disposition table

| CAP | name | disposition | effective | extend_to | consumer_cited | anchor violations |
|---|---|---|---|---|---|---|
| CAP-142 | Skill Export Portable Packaging | already_retired | already_retired | - | - | - |
| CAP-81 | A2A Protocol Server | already_retired | already_retired | - | yamlgraph/discovery.py | - |
| CAP-150 | Philosopher's Book Demo | keep | contested | - | examples/demos/philosopher_book/graph.yaml | keep without a consumer from the mechanical list |
| CAP-102 | Complete Worktree Teardown Self-Heal | keep | keep | - | yamlgraph/utils/worktree_helpers.py | - |
| CAP-11 | Subgraph & Map | keep | keep | - | yamlgraph/compile/node_compiler.py | - |
| CAP-12 | Utilities | keep | keep | - | .chaplain/actions/audit_action.py | - |
| CAP-126 | Test Speed Optimization | keep | keep | - | .github/workflows/workflow.yml | - |
| CAP-131 | Anthropic Prompt Caching Support | keep | keep | - | examples/demos/prompt-caching/graph.yaml | - |
| CAP-14 | Graph-Level Streaming | keep | keep | - | yamlgraph/cli/graph_commands.py | - |
| CAP-153 | Built-in Questionnaire Gap Utilities | keep | keep | - | examples/demos/enforcer/prompts/enforcer.yaml | - |
| CAP-184 | Novel Fandom Duplicate Entity Prevention | keep | keep | - | examples/novel_fandom/nodes/persist_genesis.py | - |
| CAP-201 | Pre-emptive Module Splits | keep | keep | - | yamlgraph/executor_async.py | - |
| CAP-209 | Root Package Seams | keep | keep | - | yamlgraph/compile/__init__.py | - |
| CAP-219 | Book-Summary Vision Fallback | keep | keep | - | examples/demos/book-summary/tools.py | - |
| CAP-221 | Demo Graph Binding Hygiene and Grounded  | keep | keep | - | .chaplain/graphs/philosopher/graph.yaml | - |
| CAP-226 | API Discovery Page-Analysis Step | keep | keep | - | examples/api-discovery/steps/page_analysis.tool.yaml | - |
| CAP-232 | API Discovery Browser-Sniff Step | keep | keep | - | examples/api-discovery/steps/browser_sniff.tool.yaml | - |
| CAP-233 | API Discovery Schema-Extract Step | keep | keep | - | examples/api-discovery/steps/schema_extract.tool.yaml | - |
| CAP-238 | API Discovery Orchestrator v2 — Recon an | keep | keep | - | examples/api-discovery/tools/fetch_page.tool.yaml | - |
| CAP-42 | Inquisitor Worktree Gate | keep | keep | - | .chaplain/inquisitor.sh | - |
| CAP-77 | Image Generation Pipeline | keep | keep | - | yamlgraph/compile/map_compiler.py | - |
| CAP-78 | .fi Domain Crawl Demo | keep | keep | - | examples/demos/fi_domain_crawl/graph.yaml | - |
| CAP-79 | Demo Proof Gate | keep | keep | - | scripts/check_demo_proof.sh | - |
| CAP-84 | Import-Linter Architectural Boundary Enf | keep | keep | - | .chaplain/graphs/watcher-plan/prompts/judge.yaml | - |
| CAP-87 | Ruff C901 Cognitive Complexity Gate | keep | keep | - | pyproject.toml | - |

## Value

value_unstated: 0 / 25

| CAP | for whom | pain | versus |
|---|---|---|---|
| CAP-102 | none_internal | Developers no longer encounter ModuleNotFoundError after worktree teardown because the ins | manual diagnosis and repair of broken editable installs afte |
| CAP-11 | author_graph | Enables graph authors to compose parallel fan-out and nested subgraph execution patterns w | Raw LangGraph node composition or manual subgraph orchestrat |
| CAP-12 | none_internal | Provides shared logging, templating, JSON extraction, and configuration utilities that int | Duplicating these utilities across each consumer or using ad |
| CAP-126 | none_internal | Developers experience slow test feedback during rapid iteration, with test suite taking ~7 | Running the full test suite without selective filtering, tak |
| CAP-131 | run_operate | Reduces token costs by 3x for stable context prefixes through Anthropic prompt caching. | Manual prompt engineering or vendor-specific caching APIs wi |
| CAP-14 | run_operate | CLI users must write Python to access streaming instead of using the YAML-first paradigm w | raw Python scripts or writing custom code to call run_graph_ |
| CAP-142 | serve_embed | Graph authors can publish reusable, agent-discoverable skill bundles directly from YAMLGra | runtime-only interoperability via MCP or A2A server setup |
| CAP-150 | author_graph | Demonstrates how to author a multi-stage LLM pipeline using YAMLGraph with tool integratio | Raw LangGraph or manual orchestration without declarative gr |
| CAP-153 | run_operate | FSM pipeline operators avoid silent routing misconfigurations by catching invalid event_ma | manual validation scripts or silent failures propagating thr |
| CAP-184 | author_graph | Prevents orphan IDs and parallel-invention duplicates from corrupting the novel_fandom kno | Manual post-hoc deduplication or accepting corrupted entity  |
| CAP-201 | none_internal | Preemptive module splits relieve size-gate pressure before unplanned splits occur under de | Unplanned split under deadline pressure when the next featur |
| CAP-209 | author_graph | Eliminates implicit module clusters and enforces architectural seams via import-linter con | Flat 27-module root package with no enforced boundaries betw |
| CAP-219 | serve_embed | Scanned PDF documents without extractable text now receive summaries instead of a refusal  | The prior loud failure (ValueError: no extractable text … vi |
| CAP-221 | debug_observe | Prevents silent variable binding failures and fabrication from empty findings in demo grap | Unguarded demo graphs that silently produce plausible but fa |
| CAP-226 | integrate | Developers can distinguish portal pages hosting APIs from plain websites by inspecting HTM | Manual page inspection or browser-sniff on every HTML respon |
| CAP-232 | integrate | Developers can now discover APIs hidden behind client-side rendering in SPAs without manua | Manual page inspection or static analysis that fails on Java |
| CAP-233 | integrate | Eliminates manual schema parsing and capability extraction by providing a routed LLM graph | Manual parsing scripts or vendor-specific adapters for each  |
| CAP-238 | integrate | Verdicts that are wrong only because the router never consulted evidence the pipeline alre | manually re-running recon or browser-sniff as standalone gra |
| CAP-42 | run_operate | Eliminates wasteful Inquisitor audits and API calls on intermediate commits during enforce | Running full audit and propose phases on every worktree comm |
| CAP-77 | author_graph | Graph authors no longer need to manually glue together fragmented image workflow pieces; t | manually chaining batch_image_prompts, file I/O, and zimage- |
| CAP-78 | author_graph | Graph authors lack a reusable crawl-and-summarise pattern combining HTTP tool nodes, map-b | raw LangGraph or custom scripts without structured YAMLGraph |
| CAP-79 | govern_process | Demos ship with syntax errors and broken imports because no proof of execution is committe | Manual review or skipped demo validation (~99% of the time). |
| CAP-81 | integrate | Graphs can now be exposed as A2A agents without Python glue code, enabling interoperabilit | Raw LangGraph or manual FastAPI/MCP wiring to expose graphs  |
| CAP-84 | govern_process | Prevents silent degradation of module boundaries by mechanically enforcing declared layer  | Convention-only enforcement documented in ARCHITECTURE.md bu |
| CAP-87 | none_internal | Cognitive complexity violations are caught at commit time instead of in code review or pro | Discovering complexity-driven refactor debt in code review o |

## Blast by journey

### author_graph

```mermaid
graph LR
  CAP-11["CAP-11 Subgraph & Map"] --> m236130["examples/ebook/prompts/chapter/wizard.yaml"]
  CAP-11["CAP-11 Subgraph & Map"] --> m919844["scripts/demo_coverage.sh"]
  CAP-11["CAP-11 Subgraph & Map"] --> m45799["yamlgraph/compile/graph_loader.py"]
  CAP-11["CAP-11 Subgraph & Map"] --> m63517["yamlgraph/compile/node_compiler.py"]
  CAP-11["CAP-11 Subgraph & Map"] --> m874918["yamlgraph/node_factory/__init__.py"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m576369[".chaplain/inquisitor.sh"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m923801[".chaplain/lib/watcher/project_contract.py"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m758553[".pre-commit-config.yaml"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m122028["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-150["CAP-150 Philosopher's Book Demo"] --> m353386["examples/demos/judge/prompts/judge.yaml"]
  CAP-209["CAP-209 Root Package Seams"] --> m428716["examples/beautify/run.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m735303["examples/beautify/tests/test_beautify.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m206116["examples/book_reviewer/tests/test_review.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m533065["examples/book_translator/tests/test_book_translator.py"]
  CAP-209["CAP-209 Root Package Seams"] --> m604633["examples/booking/run_booking.py"]
```

### run_operate

```mermaid
graph LR
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m206116["examples/book_reviewer/tests/test_review.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m399615["examples/booking/api/app.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m968265["examples/booking/main.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m651188["examples/codegen/tests/test_dependency_tools.py"]
  CAP-131["CAP-131 Anthropic Prompt Caching Sup"] --> m103977["examples/codegen/tests/test_plan_discovery_prompt.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m399615["examples/booking/api/app.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m968265["examples/booking/main.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m288126["examples/demos/hello/demo_cache.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m9771["examples/discord_bot/bot.py"]
  CAP-14["CAP-14 Graph-Level Streaming"] --> m236130["examples/ebook/prompts/chapter/wizard.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m576369[".chaplain/inquisitor.sh"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m923801[".chaplain/lib/watcher/project_contract.py"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m758553[".pre-commit-config.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m122028["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-153["CAP-153 Built-in Questionnaire Gap U"] --> m353386["examples/demos/judge/prompts/judge.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m393793[".chaplain/actions/audit_action.py"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m313932[".chaplain/config/watcher-dispatcher.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m796126["examples/ebook/graph-ch04.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m646519["examples/ebook/graph.yaml"]
  CAP-42["CAP-42 Inquisitor Worktree Gate"] --> m371952["examples/ebook/nodes/writing.py"]
```

### debug_observe

```mermaid
graph LR
  CAP-221["CAP-221 Demo Graph Binding Hygiene a"] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-221["CAP-221 Demo Graph Binding Hygiene a"] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-221["CAP-221 Demo Graph Binding Hygiene a"] --> m753774[".chaplain/lib/diary.py"]
  CAP-221["CAP-221 Demo Graph Binding Hygiene a"] --> m828721[".chaplain/philosopher.sh"]
  CAP-221["CAP-221 Demo Graph Binding Hygiene a"] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
```

### integrate

```mermaid
graph LR
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m753774[".chaplain/lib/diary.py"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m828721[".chaplain/philosopher.sh"]
  CAP-226["CAP-226 API Discovery Page-Analysis "] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m753774[".chaplain/lib/diary.py"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m828721[".chaplain/philosopher.sh"]
  CAP-232["CAP-232 API Discovery Browser-Sniff "] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
  CAP-233["CAP-233 API Discovery Schema-Extract"] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-233["CAP-233 API Discovery Schema-Extract"] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-233["CAP-233 API Discovery Schema-Extract"] --> m753774[".chaplain/lib/diary.py"]
  CAP-233["CAP-233 API Discovery Schema-Extract"] --> m828721[".chaplain/philosopher.sh"]
  CAP-233["CAP-233 API Discovery Schema-Extract"] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m753774[".chaplain/lib/diary.py"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m828721[".chaplain/philosopher.sh"]
  CAP-238["CAP-238 API Discovery Orchestrator v"] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m200938["scripts/direct_import_scan.py"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m865080["scripts/example_taxonomy_scan.py"]
```

### serve_embed

```mermaid
graph LR
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m395396[".chaplain/graphs/philosopher/graph.yaml"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m896596[".chaplain/graphs/watcher-plan/prompts/research.yaml"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m753774[".chaplain/lib/diary.py"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m828721[".chaplain/philosopher.sh"]
  CAP-219["CAP-219 Book-Summary Vision Fallback"] --> m536663[".github/hooks/scripts/memory-advisory.sh"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m200938["scripts/direct_import_scan.py"]
  CAP-81["CAP-81 A2A Protocol Server"] --> m865080["scripts/example_taxonomy_scan.py"]
```

### govern_process

```mermaid
graph LR
  CAP-79["CAP-79 Demo Proof Gate"] --> m576369[".chaplain/inquisitor.sh"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m677977[".github/hooks/tests/test_fr902_retired.py"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m602049[".github/hooks/tests/test_size_gate.py"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m122028["examples/demos/enforcer/prompts/enforcer.yaml"]
  CAP-79["CAP-79 Demo Proof Gate"] --> m701668["examples/dungeon_master/tests/test_module_size.py"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m704024[".chaplain/graphs/watcher-plan/prompts/judge.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m889234[".chaplain/graphs/watcher-plan/prompts/plan.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m824527[".chaplain/graphs/watcher-plan/prompts/summarize.yaml"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m753774[".chaplain/lib/diary.py"]
  CAP-84["CAP-84 Import-Linter Architectural "] --> m927509[".github/hooks/scripts/checks/fr-checks.sh"]
```

### none_internal

```mermaid
graph LR
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m600125[".chaplain/lib/worktree.py"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m969753["examples/bugfix/graph.yaml"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m507460["scripts/migrate_capabilities.py"]
  CAP-102["CAP-102 Complete Worktree Teardown S"] --> m475863["scripts/worktree.sh"]
  CAP-12["CAP-12 Utilities"] --> m393793[".chaplain/actions/audit_action.py"]
  CAP-12["CAP-12 Utilities"] --> m302992[".chaplain/actions/bash_context_action.py"]
  CAP-12["CAP-12 Utilities"] --> m451625[".chaplain/actions/changelog_gen_action.py"]
  CAP-12["CAP-12 Utilities"] --> m205670[".chaplain/actions/failure_cleanup_action.py"]
  CAP-12["CAP-12 Utilities"] --> m472363[".chaplain/actions/git_commit_action.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m576369[".chaplain/inquisitor.sh"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m677977[".github/hooks/tests/test_fr902_retired.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m602049[".github/hooks/tests/test_size_gate.py"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m349686[".github/workflows/workflow.yml"]
  CAP-126["CAP-126 Test Speed Optimization"] --> m758553[".pre-commit-config.yaml"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m399615["examples/booking/api/app.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m968265["examples/booking/main.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m288126["examples/demos/hello/demo_cache.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m9771["examples/discord_bot/bot.py"]
  CAP-201["CAP-201 Pre-emptive Module Splits"] --> m864950["examples/fastapi_interview.py"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m349686[".github/workflows/workflow.yml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m758553[".pre-commit-config.yaml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m877478["examples/demos/ramp_doctrine/nodes/doctrine_tools.py"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m250454["examples/dependency-taxonomy.yaml"]
  CAP-87["CAP-87 Ruff C901 Cognitive Complexi"] --> m679559["scripts/check_changelog_release_sync.py"]
```

## Failed / abstained rows

| CAP | status | reason |
|---|---|---|
| CAP-108 | row_failed | evidence_span is not a substring of the CAP yaml or FR head |
| CAP-158 | row_failed | evidence_span is not a substring of the CAP yaml or FR head |
| CAP-178 | row_failed | journey 'example_only' neither in catalog nor off_catalog:<label> |
| CAP-198 | row_failed | evidence_span is not a substring of the CAP yaml or FR head |
| CAP-203 | row_failed | evidence_span is not a substring of the CAP yaml or FR head |
