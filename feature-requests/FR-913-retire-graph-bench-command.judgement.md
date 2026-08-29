# Judgement: FR-913 Retire `yamlgraph graph bench`

**Prior art:** gate hits are this change's own sibling artifacts (FR-913 FR, FR-912 skill-export-retirement FR and judgement, committed together) and the FR-909/910 retirement arc; external precedent (FR-231, FR-299, FR-465/466, CAP-163, CAP-169, CAP-89) is dispositioned in the FR's Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS — the retirement is strategically sound and feasible, but authority activates only after the FR folds in bench-specific research evidence and closes the hellograph-speed migration gaps.

**Reviewed against:** `feature-requests/FR-913-retire-graph-bench-command.md`; cited evidence `docs/research-agentic-sdlc-providers-2026-08-29.md`; cited diary `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md`; precedent `feature-requests/FR-231-model-provider-timing-comparison.md`; precedent `feature-requests/FR-466-cap-retirement-support.md`; precedent `capabilities/CAP-163-cap-retirement-support.yaml`; sibling precedent `feature-requests/FR-909-retire-a2a-surface.judgement.md`, `feature-requests/FR-910-retire-mcp-surface.judgement.md`, and `feature-requests/FR-912-retire-skill-export-surface.md`; current capability records `capabilities/CAP-89-execution-timing-callback.yaml` and `capabilities/CAP-90-graph-bench-command.yaml`; live surfaces `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/graph_run_helpers.py`, `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/utils/llm_factory.py`, `yamlgraph/config.py`, `tests/unit/test_bench_command.py`, `tests/unit/test_timing_tracker.py`, `examples/demos/hellograph-speed/compare_speed.sh`, `examples/demos/hellograph-speed/README.md`, `examples/demos/hellograph-speed/.env.azure.example`, `examples/demos/hellograph-speed/graph.google.yaml`, `examples/demos/hellograph-speed/graph.vertex.yaml`, `examples/demos/hellograph-speed/graph.azure.yaml`, `reference/cli.md`, `reference/getting-started.md`, and `ARCHITECTURE.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `feature-requests/TEMPLATE.md`, and `CLAUDE.md`; tracked-source searches over `yamlgraph/`, `tests/`, `examples/`, `reference/`, `ARCHITECTURE.md`, `README.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `capabilities/`, and `feature-requests/`.

## What is sound

The problem is real. FR-913 names a concrete first consumer and event: maintainers and CI stop carrying a dead command's test and CAP claim at this PR pipeline (`feature-requests/FR-913-retire-graph-bench-command.md:8-11`). Its target surface is a true standalone CLI branch: the parser registers `graph bench` and its `--models`, `--runs`, `--export`, and `--full` options in `yamlgraph/cli/__init__.py:192-235`, dispatch imports `cmd_graph_bench` only for `args.graph_command == "bench"` in `yamlgraph/cli/graph_commands.py:331-346`, and CAP-90 points specifically at `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py`, and `tests/unit/test_bench_command.py` for REQ-YG-232 (`capabilities/CAP-90-graph-bench-command.yaml:8-24`).

The proposed deletion is minimal and aligned with the existing retirement mechanism. FR-913 keeps the separate timing primitive intact (`feature-requests/FR-913-retire-graph-bench-command.md:89-95`), and CAP-89 confirms that `--timing` is its own active requirement, implemented through `yamlgraph/utils/timing_tracker.py`, CLI wiring, and `tests/unit/test_timing_tracker.py` (`capabilities/CAP-89-execution-timing-callback.yaml:1-23`). CAP retirement is already first-class: FR-466 establishes `status: retired` so retired capability files remain as historical records while their REQs stop blocking strict coverage (`feature-requests/FR-466-cap-retirement-support.md:9-15`, `feature-requests/FR-466-cap-retirement-support.md:118-127`), and CAP-163 records that `req_coverage.py` excludes retired CAPs while `validate_capabilities.py` accepts retired files with relaxed requirements (`capabilities/CAP-163-cap-retirement-support.yaml:1-24`).

