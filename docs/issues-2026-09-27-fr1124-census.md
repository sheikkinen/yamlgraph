# FR-1124 census ledger — top-level `llm` nodes without `on_error` (2026-09-27)

Governing FR: [FR-1124](../feature-requests/FR-1124-llm-node-default-on-error.md), S-5.

## Method

- **Inventory:** `python scripts/fr1124_inventory.py` at `bd2c04f0` (GREEN + docs). Roots are `examples/`, `graphs/` and `.github/`. It excludes every path under a `prompts/` directory. An eligible node is a top-level node whose declared or default type is `llm` and that has no `on_error`. Map sub-nodes are nested, so they are never top-level. **Discovered: 224 nodes in 134 graph files. That equals the filing baseline of 224, so there is no difference to reconcile.**
- **Census (proposes the class):** `examples/demos/corpus_census/graph.yaml` is the shared FR-892 census; FR-1120's `cap_journey_census` has the same extract → judge → reduce shape. The slots are bound with `scripts/fr1124_census/{discover,extract}.tool.yaml`, the rubric is `scripts/fr1124_census/rubric.md`, and `labels=["a","b"]`. The model is `inception/mercury-2`, because the Anthropic key in `.env` returned 401. The run used two slices, `0:112` and `112:224`, since the census map caps at 200 items. Raw output: 199 `a`, 20 `b` or abstain (5 abstained, 0 row failures).
- **Reconciliation (decides the class):** every `b` and every abstain was checked against the graph source. 17 of the claims rested on the dossier's `NODES_REFERENCING_STATE_KEY: none`. That scan cannot see python-node readers, so each of those became A with a reason given in its row. The six `novel_fandom/create_*` `check` nodes are identical: same prompt `ref_check_entity`, same position after `persist`, same `-> END`. The census split them 3 `b` / 3 `a`. All six are B, on the evidence of the prompt's own "advisory" header.
- **Mechanical check:** `python scripts/fr1124_inventory.py --check docs/issues-2026-09-27-fr1124-census.md` asserts that the ledger's identity set equals the inventory's, with no duplicates, omissions or unknowns.

## Counts

| Class | Nodes | Resulting policy |
|---|---:|---|
| A: adopts the new `fail` default | 218 | no graph edit |
| B: advisory, tolerated continuation | 6 | explicit node `on_error: skip` (brief `feature-requests/authoring-briefs/fr-1124-novel-fandom-advisory-check-brief.md`) |
| **Total** | **224** | |

## Ledger

