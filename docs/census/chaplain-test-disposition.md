# Chaplain disposition census (FR-1012 Step 0)

Source `d7601937` · 115 rows · unresolved 0 · canaries pass

| path | kind | verdict | manual_review | reqs | reason |
|---|---|---|---|---|---|
| `capabilities/CAP-106-github-issues-remote-inbox.yaml` | cap | retire |  | REQ-YG-247 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed only via doc modules (.github/copilot-instructions.md, CLAUDE.md); the remote-inbox importer watch.sh is the retired runtime; witness test_github_issues_remote_inbox.py is already skipped and is delete. |
| `capabilities/CAP-109-harden-remote-inbox.yaml` | cap | retire |  | REQ-YG-256 | model: watch.sh gates GitHub Issue import on .chaplain/allowed-authors.txt |
| `capabilities/CAP-113-chaplain-research-step.yaml` | cap | retire |  | REQ-YG-260 | model: Research guidance in the active watcher-plan runtime. The unified planning step and watcher-plan research prompt |
| `capabilities/CAP-114-automated-post-merge-finalization.yaml` | cap | keep |  | REQ-YG-261 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed by rule and by FR-1010 R-4: finalize_lib.sh/finalize_merge.sh are live (CAP-38/45); REQ-YG-261 witnessed by test_automated_post_merge_finalization.py (keep). Drop the phantom .chaplain/watch.sh module in GREEN; the watcher-automation prose is the only dead claim. |
| `capabilities/CAP-116-acceptance-tests-before-enforce.yaml` | cap | retire |  | REQ-YG-263 | human resolution (operator (decision 'New module-map CAP, retire CAP-116' via enforcing session), 2026-09-06): OPERATOR 2026-09-06 after investigation: REQ-YG-263's two outside witnesses (test_fr331_static_module_map_tier2_context.py, test_fr335_module_map_compression.py) were mis-tagged live module-map tests — FR-331/FR-335 had no CAP. New CAP-265 / REQ-YG-667 'Static module map' allocated and both tests re-tagged in the same branch; REQ-YG-263 is then witnessed only by test_acceptance_tests_before_enforce.py (delete). CAP-116's six modules are all .chaplain/ files Phase 2 deletes. Manifest fan-in for this row reflects the tree before the re-tag. |
| `capabilities/CAP-124-watcher2-pr-reuse.yaml` | cap | retire |  | REQ-YG-272 | model: .chaplain/lib/watcher/create_pr.sh |
| `capabilities/CAP-125-pipeline-script-retirement.yaml` | cap | retire |  | REQ-YG-276 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed only via doc modules (CLAUDE.md, README.md); describes the FR-276/FR-317 retirement of watch.sh-era scripts — history the archive keeps; witness test_retire_old_pipeline_scripts.py is delete. |
| `capabilities/CAP-128-chaplain-documentation.yaml` | cap | retire |  | REQ-YG-278 | model: Comprehensive documentation for the FSM runtime orchestrator and shell library in .chaplain/README.md covering architecture, usage, and troubleshooting. |
| `capabilities/CAP-130-watcher2-finalize-optimization.yaml` | cap | retire |  | REQ-YG-286 | model: Watcher2 Finalize Pre-commit Optimization
  description: >
  Optimize watcher2 finalize step to reduce copilot session invocations by pre-formatting
  code before pre-commit loops |
