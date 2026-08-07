# Judgement: FR-780 Research-Agent Toolbelt Conversion

**Verdict:** APPROVED WITH REVISIONS — the fourth-consumer conversion is sound, but authority activates only after the FR freezes traceability/docs, canonical tool-argument semantics, FR-779 regression protection, and a mechanically grounded live witness.

**Prior art:** FR-777 (toolbelt + fit boundary — converging demos onto manifests permitted, forking manifests forbidden); FR-779 (same graph, bindings + synthesis gate — hard regression boundary); FR-215 (created the demo); CAP-220/REQ-YG-579 (shell-toolbelt traceability surface being extended).

**Reviewed against:** `feature-requests/FR-780-research-agent-toolbelt-conversion.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-777-shared-shell-toolbelt-manifests.md`; `feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md`; `feature-requests/FR-779-research-agent-demo-rot.md`; `feature-requests/FR-779-research-agent-demo-rot.judgement.md`; `feature-requests/FR-215-research-agent-demo.md`; `examples/demos/research-agent/graph.yaml`; `examples/demos/research-agent/prompts/plan_research.yaml`; `examples/demos/research-agent/prompts/execute_research.yaml`; `examples/demos/research-agent/prompts/extract_intent.yaml`; `examples/demos/research-agent/prompts/validate_findings.yaml`; `examples/demos/research-agent/prompts/synthesize_report.yaml`; `examples/shared/toolbelt/read_file.tool.yaml`; `examples/shared/toolbelt/search.tool.yaml`; `examples/shared/toolbelt/list_dir.tool.yaml`; `examples/shared/toolbelt/git_log.tool.yaml`; `examples/shared/README.md`; `capabilities/CAP-220-shared-shell-toolbelt.yaml`; `capabilities/CAP-221-demo-binding-hygiene.yaml`; `capabilities/CAP-83-research-agent-demo.yaml`; `ARCHITECTURE.md`.

## What is sound

The problem is real and evidenced by committed artifacts. FR-780 identifies the current research-agent tools as truncating or Python-only variants (`feature-requests/FR-780-research-agent-toolbelt-conversion.md:15-21`, `feature-requests/FR-780-research-agent-toolbelt-conversion.md:29-31`), and the graph confirms those exact commands: `grep ... --include="*.py" ... | head -20`, `find ... "*.py" ... | head -30`, and `head -80` (`examples/demos/research-agent/graph.yaml:22-38`). The prompts also expose the same agent-facing drift by teaching `search_code`, `list_files`, "Python files", and "first 80 lines" (`examples/demos/research-agent/prompts/plan_research.yaml:6-11`; `examples/demos/research-agent/prompts/execute_research.yaml:5-10`).