| graph | node | state_key | downstream (edges out) | class | evidence | resulting policy |
|---|---|---|---|---|---|---|
| `examples/batch_image_prompts/graph.yaml` | `decompose` | `scenes` | -> enrich | A | census `over: "{state.scenes.briefs}"` | fail (default) |
| `examples/beautify/graph.yaml` | `analyze` | `analysis` | -> mermaid | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/beautify/graph.yaml` | `mermaid` | `mermaid_code` | -> render_html | A | census `- from: mermaid     to: render_html` | fail (default) |
| `examples/book_reviewer/graph.yaml` | `synopsis_beats` | `synopsis_beats` | -> compute | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: edge `-> compute`; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/book_reviewer/graph.yaml` | `verdict` | `verdict` | -> finalize | A | census `Attach verdict, write review.md` | fail (default) |
| `examples/book_translator/graph.yaml` | `identify_chapters` | `chapter_markers` | -> split_book | A | census `description: "Split text using LLM-identified markers"` | fail (default) |
| `examples/booking/graph.yaml` | `greet` | `greeting` | -> await_request | A | census `message: "{{greeting}}"` | fail (default) |
| `examples/booking/graph.yaml` | `present_slots` | `slots_response` | -> await_selection | A | census `message: "{{slots_response}}"` | fail (default) |
| `examples/booking/graph.yaml` | `farewell` | `confirmation` | -> END | A | census `- from: farewell     to: END` | fail (default) |
| `examples/codegen/impl-agent.yaml` | `parse_story` | `parsed_request` | -> plan_discovery | A | census `requires: [parsed_request]` | fail (default) |
| `examples/codegen/impl-agent.yaml` | `plan_discovery` | `discovery_plan` | -> execute_discovery | A | census `NODES_REFERENCING_STATE_KEY: ['execute_discovery']` | fail (default) |
| `examples/codegen/impl-agent.yaml` | `synthesize` | `code_analysis` | -> plan | A | census `requires: [parsed_request, code_analysis]` | fail (default) |
| `examples/codegen/impl-agent.yaml` | `plan` | `implementation_plan` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/cost-router/cost-router.yaml` | `classify` | `classification` | classification.complexity == 'simple' -> route_simple, classification.complexity == 'medium' -> route_medium, classification.complexity == 'complex' -> route_complex | A | census `"classification.complexity == 'simple'"` | fail (default) |
| `examples/cost-router/cost-router.yaml` | `route_simple` | `result` | -> log_simple | A | census `- from: route_simple     to: log_simple` | fail (default) |
| `examples/cost-router/cost-router.yaml` | `route_medium` | `result` | -> log_medium | A | census `edges: - from: route_medium to: log_medium` | fail (default) |
| `examples/cost-router/cost-router.yaml` | `route_complex` | `result` | -> log_complex | A | census `NODES_REFERENCING_STATE_KEY: ['route_simple', 'route_medium']` (census said `b`; reconciled: `result` is the graph's answer for the complex route; no absence handling) | fail (default) |
| `examples/daily_digest/graph.yaml` | `rank_stories` | `ranked_stories` | -> format_email | A | census `- from: rank_stories     to: format_email` | fail (default) |
| `examples/demos/book-summary/graph.yaml` | `combine` | `book_summary` | -> END | A | census `- from: combine     to: END` | fail (default) |
| `examples/demos/cache/graph.yaml` | `summarize` | `summary` | -> expand | A | census `summary: "{state.summary}"` | fail (default) |
| `examples/demos/cache/graph.yaml` | `expand` | `expansion` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/chinese-horoscope/graph.yaml` | `assemble` | `document` | -> save | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/code-analysis/graph.yaml` | `generate_recommendations` | `recommendations` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/compaction/graph.yaml` | `generate_turn` | `history` | -> count_tokens | A | census `- from: generate_turn     to: count_tokens` | fail (default) |
| `examples/demos/compaction/graph.yaml` | `compact` | `history` | state._loop_counts.generate_turn < 6 -> generate_turn, state._loop_counts.generate_turn >= 6 -> END | A | census `NODES_REFERENCING_STATE_KEY: ['generate_turn', 'count_tokens']` | fail (default) |
| `examples/demos/corpus_census/graph.yaml` | `synthesize` | `claims` | -> render_brief | A | census `synthesize:     type: llm     prompt: synthesize_brief     provider: "{state.brief_llm.pro` | fail (default) |
| `examples/demos/data-files/graph.yaml` | `extract` | `extracted` | -> summarize | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/data-files/graph.yaml` | `summarize` | `summary` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/fan-out/graph.yaml` | `generate` | `content` | -> ['analyze', 'summarize', 'translate'] | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: `content` feeds the analyze/summarize/translate prompts; the fan-out has nothing to work on without it) | fail (default) |
| `examples/demos/fan-out/graph.yaml` | `analyze` | `analysis` | -> combine | A | census abstained; no tolerance evidence in graph (census said `abstain`; reconciled: edge `-> combine`; no absence handling) | fail (default) |
| `examples/demos/fan-out/graph.yaml` | `summarize` | `summary` | -> combine | A | census `- from: summarize     to: combine` | fail (default) |
| `examples/demos/fan-out/graph.yaml` | `translate` | `translation` | -> combine | A | census `- from: translate     to: combine` | fail (default) |
| `examples/demos/fan-out/graph.yaml` | `combine` | `result` | -> END | A | census `- from: combine     to: END` | fail (default) |
| `examples/demos/feature-brainstorm/graph.yaml` | `brainstorm` | `ideas` | -> prioritize | A | census `ideas: ideas` | fail (default) |
| `examples/demos/feature-brainstorm/graph.yaml` | `prioritize` | `roadmap` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/fi_domain_crawl/graph.yaml` | `plan` | `search_queries` | -> discover | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: edge `-> discover`; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/demos/fi_domain_crawl/graph.yaml` | `summarise` | `sitemap_overview` | -> END | A | census `sitemap_overview:     format: markdown     filename: sitemap_overview.md` | fail (default) |
| `examples/demos/five-whys/graph.yaml` | `ask_why` | `ask_why` | _loop_counts.ask_why < 5 -> ask_why, _loop_counts.ask_why >= 5 -> summarise | A | census `analysis: "{state.ask_why}"` | fail (default) |
| `examples/demos/five-whys/graph.yaml` | `summarise` | `summary` | -> END | A | census `exports:   summary:     format: markdown     filename: root_cause_analysis.md` | fail (default) |
| `examples/demos/forensic-failure-diary/graph.yaml` | `forensic_analysis` | `forensic_report` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/fr-atlas/graph.yaml` | `merge_themes` | `merged` | -> finalize | A | census `Key-join merge output to FR ids, enforce coverage (count-in == count-out), attach module a` | fail (default) |
| `examples/demos/fr-atlas/graph.yaml` | `story_opener` | `story` | -> render | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/git-report/graph.yaml` | `report` | `report` | -> END | A | census `EDGES_OUT: ['-> END']` | fail (default) |
| `examples/demos/graph-tool/child/graph.yaml` | `classify` | `tone` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/guards/graph.yaml` | `guarded_generate` | `result` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hello/graph.yaml` | `greet` | `greeting` | -> notify | A | census `message: "{state.greeting.greeting}"` | fail (default) |
| `examples/demos/hello-runpod/graph.yaml` | `greet` | `greeting` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hellograph-speed/graph.azure.yaml` | `greet` | `greeting` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hellograph-speed/graph.google.yaml` | `greet` | `greeting` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hellograph-speed/graph.vertex.yaml` | `greet` | `greeting` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hook_classifier/graph.yaml` | `classify` | `classification` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/hook_classifier/graphs/classify-intent.yaml` | `classify` | `classification` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/horoscope/graph.yaml` | `assemble` | `document` | -> save | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/image-that-speaks/graph.yaml` | `beast_speaks` | `beast_output` | -> ['image_judges', 'the_law'] | A | census `beast_output: "{state.beast_output}"` | fail (default) |
| `examples/demos/image-that-speaks/graph.yaml` | `reckoning` | `final_reckoning` | -> verdict | A | census `- from: reckoning     to: verdict` | fail (default) |
| `examples/demos/image-that-speaks/graph.yaml` | `verdict` | `final_verdict` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/innovation_matrix/drill-down.yaml` | `expand` | `expansion` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/innovation_matrix/graph.yaml` | `generate` | `matrix` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/innovation_matrix/pipeline.yaml` | `generate_dimensions` | `dimensions` | -> cartesian | A | census abstained; no tolerance evidence in graph (census said `abstain`; reconciled: edge `-> cartesian`; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/demos/innovation_matrix/pipeline.yaml` | `synthesize` | `top_ideas` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/interview/graph.yaml` | `generate_welcome` | `welcome_message` | -> ask_name | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/interview/graph.yaml` | `generate_response` | `greeting` | -> END | A | census `# The graph asks the user questions and generates a personalized greeting.` | fail (default) |
| `examples/demos/map/graph.yaml` | `generate` | `ideas` | -> expand | A | census `over: "{state.ideas.ideas}"` | fail (default) |
| `examples/demos/map/graph.yaml` | `summarize` | `summary` | -> END | A | census `to: END` | fail (default) |
| `examples/demos/meta/graph.yaml` | `transform` | `result` | -> END | A | census `# Apply the verb to the source and return typed MetaResult` | fail (default) |
| `examples/demos/meta_map/graph.yaml` | `reduce` | `overall` | -> render | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: edge `-> render`; `overall` is the product; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/demos/multi-turn/graph.yaml` | `respond` | `response` | -> wait_for_user | A | census `subsequent turns stream response` | fail (default) |
| `examples/demos/multi-turn/guard.yaml` | `classify` | `intent` | -> END | A | census `Returns intent: "continue" \| "stop"` | fail (default) |
| `examples/demos/person_profile_census/gh-profiler.yaml` | `synthesize` | `claims` | -> render_brief | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/person_profile_census/graph.yaml` | `synthesize` | `claims` | -> render_brief | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/persona_scenarios/graph.yaml` | `analyze_product` | `product_analysis` | -> generate_personas | A | census `over: "{state.product_analysis.target_segments}"` | fail (default) |
| `examples/demos/philosopher_book/editorial_graph.yaml` | `build_editorial_brief` | `editorial_brief` | -> edit_chapters | A | census `editorial_brief: "{state.editorial_brief}"` | fail (default) |
| `examples/demos/pipeline_audit/graph.yaml` | `analyze` | `analysis` | -> recommend | A | census `requires: [inventory, analysis]` | fail (default) |
| `examples/demos/pipeline_audit/graph.yaml` | `recommend` | `recommendations` | -> END | A | census `- from: recommend     to: END` | fail (default) |
| `examples/demos/prompt-caching/graph.yaml` | `analyze` | `analysis` | -> reflect | A | census `analysis: "{state.analysis}"` | fail (default) |
| `examples/demos/prompt-caching/graph.yaml` | `reflect` | `reflection` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/prompt_theme_analyzer/graph.yaml` | `group_themes` | `theme_groups` | -> write_report | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/promptfoo-router/graph.yaml` | `respond_positive` | `response` | -> END | A | census `- from: respond_positive     to: END` | fail (default) |
| `examples/demos/promptfoo-router/graph.yaml` | `respond_negative` | `response` | -> END | A | census `- from: respond_negative     to: END` | fail (default) |
| `examples/demos/promptfoo-router/graph.yaml` | `respond_neutral` | `response` | -> END | A | census `- from: respond_neutral     to: END` | fail (default) |
| `examples/demos/recap/graph.yaml` | `synthesize` | `recap` | -> finalize_recap | A | census `requires: [recap, fr_statuses, unreferenced]` | fail (default) |
| `examples/demos/reflexion/graph.yaml` | `draft` | `current_draft` | -> critique | A | census `content: "{state.current_draft.content}"` | fail (default) |
| `examples/demos/reflexion/graph.yaml` | `critique` | `critique` | critique.score < 0.8 -> refine, critique.score >= 0.8 -> END | A | census `feedback: "{state.critique.feedback}"` | fail (default) |
| `examples/demos/reflexion/graph.yaml` | `refine` | `current_draft` | -> critique | A | census `content: "{state.current_draft.content}"` | fail (default) |
| `examples/demos/repo_census/graph.yaml` | `synthesize` | `claims` | -> render_brief | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/req-cross-check/graph.yaml` | `report` | `traceability_report` | -> END | A | census `description: Run architecture cross-check and produce traceability report (FR-107)` | fail (default) |
| `examples/demos/research-agent/graph.yaml` | `extract_intent` | `intent` | -> plan_research | A | census `requires: [intent]` | fail (default) |
| `examples/demos/research-agent/graph.yaml` | `validate_findings` | `validation` | validation.confidence == 'low' or findings == '' -> END, validation.confidence != 'low' and findings != '' -> synthesize_report | A | census `validation.confidence == 'low' or findings == '' -> END` | fail (default) |
| `examples/demos/research-agent/graph.yaml` | `synthesize_report` | `report` | -> END | A | census `- from: synthesize_report     to: END` | fail (default) |
| `examples/demos/router/graph.yaml` | `respond_positive` | `response` | -> END | A | census `- from: respond_positive     to: END` | fail (default) |
| `examples/demos/router/graph.yaml` | `respond_negative` | `response` | -> END | A | census `- from: respond_negative     to: END` | fail (default) |
| `examples/demos/router/graph.yaml` | `respond_neutral` | `response` | -> END | A | census `- from: respond_neutral     to: END` | fail (default) |
| `examples/demos/run-analyzer/graph.yaml` | `analyze_issues` | `analysis` | -> recommend | A | census `requires: [run_info, analysis]` | fail (default) |
| `examples/demos/run-analyzer/graph.yaml` | `recommend` | `recommendations` | -> END | A | census `description: Analyze a previous run for issues and provide recommendations` | fail (default) |
| `examples/demos/safety-guards/graph.yaml` | `draft` | `current_draft` | -> review | A | census `content: "{state.current_draft}"` | fail (default) |
| `examples/demos/safety-guards/graph.yaml` | `review` | `review` | review.score < 0.8 -> revise, review.score >= 0.8 -> expand | A | census `feedback: "{state.review}"` | fail (default) |
| `examples/demos/safety-guards/graph.yaml` | `revise` | `current_draft` | -> review | A | census `content: "{state.current_draft}"` | fail (default) |
| `examples/demos/self-portrait/graph.yaml` | `synthesize` | `portrait` | -> render | A | census `- from: synthesize     to: render` | fail (default) |
| `examples/demos/soul/graph.yaml` | `respond` | `response` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/streaming/graph.yaml` | `draft` | `draft_text` | -> polish | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/streaming/graph.yaml` | `polish` | `final_text` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/subgraph/graph.yaml` | `prepare` | `prepared_text` | -> summarize | A | census `input_mapping:       prepared_text: input_text` | fail (default) |
| `examples/demos/subgraph/graph.yaml` | `format` | `final_output` | -> END | A | census `edges:   - from: format     to: END` | fail (default) |
| `examples/demos/subgraph/subgraphs/summarizer.yaml` | `summarize` | `output_summary` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/system-status/graph.yaml` | `analyze` | `diagnosis` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/tavily_rag/graph-deep.yaml` | `plan` | `sub_queries` | -> retrieve | A | census `over: "{state.sub_queries}"` | fail (default) |
| `examples/demos/tavily_rag/graph-deep.yaml` | `synthesize` | `answer` | -> END | A | census `edges:   - from: synthesize     to: END` | fail (default) |
| `examples/demos/tavily_rag/graph.yaml` | `answer` | `answer` | -> END | A | census `edges:   - from: answer     to: END` | fail (default) |
| `examples/demos/thinking/graph.yaml` | `deep_analysis` | `analysis` | -> quick_response | A | census `analysis: "{state.analysis}"` | fail (default) |
| `examples/demos/thinking/graph.yaml` | `quick_response` | `response` | -> END | A | census `EDGES_OUT: ['-> END']` | fail (default) |
| `examples/demos/verification-gate/graph.yaml` | `generate_points` | `key_points` | -> summarize | A | census `key_points: "{state.key_points}"` | fail (default) |
| `examples/demos/verification-gate/graph.yaml` | `summarize` | `summary` | -> END | A | census `verification:       question: Will return non-empty       on_fail: halt` | fail (default) |
| `examples/demos/verified-search/graph.yaml` | `report` | `report` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/web-research/graph.yaml` | `summarize` | `summary` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/demos/wiki-memory/graph.yaml` | `draft` | `drafted_page` | -> gate | A | census `data: "{state.drafted_page}"` | fail (default) |
| `examples/demos/wiki-memory/graph.yaml` | `fix` | `drafted_page` | -> gate | A | census `persist: variables: data: "{state.drafted_page}"` | fail (default) |
| `examples/demos/write_data_file/graph.yaml` | `compress` | `updated_wiki` | -> persist | A | census `NODES_REFERENCING_STATE_KEY: ['persist']` | fail (default) |
| `examples/demos/yamlgraph/graph.yaml` | `analyze` | `analysis` | -> summarize | A | census `requires: [generated, analysis]` | fail (default) |
| `examples/demos/yamlgraph/graph.yaml` | `summarize` | `final_summary` | -> END | A | census `edges:   - from: summarize     to: END` | fail (default) |
| `examples/diary_digest/graph.yaml` | `synthesize_entry` | `diary_entry` | -> write_diary | A | census `- from: synthesize_entry     to: write_diary` | fail (default) |
| `examples/diary_digest/graph.yaml` | `curate_seeds` | `seeds` | -> save_seeds | A | census `NODES_REFERENCING_STATE_KEY: ['synthesize_entry']` (census said `b`; reconciled: edge `-> save_seeds`; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/dungeon_master/chapter_close.yaml` | `chapter_close` | `chapter_close` | -> END | A | census `Output is STRUCTURED (parse_json: true): a {world_state, seam_packet} object.` | fail (default) |
| `examples/dungeon_master/chapter_outline.yaml` | `outline` | `outline` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/dungeon_master/chapter_reoutline.yaml` | `reoutline` | `reoutline` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/dungeon_master/character.yaml` | `character` | `character` | -> END | A | census `description: Weave one character from a synopsis + name + draft + instruction` | fail (default) |
| `examples/dungeon_master/character_roster.yaml` | `roster` | `roster` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/dungeon_master/final_cut.yaml` | `final_cut` | `final_cut` | -> END | A | census `A terminal leaf` | fail (default) |
| `examples/dungeon_master/plot_plan.yaml` | `author_plan` | `plan_raw` | -> validate_plan | A | census `raw: "{state.plan_raw}"` | fail (default) |
| `examples/dungeon_master/plot_plan.yaml` | `repair_plan` | `plan_raw` | -> validate_plan | A | census `raw: "{state.plan_raw}"` | fail (default) |
| `examples/dungeon_master/purgatory/plot.yaml` | `plot` | `plot` | -> END | A | census `description: Weave a plain three-act plot from a synopsis + draft + instruction` | fail (default) |
| `examples/dungeon_master/synopsis.yaml` | `synopsis` | `synopsis` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/dungeon_master/turn.yaml` | `direct` | `direction` | -> recap | A | census `direction: "{state.direction}"` | fail (default) |
| `examples/dungeon_master/turn.yaml` | `recap` | `recap` | -> END | A | census `Outputs: intents (list of {thinking, intent}, cast order), direction (dict),           rec` | fail (default) |
| `examples/fsm-router/graphs/classifier.yaml` | `classify` | `classification` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: `classification` is the subgraph's only output (`-> END`)) | fail (default) |
| `examples/fsm-router/graphs/complex-responder.yaml` | `analyze` | `analysis` | -> respond | A | census `analysis: "{state.analysis}"` | fail (default) |
| `examples/fsm-router/graphs/complex-responder.yaml` | `respond` | `response` | -> END | A | census `edges:   - from: respond     to: END` | fail (default) |
| `examples/fsm-router/graphs/simple-responder.yaml` | `respond` | `response` | -> END | A | census `edges:   - from: respond     to: END` | fail (default) |
| `examples/image_pipeline/graph.yaml` | `generate_concepts` | `concepts` | -> generate_prompts | A | census `over: "{state.concepts.concepts}"` | fail (default) |
| `examples/image_pipeline_v2/graph.yaml` | `generate_candidates` | `candidates` | -> score_filter | A | census `requires: [candidates]` | fail (default) |
| `examples/novel_fandom/close.yaml` | `extract_deltas` | `deltas` | -> apply | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/novel_fandom/create_character.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` (census said `a`; reconciled: same node, prompt and position as the five sibling create_* checks) | on_error: skip (node) |
| `examples/novel_fandom/create_event.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` (census said `a`; reconciled: same node, prompt and position as the five sibling create_* checks) | on_error: skip (node) |
| `examples/novel_fandom/create_faction.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` | on_error: skip (node) |
| `examples/novel_fandom/create_location.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` | on_error: skip (node) |
| `examples/novel_fandom/create_premise.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` | on_error: skip (node) |
| `examples/novel_fandom/create_rule.yaml` | `check` | `check_result` | -> END | B | prompt header `# Output: check_result (advisory ≤2-line verdict)`; runs after `persist`, edge `-> END` (census said `a`; reconciled: same node, prompt and position as the five sibling create_* checks) | on_error: skip (node) |
| `examples/novel_fandom/draft.yaml` | `extract_mentions` | `prose_mentions` | -> gate_prose | A | census `- from: extract_mentions     to: gate_prose` | fail (default) |
| `examples/novel_fandom/find_path.yaml` | `find_path` | `plot_path` | -> gate_path | A | census `- from: find_path     to: gate_path` | fail (default) |
| `examples/novel_fandom/find_path.yaml` | `fix_path` | `plot_path` | -> gate_path | A | census `- from: fix_path     to: gate_path` | fail (default) |
| `examples/novel_fandom/genesis.yaml` | `synopsis` | `synopsis` | -> persist_synopsis | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/novel_fandom/graph.yaml` | `draft` | `drafted_page` | -> gate | A | census `persist:     type: python     tool: save_page     variables:       path: "{state.save_path` | fail (default) |
| `examples/novel_fandom/graph.yaml` | `fix` | `drafted_page` | -> gate | A | census `data: "{state.drafted_page}"` | fail (default) |
| `examples/novel_fandom/ref_check.yaml` | `audit` | `result` | -> END | A | census `# Output: result (advisory ≤2-line verdict)` | fail (default) |
| `examples/novel_fandom/semantic_dedup.yaml` | `compare` | `merge_result` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/novel_fandom/story_extract.yaml` | `threads_from_synopsis` | `threads_1a_raw` | -> persist_1a_node | A | census abstained; no tolerance evidence in graph (census said `abstain`; reconciled: edge `-> persist_1a_node`; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/novel_fandom/story_extract.yaml` | `reconcile` | `reconcile_result` | -> persist_threads_node | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/novel_fandom/story_extract.yaml` | `throughlines` | `throughlines_raw` | -> persist_throughlines_node | A | census `- from: throughlines     to: persist_throughlines_node` | fail (default) |
| `examples/npc/encounter-loop.yaml` | `perceive` | `perception` | -> decide | A | census `- from: perceive     to: decide` | fail (default) |
| `examples/npc/encounter-loop.yaml` | `decide` | `decision` | -> narrate | A | census `decision: "{state.decision}"` | fail (default) |
| `examples/npc/encounter-loop.yaml` | `narrate` | `narration` | -> describe_scene | A | census `variables:       narration: "{state.narration}"` | fail (default) |
| `examples/npc/encounter-loop.yaml` | `describe_scene` | `scene_prompt` | -> generate_scene_image | A | census `- from: describe_scene to: generate_scene_image` | fail (default) |
| `examples/npc/encounter-loop.yaml` | `summarize` | `turn_summary` | -> next_turn | A | census `NODES_REFERENCING_STATE_KEY: ['next_turn']` | fail (default) |
| `examples/npc/encounter-multi.yaml` | `summarize` | `turn_summary` | -> describe_scene | A | census `narration: "{state.turn_summary}"` | fail (default) |
| `examples/npc/encounter-multi.yaml` | `describe_scene` | `scene_prompt` | -> generate_scene_image | A | census `- from: describe_scene     to: generate_scene_image` | fail (default) |
| `examples/npc/encounter-turn.yaml` | `perceive` | `perception` | -> decide | A | census `NODES_REFERENCING_STATE_KEY: ['decide']` | fail (default) |
| `examples/npc/encounter-turn.yaml` | `decide` | `decision` | -> narrate | A | census `decision: "{state.decision}"` | fail (default) |
| `examples/npc/encounter-turn.yaml` | `narrate` | `narration` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/npc/npc-creation.yaml` | `identity` | `identity` | -> personality | A | census `identity: "{state.identity}"` | fail (default) |
| `examples/npc/npc-creation.yaml` | `personality` | `personality` | -> knowledge | A | census `personality: "{state.personality}"` | fail (default) |
| `examples/npc/npc-creation.yaml` | `knowledge` | `knowledge` | -> behavior | A | census `knowledge: dict` | fail (default) |
| `examples/npc/npc-creation.yaml` | `behavior` | `behavior` | include_stats == 'true' -> stats, include_stats != 'true' -> END | A | census `behavior: dict` | fail (default) |
| `examples/npc/npc-creation.yaml` | `stats` | `stats` | -> END | A | census `condition: "include_stats == 'true'"` (census said `b`; reconciled: the `include_stats == 'true'` condition selects the branch; it does not tolerate its failure, and stats are the branch's product) | fail (default) |
| `examples/openai_proxy/graph.yaml` | `respond` | `response` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/plot_modeller/graphs/assign_affects.yaml` | `assign` | `affects_raw` | -> validate | A | census `# Loop control is keyed on the re-entered node (`assign`). After 3 assign entries the loop` (census said `b`; reconciled: edge `-> validate`; the loop comment covers validation retries, not LLM failure; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/plot_modeller/graphs/assign_causality.yaml` | `assign` | `causality_raw` | -> validate | A | census `# Loop control is keyed on the re-entered node (`assign`). After 3 assign entries the loop` (census said `b`; reconciled: edge `-> validate`; the loop comment covers validation retries, not LLM failure; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/plot_modeller/graphs/assign_pre_eff.yaml` | `assign` | `pre_eff_raw` | -> validate | A | census `- from: assign     to: validate` | fail (default) |
| `examples/plot_modeller/graphs/classify_kinds.yaml` | `classify` | `kinds_raw` | -> validate | A | census `- from: classify     to: validate` | fail (default) |
| `examples/plot_modeller/graphs/extract_agents.yaml` | `extract` | `agents_raw` | -> validate | A | census `# Loop control: after 3 extract entries the loop exits to END even if validation never pas` (census said `b`; reconciled: edge `-> validate`; the loop comment covers validation retries, not LLM failure; the next node is python and reads state directly; the dossier's substring scan cannot see python readers, so its `none` is not evidence of an unread output) | fail (default) |
| `examples/plot_modeller/graphs/extract_glosses.yaml` | `extract` | `glosses_raw` | -> validate | A | census `One LLM node emits YAML text; a Python validator` | fail (default) |
| `examples/plot_modeller/graphs/extract_goals.yaml` | `extract` | `goals_raw` | -> validate | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `derive_cast` | `cast` | -> author_surface | A | census abstained; no tolerance evidence in graph (census said `abstain`; reconciled: edge `-> author_surface`; the cast is the input to every later step) | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `author_surface` | `surface_sheets` | -> author_interiority | A | census `surface_sheets:     type: str     description: "A1 input: outside-only sheets (appearance/` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `author_interiority` | `interiority_sheets` | -> sketch_bare | A | census `- from: author_interiority     to: sketch_bare` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `sketch_bare` | `sketch_a0` | -> sketch_surface | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `sketch_surface` | `sketch_a1` | -> sketch_interiority | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `sketch_interiority` | `sketch_b` | -> build_pairs | A | census `- from: sketch_interiority     to: build_pairs` | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `judge_ba1` | `verdict_ba1` | -> judge_ba0 | A | census `NODES_REFERENCING_STATE_KEY: none` (census said `b`; reconciled: a missing verdict would silently skew `tally`) | fail (default) |
| `examples/plot_modeller/graphs/interiority_ab.yaml` | `judge_ba0` | `verdict_ba0` | -> tally | A | census abstained; no tolerance evidence in graph (census said `abstain`; reconciled: edge `-> tally`; a missing verdict would silently skew the tally) | fail (default) |
| `examples/plot_modeller/graphs/l5_measure.yaml` | `regenerate` | `regen_prose` | -> score_simulability | A | census `score_simulability:     type: python     tool: score_simulability         # deterministic ` | fail (default) |
| `examples/plot_modeller/graphs/l5_measure.yaml` | `judge_fidelity` | `fidelity` | -> verdict | A | census `requires: [fidelity]` | fail (default) |
| `examples/plot_modeller/graphs/l7_measure.yaml` | `regenerate` | `regen_arc` | -> score_simulability | A | census `requires: [regen_arc]` | fail (default) |
| `examples/plot_modeller/graphs/l7_measure.yaml` | `judge_fidelity` | `fidelity` | -> verdict | A | census `verdict:     type: python     tool: combine_l7_measure           # two axes -> one attribu` | fail (default) |
| `examples/plot_modeller/graphs/perspective_agent.yaml` | `summarize` | `viewpoint` | -> encode | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/plot_modeller/graphs/perspective_agent.yaml` | `encode` | `encoded_raw` | -> assemble | A | census `requires: [encoded_raw]` | fail (default) |
| `examples/plot_modeller/graphs/perspective_l5.yaml` | `extract_vocab` | `vocab_raw` | -> validate_vocab | A | census `requires: [vocab_raw]` | fail (default) |
| `examples/plot_modeller/graphs/roundtrip_skeleton.yaml` | `derive_cast` | `cast` | -> outline_chapter_briefs | A | census `cast: "{state.cast}"` | fail (default) |
| `examples/plot_modeller/graphs/roundtrip_skeleton.yaml` | `outline_chapter_briefs` | `briefs` | -> draft_chapter | A | census `over: "{state.briefs.chapters}"` | fail (default) |
| `examples/questionnaire/graph.yaml` | `opening` | `response` | -> append_opening | A | census `ask_opening:     type: interrupt     message: "{response}"     resume_key: user_message` | fail (default) |
| `examples/questionnaire/graph.yaml` | `extract` | `extracted` | -> detect_gaps | A | census `variables:       schema: "{state.schema}"       extracted: "{state.extracted}"` | fail (default) |
| `examples/questionnaire/graph.yaml` | `probe` | `response` | -> append_probe | A | census `ask_probe:     type: interrupt     message: "{response}"     resume_key: user_message` | fail (default) |
| `examples/questionnaire/graph.yaml` | `recap` | `response` | -> store_recap | A | census `- from: recap     to: store_recap` | fail (default) |
| `examples/questionnaire/graph.yaml` | `classify` | `recap_action` | recap_action.action_type == 'confirm' -> set_analyzing, correction_count >= 5 -> set_analyzing, recap_action.action_type == 'correct' and correction_count < 5 -> apply_corrections, recap_action.action_type == 'clarify' and correction_count < 5 -> recap | A | census `"recap_action.action_type == 'confirm'"` | fail (default) |
| `examples/questionnaire/graph.yaml` | `analyze` | `analysis` | -> save | A | census `analysis: "{state.analysis}"` | fail (default) |
| `examples/questionnaire/graph.yaml` | `closing` | `response` | -> END | A | census `- from: closing     to: END` | fail (default) |
| `examples/rag/graph.yaml` | `answer` | `answer` | -> END | A | census `edges:   - from: answer     to: END` | fail (default) |
| `examples/storyboard/animated-character-graph.yaml` | `expand_story` | `story` | -> animate_panels | A | census `requires: [animated_panels, story]` | fail (default) |
| `examples/storyboard/character-graph.yaml` | `expand_story` | `story` | -> generate_images | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `examples/storyboard/graph.yaml` | `expand_story` | `story` | -> generate_images | A | census `requires: [story]` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `select_snippets` | `selected_snippets` | -> assemble_graph | A | census `selected_snippets: "{state.selected_snippets}"` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `assemble_graph` | `assembled_graph` | -> generate_prompts | A | census `assembled_graph: "{state.assembled_graph}"` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `generate_prompts` | `generated_prompts` | -> generate_tools | A | census `prompts: "{state.generated_prompts}"` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `generate_tools` | `generated_tools` | -> generate_readme | A | census `tools: "{state.generated_tools}"` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `generate_readme` | `generated_readme` | -> write_files | A | census `readme: "{state.generated_readme}"` | fail (default) |
| `examples/yamlgraph_gen/graph.yaml` | `report_result` | `report` | -> END | A | census `EDGES_OUT: ['-> END']` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/classify-then-process.yaml` | `handle_positive` | `result` | -> END | A | census `- from: handle_positive     to: END` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/classify-then-process.yaml` | `handle_negative` | `result` | -> END | A | census `- from: handle_negative     to: END` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/classify-then-process.yaml` | `handle_neutral` | `result` | -> END | A | census `NODES_REFERENCING_STATE_KEY: ['handle_positive', 'handle_negative']` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/generate-then-map.yaml` | `generate_list` | `items` | -> process_items | A | census `over: "{state.items}"` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/interrupt-multi-step.yaml` | `process_1` | `step_1_result` | -> step_2 | A | census `previous: "{state.step_1_result}"` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/interrupt-multi-step.yaml` | `process_2` | `final_result` | -> END | A | census `- from: process_2     to: END` | fail (default) |
| `examples/yamlgraph_gen/snippets/patterns/map-then-summarize.yaml` | `summarize` | `summary` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `graphs/enforcement/changelog-req-check.yaml` | `check` | `verdict` | -> END | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `graphs/fr_triage/graph.yaml` | `triage` | `triage` | -> append | A | census `NODES_REFERENCING_STATE_KEY: none` | fail (default) |
| `graphs/world_distill/graph.yaml` | `distill` | `distilled` | -> write | A | census `Dated header + prose; refuses empty distill (Commandment 6)` | fail (default) |
