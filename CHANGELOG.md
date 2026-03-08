# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.61] — 2026-03-08

### Added
- **FR-154 Architecture Capability Count Guard**: Fix stale capability/requirement counts in ARCHITECTURE.md summary sentence (19→46 capabilities, 68→109 requirements) and add CI guard test to prevent future drift. (REQ-YG-150)
- **FR-145 Phantom Requirement Detection**: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md`. (REQ-YG-145)
- **FR-149 CI CHANGELOG Gate**: Add `changelog-gate` job to `.github/workflows/commitlint.yml` that blocks merge of `feat` and `fix` PRs unless `CHANGELOG.md` is modified in the PR diff. Uses job-level `if` condition to skip for other PR types. Closes the structural gap where server-side squash merges bypass local commit-msg hooks. (REQ-YG-148)
- **FR-150 Branch Protection for Main**: Configure GitHub branch protection on `main` requiring pull requests, squash-merge only, and required status checks (`commitlint`, `test`). Document emergency bypass procedure in `reference/break-glass.md` and add Branch Protection section to `CLAUDE.md`. (REQ-YG-149)
- **FR-144 Enforce Diary Reflection Content**: Add `diary-reflection-check` pre-commit hook that rejects commits containing unfilled diary reflection stubs. Modify `finalize_merge.sh` to create diary stubs as untracked files. Unstage existing unfilled stubs (FR-127, FR-128, FR-134) to comply with enforcement. (REQ-YG-144)
- **FR-124 Diary Import CLI**: `yamlgraph diary import` CLI command imports pending scheduled diary entries and git reports into `docs/diary/` with `--dry-run` and `--source` flags. Extracted shared import logic from `scripts/diary_rotate.py` into `yamlgraph/diary/importer.py`. (REQ-YG-122)
- **FR-142 Inquisitor Worktree Gate**: Add worktree-detection gate to `inquisitor.sh` that suppresses audit and propose phases when running inside a git worktree (enforce pipeline). Detects via `-f "$REPO_ROOT/.git"`; `--force` bypasses. Placed before commit-delta gate (FR-131). (REQ-YG-142)
- **FR-138 Copilot Session GC**: Shell script `scripts/copilot_session_gc.sh` prunes stale Copilot CLI sessions older than `--max-age` days (default 7). Supports `--dry-run` preview and protects the active session via `$COPILOT_SESSION_ID`. (REQ-YG-141)
- **FR-137 DeepSeek Provider**: Added DeepSeek as ninth LLM provider via `create_llm(provider="deepseek")`. Requires `DEEPSEEK_API_KEY` environment variable.
- **FR-136 Judge SPLIT Verdict**: Add fourth verdict (SPLIT) to judge prompts in `examples/copilot/prompts/judge.yaml` and `scripts/chaplain-prompts/judge.md`, enabling decomposition of multi-concern FRs into focused sub-topics. Adds Scope Count evaluation criterion and multi-concern test fixture. (REQ-YG-143)
- **FR-140 Clean GIT_* Test Fixture**: Session-scoped autouse pytest fixture strips `GIT_*` env vars injected by pre-commit, preventing subprocess bleed into `tmp_path`-based test repos. Closes the `--no-verify` bypass loophole. (REQ-YG-140)
- **FR-134 Diary Folder Refactor — Replace Single File with Date-Prefixed Entries**: Replace the monolithic `docs/diary.md` with a `docs/diary/` folder of date-prefixed entry files, eliminating merge conflicts caused by concurrent appends from `finalize_merge.sh`, `diary_rotate.py`, `inquisitor.sh`, and `examples/shared/diary.py`. (REQ-YG-131)
- **FR-131 Inquisitor commit-delta gate**: Add a pre-flight gate to `inquisitor.sh` that aborts when no `feat:` or `fix:` commits exist since the last audit, breaking the ritual loop documented in Audits XI–XIII.
- **FR-128 YAMLGraphication of Enforcer**: Approved FR to replace inline `copilot -p` calls in `enforce_worktree.sh` with `yamlgraph graph run examples/enforce/graph.yaml`, completing the FR-106 declarative enforce pipeline vision.
- **FR-127 CI Conventional Commit Enforcement**: `.github/workflows/commitlint.yml` validates PR titles against Conventional Commits via `action-semantic-pull-request@v5`; enforces `FR-XXX` reference on `feat` PRs via inline script with env-based variable passing (no script injection). `revert` type added to both CI and local `conventional-pre-commit` hook for parity.
- **FR-125 Enforce Pipeline Post-Merge Finalization**: Add a `finalize_merge.sh` script that runs after a PR from the enforce pipeline is merged, automating three post-merge obligations: CHANGELOG entry, FR status update, and diary reflection stub.
- **FR-116 Watch→Enforce Spawn**: `watch.sh` snapshots `feature-requests/` before graph execution, diffs after via `comm -13`, skips rejected FRs (`Status.*Rejected`), and spawns `enforce_worktree.sh` via `nohup ... &` for approved FRs. Output redirected to `tmp/enforce-<slug>.log`. Pure shell, no state files, no Python helpers. 16 unit tests. (REQ-YG-116)
- **FR-113 Linter W015**: Warn when cycle node has explicit `skip_if_exists: true` — the node will cache its first output and return stale results on every iteration. Only fires on explicit setting; runtime `apply_loop_node_defaults()` handles the default case. (REQ-YG-113)
- **FR-106 Next Steps Output**: Print merge, discard, and cleanup commands after successful PR creation in `enforce_worktree.sh`

### Removed
- Stale demo files: `examples/cost-router/poc_granite.py`, `scripts/loopback-poc/` experiment (419 lines, commit a0e6f00)

### Fixed
- **FR-152 Missing Diary Reflections**: Create missing diary reflections for DeepSeek provider (FR‑137) and phantom requirement detection (FR‑145). Remediates two consecutive audit violations (XXXIV/XXXV) for skipped Distill obligations. (REQ-YG-144)
- **FR-139 Enforce Worktree bare=true Corruption Guard**: Add three-layer defense against `.git/config` corruption (env sanitization, cleanup trap restoration, post-run assertion) that can set `bare = true` after worktree operations. (REQ-YG-UTIL)
- **Enforce Pipeline Timeout**: Increase `submit_pr` timeout from 120s to 500s to prevent premature abort during PR creation
- **FR-106 Enforce Worktree**: Commit new FR to main before creating worktree, ensuring FR exists in worktree for copilot context
- **FR-106 Enforce Worktree Script**: Save `MAIN_DIR` before worktree operations; cleanup trap now returns to main dir before git operations
- **FR-106 Copilot CLI Syntax**: Use standalone `copilot -p` with `--allow-all` instead of invalid `gh copilot /agent` syntax

## [0.4.60] — 2026-03-06

### Added
- **FR-112 Inception Labs Provider**: Add Inception Labs Mercury-2 as OpenAI-compatible provider. `_create_inception_llm` helper with base_url `https://api.inceptionlabs.ai/v1`, `INCEPTION_API_KEY` env var, `mercury-2` default model.

### Changed
- **FR-110 Promote W014 → E007**: Undeclared `{state.X}` references now emit `severity="error"` with code `E007` (was `W014` warning). `yamlgraph graph lint` exits non-zero on undeclared state refs. (REQ-YG-069)

## [0.4.59] — 2026-03-04

### Added
- **FR-111 Compiled Graph Cache** (CAP-34, REQ-YG-107): Process-global `GRAPH_CACHE` in `yamlgraph/graph_cache.py` so `load_and_compile_async()` results survive action module reloads. Eliminates 1.5–4s recompilation on every LLM action invocation in engines that reload action modules per FSM transition. `cache=None` opt-out for test isolation. Migrates `yamlgraph_action.py` and `yamlgraph_preload_action.py` off local `_GRAPH_CACHE` workarounds. 10 unit tests.
- **Graph Cache Demo**: `examples/demos/hello/demo_cache.py` — demonstrates cache hit/miss, `clear_cache()`, and `cache=None` bypass.
- **Reference Updates**: `async-usage.md` documents `GRAPH_CACHE`, `clear_cache()`, `cache=` parameter, and updated FastAPI integration (no manual global variable). `getting-started.md` core files table includes `graph_cache.py`. `intent-questionnaire-pattern.md` references package-level cache.
- **`__init__.py` Exports**: `GRAPH_CACHE` and `clear_cache` now exported from top-level `yamlgraph` package.

### Changed
- **FR-107 Router `route_field`**: Router nodes now require explicit `route_field` config naming the schema field that holds the route key. Replaces hardcoded `tone`/`intent` extraction in `llm_nodes.py`. Pydantic validator enforces presence for `type: router` nodes. All 10 router nodes across 6 graphs + 2 snippet templates updated. NC-111 (Pydantic object in state) solved by design — extracting the named field yields a string.

### Fixed
- **E103 Linter False Positive**: Guard-condition edges (`condition: "expr"`) targeting a router node no longer trigger E103. E103 now only fires for `type: conditional` fan-out edges with a single string target. Previously, valid expression edges to routers were incorrectly flagged, and the suggested fix (`to: [node]`) caused a runtime crash ("unhashable type: 'list'").

### Added
- **FR-109 Ninchat Voice Coordinator** (`projects/ninchat_voice`): Graph-as-coordinator for Twilio ↔ Ninchat bot voice calls
  - `graphs/ninchat-voice-coordinator.yaml`: 10-node graph with conditional call-loop and hangup guard
  - `nodes/ninchat_session.py`: NinchatConnection WebSocket client (`create_session`/`send_to_bot`/`close_session`)
  - `nodes/voice_ws.py`: Twilio Media Stream TTS/STT via shared outcaller TelcoSession
  - `prompts/`: Finnish mediator prompts (greeting rewrite + response rewrite with Jinja2)
  - `server.py`: FastAPI `/incoming` webhook + WebSocket voice endpoint
  - 21 unit tests with `NV-000` project-local req markers, lint-clean

- **FR-106 Worktree Pipeline** (CAP-33, REQ-YG-106): Parallel development via git worktrees
  - `scripts/enforce_worktree.sh`: Creates isolated worktree, runs pipeline, cleans up on exit
  - `yamlgraph/utils/worktree_helpers.py`: Branch derivation, path construction, working tree validation
  - `examples/enforce/graph.yaml`: 4-phase pipeline (implement → test/demo → precommit → PR)
  - Session continuations: All phases chain via `resume: "{state.implement_result.session_id}"`
  - Concurrency support: Multiple worktrees can run simultaneously without interference
  - 9 unit tests + 10 integration tests for worktree lifecycle

- **FR-107 Architecture Cross-Check** (ADR-001): `req_coverage.py --strict` now verifies all requirements exist in `ARCHITECTURE.md`
  - Detects phantom requirements: IDs in `ALL_REQS` missing from architecture table
  - Warning mode (no `--strict`): prints warning, exits zero
  - Strict mode: exits non-zero on undocumented requirements
  - Fixed REQ-YG-105 gap: added to CAP-30 table in `ARCHITECTURE.md`

