# Chaplain census — raw read record (FR-1012 AC-06)

**Reader:** the enforcing Claude Code session, under the operator's delegation of 2026-09-06 ("rerun not needed — retirement is not exact science. check the deletes and proceed"). The operator did not read the rows individually; this record is what was read and decided in their stead.

**Scope of the read:** all 115 generic rows by verdict, confidence and evidence span (first pass); the 41 model-decided `delete` rows against their sources — module docstring, every `.chaplain` reference, imports from `yamlgraph`/`scripts`/`examples`, other repository paths, test count, requirement fan-in (second pass, below). The 21 human resolutions were proposed from the first pass and confirmed by the operator as a block.

**Second-pass outcome:** 40 deletes upheld; 1 overridden to keep (`tests/unit/test_fr754_id_registry_package_boundary.py` — live package-boundary guard, see resolutions file). Notes on the five rows that needed a closer look:

- `test_fr413_chaplain_yamlgraph_async_shared_bridge_red.py` imports the core `yamlgraph.utils.fsm.action` but its subject is `.chaplain/actions/yamlgraph_async_action.py`; REQ-YG-319 keeps 8 outside witnesses → delete upheld.
- `test_fr796_watcher2_witness_curation.py` asserts relocated witnesses live under `.chaplain/demos` (false after removal) and that retired names are absent from default discovery; REQ-YG-206 keeps 2 outside witnesses → delete upheld; discovery keeps no `.chaplain` exclusion code, so nothing goes dead.
- `test_claude_md_chaplain_inbox.py` guards that the Submitting Proposals section stays out of CLAUDE.md and the Scripture — a guard for a dead concept swept by FR-1013; CAP-55 retires → delete upheld.
- `test_fr321_yamlgraph_async_subprocess_exec.py` imports the chaplain action package via sys.path → delete upheld.
- `test_fr278_remove_baseline_dead_code.py` asserts absences that stay true after removal; CAP-165 retires with it → delete upheld.

## Second pass, per row (source facts extracted by code)