The strategic classification is **Reject / retire stale surface**, not framework-primitive expansion. FR-231 shows the original split between the still-useful timing callback and the heavier multi-model bench command (`feature-requests/FR-231-model-provider-timing-comparison.md:123-140`). The diary already identified bench commands as a 336-line low-risk, low-value removal candidate and asked the exact liveness question this FR answers (`docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:379-384`, `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:428-436`). Repo doctrine says mature systems improve by retiring phantom claims rather than adding implementations (`.github/copilot-instructions.md:94`), and the FR follows that direction by retiring only CAP-90 while preserving CAP-89 and the historical FR-231 spec (`feature-requests/FR-913-retire-graph-bench-command.md:55-63`).

Most acceptance criteria are mechanically checkable. The FR names concrete absence checks for deleted code and live references (`feature-requests/FR-913-retire-graph-bench-command.md:99-100`), capability validation and strict requirement coverage (`feature-requests/FR-913-retire-graph-bench-command.md:101-104`), documentation updates (`feature-requests/FR-913-retire-graph-bench-command.md:103`), unit-suite validation (`feature-requests/FR-913-retire-graph-bench-command.md:105`), and a removal changelog (`feature-requests/FR-913-retire-graph-bench-command.md:106`). This gives the enforcer direct tests rather than aspirational prose, satisfying the judge doctrine's measurability and testability requirements (`.github/skills/judge-fr/doctrine.md:43-61`).

## Required revisions

### R-1: Replace the generic research pointer with bench-specific consumer evidence

Amend the `**Research:**` line so it points to a committed bench-specific evidence record or explicitly says the committed in-body record is the evidence. The current line cites the method of `docs/research-agentic-sdlc-providers-2026-08-29.md` section 4.4 (`feature-requests/FR-913-retire-graph-bench-command.md:12-16`), but that section evaluates MCP and A2A, not bench (`docs/research-agentic-sdlc-providers-2026-08-29.md:237-272`). The FR body does contain useful bench evidence: one demo consumer, one own-test consumer, two doc mentions, and the corrected widened grep (`feature-requests/FR-913-retire-graph-bench-command.md:36-51`). Fold that into the research field by recording the actual searched terms and result classes, or add a sibling `feature-requests/FR-913.research.md` with the same consumer sweep.

The revised research evidence must include, at minimum, the live result classes already found in this judgement: `yamlgraph/cli/bench_commands.py`, parser wiring in `yamlgraph/cli/__init__.py`, dispatch in `yamlgraph/cli/graph_commands.py`, `tests/unit/test_bench_command.py`, `examples/demos/hellograph-speed/compare_speed.sh`, `reference/cli.md`, `reference/getting-started.md`, `ARCHITECTURE.md`, and CAP-90. This is required by the local research-evidence rule: a new FR whose research field is absent, dangling, or strawman receives no authority (`.github/skills/judge-fr/doctrine.md:118-125`; `feature-requests/TEMPLATE.md:11-20`).

### R-2: Make the hellograph-speed migration preserve or explicitly retire model/run-count semantics

Amend the consumer-migration step and acceptance criteria to specify the exact behavior of `examples/demos/hellograph-speed/compare_speed.sh` after `graph bench` is gone. The current script uses `yamlgraph graph bench` three times with `--runs "$runs"` (`examples/demos/hellograph-speed/compare_speed.sh:15-24`, `examples/demos/hellograph-speed/compare_speed.sh:33-36`, `examples/demos/hellograph-speed/compare_speed.sh:47-51`). FR-913 says to use `graph run <graph> --var-file ./vars.yaml --timing` and "loop `--runs` in shell if the demo keeps repetition" (`feature-requests/FR-913-retire-graph-bench-command.md:72-76`), but it does not freeze whether the positional run-count argument remains part of the demo contract.

Choose one behavior and write it into the FR mechanically:

1. Preserve the script argument by looping each provider exactly N times with `yamlgraph graph run ... --timing`, and update the README to say the script prints per-run timings rather than bench mean/min/max aggregation; or
2. Retire the repetition contract by removing the run-count argument from the script and README.

Do not leave this implicit. The current README documents the argument as "run count per provider" and recommends larger values for a stable average (`examples/demos/hellograph-speed/README.md:49-56`), so an enforcer cannot tell whether dropping aggregation is intentional or accidental.

### R-3: Add the demo-local stale documentation and Azure model override to the authorized sweep