- **FR-105 Copilot Session Continuations** (CAP-30, REQ-YG-105): Enable multi-task workflows where sequential copilot nodes share a session
  - `cli_flags.resume`: Resume a specific session by ID (`--resume <id>`)
  - `cli_flags.continue_session`: Resume most recent session (`--continue`)
  - `CopilotResult.session_id`: Extracted from CLI stderr for downstream nodes
  - State expression support: `{state.prev_result.session_id}` in resume
  - Linter rules: `E-COPILOT-RESUME` (mutual exclusion), `W-COPILOT-SESSION` (pattern warning)
  - Updated example in `examples/copilot/graph.yaml` with session continuation

### Fixed
- **FR-106 Worktree Pipeline**: Exclude `docs/diary.md` from clean working tree check
  - Inquisitor writes to diary after commits, which would block worktree creation
  - `validate_clean_working_tree(exclude_paths=["docs/diary.md"])` now allows diary changes

## [0.4.58] - 2026-02-25

### Added
- **FR-103 eBook Judge-Amend Subgraph** (REQ-YG-092): Validation pattern for per-chapter content verification
  - `examples/ebook/subgraphs/validate_chapter.yaml`: Judge→amend cycle subgraph
  - `examples/ebook/prompts/judge/chapter.yaml`: Validates inline citations against source files
  - `examples/ebook/prompts/amend/chapter.yaml`: Fixes chapters when validation fails
  - `examples/ebook/prompts/chapter/*.yaml`: 6 merged chapter prompts with inline citations
  - `persist_chapter` tool node for single chapter persistence
  - Rewired graph to 18 nodes (write→validate→persist per chapter)
  - 4 new doctrine validation tests in `tests/unit/test_ebook_doctrine_validation.py`

- **eBook Landing Page**: Added ToC section to `docs/index.html` with links to all 9 chapters