The proposed destination aligns with existing architecture instead of extending the framework. FR-777 shipped the shared shell toolbelt and defined the fit boundary "verbatim two-plus-consumer contracts earn manifests; demo-local variants stay inline" (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:132-139`, `feature-requests/FR-777-shared-shell-toolbelt-manifests.md:152-157`), while the actual manifests already provide the desired contracts: full-file `cat {file}` (`examples/shared/toolbelt/read_file.tool.yaml:5-12`), glob-scoped `rg` (`examples/shared/toolbelt/search.tool.yaml:5-13`), `ls {dir}` (`examples/shared/toolbelt/list_dir.tool.yaml:4-9`), and history search (`examples/shared/toolbelt/git_log.tool.yaml:5-12`). Repo doctrine requires graph/prompt artifact changes to go through the authoring route (`.github/copilot-instructions.md:15`) and keeps orchestration in YAML (`ARCHITECTURE.md:38-70`); FR-780 follows that route and forbids `yamlgraph/` changes (`feature-requests/FR-780-research-agent-toolbelt-conversion.md:39-43`, `feature-requests/FR-780-research-agent-toolbelt-conversion.md:55`).

The strategic classification is **Contrib/example hardening**. This is not a new framework primitive: FR-768/FR-777 already supplied the manifest abstraction and shell toolbelt. FR-780 converts a fourth example consumer after FR-779 made the demo trustworthy enough to run, preserving `count_lines` as a demo-local inline tool (`feature-requests/FR-780-research-agent-toolbelt-conversion.md:19-20`, `feature-requests/FR-780-research-agent-toolbelt-conversion.md:58-60`) rather than manufacturing a manifest to grow the toolbelt.

The sequencing premise is correct. FR-780 explicitly waits for FR-779 (`feature-requests/FR-780-research-agent-toolbelt-conversion.md:44`), and FR-779 is now marked enforced with the binding fix, state declarations, conditional empty-findings gate, and live witness recorded (`feature-requests/FR-779-research-agent-demo-rot.md:5`, `feature-requests/FR-779-research-agent-demo-rot.md:120-128`). The current graph reflects that base with `state: query/scope` and conditional routes from `validate_findings` to either `END` or `synthesize_report` (`examples/demos/research-agent/graph.yaml:10-12`, `examples/demos/research-agent/graph.yaml:101-105`).

## Required revisions

### R-1: Freeze the fourth-consumer traceability and documentation surface

Replace the open-ended AC-6 choice ("extend REQ-YG-579/CAP-220 ... or add a REQ if the judge prefers") with the exact decision: extend `CAP-220` / `REQ-YG-579` to name research-agent as the fourth shell-toolbelt manifest consumer, and mark the new/changed tests with `@pytest.mark.req("REQ-YG-579")`. `CAP-220` currently describes only planner, enforcer, and judge (`capabilities/CAP-220-shared-shell-toolbelt.yaml:4-12`, `capabilities/CAP-220-shared-shell-toolbelt.yaml:18-28`), and `examples/shared/README.md` also lists only those three committed consumers (`examples/shared/README.md:157-186`). The four manifest header comments likewise still say the first committed consumers are planner, enforcer, and judge (`examples/shared/toolbelt/read_file.tool.yaml:1-6`; `examples/shared/toolbelt/search.tool.yaml:1-7`; `examples/shared/toolbelt/list_dir.tool.yaml:1-3`; `examples/shared/toolbelt/git_log.tool.yaml:1-6`). Fold into the FR that enforcement updates those documentation/traceability surfaces to include research-agent without changing the shared manifest runtime contracts.

### R-2: Specify the canonical tool-argument and scope contract in the prompts

Fold a mechanical prompt contract into the FR. `search_code` currently took `{scope}` as a shell argument (`examples/demos/research-agent/graph.yaml:22-26`), but canonical `search` takes `{pattern}` and `{glob}` and searches from `.` (`examples/shared/toolbelt/search.tool.yaml:8-13`). `list_files` currently takes `{path}` and filters Python files (`examples/demos/research-agent/graph.yaml:27-30`), while canonical `list_dir` takes `{dir}` and lists the directory without a Python-only filter (`examples/shared/toolbelt/list_dir.tool.yaml:4-9`). Because the graph still exposes `scope` as an input (`examples/demos/research-agent/graph.yaml:10-20`), the FR must state how prompts preserve scope: `plan_research` and `execute_research` must teach the canonical tool names and argument names (`search(pattern, glob)`, `list_dir(dir)`, `read_file(file)`, `git_log(pattern)`, `count_lines(file)`) and instruct the agent to translate `scope` into `list_dir.dir` and `search.glob` prefixes rather than silently broadening every search to the whole repository.

### R-3: Preserve the FR-779 binding and empty-findings gate as an explicit regression boundary

Add an acceptance criterion that the conversion must not revert FR-779. The graph must retain declared `state.query` / `state.scope` fields and `{state.query}` / `{state.scope}` node bindings (`examples/demos/research-agent/graph.yaml:10-12`, `examples/demos/research-agent/graph.yaml:46-69`, `examples/demos/research-agent/graph.yaml:86-89`), and it must retain the conditional route that sends `validation.confidence == 'low' or findings == ''` to `END` with no `report` (`examples/demos/research-agent/graph.yaml:101-105`). FR-779 made this a hard gate because empty findings had produced a fabricated report (`feature-requests/FR-779-research-agent-demo-rot.md:41-56`), and its judgement forbids prompt-only anti-fabrication in place of graph topology (`feature-requests/FR-779-research-agent-demo-rot.judgement.md:63-72`). FR-780 touches the same graph and prompts, so the regression guard must be named, not assumed.

### R-4: Strengthen the live witness from "topic echo" to grounded state evidence

Replace AC-5's loose "topic echo visible" witness with a mechanically checkable full-output witness. The committed `demo-output.log` must show a successful run with non-empty `findings`, `validation.confidence` not `low`, a produced `report`, visible query/topic echo, at least one concrete in-scope file citation or line citation from tool findings, and no fatal markers. A final report alone is insufficient: FR-779's evidence shows the demo can synthesize a plausible multi-section report from empty findings (`feature-requests/FR-779-research-agent-demo-rot.md:41-56`), and repo doctrine warns that a plausible wrong answer is harder to catch than a crash (`.github/copilot-instructions.md:218`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-780-research-agent-toolbelt-conversion.md` revisions folding R-1 through R-4 |
| D-2 | `examples/demos/research-agent/graph.yaml` tool declarations converted so `read_file`, `search`, `list_dir`, and `git_log` are manifest refs; `count_lines` remains inline |
| D-3 | `examples/demos/research-agent/graph.yaml` agent tool lists renamed to canonical tool names while preserving FR-779 state declarations, bindings, and conditional routes |
| D-4 | `examples/demos/research-agent/prompts/plan_research.yaml` and `execute_research.yaml` updated to canonical tool names, argument names, scope translation, and full-fidelity semantics |
| D-5 | Tests proving manifest-only declarations, effective shell config equivalence, prompt/name cleanup, `count_lines` inline status, and FR-779 routing preservation |
| D-6 | `examples/shared/README.md`, the four `examples/shared/toolbelt/*.tool.yaml` header comments, and `capabilities/CAP-220-shared-shell-toolbelt.yaml` updated to record research-agent as the fourth consumer without altering runtime contracts |
| D-7 | Regenerated grounded `examples/demos/research-agent/demo-output.log`, authoring validation report, changelog fragment, FR implementation-status fold, and diary reflection |

Not authorized: changes under `yamlgraph/`; changes to shared manifest `runtime.command`, `runtime.parse`, timeout semantics, or canonical descriptions; converting `count_lines` to a manifest; adding `examples/shared/toolbelt/research.tool.yaml`; modifying `.github/skills/judge-fr/adapters/graph.yaml`; changing judge/authoring/review doctrine, hooks, CI, provider defaults, shell execution semantics, graph lint behavior, or unrelated demos; increasing `plan_research` / `execute_research` `max_iterations` as a substitute for tool fidelity.

## Revised acceptance criteria

- [ ] AC-01: RED test proves the committed research-agent graph does not yet declare `read_file`, `search`, `list_dir`, and `git_log` solely via `manifest:` refs while keeping `count_lines` inline; GREEN converts exactly those four shared tools and no others.
- [ ] AC-02: A committed test loads the research-agent graph and proves the effective shell config for `read_file`, `search`, `list_dir`, and `git_log` matches the shared manifest contracts: `command`, canonical `description`, `parse`, and `timeout == 30`.
- [ ] AC-03: `plan_research` and `execute_research` tool lists use canonical names (`search`, `list_dir`, `read_file`, `git_log`, plus inline `count_lines` where appropriate); no `search_code` or `list_files` references remain anywhere under `examples/demos/research-agent/`.
- [ ] AC-04: The updated research-agent prompts describe the canonical tool names and argument names, remove Python-only / first-80-lines semantics, and instruct the agent to honor `scope` through `list_dir.dir` and `search.glob` rather than silently searching the whole repository.
- [ ] AC-05: FR-779 behavior is preserved: `state.query` / `state.scope` remain declared and bound through `{state...}` templates, and empty findings or low validation confidence still terminates after `validate_findings` without producing `report`.
- [ ] AC-06: `examples/shared/README.md`, the four shared toolbelt manifest header comments, and `CAP-220` / `REQ-YG-579` are updated to record research-agent as the fourth shell-toolbelt manifest consumer; every new or changed test carries `@pytest.mark.req("REQ-YG-579")`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: Governed graph and prompt edits are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint, validate, smoke, and the relevant test evidence for the changed demo.
- [ ] AC-08: A regenerated committed `examples/demos/research-agent/demo-output.log` from a live successful run shows non-empty `findings`, `validation.confidence` not `low`, a produced `report`, visible query/topic echo, at least one concrete in-scope file or line citation from tool findings, and no fatal markers.
- [ ] AC-09: No files under `yamlgraph/` change; shared manifest runtime contracts are not changed; `count_lines` is not moved to the toolbelt; no research graph manifest or judge adapter branch is added; `max_iterations` is not increased as the fix.
- [ ] AC-10: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-780-research-agent-toolbelt-conversion.md`. | GATE |
| C-2 | Governed edits to `graph.yaml` and `prompts/*.yaml` must be authored through `scripts/author.sh` and retain its validation record. | GATE |
| C-3 | If canonical `search` / `list_dir` cannot preserve `scope` without changing shared manifest contracts, stop for a revised FR; do not fork or mutate the toolbelt contract inside enforcement. | GATE |
| C-4 | FR-779's empty-findings topology and `{state...}` binding contract must survive unchanged; prompt wording alone is not an acceptable guard. | GATE |
| C-5 | Any required `yamlgraph/`, judge-adapter, hook, CI, or doctrine change stops this FR and must enter a separate judged proposal. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may convert only the research-agent demo to consume the four existing shell toolbelt manifests, update its prompts/tests/docs/traceability/witness artifacts, and preserve the existing FR-779 hardening boundary.