Amend the docs/consumer-migration scope to include `examples/demos/hellograph-speed/README.md` and `examples/demos/hellograph-speed/.env.azure.example`. The current FR lists the script migration but not the demo-local docs/templates (`feature-requests/FR-913-retire-graph-bench-command.md:72-83`, `feature-requests/FR-913-retire-graph-bench-command.md:99-104`). That misses a live stale string: `.env.azure.example` says `AZURE_MODEL` is "used for bench model override" (`examples/demos/hellograph-speed/.env.azure.example:5-6`), while the proposed replacement path uses `graph run`, whose parser has `--var-file` and `--timing` but no model override option (`yamlgraph/cli/__init__.py:58-63`, `yamlgraph/cli/__init__.py:119-124`).

Because FR-913 explicitly does not authorize changing the hellograph-speed graphs (`feature-requests/FR-913-retire-graph-bench-command.md:93-95`), the revision must either:

1. Retire the `AZURE_MODEL` demo override by removing it from `.env.azure.example` and from README env documentation, relying on `graph.azure.yaml`'s configured model (`examples/demos/hellograph-speed/graph.azure.yaml:11-14`); or
2. Explicitly amend/split scope to authorize a graph-artifact change through the graph-authoring-governed route if preserving runtime model selection is required.

The first path is the smaller path and fits this retirement FR. The second path is only authorized after the FR says so; otherwise, `graph run` will pass the graph default model into `execute_prompt` (`yamlgraph/node_factory/llm_nodes.py:145-150`, `yamlgraph/node_factory/llm_nodes.py:331-340`), and `create_llm` uses environment model defaults only when no model parameter is supplied (`yamlgraph/utils/llm_factory.py:177-180`).

### R-4: Replace broad prose checks with one live-surface denylist

Revise the acceptance criteria so live-reference removal is checked by one denylist rather than scattered prose. Keep historical records in `feature-requests/`, `docs/diary/`, frozen changelog, and the retired CAP-90 file out of the zero-match gate.

Use this shape:

```bash
rg -n 'yamlgraph graph bench|graph bench|bench_commands|cmd_graph_bench|BenchResult|bench model override' \
  yamlgraph tests reference examples/demos/hellograph-speed ARCHITECTURE.md README.md CLAUDE.md .github/copilot-instructions.md \
  --glob '!**/__pycache__/**'
```