| `capabilities/CAP-132-watcher2-ci-resilience.yaml` | cap | retire |  | REQ-YG-294, REQ-YG-298, REQ-YG-299, REQ-YG-300, REQ-YG-301 | model: Fix wait_ci.sh check ordering and CI resilience patterns for the watcher pipeline. v1 CI remediation artifacts (step-ci-remediate, enforce-ci-remediate) retired by FR-305; v2 handles CI fixes inside enforce_session. |
| `capabilities/CAP-133-watcher2-ci-remediation-crash-fix.yaml` | cap | retire |  | REQ-YG-307 | model: Fix three bugs in the watcher2 CI remediation loop that cause immediate script crash |
| `capabilities/CAP-134-watcher2-changelog-auto-generation.yaml` | cap | retire |  | REQ-YG-308 | model: Auto-generate changelog fragments in watcher2 pipeline to eliminate manual intervention. Defense-in-depth approach with shell generation, prompt instructions, finalize verification, and CI remediation context. |
| `capabilities/CAP-135-watcher2-forensic-failure-diary.yaml` | cap | retire |  | REQ-YG-309 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model retire 0.95 but evidence span stitched name+description across YAML lines (inexact). Watcher2 forensic diary is runtime-only; REQ-YG-309's only witness is test_retire_old_pipeline_scripts.py (delete). |
| `capabilities/CAP-137-watcher-fsm-startup-script.yaml` | cap | retire |  | REQ-YG-315 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model retire 0.95, inexact span (YAML folded description). Sole module .chaplain/scripts/start-system.sh; FR-1010 R-3 cites it as proof the archive is not runnable. |
| `capabilities/CAP-138-watcher-pipeline-fsm-simplification.yaml` | cap | retire |  | REQ-YG-316 | model: Simplified watcher pipeline v2: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session. Enforce resumes plan session. Dispatcher flag-gated via pipeline_version. |
| `capabilities/CAP-140-watcher2-validate-split-fix-gate.yaml` | cap | retire |  | REQ-YG-318 | model: Split watcher2 post-enforce validation into deterministic micro-remediation fast path (micro_changelog + micro_title), explicit LLM remediation fallback (validate_fix), and deterministic CI-parity gate (validate_gate) |
| `capabilities/CAP-142-skill-export.yaml` | cap | retire |  | REQ-YG-320, REQ-YG-321, REQ-YG-322, REQ-YG-323, REQ-YG-324, REQ-YG-325, REQ-YG-326 | model: RETIRED by FR-912. Four months, zero committed artifacts: every file under `.github/skills/` is hand-authored (CAP-158/FR-446), including the flagship graph-authoring skill written by hand while this generator existed. No script, CI job, hook, or chaplain pipeline ever invoked the exporter; its only importers were its own CLI dispatch and its own RED tests. |
| `capabilities/CAP-150-philosopher-book-demo.yaml` | cap | keep |  | REQ-YG-404, REQ-YG-405 | model: Demo pipeline generating one chapter at a time of a philosophical work on cognitive traps. Plan → write a single chapter using Copilot with diary search tools. |
| `capabilities/CAP-152-watcher2-dispatcher-audit-cadence.yaml` | cap | retire |  | REQ-YG-407 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed only via generated ARCHITECTURE.md listed as a module; dispatcher/inquisitor cadence is the retired runtime; witness test_fr411_*.py is delete. |
| `capabilities/CAP-158-copilot-skill-promotion.yaml` | cap | keep |  | REQ-YG-423 | model: Promote reference docs to Copilot Skills (.github/skills/) for on-demand loading in VS Code Copilot Chat. |
| `capabilities/CAP-165-watcher2-baseline-dead-code-removal.yaml` | cap | retire |  | REQ-YG-466 | model: Remove all FR-277 watcher2 baseline checkpointing dead code: Python modules, packages, graphs, tests, capability registrations, and documentation references. |
| `capabilities/CAP-193-watcher-wrapper-json-envelope.yaml` | cap | retire |  | REQ-YG-528 | model: .chaplain/lib/watcher/worktree_setup.sh |
| `capabilities/CAP-205-world-distill.yaml` | cap | keep |  | REQ-YG-563 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model keep 0.95 but quoted the RUBRIC, not the payload. Live: graphs/world_distill relocated by FR-1011; test_world_distill.py keep. |
| `capabilities/CAP-206-fr-triage-graph.yaml` | cap | keep |  | REQ-YG-564 | model: graphs/fr_triage |
| `capabilities/CAP-259-declared-text-encoding.yaml` | cap | keep |  | REQ-YG-638 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model keep 0.95, inexact span. Live encoding contract (FR-951) that merely lists .chaplain/ among covered roots; REQ-YG-638 has 2 outside witnesses. |
| `capabilities/CAP-264-chaplain-runtime-retired.yaml` | cap | keep |  | REQ-YG-666 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model retire 0.95 — self-referential error: this is the live capability record for Phase 2 itself (census tooling, REQ-YG-666). |
| `capabilities/CAP-36-inquisitor-auto-propose.yaml` | cap | retire |  | REQ-YG-118 | model: Inquisitor Auto-Propose
  description: >
  --propose flag on inquisitor.sh detects violations persisting across
  consecutive Inquisitor Audit entries and writes targeted fix proposals to
  .chaplain/inbox/. |