```
### tests/unit/test_acceptance_tests_before_enforce.py  [12 tests] fan-in {'REQ-YG-263': 2}
    doc: Tests for FR-260: acceptance tests are authored before enforce execution.
    chaplain refs: ['".chaplain" / "config" / "watcher-pipeline-v2.yaml"', '".chaplain" / "graphs" / "watcher-enforce" / "enforce-session.yaml"', '".chaplain" / "graphs" / "watcher-enforce" / "prompts"', '".chaplain" / "graphs" / "watcher-plan" / "prompts"']
    other paths: ['graphs/watcher-plan/step-plan-unified.yaml']
    model span: 'PIPELINE_CONFIG = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml"'
### tests/unit/test_chaplain_readme_documentation.py  [12 tests] fan-in {'REQ-YG-278': 0}
    doc: (no module docstring)
    chaplain refs: ['".chaplain" in readme_content or "chaplain" in readme_content', '.chaplain', '.chaplain/README.md', '.chaplain/failed/']
    other paths: ['scripts/start-system.sh']
    model span: 'Tests for FR-195: Chaplain Documentation\n\nValidates that .chaplain/README.md exists and contains compre'
### tests/unit/test_chaplain_research_step.py  [12 tests] fan-in {'REQ-YG-260': 0}
    doc: Tests for FR-257: Chaplain research guidance in watcher-plan runtime.
    chaplain refs: ['".chaplain" / "config" / "watcher-pipeline-v2.yaml"', '".chaplain" / "graphs" / "watcher-plan" / "prompts"', '".chaplain" / "graphs" / "watcher-plan" / "step-judge-v2.yaml"', '".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml"']
    model span: 'Tests for FR-257: Chaplain research guidance in watcher-plan runtime.'
### tests/unit/test_claude_md_chaplain_inbox.py  [2 tests] fan-in {'REQ-YG-153': 0}
    doc: FR-163 chaplain inbox instructions — retired under FR-942. Operator amendment during FR-942 enforcement (2026-08-31): the chaplain runtime is not running, so the Submitting Proposals section was deleted from BOTH per-turn instruction files rather than deduplic
    chaplain refs: []
    model span: 'FR-163 chaplain inbox instructions — retired under FR-942.\n\nOperator amendment during FR-942 enforcemen'
### tests/unit/test_create_worktree.py  [8 tests] fan-in {'REQ-YG-106': 3}
    doc: Unit tests for .chaplain/lib/worktree.py create_worktree() (FR-265). Tests force-add staging, multi-draft guard, commit idempotency, and draft file survival using mocked subprocess + real tmp_path filesystem.
    chaplain refs: ['".chaplain" / "lib" / "worktree.py"', '.chaplain/lib/worktree.py']
    model span: 'Unit tests for .chaplain/lib/worktree.py create_worktree() (FR-265).'
### tests/unit/test_enforce_simplify.py  [5 tests] fan-in {'REQ-YG-001': 5, 'REQ-YG-012': 9}
    doc: Tests for active watcher enforce session graph.
    chaplain refs: ['.chaplain/graphs/watcher-enforce/enforce-session.yaml', '.chaplain/graphs/watcher-enforce/prompts']
    other paths: ['graphs/watcher-enforce/enforce-session.yaml', 'graphs/watcher-enforce/prompts']
    model span: '"""Tests for active watcher enforce session graph."""'
### tests/unit/test_fr278_remove_baseline_dead_code.py  [18 tests] fan-in {'REQ-YG-466': 0}
    doc: Acceptance tests for FR-278: Remove FR-277 Watcher2 Baseline Dead Code. These tests verify that all baseline checkpointing dead code is completely removed.
    chaplain refs: ['".chaplain" / "README.md"', '".chaplain" / "graphs" / "baseline"', '".chaplain" / "graphs" / "baseline" / "graph.yaml"', '".chaplain" / "start-system.sh"']
    other paths: ['graphs/baseline/', 'graphs/baseline/graph.yaml', 'yamlgraph/chaplain/__init__.py', 'yamlgraph/chaplain/baseline.py', 'yamlgraph/models/baseline.py']
    model span: 'yamlgraph/chaplain/baseline.py must not exist'
### tests/unit/test_fr289_watcher2_post_merge_inbox_consumption.py  [9 tests] fan-in {'REQ-YG-276': 0}
    doc: Acceptance tests for FR-289: watcher2 post-merge inbox consumption. These tests define the RED contract for consuming stale inbox items that reference the FR that was just merged. They MUST fail on the unmodified codebase.
    chaplain refs: ['".chaplain" / "README.md"', '".chaplain" / "lib" / "watcher" / "post_merge.sh"', '.chaplain/done', '.chaplain/inbox']
    model span: 'POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh"'
### tests/unit/test_fr296_watcher_fsm_startup_script.py  [19 tests] fan-in {'REQ-YG-315': 0}
    doc: FR-296: Watcher FSM System Startup Script. Tests for .chaplain/scripts/start-system.sh — validates the script exists, is executable, has correct structure (phases, signal handling, --inbox flag), and uses the correct statemachine CLI invocations.
    chaplain refs: ['".chaplain" / "scripts" / "start-system.sh"', '.chaplain', '.chaplain/scripts/start-system.sh']
    other paths: ['scripts/start-system.sh']
    model span: 'Tests for .chaplain/scripts/start-system.sh — validates the script exists, is executable, has correct s'
### tests/unit/test_fr305_watcher_pipeline_v2.py  [52 tests] fan-in {'REQ-YG-316': 0}
    doc: FR-305: Watcher Pipeline FSM Simplification. Tests for the v2 pipeline config: - 11 operational states + 3 terminals - Transition correctness (happy path, revise loop, failure paths, timeouts) - Judge uses different model from plan (no session resume) - FR-309
    chaplain refs: ['".chaplain"']
    model span: 'FR-305: Watcher Pipeline FSM Simplification.\n\nTests for the v2 pipeline config:\n- 11 operational states'
### tests/unit/test_fr310_watcher2_validate_precommit_states.py  [9 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for watcher2 validate_fix + validate_gate states. These tests define RED contracts for inserting validate_fix/validate_gate states into watcher-pipeline-v2 and tightening enforce/validate prompt boundaries.
    chaplain refs: ['".chaplain"']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\n\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"'
### tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py  [7 tests] fan-in {'REQ-YG-027': 4}
    doc: RED acceptance tests for FR-311 git_commit hook-fix retry behavior.
    chaplain refs: ['".chaplain" / "actions" / "git_commit_action.py"', '.chaplain/actions']
    other paths: ['yamlgraph/core.py']
    model span: 'ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "git_commit_action.py"'
### tests/unit/test_fr312_watcher2_post_merge_main_sync.py  [7 tests] fan-in {'REQ-YG-276': 0}
    doc: Acceptance tests for FR-312: watcher2 post-merge main sync reconciliation.
    chaplain refs: ['".chaplain" / "README.md"', '".chaplain" / "lib" / "watcher" / "post_merge.sh"']
    model span: 'POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh"'
### tests/unit/test_fr315_yamlgraph_async_stdout_logging_without_event_map.py  [4 tests] fan-in {'REQ-YG-027': 4}
    doc: RED acceptance tests for FR-315 yamlgraph_async stdout logging.
    chaplain refs: ['".chaplain" / "actions" / "yamlgraph_async_action.py"', '.chaplain/graphs/watcher-plan/step-plan-unified.yaml', '.chaplain/processing/gh-288.md']
    other paths: ['graphs/watcher-plan/step-plan-unified.yaml']
    model span: 'ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py"'
### tests/unit/test_fr316_watcher2_sanity_check_state.py  [7 tests] fan-in {'REQ-YG-318': 0}
    doc: RED acceptance tests for FR-316 watcher2 sanity_check state.
    chaplain refs: ['".chaplain"', '.chaplain/graphs/watcher-enforce/sanity-check-session.yaml']
    other paths: ['graphs/watcher-enforce/sanity-check-session.yaml']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"'
### tests/unit/test_fr316_watcher2_validate_split_fix_gate.py  [9 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for FR-316 watcher2 validate split (fix + deterministic gate).
    chaplain refs: ['".chaplain"']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"'
### tests/unit/test_fr318_watcher2_sanity_check_diary_contract.py  [4 tests] fan-in {'REQ-YG-316': 0}
    doc: (no module docstring)
    chaplain refs: ['.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml']
    other paths: ['graphs/watcher-enforce/prompts/sanity-check-session.yaml']
    model span: 'PROMPT_FILE = Path(".chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml")'
### tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py  [3 tests] fan-in {'REQ-YG-027': 4}
    doc: RED acceptance tests for FR-319 yamlgraph_async shell-safe vars.
    chaplain refs: ['".chaplain" / "actions" / "yamlgraph_async_action.py"', '.chaplain/graphs/watcher-enforce/validate-session.yaml', '.chaplain/processing/gh-304.md']
    other paths: ['graphs/watcher-enforce/validate-session.yaml']
    model span: 'ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py"'
### tests/unit/test_fr321_watcher_validate_fix_gate_diagnostics_handoff.py  [5 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for FR-321 watcher validate-fix gate diagnostics handoff.
    chaplain refs: ['".chaplain"']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"\nVALIDA'
### tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py  [0 tests] fan-in {'REQ-YG-027': 4}
    doc: (no module docstring)
    chaplain refs: ['.chaplain']
    model span: 'sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.chaplain"))\nfrom actions.yamlgraph_a'
### tests/unit/test_fr329_agent_sdk_planner_spike.py  [6 tests] fan-in {'REQ-YG-087': 2}
    doc: RED acceptance tests for FR-329 Agent SDK planner spike.
    chaplain refs: ['".chaplain" / "config" / "watcher-pipeline-v2.yaml",', '".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml",']
    model span: 'WORKTREE / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml",\n    WORKTREE / ".chaplai'
### tests/unit/test_fr337_context_planner_pre_node.py  [8 tests] fan-in {'REQ-YG-001': 5}
    doc: Tests for FR-337 context planner pre-node implementation.
    chaplain refs: ['.chaplain/graphs/watcher-enforce/enforce-session.yaml', '.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml', '.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml', '.chaplain/graphs/watcher-enforce/tools.py']
    other paths: ['graphs/watcher-enforce/enforce-session.yaml', 'graphs/watcher-enforce/prompts/context-planner.yaml', 'graphs/watcher-enforce/prompts/enforce-session.yaml', 'graphs/watcher-enforce/tools.py', 'graphs/watcher-pipeline-v2.yaml']
    model span: '.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml'
### tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py  [6 tests] fan-in {'REQ-YG-276': 0}
    doc: Acceptance tests for FR-339: watcher2 post-merge processing cleanup. These tests define the RED contract for consuming stale processing topics after a successful merge. They MUST fail on the unmodified codebase.
    chaplain refs: ['".chaplain"', '.chaplain/done', '.chaplain/done/', '.chaplain/lib/watcher/post_merge.sh']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"\nPOST_M'
### tests/unit/test_fr358_watcher2_primary_pr_title_selection.py  [6 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for FR-358 watcher2 primary PR title selection.
    chaplain refs: ['".chaplain"']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"\nVALIDA'
### tests/unit/test_fr390_watcher_validate_fix_context_and_sanity_timeout.py  [5 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for FR-390 watcher validate_fix context + sanity timeout.
    chaplain refs: ['".chaplain"', '.chaplain/graphs/watcher-enforce/validate-session.yaml']
    other paths: ['graphs/watcher-enforce/validate-session.yaml']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nACTION_PATH = CHAPLAIN / "actions" / "yamlgraph_async_action.py"\nPIPE'
### tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py  [9 tests] fan-in {'REQ-YG-407': 0}
    doc: Acceptance tests for FR-411 watcher2 inquisitor audit cadence reintegration.
    chaplain refs: ['".chaplain"', '.chaplain/inbox', '.chaplain/inquisitor.sh', '.chaplain/processing/gh-411.md']
    model span: 'Acceptance tests for FR-411 watcher2 inquisitor audit cadence reintegration'
### tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py  [8 tests] fan-in {'REQ-YG-318': 0}
    doc: Acceptance tests for FR-412 watcher2 micro-remediation fast path.
    chaplain refs: ['".chaplain"']
    model span: 'CHAPLAIN = WORKTREE / ".chaplain"\nPIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"\nVALIDA'
### tests/unit/test_fr413_chaplain_yamlgraph_async_shared_bridge_red.py  [3 tests] fan-in {'REQ-YG-319': 8}
    doc: RED acceptance tests for FR-413 Chaplain shared FSM bridge migration.
    chaplain refs: ['".chaplain" / "actions" / "yamlgraph_async_action.py"', '.chaplain/graphs/watcher-plan/step-judge-v2.yaml', '.chaplain/processing/gh-415.md']
    imports: ['yamlgraph.utils.fsm.action']
    other paths: ['graphs/watcher-plan/step-judge-v2.yaml']
    model span: '"RED acceptance tests for FR-413 Chaplain shared FSM bridge migration."'
### tests/unit/test_fr423_watcher_convergence_persistence.py  [7 tests] fan-in {'REQ-YG-316': 0}
    doc: FR-423: enforce stable FR identity and durable judge rationale persistence.
    chaplain refs: ['".chaplain"', '".chaplain" / "actions" / "yamlgraph_async_action.py"', '".chaplain" / "config" / "watcher-pipeline-v2.yaml"', '".chaplain" / "graphs" / "watcher-plan" / "prompts" / "judge.yaml"']
    model span: 'PIPELINE = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml"'
### tests/unit/test_fr754_id_registry_package_boundary.py  [1 tests] fan-in {'REQ-YG-001': 5}
    doc: FR-754: package boundary stays free of .chaplain references.
    chaplain refs: ['".chaplain" in py_file.read_text(encoding="utf-8"):', '.chaplain']
    other paths: ['yamlgraph/utils/id_registry.py']
    model span: 'No Python module under yamlgraph/ may reference .chaplain directly.'
### tests/unit/test_fr796_watcher2_witness_curation.py  [3 tests] fan-in {'REQ-YG-206': 2}
    doc: Regression tests for FR-796 watcher2 witness curation (REQ-YG-206).
    chaplain refs: ['".chaplain" / "demos"']
    imports: ['yamlgraph.discovery']
    other paths: ['examples/demos.']
    model span: 'Regression tests for FR-796 watcher2 witness curation (REQ-YG-206).'
### tests/unit/test_frfsm015_watcher2_pipeline_logging.py  [5 tests] fan-in {'REQ-YG-316': 0}
    doc: FR-FSM-015: Dispatcher pipeline logging contract.
    chaplain refs: ['".chaplain" / "config" / "watcher-dispatcher.yaml"', '".chaplain" / "scripts" / "start-system.sh"']
    model span: 'DISPATCHER_CONFIG_PATH = WORKTREE / ".chaplain" / "config" / "watcher-dispatcher.yaml"'
### tests/unit/test_github_issues_remote_inbox.py  [18 tests] fan-in {'REQ-YG-247': 0}
    doc: Tests for FR-243: GitHub Issues as Remote Chaplain Inbox. Validates that watch.sh: 1. Syncs open GitHub Issues labeled 'chaplain' into .chaplain/inbox/gh-{number}.md 2. Removes the 'chaplain' label after import to prevent re-import loops 3. Gracefully skips wh
    chaplain refs: ['".chaplain", "lib", "watcher")', '".chaplain", "start-system.sh")', '.chaplain/inbox/gh-']
    model span: 'pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")'
### tests/unit/test_harden_remote_inbox.py  [18 tests] fan-in {'REQ-YG-256': 0}
    doc: Tests for FR-251: Harden GitHub Issues Remote Inbox. Validates that watch.sh: 1. Checks issue author against .chaplain/allowed-authors.txt before import 2. Truncates issue body at 10,000 characters 3. Prepends <!-- author: @username --> audit header to importe
    chaplain refs: ['".chaplain", "allowed-authors.txt")', '".chaplain", "lib", "watcher")', '".chaplain", "start-system.sh")', '.chaplain/.']
    model span: 'pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")'
### tests/unit/test_inquisitor_auto_propose.py  [15 tests] fan-in {'REQ-YG-118': 0}
    doc: Unit tests for inquisitor.sh --propose flag (FR-118). Tests the flag parsing and propose gating logic in inquisitor.sh. The propose mode detects persistent violations in diary entries and writes fix proposals to .chaplain/inbox/. The flag parsing and gating lo
    chaplain refs: ['".chaplain" / "inbox"', '".chaplain", "inquisitor.sh"', '.chaplain/inbox', '.chaplain/inbox/']
    model span: 'Tests the flag parsing and propose gating logic in inquisitor.sh. The propose mode detects persistent v'
### tests/unit/test_inquisitor_gate.py  [40 tests] fan-in {'REQ-YG-131': 0}
    doc: Unit tests for inquisitor.sh commit-delta gate (FR-131). Tests the commit-delta pre-flight gate that aborts the Inquisitor when no feat: or fix: commits exist since the last audit. The gate logic is pure shell, tested via subprocess with temporary git reposito
    chaplain refs: ['".chaplain", "inquisitor.sh"']
    model span: 'Tests the commit-delta pre-flight gate that aborts the Inquisitor when no feat: or fix: commits exist s'
### tests/unit/test_inquisitor_worktree_gate.py  [7 tests] fan-in {'REQ-YG-142': 0}
    doc: Unit tests for inquisitor.sh worktree gate (FR-142). Tests the worktree-detection gate that suppresses audit and propose phases when running inside a git worktree (i.e., during an enforce pipeline). The gate fires before the commit-delta gate (FR-131) and is b
    chaplain refs: ['".chaplain", "inquisitor.sh"']
    model span: 'script_path = os.path.join(\n            os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor'
### tests/unit/test_judge_split_verdict.py  [17 tests] fan-in {'REQ-YG-143': 0}
    doc: FR-136: Judge SPLIT Verdict — TDD tests. Verifies that judge prompt files include the SPLIT verdict alongside APPROVE, AMEND, and REJECT, and that a Scope Count evaluation criterion exists for detecting multi-concern feature requests.
    chaplain refs: ['".chaplain"', '.chaplain/graphs/watcher-plan/prompts/judge.yaml', '.chaplain/inbox/', '.chaplain/inbox/.']
    other paths: ['graphs/watcher-plan/prompts/judge.yaml', 'scripts/chaplain-prompts/judge.md']
    model span: '.chaplain/graphs/watcher-plan/prompts/judge.yaml'
### tests/unit/test_retire_old_pipeline_scripts.py  [9 tests] fan-in {'REQ-YG-276': 0, 'REQ-YG-309': 0}
    doc: Acceptance tests for FR-276/FR-317 runtime retirement and FSM entrypoint.
    chaplain refs: ['.chaplain/README.md', '.chaplain/config/watcher-pipeline-v2.yaml', '.chaplain/failed', '.chaplain/failed/']
    other paths: ['graphs/watcher-forensic/graph.yaml', 'scripts/bugfix_worktree.sh', 'scripts/enforce_worktree.sh', 'scripts/start-system.sh']
    model span: 'Acceptance tests for FR-276/FR-317 runtime retirement and FSM entrypoint'
### tests/unit/test_watcher2_create_pr_reuse.py  [13 tests] fan-in {'REQ-YG-272': 0}
    doc: Acceptance tests for FR-275: Watcher2 should reuse existing PRs. Tests the enhanced create_pr.sh functionality to check for existing PRs before creating new ones, following the TDD RED-GREEN-REFACTOR pattern. Testing approach: - Mock bash subprocess calls to s
    chaplain refs: ['".chaplain" / "lib" / "watcher" / "create_pr.sh"']
    other paths: ['yamlgraph/pull/185']
    model span: 'pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")'
### tests/unit/test_watcher_worktree_wrapper_red.py  [2 tests] fan-in {'REQ-YG-528': 0}
    doc: Acceptance tests for FR-698 watcher wrapper delegation.
    chaplain refs: ['".chaplain" / "lib" / "watcher" / "worktree_setup.sh"', '".chaplain" / "lib" / "watcher" / "worktree_teardown.sh"']
    other paths: ['scripts/worktree.sh']
    model span: 'SETUP_WRAPPER = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_setup.sh"\nTEARDOWN_WRAPPER = RE'
```