The criterion must require zero live matches except the new FR-913 witness test if it intentionally names the rejected `bench` token. This closes the current gap where AC-01 checks implementation symbols under `yamlgraph/` only (`feature-requests/FR-913-retire-graph-bench-command.md:99`), AC-05 names only three documentation surfaces (`feature-requests/FR-913-retire-graph-bench-command.md:103`), and the demo-local env template would otherwise remain stale (`examples/demos/hellograph-speed/.env.azure.example:5-6`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `yamlgraph/cli/bench_commands.py`. |
| D-2 | Remove the `graph bench` parser block from `yamlgraph/cli/__init__.py` and the `bench` dispatch branch from `yamlgraph/cli/graph_commands.py`. |
| D-3 | Delete `tests/unit/test_bench_command.py`; add one narrow FR-913 witness test that proves `yamlgraph graph bench` is rejected as an unknown graph subcommand. |
| D-4 | Migrate `examples/demos/hellograph-speed/compare_speed.sh` to `yamlgraph graph run ... --var-file ./vars.yaml --timing` for Google, Vertex, and Azure, with the run-count behavior explicitly chosen per R-2. |
| D-5 | Update `examples/demos/hellograph-speed/README.md` and `.env.azure.example` so they describe the migrated script and no longer claim a bench-only model override. |
| D-6 | Remove live bench advertising from `reference/cli.md`, `reference/getting-started.md`, and `ARCHITECTURE.md`; regenerate `reference/module-map.md`. |
| D-7 | Retire `capabilities/CAP-90-graph-bench-command.yaml` with `status: retired` and a `RETIRED by FR-913` description prefix while preserving the file as historical record. |
| D-8 | Add a changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-913. |
| D-9 | Update `feature-requests/FR-913-retire-graph-bench-command.md` with implementation status, folded revisions, and any deviations. |

Not authorized: changing `yamlgraph/utils/timing_tracker.py` semantics; removing the `--timing` flag from `graph run`; retiring or weakening CAP-89 / REQ-YG-231; deleting `examples/demos/hellograph-speed/` or its graph files under the current FR; implementing an eval harness; retiring A2A, MCP, skill export, or any sibling surface; sweeping historical diary, feature-request, memento, or frozen changelog records merely because they mention bench. If preserving Azure runtime model override requires editing `examples/demos/hellograph-speed/graph.azure.yaml`, stop and amend the FR through the graph-authoring route before touching that graph artifact.

## Revised acceptance criteria

- [ ] AC-01: `git ls-files 'yamlgraph/cli/bench_commands.py'` prints nothing.
- [ ] AC-02: `yamlgraph/cli/__init__.py` contains no `graph bench` subparser block and `yamlgraph/cli/graph_commands.py` contains no `bench` dispatch branch or `cmd_graph_bench` import.
- [ ] AC-03: the live-surface denylist command from R-4 returns zero matches except the new FR-913 witness test line that names the rejected `bench` token.
- [ ] AC-04: `tests/unit/test_bench_command.py` is deleted, and a new FR-913 witness test asserts the `graph` subparser rejects `bench` as an unknown subcommand.
- [ ] AC-05: `tests/unit/test_timing_tracker.py` still passes, CAP-89 remains active, and `git diff -- capabilities/CAP-89-execution-timing-callback.yaml yamlgraph/utils/timing_tracker.py` is empty unless the FR is amended.
- [ ] AC-06: `examples/demos/hellograph-speed/compare_speed.sh` contains no `graph bench` invocation and runs via `yamlgraph graph run ... --var-file ./vars.yaml --timing` for each retained provider; the script's run-count behavior matches the revised FR text from R-2.
- [ ] AC-07: `examples/demos/hellograph-speed/README.md` and `.env.azure.example` contain no bench-only wording such as `bench model override`; if `AZURE_MODEL` is removed from the demo contract, README env documentation is updated accordingly.
- [ ] AC-08: the diff includes a fresh `examples/demos/hellograph-speed/demo-output.log` produced after the migration.
- [ ] AC-09: `reference/cli.md`, `reference/getting-started.md`, and `ARCHITECTURE.md` contain no live bench advertising, and `reference/module-map.md` is regenerated.
- [ ] AC-10: `capabilities/CAP-90-graph-bench-command.yaml` contains `status: retired` and a description prefixed `RETIRED by FR-913`; `scripts/validate_capabilities.py` passes.
- [ ] AC-11: `python scripts/req_coverage.py --strict` passes with CAP-90 retired.
- [ ] AC-12: the full unit suite passes with the obsolete bench tests deleted and the FR-913 witness test present.
- [ ] AC-13: a changelog fragment under `changelog/unreleased/` exists with `type: removal` and names FR-913.
- [ ] AC-14: `feature-requests/FR-913-retire-graph-bench-command.md` records implementation status, folded revisions, and any deviations before enforcement is considered complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-4 are folded into `feature-requests/FR-913-retire-graph-bench-command.md`. | GATE |
| C-2 | Preserve CAP-89 / REQ-YG-231, `yamlgraph/utils/timing_tracker.py`, and `graph run --timing`; this FR retires only CAP-90 / REQ-YG-232. | GATE |
| C-3 | Do not edit `examples/demos/hellograph-speed/*.yaml` under this authority; graph-artifact changes require an amended/split graph-authoring-governed FR. | GATE |
| C-4 | Do not retire or modify sibling A2A, MCP, skill-export, export-package, or eval-harness surfaces under this FR. | GATE |
| C-5 | Deleted-import test failures are not acceptable evidence of success; residual tests must be updated or deleted so failures map to the revised acceptance criteria. | GATE |
| C-6 | If a tracked search finds a real `graph bench` consumer outside the named test, docs, CAP, and hellograph-speed surfaces, stop and amend the FR rather than silently deleting or preserving it. | GATE |

Authority granted: after the required revisions are folded, the enforcer may retire only the YAMLGraph `graph bench` command, its direct tests/docs/CAP-90 claim, and the hellograph-speed script/docs references necessary to keep the demo working on `graph run --timing`.