### Fixed
- **GitHub Pages Build**: Fixed Liquid syntax errors by wrapping Jinja2 template syntax in `{% raw %}` tags (Jekyll 3.x doesn't support `render_with_liquid` front matter)

- **FR-103 Per-chapter persistence**: Restored visibility and resume capability
  - Added 6 persist functions (`persist_introduction`, `persist_doctrine`, etc.)
  - Graph flow: write→validate→save per chapter (chapters saved immediately)
  - Judge prompt returns detailed feedback (not just PASSED/FAILED)

- **FR-100 eBook Authoring Pipeline** (CAP-32, REQ-YG-091): YAMLGraph-driven pipeline to write development pipeline documentation as an eBook
  - `examples/ebook/graph.yaml`: 14-node pipeline with copilot research nodes, LLM writing nodes, judge, and write tool
  - `examples/ebook/nodes/writing.py`: `write_chapters_tool` writes formatted chapter content to disk
  - `examples/ebook/prompts/research/*.yaml`: 6 research prompts for gathering source material
  - `examples/ebook/prompts/write/*.yaml`: 6 writing prompts for drafting chapters
  - `examples/ebook/prompts/judge_draft.yaml`: Review prompt for accuracy and completeness
  - `docs/ebook/README.md`: Build instructions and contribution guide
  - `docs/ebook/_build.sh`: pandoc-based HTML/PDF renderer
  - Unit tests for `write_chapters_tool` in `tests/unit/test_ebook_writing.py`

## [0.4.57] - 2026-02-24

### Added
- **FR-093 Chaplain Diary Append** (CAP-31, REQ-YG-090): Extend `.chaplain/graph.yaml` with automatic diary entry creation
  - `summarize` (LLM) node produces DiaryEntry schema (theme, body, seed) from Plan→Judge output
  - `write_diary` (Python) node appends formatted entry to `docs/diary.md`
  - `format_diary_entry()` now accepts configurable `prefix` parameter (default "World Digest")
  - `watch.sh` passes `--var date` and `--var diary_prefix=Chaplain` to graph
  - `.chaplain/prompts/summarize.yaml` with inline Pydantic schema
- **FR-094 Memory Nodes** Approve declarative `memory_read` / `memory_write` node types for cross-session semantic memory via LanceDB. REQ-YG-091, REQ-YG-092.
- **FR-097 Shared Diary Module** Move diary writing utilities to `examples/shared/diary.py` for neutral ownership. Re-exports in `examples/diary_digest/nodes/writing.py` maintain backward compatibility.
- **FR-098 Copilot Graph Consolidation** Merge `.chaplain/graph.yaml` into `examples/copilot/graph.yaml` as canonical 4-stage workflow (Plan → Judge → Summarize → Write Diary). Delete `.chaplain/graph.yaml` and `.chaplain/prompts/`. Update `.chaplain/watch.sh` to reference consolidated graph.

### Fixed
- **FR-093 Diary Entry Parsing** Fix `write_diary()` failing to append when `diary_entry` arrives as Pydantic model string representation (e.g., `theme='...' body='...' seed='...'`). Added regex parsing branch to handle this serialization format from LLM structured output.
- **FR-083 Commit-Msg Hook Bug** Fix `bash -c` positional argument bug in both `feat-requires-fr` and `changelog-required` pre-commit hooks. Added `_` placeholder to both hook entries so the commit message file properly becomes `$1`. Removed stale `backend: sampling` CHANGELOG entry for FR-081 (was deleted in FR-082 teardown). Added 19 integration tests for commit-msg hook behavior.
- **FR-087 Stale REQ Range** Replace stale `REQ-YG-087–089` range notation with explicit `REQ-YG-087, REQ-YG-089` in ARCHITECTURE.md and CHANGELOG.md since REQ-YG-088 was removed during FR-082 teardown.
- **FR-089 Capability Numbering** Remove strikethrough CAP-29 row from ARCHITECTURE.md capability table. Add footnote explaining stable numbering policy (retired capabilities are removed, not renumbered).
- **FR-091 Missing Node Types** Add `copilot` and `interactive_tool` to `reference/README.md` Node Types table. Add `copilot` to `reference/getting-started.md`.
- **FR-092 Orphan Docs Index** Link `expressions.md`, `scheduling-agents.md`, and `intent-questionnaire-pattern.md` to `reference/README.md` index.

### Changed
- **FR-084 Watch.sh Migration** Migrate `.chaplain/watch.sh` from inline copilot calls to `yamlgraph graph run`. Added `.chaplain/graph.yaml` (Plan→Judge workflow) and `.chaplain/prompts/{plan,judge}.yaml`. The bash script is now a thin polling wrapper; all workflow logic lives in the YAMLGraph graph.
- **FR-085 Value Statement Field** Add mandatory Value Statement field to FR template (`feature-requests/TEMPLATE.md`). Add Judge criterion 7 (Value Clarity) to `scripts/chaplain-prompts/judge.md`. Graduate `intent_drift` trap to Knowledge Graph (`.github/copilot-instructions.md`).
- **FR-086 README When NOT to Use** Add honest "When NOT to Use YAMLGraph" section to README.md covering dynamic topology, complex state transformations, custom node types, and multi-modal pipelines. Includes escape hatch guidance for `type: python` nodes.
- **FR-088 README Development Process** Replace buried "Remember" section with visible "Development Process" section positioned between Testing and Security. Links to Scripture with five-step workflow summary (Research, Plan, Judge, Enforce, Distill).
- **FR-090 Projects vs Examples** Document `projects/` vs `examples/` distinction in ARCHITECTURE.md with comparison table and graduation criteria.

## [0.4.56] - 2026-02-24

### Added
- **FR-081 Copilot Node Type** (CAP-30, REQ-YG-087, REQ-YG-089): New `copilot` node for delegating to GitHub Copilot CLI
  - `type: copilot` — invokes Copilot CLI with `--silent` flag and configurable `cli_flags`
  - `backend: cli` — subprocess execution with list-based command (injection-safe)
  - `cli_flags`: `allow_all_paths`, `allow_all_tools`, `model` options
  - `timeout` field (default 300s) per-node configurable
  - `CopilotResult` model: `output`, `exit_code`, `model`, `backend`
  - `examples/copilot/`: Plan → Judge → Summarize demo based on `.chaplain/watch.sh`
  - `reference/graph-yaml.md`: Full `type: copilot` documentation section
  - 12 tests covering all three requirements

## [0.4.55] - 2026-02-23

### Added
- **IC-000 Incaller Voice Demo** (REQ-YG-084–086): Inbound Twilio voice call with ElevenLabs TTS/STT
  - `projects/incaller/`: Receives incoming calls to Twilio phone number
  - `await_call`: New node starts HTTP+WS server, waits for `/incoming` webhook (300s timeout)
  - `/incoming` webhook: Returns TwiML `<Connect><Stream>` for bidirectional audio
  - Reuses outcaller TTS/STT/probe-recap nodes — only `await_call` is new
  - TelcoSession extended with `caller_number` field and `start_with_app()` method
  - 7 prompts adapted for inbound tone ("Thank you for calling...")
  - `start.sh`: Automated setup — starts ngrok, updates Twilio webhook via API, runs graph
  - Unit tests: `test_incaller.py` (9 pass) covering all three requirements

## [0.4.54] - 2026-02-23

### Added
- **FR-077 CHANGELOG commit enforcement**: `feat:` and `fix:` commits now require `CHANGELOG.md` to be staged; blocks commits missing changelog entries
- **FR-076 Chaplain Inquisitor**: `.chaplain/inquisitor.sh` — one-shot audit script that checks recent commits against the Scripture (CLAUDE.md doctrine), classifies findings as ✓ COMPLIANT / ⚠ DRIFT / ✗ VIOLATION, and appends results to `docs/diary.md`
  - Post-commit hook: `inquisitor-background` spawns audit asynchronously after each commit
  - Output logged to `.chaplain/inquisitor.log` (gitignored)

### Changed
- **FR-073 Unit test performance**: Reduced unit test time from 32s → ~19s (40% improvement)
  - `test_mcp_server.py`: `time.sleep(10)` → `time.sleep(0.5)` (thread-pool starvation fix)
  - `test_streaming_chaos.py`: `CHAOS_DELAY=5` → `CHAOS_DELAY=1` (async teardown speed)

## [0.4.53] - 2026-02-22

### Added
- **FR-071 Telco Voice Call Demo** (REQ-YG-078–082): Outbound Twilio voice call with ElevenLabs TTS/STT
  - `projects/outcaller/`: YAMLGraph orchestrates call flow via Python tool nodes
  - `initiate_call`: Twilio REST API + FastAPI WebSocket server + ngrok tunnel
  - `speak`: ElevenLabs TTS → ffmpeg mulaw 8kHz → Twilio Media Stream
  - `listen_and_transcribe`: Twilio audio → ffmpeg PCM16 → ElevenLabs STT
  - `accumulate_answer`: Append transcript to state, loop back to LLM
  - Conditional edges replace router node for `[DONE]` detection
  - No audioop dependency (ffmpeg only); Python 3.13 compatible
  - Integration tests: `test_telco_twilio.py` (4 pass), `test_telco_elevenlabs.py` (4 pass)
  - Unit tests: `test_telco_nodes.py` (17 pass) with fixture-based mocking (no test pollution)
  - Optional `[telco]` extra: `twilio>=9.0.0`, `elevenlabs>=1.0.0`

## [0.4.52] - 2026-02-20

### Fixed
- **FR-060 Interrupt node two-node split** (REQ-YG-021): `interrupt()` raises `GraphInterrupt` before the node returns, so `state_key` was never committed. Split `create_interrupt_node()` into `(prepare_fn, interrupt_fn)` tuple: prepare computes and commits payload to state, interrupt reads from state and pauses. `compile_node()` adds both with internal edge; `_process_edge()` redirects incoming edges to prepare node. Works with all checkpointers including `SimpleRedisCheckpointer`. Nine new tests, 17 existing updated.

## [0.4.51] - 2026-02-20

### Fixed
- **FR-059 Normalize agent response.content to string** (REQ-YG-018): Anthropic Claude returns `response.content` as `list[dict]` content blocks instead of `str`. Added `_normalize_content()` helper that extracts text from list blocks, passes strings through, and converts None to empty string. Applied at both agent return paths (normal completion and max-iterations). Four new tests.

## [0.4.50] - 2026-02-20

### Fixed
- **FR-058 Agent streaming message type filter** (REQ-YG-065): `run_graph_streaming_native` now yields only `AIMessageChunk` content without `tool_calls`. Previously, `hasattr(chunk, "content")` duck-type check leaked SystemMessage (prompt text), HumanMessage (echoed input), ToolMessage (raw tool data), and intermediate AIMessage with tool_calls to clients. Replaced with `isinstance(chunk, AIMessageChunk)` + `not chunk.tool_calls` guard. Five new tests.

## [0.4.49] - 2026-02-20

### Fixed
- **FR-057 Agent messages quadratic growth** (REQ-YG-018): Agent node now returns only new messages (delta) instead of the full conversation. The `add` reducer on `messages` was causing quadratic growth when agent nodes were invoked multiple times across interrupt boundaries. Both return paths (normal completion and max-iterations) now slice `messages[len(existing_messages):]`. Three new tests: delta return, 5-turn linear growth, max-iterations delta.

### Added
- **FR-055 Autonomous Chaplain**: `scripts/chaplain.sh` — plan→judge→amend pipeline for automated FR generation from subject lines
- **Tavily RAG docs**: Scryfall/Giada usage examples in tavily_rag README
- **Tavily RAG deep graph fix**: `parse_json: true` for provider-compatible query decomposition
- **Tavily RAG requires fix**: `requires:` checks state keys not node names

## [0.4.48] - 2026-02-20

### Fixed
- **CI pipeline fix**: Add `pytest.importorskip("feedparser")` to `test_diary_digest.py` so tests skip gracefully in CI where only `[dev]` extras are installed (no `[digest]`). This was blocking all PyPI releases since v0.4.43.

## [0.4.47] - 2026-02-20

### Added
- **FR-053 Tavily Domain RAG Demo** (CAP-25, REQ-YG-076): Domain-scoped RAG with Tavily web search
  - Simple graph: retrieve → answer; Deep graph: plan → map(retrieve) → synthesize
  - Python tool node retrieves context via Tavily API with `TAVILY_TARGET_DOMAIN` scoping
  - 11 unit tests (all mocked, no API key needed)
  - `tavily` optional extra in pyproject.toml

## [0.4.46] - 2026-02-20

### Added
- **FR-049 Interactive Tool Node** (CAP-24, REQ-YG-075): New `type: interactive_tool` node that expands a single YAML node into a full multi-turn conversation loop (`__start` → `__ask` → `__step` ↺ → `__end`) at compile time
  - Config-level expansion via `expand_interactive_tools()` — no new factory needed
  - `loop_until` condition with automatic `negate_condition()` for loop-back routing
  - `max_iterations` safety guard, optional `end` tool, `on_error` propagation
  - 31 unit tests + 10 integration tests (stub chatbot, sync/async, SQLite, streaming)
- **Trivia quiz demo**: `examples/demos/interactive_tool/` — deterministic 3-question quiz showcasing the full interactive_tool pattern (no LLM needed)
- **Reference docs**: `interactive_tool` node type section in `graph-yaml.md` with properties table and expansion diagram; added missing node types to `getting-started.md`

### Fixed
- **Condition evaluation `state.` prefix**: `resolve_value()` in `conditions.py` now strips the `state.` prefix from paths (e.g. `state.session_done == True`), fixing `loop_until` routing that silently resolved to `None`

## [0.4.45] - 2026-02-20

### Changed
- **Absolution hook**: Migrated from inline bash to Python script (`scripts/absolution.py`) for maintainability

### Fixed
- **Jinja2 filter extraction**: `extract_variables()` now strips filter expressions (`|length`, `|join` etc.) before parsing — fixes false "missing variable" errors
- **Linter prompts_relative**: `resolve_prompts_dir()` now checks `defaults.prompts_relative` in addition to graph-level setting
- **Scheduler plist**: Changed from `python -m yamlgraph` (fails — no `__main__.py`) to `.venv/bin/yamlgraph` CLI entry point

### Removed
- **`get_map_result()` (BREAKING)**: Deprecated helper removed per Scripture Commandment 8 — use `flatten_output: true` on map nodes instead

## [0.4.44] - 2026-02-20

### Added
- **FR-052 Map Output Flattening**: `flatten_output: true` option for map nodes — merges `_map_xxx_sub` contents into items, converts Pydantic models via `model_dump()`, preserves `_map_index` (REQ-YG-075)
  - `flatten_map_results()` function in `map_compiler.py`
  - `flatten_output` field in `NodeConfig` model
  - Wired through `wrap_for_reducer` in `compile_map_node`
- **Pattern 12**: Quality Gate for Map Output — manual validation pattern documented
- **Pattern 13**: Monitoring No-Op Pipelines — canary detection via launchd

### Changed
- Updated `reference/map-nodes.md` with `flatten_output` property and documentation

## [0.4.43] - 2026-02-19

### Added
- **FR-044d SkipReport**: `on_error: skip` now returns structured `SkipReport` for visibility
- **FR-045 A2A Protocol**: Research and feature requests for A2A provider/consumer patterns
- **FR-046 Diary World Digest**: 8-node pipeline (fetch → analyze → filter → synthesize → write → curate seeds), scheduled via launchd
- **FR-047 Inline LLM Lint**: Pre-commit hook detects inline LLM orchestration outside YAML
- **FR-050 Skip-If-Exists Truthiness**: `_should_skip_if_exists()` helper function with truthiness semantics
- **Pipeline-audit graph**: Structural health scanner for graph YAML files
- **Noqa confession registry**: Enforcement hook ensures all `# noqa` suppressions documented
- **Diary rotation hook**: Automated diary file rotation on day change via pre-commit
- **Seed curation**: LLM-curated seed list (capped at 10) integrated into diary-digest pipeline
- **Pre-commit safety hooks**: `check-merge-conflict`, `check-ast`, `check-toml`, `debug-statements`, `detect-private-key`
- `__version__` exported from `yamlgraph.__init__`

### Changed
- **FR-050 skip_if_exists semantics (BREAKING)**: Now checks truthiness, not existence. Empty `[]`, `""`, `None`, `0`, `False` do NOT trigger skip — fixes diary-digest curate_seeds bug
- **Contrib migration (FR-044b)**: `get_map_result`, `to_serializable` moved to `yamlgraph.contrib.utils`; 10 files migrated
- **Feed sources upgraded**: Diary-digest feeds expanded 5→9 (added OpenAI, HuggingFace, Google AI, GitHub releases, hnrss.org)
- **pyproject.toml**: Added `authors`, `keywords`, `classifiers`, `urls`; excluded `tests`/`examples`/`scripts` from package; added `radon`, `vulture`, `pre-commit` to dev deps

### Fixed
- **Pre-commit hook installation**: `.git/hooks/pre-commit` was missing — only commit-msg hooks ran; now both stages install correctly
- **Diary-digest map output unwrapping**: `filter_relevant` now extracts scores from Pydantic model wrapper
- **Relevance scoring**: Replaced overly strict prompt with calibrated 0.0–1.0 rubric; lowered threshold 0.5→0.3
- **Jinja2 template variable extraction**: Excluded Jinja2 keywords (`for`, `if`, `endif`, etc.) from `extract_variables`
- **Pydantic v1 shims removed**: Dead `.dict()` compatibility code cleaned up

### Removed
- `scripts/diary_digest.py` and `scripts/diary_digest_tools.py` (three-layer violation — replaced by graph pipeline)
- Dead `replicate_tool.py` re-export

## [0.4.41] - 2026-02-16

### Added
- **`--var-file` CLI flag**: Load variables from YAML/JSON file
  - `yamlgraph graph run graph.yaml --var-file config.yaml`
  - Supports both `.yaml` and `.json` files
- **`@file` syntax in `--var`**: Read file content into variable
  - `yamlgraph graph run graph.yaml --var document=@report.txt`
  - Only treats as file if value starts with `@` (emails like `user@domain.com` stay literal)
- **Variable precedence**: `--var` overrides `--var-file` values
- 7 new unit tests for variable loading

### Changed
- Refactored `parse_vars` and `load_var_file` to `cli/helpers.py` (file size gate compliance)

## [0.4.40] - 2026-02-15

### Added
- **FR-036 Phase 1: Agent Sub-nodes in Map** (REQ-YG-040, REQ-YG-041)
  - `type: agent` now supported in map sub-node configuration
  - Enables parallel web search and tool-calling loops over dynamic lists
  - Tools registry passed through map compilation
  - Unit test for agent sub-node error handling
- **W014 Linter Check**: Warns when node variables reference undeclared state keys (REQ-YG-069)

### Changed
- **Pre-commit optimization**: Unit tests only (~18s vs 130s), integration tests run separately

### Fixed
- Dead code: Prefixed unused signal handler args with underscore (vulture)
- Code style: UP038 isinstance fix + ruff format

## [0.4.39] - 2026-02-15

### Added
- **CAP-19: MCP Server Interface** (REQ-YG-066, REQ-YG-067, REQ-YG-068)
  - `yamlgraph/mcp_server.py`: Expose graphs as MCP tools via stdio transport
  - `yamlgraph_list_graphs`: Discover available graphs with descriptions and required vars
  - `yamlgraph_run_graph`: Invoke any graph by name with variables, returns structured JSON
  - Graph discovery scans `examples/demos/*/graph.yaml` and `examples/*/graph.yaml`
  - `.mcp.json` and `.vscode/mcp.json` workspace configs for MCP integration
  - `reference/mcp-server.md` documentation
  - 8 unit tests covering discovery, schema, invocation, error handling, timeout
- `mcp` optional dependency group in `pyproject.toml`

## [0.4.38] - 2026-02-13

### Added
- `last_value` reducer tests in `test_state_builder.py` (4 tests, REQ-YG-024)

### Fixed
- **Map fan-in safety**: `last_value` reducer on BASE_FIELDS (`current_step`, `error`, `_loop_counts`, etc.) prevents `INVALID_CONCURRENT_GRAPH_UPDATE` when parallel map branches write to shared tracking fields.

## [0.4.37] - 2026-02-13

### Added
- **FR-030 Phase 1: Subgraph Token Streaming**: `run_graph_streaming_native()` now accepts `subgraphs: bool = False` parameter. When `True`, tokens from `mode=direct` subgraphs are included in the stream.
- **FR-030 Phase 2 Verification**: Tests confirm `subgraphs=True` also enables streaming from `mode=invoke` subgraphs — no async conversion needed. LangGraph's callback system propagates `StreamMessagesHandler` through sync `invoke()` boundary.
- Two new integration tests: `test_native_streaming_mode_invoke_subgraph`, `test_native_streaming_mode_invoke_subgraph_filtered`

### Fixed
- **FR-030 Bug Fix: Dict token crash**: Router nodes emit dict content (classification result) which caused callers to crash with `TypeError`. Added `isinstance(chunk.content, str)` guard to filter non-string tokens.

## [0.4.36] - 2026-02-13

### Fixed
- Removed unused `Interrupt` imports that caused ruff F401 lint failure in CI.

## [0.4.35] - 2026-02-12

### Added
- **FR-028 Multi-Turn Streaming** (REQ-YG-049): `run_graph_streaming_native()` accepts `Command(resume=...)` and `config` parameter for checkpoint-based multi-turn resume.
- **FR-029 Native LangGraph Streaming** (REQ-YG-065): New `run_graph_streaming_native()` uses LangGraph's `astream(stream_mode="messages")` to stream tokens from ALL LLM nodes (not just first found). Supports `node_filter` parameter.
- **Multi-turn example**: New `examples/demos/multi-turn/` with interrupt-loop graph, guard classification as separate call pattern, and comprehensive README.
- 5 new unit tests for streaming API signature (test_async_executor.py)
- 5 new integration tests for multi-turn patterns (test_multi_turn_streaming.py)
- 7 new unit tests for native streaming (test_async_executor.py)
- 5 new integration tests for native streaming (test_native_streaming.py)

### Removed
- **`run_graph_streaming()`**: Deprecated legacy function removed. Use `run_graph_streaming_native()` instead. The native version streams from ALL LLM nodes using LangGraph's native streaming (was: passthrough hack for first node only).
- **`test_graph_streaming.py`**: Legacy passthrough streaming tests removed. REQ-YG-048 coverage migrated to test_native_streaming.py.

### Fixed
- **Missing dependency**: Installed `langchain-google-genai` which was declared in pyproject.toml but not installed in dev environment, causing `test_google_provider` failure.

### Stats
- 1650 passed, 4 skipped, 2 xfailed, 65/65 reqs.

## [0.4.34] - 2026-02-11

### Added
- **Token usage tracking** (REQ-YG-064): `TokenUsageCallbackHandler` callback accumulates `input_tokens`, `output_tokens`, and `total_calls` across all LLM invocations in a graph run. CLI `--token-usage` flag prints summary. Follows the same `config["callbacks"]` pattern as LangSmith tracer. Completes FR-027 P2-8.
- **Requirement traceability enforcement** (REQ-YG-063): `pytest_collection_modifyitems` hook in `tests/conftest.py` now **structurally enforces** ADR-001. Every test must have `@pytest.mark.req("REQ-YG-XXX")` or collection fails with `UsageError`. Implements Commandment #10.
- 8 new tests (6 token tracking + 2 enforcement) in `tests/unit/test_fr027_execution_safety.py` and `tests/unit/test_requirement_enforcement.py`.

### Stats
- 1619 passed, 1 skipped, 2 xfailed, 64/64 reqs, 91.66% coverage.

## [0.4.33] - 2026-02-11

### Added
- **Linter W013** (REQ-YG-062): Warns when map node `over:` is a dynamic expression (state reference) without `max_items` or `config.max_map_items`. Completes FR-027 P2-9.
- 4 new W013 tests in `TestLinterW013DynamicMap`.

### Fixed
- **CI fix**: Replicate `max_tokens` tests now skip with `pytest.importorskip("langchain_litellm")` when the optional dependency is missing. Fixes v0.4.32 CI failure.
- **Dead code removed**: `DEFAULT_MAX_TOKENS = 4096` constant deleted from `config.py` — was never wired (superseded by explicit `max_tokens` parameter in v0.4.31).

### Stats
- 1611 passed, 91.74% coverage, 62/62 reqs, 44 FR-027 tests.

## [0.4.32] - 2026-02-11

### Fixed
- **Replicate `max_tokens` bug**: `_create_replicate_llm()` now receives and forwards `max_tokens` via `**kwargs`. Previously silently dropped. (REQ-YG-060)
- **Timeout signal handler save/restore**: `_setup_timeout` / `_teardown_timeout` extracted as named functions; previous `SIGALRM` handler saved and restored in `finally`. Eliminates handler leak.
- **Dead code removed**: `_timeout_fired` variable was assigned but never read.
- **Windows timeout warning**: Emits `logger.warning()` when `--timeout` is configured on Windows (unsupported platform) instead of silently ignoring.
- **Deprecated `asyncio.get_event_loop()`**: Replaced with `asyncio.get_running_loop()` in `llm_factory_async.py`.
- **FR-026 stale metadata**: Updated status from "Proposed" to "✅ Implemented (v0.4.28)", checked all acceptance criteria boxes.

### Stats
- 3 new tests, 1608 total passing, 91.71% coverage, 61/61 reqs, 40 FR-027 tests.

## [0.4.31] - 2026-02-11

### Added
- **FR-027 P1 complete**: Execution safety guards — all P1 items implemented under TDD.
  - **`max_iterations` default fix**: Corrected agent node default from 5→10 to match Pydantic schema; eliminates silent shadowing across 6 sources. (REQ-YG-059)
  - **`max_tokens` end-to-end wiring**: Wired from graph YAML `config.max_tokens` and node-level `max_tokens` through `graph_loader` → `llm_factory` → `executor` → `llm_nodes` → all providers. Uses `optional_kwargs` pattern (only sent when explicitly set). LLM cache key expanded to 4-tuple. (REQ-YG-060)
  - **Global execution timeout**: `config.timeout` in YAML and `--timeout` CLI flag; uses `signal.alarm` on Unix. Raises `SystemExit(1)` on expiry. CLI overrides YAML. (REQ-YG-061)
- `max_tokens` and `timeout` added to `graph-v1.json` schema.
- New `### config` section in `reference/graph-yaml.md` documenting all 4 config keys with CLI overrides.
- 17 new tests (3 + 9 + 5) across 3 test classes; total FR-027 tests: 37.
- Requirements REQ-YG-059 through REQ-YG-061 in ARCHITECTURE.md.

## [0.4.30] - 2026-02-11

### Added
- **FR-027 P0 complete**: 3 new tests proving `recursion_limit` wiring from YAML/CLI to `graph.invoke(config=...)`. Covers YAML-only, CLI override, and default-50 paths. (REQ-YG-056)
- FR-027 acceptance criteria checkboxes updated — all P0 items checked off.

## [0.4.29] - 2026-02-10

### Added
- **Execution Safety Guards (FR-027)** — P0 tier: protect against unbounded execution in graph pipelines.
  - **Map fan-out cap (`max_items`)**: Node-level `max_items` and graph-level `config.max_map_items` limit Send() fan-out; default 100. Truncates with warning. (REQ-YG-055)
  - **`recursion_limit` exposure**: `config.recursion_limit` parsed from YAML into `GraphConfig`; default 50. (REQ-YG-056)
  - **Loop limits in all node types**: `check_loop_limit` now enforced in tool, python, and passthrough nodes (was LLM-only). (REQ-YG-057)
  - **Linter W012**: Warns when cycle-participating nodes lack `loop_limits` entries. (REQ-YG-058)
- New constants `DEFAULT_RECURSION_LIMIT` (50) and `DEFAULT_MAX_MAP_ITEMS` (100) in `config.py`.
- Requirements REQ-YG-055 through REQ-YG-058 and capability 17 "Execution Safety Guards" in ARCHITECTURE.md.
- 17 new tests in `test_fr027_execution_safety.py`.

## [0.4.28] - 2026-02-10

### Fixed
- **Chaplain audit fixes (FR-026, REQ-YG-054)** — 4 findings from code audit:
  - **HIGH**: `wrap_for_reducer` crash on non-dict python sub-node return — `AttributeError` on `.get()` when function returns string/int/list. Fixed with early `isinstance` guard.
  - **MEDIUM**: LLM `on_error: skip` silently dropped errors — no `PipelineError` recorded in `errors` list, unlike tool/python nodes. Now records error consistently.
  - **MEDIUM**: `on_error: retry/fallback` on tool/python nodes silently became `fail` — added linter check E011 to catch unsupported error strategies at lint time.
  - **LOW**: `prompts_relative=True` with `graph_path=None` + `prompts_dir` set — no warning about degraded resolution. Now logs warning.
- 18 new tests, 2 new linter fixtures. 54 total requirements, 1568 tests, 91% coverage.

## [0.4.27] - 2026-02-10

### Added
- **Linter cross-reference & semantic checks (FR-025, REQ-YG-053)** — 6 new check functions, 9 new issue codes: edge endpoint validation (E006), loop_limits references (E008), passthrough output (E601), tool_call fields (E701/E702), condition syntax (W801), variable prefix (W007), fallback config (E010), conditional edge type (E802). 16 YAML fixture files, 26 new tests. 53 total requirements, 1550 tests, 91% coverage.

## [0.4.26] - 2026-02-10

### Fixed
- **Expression language hardening (REQ-YG-052)** — Three TDD-discovered defects fixed: (1) quote-aware compound split — `and`/`or` inside quoted string values no longer breaks conditions; (2) right-side state reference — unquoted identifiers resolve as state path before literal fallback, enabling `score < threshold`; (3) chained arithmetic detection — `{state.a + state.b + state.c}` raises `ValueError` instead of silent wrong results. 24 new tests.
- 52 total requirements covered. 1524 tests, 91% coverage.

### Changed
- Updated `reference/expressions.md` to reflect new capabilities: right-side state refs, quote-aware parsing, chained arithmetic error.
- Updated FR-024 status to Implemented.

## [0.4.25] - 2026-02-10

### Added
- **Expression Language Reference** (`reference/expressions.md`) — Canonical specification for the YAMLGraph expression language, covering value expressions (`{state.field}`, arithmetic, list/dict operations), condition expressions (comparisons, compound AND/OR, precedence), literal parsing, and `resolve_node_variables` behavior. Includes semi-formal EBNF grammar. Every documented behavior backed by TDD tests. REQ-YG-051.
- **130 TDD tests** (`tests/unit/test_expression_language.py`) — Comprehensive specification tests for the expression language. Discovered and documented several edge cases: dict-in-list limitation, `and`/`or` keywords in string values, multi-item list literals, string vs boolean `true` comparison.
- **Capability 15** in ARCHITECTURE.md — Expression Language (REQ-YG-051). 51 total requirements covered.

### Fixed
- **passthrough-nodes.md** — Corrected incorrect dict-in-list syntax `[{'key': state.val}]` to working dict-direct syntax `{'key': state.val}`. Removed documented-but-unsupported features (chained string concat, Python ternary expressions).

### Changed
- Cross-linked `expressions.md` from `graph-yaml.md`, `passthrough-nodes.md`, `map-nodes.md`, and `getting-started.md`.

## [0.4.24] - 2026-02-10

### Fixed
- **Node-level `model` override (REQ-YG-050)** — The `model` field in graph YAML node config and `defaults` was silently ignored. Only `temperature` and `provider` were extracted. Now `model` flows through the full call chain: `create_node_function()` → `execute_prompt()` → `prepare_messages()` → `create_llm()`. Priority: node config > defaults > prompt YAML > provider default. 8 new tests.

### Changed
- `execute_prompt()`, `PromptExecutor.execute()`, `execute_prompt_async()`, and `execute_prompt_streaming()` all accept `model: str | None` parameter.
- req-coverage: 50/50 requirements covered (was 49/49).

## [0.4.23] - 2026-02-10

### Added
- **Graph-level streaming (FR-023)** — New `run_graph_streaming()` async generator in `executor_async.py`. Runs non-LLM nodes (python, tool) first, then streams the LLM node token-by-token via `llm.astream()`. REQ-YG-048, REQ-YG-049. 7 new tests.
- **Real SSE streaming in proxy** — OpenAI-compatible proxy now streams LLM tokens in real-time via `run_graph_streaming()`, replacing the previous fake word-splitting approach. TTFT reduced from full-generation time to ~200ms.
- **Capability 14** in ARCHITECTURE.md — Graph-Level Streaming (REQ-YG-048, REQ-YG-049). 49 total requirements covered.
- **Proxy demo script** (`examples/openai_proxy/demo.py`) — OpenAI SDK demo with `--stream`, `--verify`, `--prompt`, `--base-url` flags. Works against deployed Fly.io proxy or local server.

## [0.4.22] - 2026-02-10

### Added
- **Google/Gemini provider** — New `google` provider in `llm_factory` using `langchain-google-genai`. Set `PROVIDER=google`, `GOOGLE_API_KEY`, and optionally `GOOGLE_MODEL` (default: `gemini-2.0-flash`). 3 new tests, TDD.
- **OpenAI-compatible guardrail proxy** (`examples/openai_proxy/`) — Fly.io-deployable FastAPI proxy with OpenAI `/v1/chat/completions` API. Graph pipeline: `echo_input` → `validate_input` (stamps `*validation missing*`) → LLM respond. Bearer token auth via `WEB_API_KEY`. 45 tests. Deployed at `yamlgraph-proxy.fly.dev`.
- `python-dotenv` support in proxy for local `.env` loading.

## [0.4.21] - 2026-02-10

### Added
- **LangSmith trace URL display (FR-022)** — After each `graph run` invoke, the LangSmith trace URL is printed when tracing is enabled (`LANGCHAIN_TRACING_V2=true` + `LANGSMITH_API_KEY`). New `--share-trace` flag makes the trace publicly accessible and prints the shareable URL.
- **`yamlgraph/utils/tracing.py`** — Core tracing utilities: `is_tracing_enabled()`, `create_tracer()`, `get_trace_url()`, `share_trace()`, `inject_tracer_config()`. All fail-safe (return None on error).
- **REQ-YG-047** — New requirement for LangSmith tracing. 13 capabilities, 47 requirements, 1341 unique tagged tests, 1671 test-req pairs.

## [0.4.20] - 2026-02-10

### Fixed
- **4 malformed test names** in `test_simple_redis.py` — `testdeep_*` / `teststringify_*` renamed to `test_deep_*` / `test_stringify_*` (pytest convention requires `test_` prefix).
- **req_coverage.py key collisions** — switched from `{stem}::{func}` to class-qualified `{stem}::{Class}::{func}` keys. Fixes 7 tests lost when duplicate method names appeared in different classes within the same file.
- **16 untagged tests** — all test functions now carry `@pytest.mark.req` markers. Tagged tests: 1288 → 1315 unique (matches pytest's 1315 base test functions).

## [0.4.19] - 2026-02-10

### Added
- **Test requirement traceability (ADR-001)** - All 1197 unit tests tagged with `@pytest.mark.req("REQ-YG-XXX")` markers, linking 1623 test-requirement pairs across 46 requirements and 12 capabilities. See `docs/adr/001-test-requirement-traceability.md`.
- **Requirement coverage report** - `scripts/req_coverage.py` generates traceability matrix showing per-capability coverage. Supports `--detail` and `--strict` (CI gate) modes.
- **`req` pytest marker** - Registered in `pyproject.toml` for `@pytest.mark.req(id)` usage.

## [0.4.18] - 2026-02-10

### Changed
- **ARCHITECTURE.md is single source of truth** - Merged `docs/architecture-from-requirements.md` into `ARCHITECTURE.md`. Added end-to-end flow, capabilities & requirements traceability section (12 capabilities, 46 requirements mapped to modules), and expanded file reference table covering all modules with capability cross-references.

### Removed
- **docs/architecture-from-requirements.md** - Content merged into `ARCHITECTURE.md`

## [0.4.17] - 2026-02-08

### Added
- **Reqtracer full-run pipeline** - New `--run-full` flow to run mapping + traceability + baseline under reqtracer
- **Reqtracer graphs** - Mapping and traceability graphs with reqtracer-owned tools and prompts
- **Reqtracer runner tests** - Unit tests for runner command wiring and repo-root module key handling

### Changed
- **Reqtracer E2E flow** - Uses the new run-full pipeline and reqtracer outputs

## [0.4.16] - 2026-02-07

### Fixed
- **Empty YAML error handling** - `load_graph_config()` now raises `ValueError("Empty or invalid YAML file")` instead of `AttributeError` when YAML file is empty or contains only comments/null
- **JSON extraction continuation** - `find_balanced_json()` now continues searching after finding invalid balanced candidates, so valid JSON later in the text is discovered

### Added
- Test coverage for both fixes (9 new tests)

## [0.4.15] - 2026-02-07

### Fixed
- **LLM Jinja2 state context** - `{{ state.foo }}` now renders correctly in LLM node prompts (was passing state as variables only, not as Jinja2 context)
- **Interrupt Jinja2 state context** - Same fix for interrupt node prompts
- **Streaming node resolution** - Streaming nodes now receive `graph_path`, `prompts_dir`, `prompts_relative`, and `state` parameters for full prompt resolution
- **Map node KeyError context** - Raw `KeyError` now includes node name, expression, and available state keys for easier debugging

### Added
- Test coverage for all 4 bug fixes (12 new tests)

## [0.4.14] - 2026-02-07

### Fixed
- **Agent prompt formatting** - Now uses `format_prompt()` instead of regex, supporting Jinja2 templates (`{{ state.topic }}`) and dot notation variables
- **Router dict routing** - Router nodes now correctly route dict outputs (e.g., `parse_json: true`) by checking `isinstance(result, dict)` and using `.get()` instead of `getattr()`
- **on_error: skip stale state** - Skip now returns `{state_key: None, "_skipped": True, "_skip_reason": "error"}` to prevent downstream nodes from using stale data

### Added
- Test coverage for all 3 bug fixes (14 new tests)

## [0.4.13] - 2026-02-05

### Added
- **FR-021: Python sub-nodes in map nodes** - Fan-out over items with Python tool processing
  - `type: python` now supported in map node `node:` configuration
  - Enables parallel Python tool execution with `_map_index` preservation
  - Clear error messages for missing/unknown tools
  - Documentation in `reference/map-nodes.md`
- **Python-map demo** - `examples/demos/python-map/` demonstrating parallel Python tools
- **Soul pattern example** - AI agent personality via `data_files`
  - `examples/demos/soul/` with 3 soul variants (friendly, formal, emo-teen)
  - Pattern 9 documented in `reference/patterns.md`

## [0.4.12] - 2026-02-03

### Added
- **CLI interrupt handling** - `yamlgraph graph run` now handles interrupt nodes interactively
  - Detects `__interrupt__` in graph state and prompts for user input
  - Resumes with `Command(resume=input)` for human-in-the-loop flows
  - Helper `_get_interrupt_message()` extracts display message from interrupt payload
- **Questionnaire example** - Feature request collector demonstrating:
  - `data_files` for schema loading
  - Interrupt loops for multi-turn conversation
  - Probe loop with gap detection and 10-iteration guard
  - Recap flow with confirm/correct/clarify routing
  - Critical analysis and markdown output
  - 31 tests (16 unit + 15 integration)

### Fixed
- Pre-existing ruff issues in `examples/beautify/run.py` and `examples/ocr_cleanup/run.py`

## [0.4.11] - 2026-02-02

### Added
- **FR-021: `data_files` directive** - Load external YAML files into graph state at compile time
  - New `yamlgraph/data_loader.py` module with `load_data_files()` and `DataFileError`
  - Paths resolved relative to graph file (not CWD) for portability
  - Security: Path traversal (`../`) and symlinks blocked via `relative_to()`
  - Empty files normalize to `{}` (not `None`)
  - State collision: Input variables win over `data_files` values
  - Example: `data_files: { schema: schema.yaml }` → `state.schema`
  - Documentation in `reference/graph-yaml.md`
  - Demo: `examples/demos/data-files/`

### Changed
- **State builder** - Now includes `data_files` keys as `Any` type in generated state class

## [0.4.10] - 2026-01-31

### Added
- **CLI --async flag** - `yamlgraph graph run --async` for parallel map node execution
  - Uses `ainvoke()` for guaranteed parallel processing with all LLM providers
  - Particularly useful for Mistral provider which requires async for parallel execution
  - Short form: `-a`
  - Example: `yamlgraph graph run graph.yaml --var topic=AI --async`

### Changed
- **Map nodes documentation** - Added provider comparison table showing parallel behavior
  - Anthropic/OpenAI: Parallel with both `invoke()` and `ainvoke()`
  - Mistral: Requires `ainvoke()` (or `--async` flag) for parallel execution

### Fixed
- `.gitignore` - Added `tmp/` to ignore temporary test files

## [0.4.7] - 2026-01-29

### Removed
- **LangSmith utils from core** - Moved to `examples/demos/run-analyzer/` (464 LOC)
  - `yamlgraph/utils/langsmith.py` → `examples/demos/run-analyzer/utils/`
  - `yamlgraph/utils/langsmith_trace.py` → `examples/demos/run-analyzer/utils/`
  - Tests moved to `examples/demos/run-analyzer/tests/`
  - **Breaking:** `from yamlgraph.utils.langsmith import` no longer works
  - Core LOC: 9,694 → 9,266 (-428 lines)

## [0.4.6] - 2026-01-29

### Changed
- **Linter extracted to subpackage** - Moved from `yamlgraph/tools/` to `yamlgraph/linter/`
  - Public API: `from yamlgraph.linter import lint_graph, LintIssue`
  - Internal structure: `linter/checks.py`, `linter/patterns/*.py`
  - CLI `yamlgraph graph lint` unchanged
  - 1,232 LOC now isolated in dedicated subpackage

### Fixed
- Code-analysis demo: `ruff --output-format=text` → `concise` (text no longer valid)

## [0.4.5] - 2026-01-29

### Removed
- **Websearch from core** - Moved `type: websearch` to examples (243 LOC)
  - `yamlgraph/tools/websearch.py` deleted
  - Removed `websearch_tools` parameter from graph_loader, node_compiler, agent
  - Core LOC: 9,958 → 9,694 (-264 lines)

### Added
- `examples/shared/websearch.py` - Simplified websearch tool for demos (76 LOC)

### Changed
- Web-research and feature-brainstorm demos now use `type: python` for search
  ```yaml
  tools:
    search_web:
      type: python
      module: examples.shared.websearch
      function: search_web
  ```
- Agent nodes now only look up tools in shell or python registries

## [0.4.4] - 2026-01-28

### Removed
- **Mermaid diagram generation** - Removed `yamlgraph graph mermaid` command (106 LOC)
  - Use external tools like mermaid.live or paste YAML to LLMs for diagrams
  - Reduces core complexity; visualization not essential to pipeline execution
- **graph list command** - Removed `yamlgraph graph list` (hardcoded to non-existent `graphs/` dir)
  - Use `find examples -name '*.yaml'` or IDE file search instead

## [0.4.3] - 2026-01-28

### Fixed
- Agent nodes now respect `prompts_relative` and `prompts_dir` config
- Map nodes now respect `prompts_relative` for sub-node prompts
- LLM nodes properly inherit top-level prompt settings
- GraphConfig checks top-level `prompts_relative`/`prompts_dir` before `defaults` block

### Changed
- Refactored `create_agent_node` to use `defaults` dict pattern (consistent with other factories)
- `effective_defaults` now built once at top of `compile_node()` for all node types

### Added
- `tests/unit/test_prompts_relative.py` - 6 tests for prompt config propagation

## [0.4.2] - 2026-01-28

### Breaking Changes
- **FR-013: Demo reorganization** - Demo graphs and prompts moved to `examples/demos/`
  - `graphs/*.yaml` → `examples/demos/{name}/graph.yaml`
  - `prompts/{demo}/` → `examples/demos/{demo}/prompts/`
  - `scripts/demo.sh` → `examples/demos/demo.sh`
  - `DEFAULT_GRAPH` now points to `examples/demos/yamlgraph/graph.yaml`

### Changed
- Demo graphs now use `prompts_relative: true` with co-located prompts
- Updated all tests to use new demo paths
- Linter now correctly resolves `prompts_relative` paths

### Added
- `examples/demos/` directory structure with 14 self-contained demos
- TDD tests in `tests/integration/test_demo_structure.py`

### Removed
- Empty `graphs/` directory (demos moved to `examples/demos/`)
- Demo prompts from global `prompts/` directory

## [0.4.1] - 2026-01-28

### Breaking Changes
- Removed `yamlgraph/builder.py` module
- Removed `build_graph()` from public API

### Changed
- Export `load_and_compile` directly from `yamlgraph` package
- Updated tests to use `load_and_compile()` instead of `build_graph()`

### Added
- New `[npc]` optional dependency group with `python-multipart`

## [0.4.0] - 2026-01-28

### Breaking Changes
- **FR-012: Legacy CLI Removal** (~1,190 lines deleted)
  - Removed `yamlgraph list-runs` command
  - Removed `yamlgraph resume` command
  - Removed `yamlgraph trace` command
  - Removed `yamlgraph export` command
  - Removed `YamlGraphDB` class (use LangGraph checkpointers instead)
  - Removed `build_resume_graph()` function
  - Removed `run_pipeline()` function
  - Removed `yamlgraph/cli/commands.py` and `yamlgraph/cli/validators.py`
  - Removed `yamlgraph/storage/database.py`

### Changed
- **FR-012-0**: `yamlgraph graph run --thread` now uses graph's configured checkpointer
- Refactored `examples/yamlgraph_gen` to use `load_and_compile()` directly
- Updated docs to reflect modern API (`load_and_compile()` vs deprecated `build_graph()`)

### Migration Guide
```python
# Before (deprecated)
from yamlgraph.builder import build_graph
graph = build_graph().compile()

# After (recommended)
from yamlgraph.graph_loader import load_and_compile
graph = load_and_compile("graphs/my-graph.yaml").compile()

# State persistence: use checkpointers in graph.yaml
# checkpointer:
#   type: sqlite
#   path: ~/.yamlgraph/checkpoints.db
```

## [0.3.33] - 2026-01-28

### Added
- **FR-010: Auto-detect Loop Nodes for skip_if_exists**
  - Automatically detect nodes in graph cycles at load time
  - Auto-apply `skip_if_exists: false` to loop nodes (eliminates common footgun)
  - Explicit `skip_if_exists` in YAML overrides auto-detection
  - New `detect_loop_nodes()` and `apply_loop_node_defaults()` functions
  - 16 unit tests for loop detection and auto-application

## [0.3.32] - 2026-01-28

### Added
- **FR-009: JSON Schema Export for IDE Support**
  - New `yamlgraph schema export` CLI command for JSON Schema generation
  - New `yamlgraph schema path` to get bundled schema location
  - Export Pydantic-based schema for VS Code YAML extension support
  - Bundled `graph-v1.json` schema in package
  - New `get_schema_path()` function in public API
  - 22 unit tests for schema export functionality

## [0.3.31] - 2026-01-28

### Added
- **FR-008: TypedDict Code Generation for IDE Support**
  - New `yamlgraph graph codegen <graph.yaml>` CLI command
  - Generates TypedDict Python code from graph state configuration
  - Options: `--output/-o FILE` to write to file, `--include-base` to include base fields
  - Auto-generates class name from graph name (e.g., `hello-world` → `HelloWorldState`)
  - Includes docstrings and generation comments
  - 13 unit tests for codegen functionality

## [0.3.30] - 2026-01-27

### Changed
- Version bump for PyPI release via GitHub Actions

## [0.3.29] - 2026-01-27

### Added
- **LM Studio Provider Support**
  - New `lmstudio` provider for local LLM inference via LM Studio
  - Uses OpenAI-compatible API with custom `base_url`
  - No API key required (local server)
  - Config: `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL`
  - Default model: `qwen2.5-coder-7b-instruct`
  - 8 unit tests for provider integration

## [0.3.28] - 2026-01-27

### Added
- **RAG Tool Demo Fixes & Script**
  - Fixed `examples/rag/graph.yaml` structure: flat YAML (not nested `graph:`), proper `from/to` edges
  - Added `rag_retrieve_node()` state-based wrapper for `type: python` nodes
  - Fixed `prompts/answer.yaml` schema format (`schema:` with `name/fields`)
  - Added `examples/rag/demo.sh` script for one-command demo execution
  - Added `vectorstore/` to `.gitignore`

### Fixed
- **Code Duplication Reduction** (0.3.27 continuation)
  - Core yamlgraph: 2.17% → 0.71% duplication
  - Extracted `build_skip_error_state()` helper to `error_handlers.py`
  - Moved `Chunk` dataclass to `examples/book_translator/models.py`
  - Simplified `storyboard/replicate_tool.py` to re-export from shared

## [0.3.27] - 2026-01-27

### Fixed
- **FR-007: JSON Key Type Coercion for Schema Coding Dicts**
  - Root cause: JSON serialization (Redis checkpointer) converts integer dict keys to strings, causing silent Jinja2 lookup failures
  - Fix: Added `normalize_coding_keys()` to convert integer keys to strings during schema loading
  - Applied in both `build_pydantic_model()` and `build_pydantic_model_from_json_schema()`
  - Ensures coding dicts survive checkpoint round-trips consistently

## [0.3.26] - 2026-01-26

### Fixed
- **CI Test Fixes**
  - Fixed 15 failing unit tests in CI by mocking `load_prompt` instead of requiring external prompt files
  - `test_agent_nodes.py`: Added autouse fixture to mock load_prompt
  - `test_conversation_memory.py`: Added autouse fixture to mock load_prompt
  - `test_jinja2_prompts.py`: Use inline template constant instead of loading from file

## [0.3.25] - 2026-01-26

### Fixed
- **Booking Example Cleanup**
  - Removed accidentally copied yamlgraph core library, demo graphs, and demo prompts from `examples/booking/`
  - Fixed `fly.toml` BOOKING_GRAPH_PATH to point to correct file location (`graph.yaml` not `graphs/booking.yaml`)
  - Code formatting fixes (trailing whitespace, import sorting)

## [0.3.24] - 2026-01-26

### Fixed
- **FR-006: Redis Checkpointer Serialization for Subgraph Interrupts**
  - Root cause: `SimpleRedisCheckpointer` failed when serializing LangGraph internal runtime objects (`CallbackManager`, checkpointers) propagated via `__pregel_checkpointer` during subgraph execution
  - Fix: Updated `serializers.py` to skip LangGraph/LangChain internal types that can't be meaningfully serialized
  - Skipped types include: `CallbackManager`, `BaseCheckpointSaver`, `MemorySaver`, `RedisSaver`, `SimpleRedisCheckpointer`, `PregelLoop`, etc.
  - All 51 Redis unit tests pass
  - All 27 subgraph unit/integration tests pass
  - Added TDD test script: `scripts/test_subgraph_interrupt.py`
  - Added test graphs: `graphs/interrupt-parent-redis.yaml`, `graphs/subgraphs/interrupt-child-with-checkpointer-redis.yaml`

## [0.3.23] - 2026-01-25

### Added
- **xAI/Grok LLM Provider Support**
  - Added `xai` provider to multi-provider LLM factory
  - Uses OpenAI-compatible API with `base_url="https://api.x.ai/v1"`
  - Default model: `grok-beta` (configurable via `XAI_MODEL` env var)
  - Updated router demo to use xAI instead of Mistral
  - Added comprehensive tests for xAI provider

### Fixed
- **Interview Demo Linting**
  - Fixed missing state declarations for interrupt node `state_key` fields
  - Added `name_question` and `topic_question` to state section

## [0.3.22] - 2026-01-24

### Added
- **YAMLGraph Generator** (`examples/yamlgraph_gen/`)
  - Generate complete YAMLGraph pipelines from natural language descriptions
  - Pattern classification: linear, router, map, interrupt, agent, subgraph
  - Snippet-based assembly with 15+ reusable YAML templates
  - Prompt generation for all nodes in the graph
  - Tool stub generation for agent patterns (websearch, python tools)
  - README generation with usage instructions
  - Built-in linting and validation
  - 64 unit tests + 5 E2E tests
  - Helper script `run_generator.py` for CLI usage

### Fixed
- **Template escaping** in prompts with code examples
  - Use `dict()` syntax instead of `{}` to avoid conflicts with Jinja2/format templates
- **`.env` loading** in `run_generator.py`
  - Load `.env` from project root before yamlgraph imports

## [0.3.21] - 2026-01-23

### Added
- **Book Translator Example** (`examples/book_translator/`)
  - Two-phase splitting: LLM identifies markers, Python splits reliably
  - Parallel chunk translation with map nodes
  - Glossary extraction and consistency across chunks
  - Quality gates with optional human review interrupt
  - Sample Finnish Winter War diary (17KB) and German fairy tale
  - Full test coverage with 4 test files

- **`get_map_result()` helper** in book_translator tools
  - Extract results from map node output without hardcoding `_map_*_sub` keys
  - Decouples tools from internal map node key naming

### Fixed
- Pass `graph_path` to map node sub-nodes for relative prompt resolution

## [0.3.20] - 2026-01-22

### Added
- **`adelete_thread()` and `delete_thread()`** methods in `SimpleRedisCheckpointer`
  - Delete all checkpoints for a given thread ID
  - Uses SCAN to find all keys matching thread pattern
  - Required for session cleanup in applications using Redis checkpointer
  - 3 new unit tests added

## [0.3.19] - 2026-01-22

### Added
- **Tuple dict key serialization** in `SimpleRedisCheckpointer`
  - Tuple keys serialized as `"__tuple__:[json_array]"` strings for orjson compatibility
  - LangGraph checkpoints use tuple keys in `channel_versions` and `versions_seen`
  - New `_stringify_keys()` / `_unstringify_keys()` for recursive key conversion
  - 4 new unit tests for tuple key serialization

## [0.3.18] - 2026-01-22

### Added
- **Function serialization** in `SimpleRedisCheckpointer`
  - Functions/callables serialized as `{"__type__": "function", "value": null}`
  - Allows LangGraph internals that include callables to be checkpointed
  - 3 new unit tests for function serialization

## [0.3.17] - 2026-01-22

### Added
- **ChainMap serialization** in `SimpleRedisCheckpointer`
  - Fixes `TypeError: Cannot serialize <class 'collections.ChainMap'>` when graphs contain ChainMap in state
  - ChainMap serialized as `{"__type__": "chainmap", "value": {...}}`
  - Deserialized back to `ChainMap` instance
  - 2 new unit tests for ChainMap serialization

## [0.3.16] - 2026-01-22

### Added
- **Replicate provider support** - New `replicate` provider using LiteLLM for IBM Granite and other Replicate-hosted models
  - Uses `langchain-litellm` for LangChain integration
  - Requires `REPLICATE_API_TOKEN` in `.env`
  - Default model: `ibm-granite/granite-4.0-h-small`
  - Install with: `pip install -e ".[replicate]"`
- **Cost Router example** - New `examples/cost-router/` demonstrating intelligent query routing
  - Classifies queries as simple/medium/complex using cheap Granite model
  - Routes to appropriate tier: Granite (simple), Mistral (medium), Claude (complex)
  - Demonstrates `parse_json: true` for providers without structured output
- **`costrouter` demo** - Added to `scripts/demo.sh` to showcase multi-provider routing

### Changed
- **`parse_json: true` now bypasses output_model** - When set, skips structured output allowing same prompt to work with providers that don't support `response_format`
- **Suppressed Pydantic serializer warnings** for Replicate provider (langchain-litellm type mismatch)
- **Cleaned up replicate dependencies** - Only `langchain-litellm` needed (includes `litellm`)

### Fixed
- **Removed broken innovation symlink** from demo.sh lint command

## [0.3.15] - 2026-01-22

### Fixed
- **Graph linter now supports `defaults.prompts_dir`** - Previously only checked top-level `prompts_dir`, now also checks `defaults.prompts_dir` section for custom prompt directories

### Removed
- **Innovation Matrix example** - Moved to separate [innovation-matrix](https://github.com/sheikki/innovation-matrix) repository

## [0.3.14] - 2026-01-22

### Added
- **Demo script now lints all graphs first** - `scripts/demo.sh` runs `graph lint` on all core graphs before executing demos

### Fixed
- **Graph linter now respects `prompts_dir` config** - Previously always looked in `prompts/`, now uses:
  - Graph's `prompts_dir` setting when present
  - Default `prompts/` folder otherwise
  - Fix suggestions show correct path based on config
- **Added missing node types to linter** - Now recognizes: `agent`, `interrupt`, `llm`, `map`, `passthrough`, `python`, `router`, `subgraph`

## [0.3.13] - 2026-01-21

### Changed
- **Refactored graph_commands.py into modules** - Split 541-line file into focused modules
  - `graph_commands.py` (243 lines) - Core commands: run, list, info, dispatch
  - `graph_mermaid.py` (107 lines) - Mermaid diagram generation
  - `graph_validate.py` (230 lines) - Validation and linting commands
  - All modules under 250 lines (limit: 400)

- **Added debug logging to prompt resolution** - `resolve_prompt_path()` now logs:
  - Which resolution path was chosen (graph-relative, prompts_dir, default, fallback)
  - All tried paths on failure for easier debugging

- **Documented sync/async design pattern** in ARCHITECTURE.md
  - Explains sync-first with async wrappers approach
  - Rationale for current structure vs async-first alternative

### Fixed
- Ruff B904/B905 lint errors in examples (raise from err, zip strict)

### Removed
- Redundant `scripts/test_interrupt_fix.py` (covered by integration tests)

## [0.3.12] - 2026-01-21

### Changed
- **DRY refactor of executor modules** - Extracted shared code to `executor_base.py`
  - New `prepare_messages()` helper eliminates 3x duplicated prompt loading logic
  - Shared `format_prompt()` and `is_retryable()` functions
  - `executor.py` and `executor_async.py` now import from base module
  - Cleaner separation of sync/async concerns

### Added
- **Documentation for error/errors design pattern**
  - `state_builder.py` - Explains `error` (singular, overwrite) vs `errors` (plural, accumulator)
  - `tool_nodes.py` - Clarifies nested tool result `error` is not state-level
  - `llm_nodes.py` - Notes `errors` uses add reducer for accumulation

## [0.3.11] - 2026-01-21

### Changed
- **Refactored node_factory into package** - Split 768-line monolith into focused modules
  - `base.py` (90 lines) - `resolve_class`, `get_output_model_for_node`
  - `llm_nodes.py` (208 lines) - `create_node_function`
  - `streaming.py` (72 lines) - `create_streaming_node`
  - `tool_nodes.py` (90 lines) - `create_tool_call_node`
  - `control_nodes.py` (147 lines) - `create_interrupt_node`, `create_passthrough_node`
  - `subgraph_nodes.py` (220 lines) - `create_subgraph_node`, state mapping helpers
  - All modules under 230 lines (limit: 400)
  - Public API unchanged via `__init__.py` re-exports

## [0.3.10] - 2026-01-21

### Added
- **redis-simple checkpointer type** - Plain Redis support for Upstash/Fly.io (FR add-simple-redis-checkpointer)
  - New `SimpleRedisCheckpointer` class using standard Redis commands (GET, SET, SCAN, DEL)
  - No Redis Stack (RediSearch, RedisJSON) requirement
  - Uses `orjson` for secure JSON serialization (no pickle)
  - Supports both sync and async Redis operations
  - Stores only latest checkpoint per thread (no history)
  - New optional dependency: `pip install yamlgraph[redis-simple]`

- **Async checkpointer factory** - New `get_checkpointer_async()` function
  - Properly initializes async checkpointers with `await saver.asetup()`
  - Deprecated `async_mode=True` parameter on `get_checkpointer()`
  - Added `shutdown_checkpointers()` for graceful cleanup

### Fixed
- **Async Redis checkpointer bug** (FR fix-async-redis-checkpointer)
  - `AsyncRedisSaver.from_conn_string()` returns context manager, not saver instance
  - Sync Redis now uses direct instantiation: `RedisSaver(redis_url=url)`
  - Async Redis uses `get_checkpointer_async()` for proper initialization
  - `compile_graph_async()` is now properly async

### Changed
- `compile_graph_async()` changed from sync to async function
- `load_and_compile_async()` now awaits `compile_graph_async()`

## [0.3.8] - 2026-01-20

### Added
- **interrupt_output_mapping for subgraphs** (FR-006) - Expose child state during interrupts
  - New `interrupt_output_mapping` field in subgraph node config
  - Maps child state → parent when subgraph hits an interrupt node
  - Uses LangGraph's internal `__pregel_send` to update parent state before interrupt propagates
  - `output_mapping` still used for normal completion (reaches END)
  - 3 integration tests for interrupt output mapping
  - See [reference/subgraph-nodes.md](reference/subgraph-nodes.md#interrupt-output-mapping-fr-006)

## [0.3.7] - 2026-01-20

### Added
- **interrupt_output_mapping for subgraphs** (FR-006) - Expose child state during interrupts
  - New `interrupt_output_mapping` field in subgraph node config
  - Maps child state → parent when subgraph hits an interrupt node
  - `output_mapping` still used for normal completion (reaches END)
  - `__interrupt__` marker auto-forwarded to parent graph
  - See [reference/subgraph-nodes.md](reference/subgraph-nodes.md#interrupt-output-mapping-fr-006)

### Fixed
- **prompts_relative + prompts_dir** - When both are set, prompts_dir is now resolved relative to graph_path.parent
  - Fixed `yamlgraph/utils/prompts.py` resolve_prompt_path() to combine graph_path.parent with prompts_dir
  - New resolution order: graph-relative + prompts_dir takes precedence over standalone prompts_dir
  - Added `test_prompts_relative_with_prompts_dir_combines_paths()` regression test
  - All 16 unit tests and 2 integration tests pass

## [0.3.6] - 2026-01-20

### Fixed
- **prompts_relative bug** - Complete fix for graph-relative prompt resolution
  - `node_factory.create_node_function()` now passes path params to executor
  - `create_interrupt_node()` now accepts and forwards path params
  - `graph_loader._compile_node()` extracts prompts config from defaults
  - Integration test verifies path params forwarded to `execute_prompt()`

## [0.3.5] - 2026-01-20

### Fixed
- **prompts_relative bug (partial)** - Added path params to executor API
  - Added `graph_path`, `prompts_dir`, `prompts_relative` params to `execute_prompt()`
  - Added same params to `PromptExecutor.execute()` method
  - 3 new unit tests for executor path resolution

## [0.3.4] - 2026-01-20

### Fixed
- Ruff linter compliance: 17 style fixes across test files
  - Combined nested `with` statements (SIM117)
  - Combined nested `if` statements (SIM102)
  - Removed unused variables (F841)
  - Removed whitespace in blank lines (W293)

## [0.3.3] - 2026-01-20

### Added
- **Graph-Relative Prompts** (FR-A) - Colocate prompts with graphs
  - `defaults.prompts_relative: true` resolves prompts relative to graph file
  - `defaults.prompts_dir: path/to/prompts` explicit prompts directory
  - Enables clean multi-graph project structures
  - See [reference/graph-yaml.md](reference/graph-yaml.md#defaults)
- **JSON Extraction** (FR-B) - Auto-extract JSON from LLM responses
  - Node-level `parse_json: true` extracts JSON from markdown code blocks
  - `extract_json()` utility in `yamlgraph.utils`
  - Cascading extraction: raw → ```json``` → ```...``` → `{...}` pattern
  - See [reference/graph-yaml.md](reference/graph-yaml.md#type-llm---standard-llm-node)
- Integration test for colocated prompts
- 22 new unit tests for FR-A and FR-B

### Changed
- `resolve_prompt_path()` accepts `graph_path` and `prompts_relative` params
- `create_node_function()` threads graph_path for relative resolution
- `load_prompt()` and `load_prompt_path()` support new resolution options

## [0.3.2] - 2026-01-20

### Added
- **NPC Encounter Web API** - HTMX-powered web UI for running NPC encounters
  - FastAPI backend with session persistence (`examples/npc/api/`)
  - Session adapter pattern for stateless servers with checkpointer state
  - MemorySaver default, RedisSaver via `REDIS_URL` env var
  - Interrupt detection and resume with `Command(resume=input)`
  - Map node output parsing (`{'_map_index': N, 'value': '...'}`)
  - HTML templates with HTMX fragments
  - Integration tests (20 passing)
- **Web UI + API Reference** - `reference/web-ui-api.md`
  - Architecture diagram, directory structure
  - Session adapter, routes, HTMX templates patterns
  - Interrupt handling and checkpointer options
- **Application Layer Pattern** in ARCHITECTURE.md
  - Three-layer architecture: Presentation → Logic → Side Effects
  - API integration patterns with example code

### Changed
- NPC example graphs now use `mistral` provider (was `anthropic`)

## [0.3.1] - 2026-01-20

### Added
- **ARCHITECTURE.md** - Internal architecture guide for core developers
  - Design philosophy (YAML-first, dynamic state)
  - Module architecture diagrams
  - Extension points (adding node types, LLM providers, tool types)
  - Testing strategy and code quality rules
- **CLI Reference** - `reference/cli.md` with complete command documentation
- **Subgraph Nodes Reference** - `reference/subgraph-nodes.md` with state mapping patterns
- **Documentation Index** - Comprehensive reference/README.md with reading order
- **Reading Order Guide** - Beginner → Intermediate → Advanced path in main README

### Changed
- Reorganized reference documentation with structured tables
- Updated graph-yaml.md with all 9 node types documented
- Added websearch tool documentation to graph-yaml.md
- Fixed broken link: `docs/tools-langsmith.md` → `reference/langsmith-tools.md`
- Fixed outdated path: `graphs/impl-agent.yaml` → `examples/codegen/impl-agent.yaml`
- Renamed getting-started.md to clarify it's for AI coding assistants
- Added link to ARCHITECTURE.md from main README

### Fixed
- Accurate line counts in ARCHITECTURE.md file reference table

## [0.3.0] - 2026-01-19

### Added
- **Subgraph Nodes** for composing graphs from other YAML graphs
  - New `type: subgraph` node embeds child graphs
  - Two modes: `mode: invoke` (explicit state mapping) or `mode: direct` (shared schema)
  - Input/output mapping: `{parent_key: child_key}`, `"auto"`, or `"*"`
  - Thread ID propagation for checkpointer continuity
  - Circular reference detection with clear error messages
  - Nested subgraphs supported (graphs within graphs)
  - See demo: `graphs/subgraph-demo.yaml`

### Changed
- Moved impl-agent to `examples/codegen/` as self-contained example
  - Tools: `examples/codegen/tools/` (13 analysis tools)
  - Prompts: `examples/codegen/prompts/`
  - Graph: `examples/codegen/impl-agent.yaml`
  - Tests: `examples/codegen/tests/` (16 test files)
  - Run: `yamlgraph graph run examples/codegen/impl-agent.yaml`
- Updated ruff linting rules: added B (bugbear), C4 (comprehensions), UP (pyupgrade), SIM (simplify)
- Removed dead code: `log_execution`, `set_executor`, `get_checkpointer_for_graph`, `log_with_context`

## [0.2.0] - 2026-01-19

### Added
- **Interrupt Nodes** for human-in-the-loop workflows
  - New `type: interrupt` node pauses graph execution
  - Resume with `Command(resume={...})` providing user input
  - See [reference/interrupt-nodes.md](reference/interrupt-nodes.md)
- **Checkpointer Factory** with Redis support
  - Configure checkpointers in YAML: `memory`, `sqlite`, `redis`
  - Async variants: `redis_async`, `memory` (for async)
  - Environment variable expansion in connection strings
  - Optional dependency: `pip install yamlgraph[redis]`
  - See [reference/checkpointers.md](reference/checkpointers.md)
- **Async Executor** for web framework integration
  - `run_graph_async()` - Run graphs with interrupt handling
  - `compile_graph_async()` - Compile with async checkpointer
  - `load_and_compile_async()` - Load YAML and compile async
  - See [reference/async-usage.md](reference/async-usage.md)
- **Streaming Support** for real-time token output
  - `execute_prompt_streaming()` - Async generator yielding chunks
  - `stream: true` node config for YAML-defined streaming
  - `create_streaming_node()` factory function
  - See [reference/streaming.md](reference/streaming.md)
- FastAPI integration example (`examples/fastapi_interview.py`)
- Interview demo graph (`graphs/interview-demo.yaml`)
- 51 new unit tests (891 total, 86% coverage)

### Changed
- `executor_async.py` expanded with graph execution APIs
- `node_factory.py` supports `type: interrupt` and `stream: true`
- `graph_loader.py` integrates checkpointer factory

## [0.1.4] - 2026-01-18

### Added
- Implementation Agent expanded to **14 tools** for comprehensive code analysis
  - `git_blame` - Get author, date, commit for specific lines
  - `git_log` - Get recent commits for a file
  - `syntax_check` - Validate Python code syntax
  - `get_imports` - Extract all imports from a Python file
  - `get_dependents` - Find files that import a given module
- Patch-style output format in implementation plans
  - Changes now include actual code: `file:LINE ACTION | after: context | code: ...`
  - Supports ADD, MODIFY, CREATE, DELETE actions
- 33 new tests for Phase 4-6 tools

### Changed
- Analyze prompt now includes git context guidance
- Single-line references in output (e.g., `shell.py:38` not `:1-50`)
- Structured discovery output (no narrative paragraphs)

## [0.1.3] - 2026-01-18

### Added
- Implementation Agent (`graphs/impl-agent.yaml`) for code analysis
  - Analyzes codebases and generates implementation plans
  - 9 tools: AST analysis, text search, jedi semantic analysis
  - Detects existing implementations before suggesting changes
- Code analysis tools subpackage (`yamlgraph.tools.analysis`)
  - `get_module_structure` - AST-based structure extraction
  - `read_lines`, `search_in_file`, `search_codebase` - text search
  - `find_refs`, `get_callers`, `get_callees` - jedi semantic analysis
  - `list_package_modules` - package module discovery
- `analysis` optional dependency group (`pip install yamlgraph[analysis]`)
- Reference documentation for impl-agent (`reference/impl-agent.md`)

### Changed
- Refactored analysis tools into `examples/codegen/tools/` as self-contained example
- Agent nodes now support `max_iterations` config (default 10)

## [0.1.2] - 2026-01-18

### Added
- Graph linter (`yamlgraph graph lint`) for static analysis of YAML graphs
  - Checks: missing state declarations, undefined tools, missing prompts, unreachable nodes, invalid node types
  - Error codes: E001-E005 (errors), W001-W003 (warnings)
- Feature Brainstormer meta-graph (`graphs/feature-brainstorm.yaml`)
  - Analyzes YAMLGraph codebase and proposes new features
  - Uses web search for competitive analysis
  - Outputs prioritized roadmap
- Web search tool (`type: websearch`) with DuckDuckGo integration
- `websearch` optional dependency group (`pip install yamlgraph[websearch]`)
- Sample `web-research.yaml` graph demonstrating web search agent

## [0.1.1] - 2026-01-17

### Added
- `demo.sh` script to run all demos with single command
- Pydantic schema validation for graph configuration (`GraphConfigSchema`, `NodeConfig`, `EdgeConfig`)
- Compile-time validation of condition expressions in edges
- `sorted_add` reducer for guaranteed ordering in map node fan-in
- Consolidated expression resolution in `expressions.py` module
- Comprehensive unit tests for conditions, routing, and expressions
- Security section in README documenting shell injection protection

### Changed
- State is now dynamically generated from YAML config (no manual `state.py` needed)
- Map node results are automatically sorted by `_map_index` during collection
- Config paths (`prompts/`, `graphs/`, `outputs/`, `.env`) now resolve from current working directory instead of package install location

### Removed
- `output_key` node config field - use `state_key` instead
- `should_continue()` routing function - use expression-based conditions
- Legacy `continue`/`end` condition keywords - use expression conditions like `field > value`
- Legacy `mermaid` CLI command - use `graph info` for graph visualization
- `get_graph_mermaid()`, `print_graph_mermaid()`, `export_graph_png()` functions
- `PROJECT_ROOT` config constant - use `WORKING_DIR` instead

### Fixed
- Map node ordering now guaranteed regardless of parallel execution timing
- README architecture documentation updated to reflect dynamic state generation
- `.env` file now correctly loaded from current directory when installed via `pip install yamlgraph`

## [0.1.0] - 2026-01-17

### Added
- YAML-based graph definition with `graphs/*.yaml`
- YAML prompt templates with Jinja2 support
- Multi-provider LLM support (Anthropic, Mistral, OpenAI)
- Node types: `llm`, `router`, `agent`, `tool`, `python`, `map`
- Expression-based conditional routing
- Loop limits with automatic termination
- Map nodes for parallel fan-out/fan-in processing
- Agent nodes with tool calling
- Shell tool execution with `shlex.quote()` sanitization
- SQLite state persistence and checkpointing
- LangSmith integration for observability
- CLI commands: `graph run`, `graph list`, `graph info`, `graph validate`
- Resume support for interrupted pipelines
- JSON export of pipeline runs
- Animated storyboard demo with image generation

### Security
- Shell command variables sanitized with `shlex.quote()`
- Prompt input sanitization for dangerous patterns
- No use of `eval()` for expression evaluation