| `capabilities/CAP-39-inquisitor-commit-delta-gate.yaml` | cap | retire |  | REQ-YG-131 | model: inquisitor.sh commit-delta gate extracts last audit SHA from docs/diary/, counts feat:/fix: commits since that SHA, and aborts when none found. |
| `capabilities/CAP-42-inquisitor-worktree-gate.yaml` | cap | retire |  | REQ-YG-142 | model: inquisitor.sh worktree gate detects git worktree context and exits early, suppressing audit and propose phases during enforce pipeline |
| `capabilities/CAP-44-judge-split-verdict.yaml` | cap | retire |  | REQ-YG-143 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model abstained (schema validation error on its own output). Modules: examples/copilot/prompts/judge.yaml (absent), scripts/chaplain-prompts/judge.md (non-census deletion set); its only witness test_judge_split_verdict.py is delete; the live judge is .github/skills/judge-fr. |
| `capabilities/CAP-55-chaplain-inbox-documentation.yaml` | cap | retire |  | REQ-YG-153 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed only because its module CLAUDE.md exists; the documented behaviour (.chaplain/inbox/ workflow) is gone since FR-1011 and FR-942. Witness test_claude_md_chaplain_inbox.py is delete. |
| `capabilities/CAP-64-concurrency-safety-map.yaml` | cap | keep |  | REQ-YG-160 | model: Covers 6 areas: map node fan-out, checkpoint writes, graph cache, inquisitor diary writes, MCP server, async executor. |
| `capabilities/CAP-67-philosopher-daemon.yaml` | cap | keep |  | REQ-YG-184, REQ-YG-185, REQ-YG-194 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model asked for manual review. The philosopher graph was relocated and kept by FR-1010/FR-1011 (graphs/philosopher/); CAP-67's module list still points at examples/philosopher/* (absent since FR-196) and .chaplain/philosopher.sh — module paths must be repointed in GREEN, capability stays. |
| `capabilities/CAP-72-knowledge-graph-mass-graduation-fr193.yaml` | cap | keep |  | REQ-YG-192 | model: Graduates 8 recurring patterns from diary analysis into the Scripture Knowledge Graph in .github/copilot-instructions.md |
| `capabilities/CAP-73-philosopher-challenge-node.yaml` | cap | keep |  | REQ-YG-193 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): mixed by rule: REQ-YG-193 witnessed by test_philosopher.py (keep); modules point at examples/philosopher/* (absent). Philosopher kept by FR-1010; repoint modules to graphs/philosopher/ in GREEN. |
| `capabilities/CAP-75-portable-chaplain.yaml` | cap | keep |  | REQ-YG-196, REQ-YG-529 | model: Enables graph-scope portability (graphs/philosopher/) by bypassing dotted-package import restrictions with deterministic graph-scoped loading. |
| `capabilities/CAP-79-demo-proof-gate.yaml` | cap | keep |  | REQ-YG-200 | model: CI gate and pre-commit hook requiring demo-output.log artifact when demos are created or modified |
| `tests/integration/test_copilot_session_propagation.py` | test | keep |  | REQ-YG-105 | model: from yamlgraph.compile.graph_loader import compile_graph, load_graph_config |
| `tests/unit/test_acceptance_tests_before_enforce.py` | test | delete |  | REQ-YG-263 | model: PIPELINE_CONFIG = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml" |
| `tests/unit/test_automated_post_merge_finalization.py` | test | keep |  | REQ-YG-261 | model: Shared library `scripts/lib/finalize_lib.sh` functions work correctly (relocated by FR-1011)
2. `scripts/finalize_merge.sh` sources the shared library |
| `tests/unit/test_chaplain_graph_compile.py` | test | keep |  | REQ-YG-529 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model delete 0.95 with an inexact span (comment lines). The test compiles graphs/ (live) and .chaplain/graphs (runtime); its REQ-YG-529 (CAP-75 proxy wiring) has no other witness. Keep; GREEN drops the .chaplain root from its glob and lowers the >=7 count. |
| `tests/unit/test_chaplain_readme_documentation.py` | test | delete |  | REQ-YG-278 | model: Tests for FR-195: Chaplain Documentation

Validates that .chaplain/README.md exists and contains comprehensive
documentation covering the FSM runtime architecture and shell library. |
| `tests/unit/test_chaplain_research_step.py` | test | delete |  | REQ-YG-260 | model: Tests for FR-257: Chaplain research guidance in watcher-plan runtime. |
| `tests/unit/test_ci_demo_proof_gate.py` | test | keep |  | REQ-YG-200 | model: Validates that the `demo-gate` job in `.github/workflows/commitlint.yml` blocks PRs that modify demo files without including a `demo-output.log`, and that `scripts/check_demo_proof.sh` enforces the same locally via pre-commit. |
| `tests/unit/test_claude_md_chaplain_inbox.py` | test | delete |  | REQ-YG-153 | model: FR-163 chaplain inbox instructions — retired under FR-942.

Operator amendment during FR-942 enforcement (2026-08-31): the chaplain
runtime is not running |
| `tests/unit/test_concurrency_safety_doc.py` | test | keep |  | REQ-YG-160 | model: # The areas from the FR acceptance criteria (MCP server retired by FR-910)
REQUIRED_SECTIONS = [
    "Map Node Fan-Out",
    "Checkpoint Writes",
    "Graph Cache",
    "Inquisitor Diary Writes",
    "Async Executor",
] |
| `tests/unit/test_create_worktree.py` | test | delete |  | REQ-YG-106 | model: Unit tests for .chaplain/lib/worktree.py create_worktree() (FR-265). |
| `tests/unit/test_diary_digest.py` | test | keep |  | REQ-YG-072, REQ-YG-090 | model: from examples.diary_digest.nodes.writing import format_diary_entry |
| `tests/unit/test_diary_index.py` | test | keep |  | REQ-YG-257 | model: Tests for the diary-index demo: aggregate_index() ground-truth fixture, graph YAML loading/linting, list_diary_files() structure, write_index() output. |
| `tests/unit/test_ebook_writing.py` | test | keep |  | REQ-YG-091 | model: write_chapters_tool writes formatted chapter content to disk |
| `tests/unit/test_enforce_simplify.py` | test | delete |  | REQ-YG-001, REQ-YG-012 | model: """Tests for active watcher enforce session graph.""" |
| `tests/unit/test_fr1011_relocation.py` | test | keep |  |  | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model delete 0.95 — wrong: this is the FR-1011 relocation witness for the live graphs and proposals/ route (module-level pytestmark, so the extractor sees no REQ and fan-in could not protect it). |
| `tests/unit/test_fr1012_chaplain_census.py` | test | keep |  |  | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model delete 0.95 — self-referential error: the census tooling's own witness (REQ-YG-666 via module-level pytestmark). |
| `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` | test | keep |  |  | model: graphs/fr_triage/graph.yaml", "exists", True),  # relocated by FR-1011 |
| `tests/unit/test_fr278_remove_baseline_dead_code.py` | test | delete |  | REQ-YG-466 | model: yamlgraph/chaplain/baseline.py must not exist |
| `tests/unit/test_fr289_watcher2_post_merge_inbox_consumption.py` | test | delete |  | REQ-YG-276 | model: POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh" |
| `tests/unit/test_fr296_watcher_fsm_startup_script.py` | test | delete |  | REQ-YG-315 | model: Tests for .chaplain/scripts/start-system.sh — validates the script exists, is executable, has correct structure (phases, signal handling, --inbox flag), and uses the correct statemachine CLI invocations. |
| `tests/unit/test_fr305_watcher_pipeline_v2.py` | test | delete |  | REQ-YG-316 | model: FR-305: Watcher Pipeline FSM Simplification.

Tests for the v2 pipeline config:
- 11 operational states + 3 terminals
- Transition correctness (happy path, revise loop, failure paths, timeouts)
- Judge uses different model from plan (no session resume)
- FR-309: Judge event_map aligned to prompt vocabulary
- FR-309: Enforce session runs fresh (no resume)
- Action types correct for each state |
| `tests/unit/test_fr310_watcher2_validate_precommit_states.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"

PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml" |
| `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py` | test | delete |  | REQ-YG-027 | model: ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "git_commit_action.py" |
| `tests/unit/test_fr312_watcher2_post_merge_main_sync.py` | test | delete |  | REQ-YG-276 | model: POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh" |
| `tests/unit/test_fr315_yamlgraph_async_stdout_logging_without_event_map.py` | test | delete |  | REQ-YG-027 | model: ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py" |
| `tests/unit/test_fr316_watcher2_sanity_check_state.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml" |
| `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml" |
| `tests/unit/test_fr318_watcher2_sanity_check_diary_contract.py` | test | delete |  | REQ-YG-316 | model: PROMPT_FILE = Path(".chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml") |
| `tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py` | test | delete |  | REQ-YG-027 | model: ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py" |
| `tests/unit/test_fr321_watcher_validate_fix_gate_diagnostics_handoff.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_SESSION_GRAPH = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "validate-session.yaml"
) |
| `tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py` | test | delete |  | REQ-YG-027 | model: sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.chaplain"))
from actions.yamlgraph_async_action import YamlgraphAsyncAction |
| `tests/unit/test_fr329_agent_sdk_planner_spike.py` | test | delete |  | REQ-YG-087 | model: WORKTREE / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml",
    WORKTREE / ".chaplain" / "config" / "watcher-pipeline-v2.yaml", |
| `tests/unit/test_fr337_context_planner_pre_node.py` | test | delete |  | REQ-YG-001 | model: .chaplain/graphs/watcher-enforce/prompts/context-planner.yaml |
| `tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py` | test | delete |  | REQ-YG-276 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
POST_MERGE_SH = CHAPLAIN / "lib" / "watcher" / "post_merge.sh" |
| `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py"
SELECT_PRIMARY_TITLE = CHAPLAIN / "lib" / "watcher" / "select_primary_pr_title.sh" |
| `tests/unit/test_fr372_gitignore_boundary_guard.py` | test | keep |  | REQ-YG-002 | model: scripts/check_gitignore_boundary.sh |
| `tests/unit/test_fr382_chaplain_prompt_caching_scope_red.py` | test | keep |  | REQ-YG-287, REQ-YG-289 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model keep 0.92, inexact span. Live FR-382 caching-scope witness (REQ-YG-287/289, outside fan-in 2/1), but its inventory still spans .chaplain/graphs and asserts context-planner.yaml exists there — GREEN must narrow it to graphs/ or the deletion breaks it. |
| `tests/unit/test_fr390_watcher_validate_fix_context_and_sanity_timeout.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
ACTION_PATH = CHAPLAIN / "actions" / "yamlgraph_async_action.py"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
SANITY_GRAPH = CHAPLAIN / "graphs" / "watcher-enforce" / "sanity-check-session.yaml" |
| `tests/unit/test_fr392_fsm_on_launch_hook_red.py` | test | keep |  | REQ-YG-347 | model: from yamlgraph.utils.fsm.action import YamlgraphAsyncAction |
| `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py` | test | delete |  | REQ-YG-407 | model: Acceptance tests for FR-411 watcher2 inquisitor audit cadence reintegration |
| `tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py` | test | delete |  | REQ-YG-318 | model: CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py" |
| `tests/unit/test_fr413_chaplain_yamlgraph_async_shared_bridge_red.py` | test | delete |  | REQ-YG-319 | model: "RED acceptance tests for FR-413 Chaplain shared FSM bridge migration." |
| `tests/unit/test_fr419_action_config_schema_boundary.py` | test | keep |  | REQ-YG-319 | model: from yamlgraph.utils.fsm.action import ActionConfig |
| `tests/unit/test_fr423_watcher_convergence_persistence.py` | test | delete |  | REQ-YG-316 | model: PIPELINE = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml" |
| `tests/unit/test_fr436_req_traceability_scope_red.py` | test | keep |  | REQ-YG-063 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model delete 0.95 — wrong: subject is the ADR-001 traceability scope contract (ARCHITECTURE.md, docs/adr/001); it names inquisitor.sh only as an excluded-scope example. REQ-YG-063 fan-in 7. |
| `tests/unit/test_fr446_copilot_skills.py` | test | keep |  | REQ-YG-423 | model: FR-765 extends the registry with the `graph-authoring` workflow skill |
| `tests/unit/test_fr693_event_revision.py` | test | keep |  | REQ-YG-537, REQ-YG-538 | model: def _waiver(
    thread: str, reason: str = "texture, not defect", decided_by: str = "chaplain"
) -> dict: |
| `tests/unit/test_fr747_loader_error_ux.py` | test | keep |  | REQ-YG-565 | model: FR-747: loader error UX — the two FR-744 boundary errors name their fix |
| `tests/unit/test_fr748_fr_atlas.py` | test | keep |  | REQ-YG-566 | model: FR-748 RED witness: FR Atlas — the deterministic spine (REQ-YG-566) |
| `tests/unit/test_fr754_id_registry_package_boundary.py` | test | keep |  | REQ-YG-001 | human resolution (enforcing session under operator delegation ('check the deletes and proceed', 2026-09-06), 2026-09-06): model delete 0.95 — wrong on read: the file is a live package-boundary guard (no module under yamlgraph/ may reference .chaplain; yamlgraph/utils/id_registry.py must stay removed). Both assertions remain meaningful after Phase 2 — a .chaplain reference inside yamlgraph/ would then be dangling. REQ-YG-001 fan-in 5. |
| `tests/unit/test_fr796_watcher2_witness_curation.py` | test | delete |  | REQ-YG-206 | model: Regression tests for FR-796 watcher2 witness curation (REQ-YG-206). |
| `tests/unit/test_fr893_diary_census.py` | test | keep |  | REQ-YG-624 | model: from examples.demos.corpus_census.adapters.diary_recurrence import aggregate |
| `tests/unit/test_fr896_precedent_traceability.py` | test | keep |  | REQ-YG-623 | model: exercises scripts/ + examples/ (FR-756) |
| `tests/unit/test_fr942_instruction_diet.py` | test | keep |  |  | model: the chaplain runtime is not running — the Submitting Proposals section is deleted from BOTH instruction files |
| `tests/unit/test_fr_triage.py` | test | keep |  | REQ-YG-564 | model: TOOLS = REPO / "graphs/fr_triage/tools.py" |
| `tests/unit/test_frfsm015_watcher2_pipeline_logging.py` | test | delete |  | REQ-YG-316 | model: DISPATCHER_CONFIG_PATH = WORKTREE / ".chaplain" / "config" / "watcher-dispatcher.yaml" |
| `tests/unit/test_fsm_claude_md_doctrine.py` | test | keep |  | REQ-YG-195 | model: Verifies that fsm/CLAUDE.md contains all doctrinal sections from the root CLAUDE.md/copilot-instructions.md, adapted for FSM paths and idioms. |
| `tests/unit/test_github_issues_remote_inbox.py` | test | delete |  | REQ-YG-247 | model: pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)") |
| `tests/unit/test_harden_remote_inbox.py` | test | delete |  | REQ-YG-256 | model: pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)") |
| `tests/unit/test_id_registry.py` | test | delete |  | REQ-YG-001, REQ-YG-004 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model keep 0.95 — wrong under FR-1015: scripts/id_registry.py is in the non-census deletion set and this is its test; REQ-YG-001/004 keep 5 and 4 outside witnesses. |
| `tests/unit/test_inquisitor_auto_propose.py` | test | delete |  | REQ-YG-118 | model: Tests the flag parsing and propose gating logic in inquisitor.sh. The propose mode detects persistent violations in diary entries and writes fix proposals to .chaplain/inbox/. |
| `tests/unit/test_inquisitor_gate.py` | test | delete |  | REQ-YG-131 | model: Tests the commit-delta pre-flight gate that aborts the Inquisitor when no feat: or fix: commits exist since the last audit. |
| `tests/unit/test_inquisitor_worktree_gate.py` | test | delete |  | REQ-YG-142 | model: script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor.sh"
        ) |
| `tests/unit/test_judge_split_verdict.py` | test | delete |  | REQ-YG-143 | model: .chaplain/graphs/watcher-plan/prompts/judge.yaml |
| `tests/unit/test_knowledge_graph_fr193.py` | test | keep |  | REQ-YG-192 | model: Graduates 5 process heuristics and 3 seeds into the Knowledge Graph in .github/copilot-instructions.md |
| `tests/unit/test_loops.py` | test | keep |  | REQ-YG-006, REQ-YG-093 | model: from yamlgraph.utils.conditions import evaluate_condition |
| `tests/unit/test_migrate_diary.py` | test | keep |  | REQ-YG-063 | human resolution (operator (confirmed via enforcing session; proposed by the census session), 2026-09-06): model delete 0.95 — wrong: its subject scripts/migrate_diary_to_folder.py exists and is live; the file matched the discovery needle only in passing. |
| `tests/unit/test_philosopher.py` | test | keep |  | REQ-YG-184, REQ-YG-185, REQ-YG-193, REQ-YG-194 | model: graphs/philosopher/graph.yaml |
| `tests/unit/test_philosopher_book.py` | test | keep |  | REQ-YG-404, REQ-YG-405 | model: from examples.demos.philosopher_book.tools import |
| `tests/unit/test_python_node_graph_integration.py` | test | keep |  | REQ-YG-020, REQ-YG-106 | model: Replicate chaplain worktree → downstream variable resolution pattern. |
| `tests/unit/test_python_nodes.py` | test | keep |  | REQ-YG-020, REQ-YG-196 | model: path=".chaplain/lib/diary.py" |
| `tests/unit/test_ramp_installer.py` | test | keep |  | REQ-YG-610, REQ-YG-611, REQ-YG-612, REQ-YG-613 | model: import ramp_installer as ri |
| `tests/unit/test_retire_old_pipeline_scripts.py` | test | delete |  | REQ-YG-276, REQ-YG-309 | model: Acceptance tests for FR-276/FR-317 runtime retirement and FSM entrypoint |
| `tests/unit/test_router_dict_routing.py` | test | keep |  | REQ-YG-022 | model: Tests for router node dict output handling.

Verifies that router nodes correctly extract route keys from both
Pydantic model attributes and dict outputs using the explicit
route_field config (FR-107). |
| `tests/unit/test_router_race.py` | test | keep |  | REQ-YG-266, REQ-YG-271 | model: from yamlgraph.node_factory.llm_nodes import create_node_function |
| `tests/unit/test_watcher2_create_pr_reuse.py` | test | delete |  | REQ-YG-272 | model: pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)") |
| `tests/unit/test_watcher_worktree_wrapper_red.py` | test | delete |  | REQ-YG-528 | model: SETUP_WRAPPER = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_setup.sh"
TEARDOWN_WRAPPER = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_teardown.sh" |
| `tests/unit/test_world_distill.py` | test | keep |  | REQ-YG-563 | model: TOOLS = REPO / "graphs/world_distill/tools.py" |
