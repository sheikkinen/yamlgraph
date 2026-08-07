# Feature Request: Research-Agent Toolbelt Conversion — Fourth Shell-Manifest Consumer

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged 2026-08-07 — APPROVED WITH REVISIONS; R-1..R-4 folded below; authority active per judgement
**Requested:** 2026-08-07
**First consumer / first event:** the research-agent demo itself, on its next research run — concretely, the FR-777 assumption path (research graph published as a toolbelt tool for the judge_fr adapter) needs the graph to produce grounded findings first; the 2026-08-06 dogfood run produced empty findings within 10 iterations, plausibly because its truncating tools starve the agent of context.

**Prior art:** FR-777 created `examples/shared/toolbelt/` and froze the fit boundary — "verbatim two-plus-consumer contracts earn manifests; demo-local variants stay inline." Research-agent's tools are variants today (that is why FR-777 correctly left it inline); this FR proposes *changing the variants to the canonical contracts*, which the boundary permits — it forbids forking manifests per demo, not converging demos onto manifests. FR-779 (judged) fixes the same demo's bindings and synthesis gate but explicitly does not authorize tool semantics changes.

## Summary

Convert `examples/demos/research-agent/graph.yaml` from four inline shell tool variants to the shared toolbelt manifests, making it the fourth committed shell-manifest consumer:

| Current inline | Replacement |
|---|---|
| `read_file`: `head -80 {file}` | `toolbelt/read_file.tool.yaml` (`cat {file}`) |
| `search_code`: `grep -rn "{pattern}" --include="*.py" {scope} \| head -20` | `search` via `toolbelt/search.tool.yaml` (`rg -n --glob {glob} {pattern} .`) |
| `list_files`: `find {path} -name "*.py" \| head -30` | `list_dir` via `toolbelt/list_dir.tool.yaml` (`ls {dir}`) |
| `count_lines`: `wc -l {file}` | keep inline (no toolbelt equivalent; demo-local) |
| (absent) | add `git_log` via `toolbelt/git_log.tool.yaml` (prior-art search, parity with planner/enforcer/judge) |

## Value Statement

The research agent stops reading 80-line fragments through a py-only grep and gains the same full-fidelity read/search/history surface the planner, enforcer, and judge agents use — a prerequisite for publishing it as the FR-777 research tool.

## Problem

- `head -80` truncation means any file beyond 80 lines is invisible past its header; `| head -20` caps search results; `--include="*.py"` blinds the agent to YAML, Markdown, and configs — in a YAML-first framework.
- Evidence: the 2026-08-06 run (FR-779 evidence section) exhausted 10 iterations without producing findings on a question whose answers live in `.py` files longer than 80 lines and in `.yaml`/`.md` files the grep could not see.
- Tool-name drift (`search_code` vs `search`, `list_files` vs `list_dir`) forces prompt-level renames per demo and blocks the toolbelt's union-description convergence.

## Ideal Result

Research-agent declares read/search/list/git-history tools purely by toolbelt manifest reference — identical contracts to the other three agent demos — keeps only genuinely demo-local tools inline, and its prompts reference the canonical tool names. A live demo run produces non-empty grounded findings within its iteration budget.

## Proposed Solution

1. Via `scripts/author.sh` (FR-767 sole route): replace the three convertible inline tools with `manifest:` refs (tool keys renamed to canonical `read_file`/`search`/`list_dir`), add `git_log` by manifest ref, keep `count_lines` inline.
2. Update the agent-node `tools:` lists and any prompt text referencing old tool names (`search_code`, `list_files`) — prompts are governed artifacts, same route.
3. Extend the FR-777 test suite pattern: research-agent's four shared tools resolve to effective configs equal to the manifest contracts; `count_lines` stays inline.
4. Regenerate `demo-output.log` from a grounded successful run (demo-gate; the anti-XYZZY topic-echo check from FR-779 applies).

**Scope translation (R-2):** canonical `search` takes `(pattern, glob)` from `.` and `list_dir` takes `(dir)` — neither takes `scope`. The graph keeps `scope` as input; the prompts must teach the canonical names and argument names (`search(pattern, glob)`, `list_dir(dir)`, `read_file(file)`, `git_log(pattern)`, inline `count_lines(file)`) and instruct the agent to honor `scope` by translating it into `list_dir.dir` and `search.glob` prefixes — never silently broadening every search to the whole repository.

**FR-779 regression boundary (R-3):** the conversion must not revert FR-779 — `state.query`/`state.scope` declarations and `{state.…}` bindings stay; the conditional `validate_findings → END` route for empty findings / low confidence stays; prompt wording alone is not an acceptable guard.

**Traceability surface (R-1):** extend `CAP-220`/`REQ-YG-579` to name research-agent as the fourth consumer; update `examples/shared/README.md` and the four manifest header comments — documentation only, no runtime contract changes.

**Sequencing:** enforce after FR-779 lands — both FRs touch the same graph file; FR-779's binding/routing changes are the base. RED-before-authoring per FR-779's R-3 precedent.

## Acceptance Criteria (revised per judgement 2026-08-07)

- [ ] AC-01: RED test proves the committed research-agent graph does not yet declare `read_file`, `search`, `list_dir`, and `git_log` solely via `manifest:` refs while keeping `count_lines` inline; GREEN converts exactly those four shared tools and no others.
- [ ] AC-02: A committed test loads the research-agent graph and proves the effective shell config for `read_file`, `search`, `list_dir`, and `git_log` matches the shared manifest contracts: `command`, canonical `description`, `parse`, and `timeout == 30`.
- [ ] AC-03: `plan_research` and `execute_research` tool lists use canonical names; no `search_code` or `list_files` references remain anywhere under `examples/demos/research-agent/`.
- [ ] AC-04: The updated research-agent prompts describe the canonical tool names and argument names, remove Python-only / first-80-lines semantics, and instruct the agent to honor `scope` through `list_dir.dir` and `search.glob` rather than silently searching the whole repository.
- [ ] AC-05: FR-779 behavior is preserved: `state.query` / `state.scope` remain declared and bound through `{state...}` templates, and empty findings or low validation confidence still terminates after `validate_findings` without producing `report`.
- [ ] AC-06: `examples/shared/README.md`, the four shared toolbelt manifest header comments, and `CAP-220` / `REQ-YG-579` are updated to record research-agent as the fourth shell-toolbelt manifest consumer; every new or changed test carries `@pytest.mark.req("REQ-YG-579")`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: Governed graph and prompt edits are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint, validate, smoke, and the relevant test evidence for the changed demo.
- [ ] AC-08: A regenerated committed `examples/demos/research-agent/demo-output.log` from a live successful run shows non-empty `findings`, `validation.confidence` not `low`, a produced `report`, visible query/topic echo, at least one concrete in-scope file or line citation from tool findings, and no fatal markers.
- [ ] AC-09: No files under `yamlgraph/` change; shared manifest runtime contracts are not changed; `count_lines` is not moved to the toolbelt; no research graph manifest or judge adapter branch is added; `max_iterations` is not increased as the fix.
- [ ] AC-10: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Alternatives Considered

- **Raise `max_iterations` instead:** treats the symptom — the agent would still read 80-line fragments; cap increases without tool fidelity are cost without grounding.
- **Widen the inline variants in place (cat/rg inline):** re-creates the byte-duplication FR-777 just eliminated; four consumers of the same contract belong on the manifest.
- **Convert `count_lines` too:** no second consumer exists; the fit boundary says demo-local variants stay inline.

## Related

- feature-requests/FR-780-research-agent-toolbelt-conversion.judgement.md — verdict APPROVED WITH REVISIONS (2026-08-07); scope D-1..D-7 and conditions C-1..C-5 govern enforcement
- feature-requests/FR-777-shared-shell-toolbelt-manifests.md — toolbelt + fit boundary
- feature-requests/FR-779-research-agent-demo-rot.md — same graph, bindings + synthesis gate (base for this FR)
- examples/shared/toolbelt/ — the four manifests
- feature-requests/FR-215-research-agent-demo.md — created the demo

## Judgement (2026-08-07)

**Verdict:** APPROVED WITH REVISIONS — see feature-requests/FR-780-research-agent-toolbelt-conversion.judgement.md. R-1 (freeze CAP-220/REQ-YG-579 traceability + doc surfaces), R-2 (canonical argument names + scope translation contract in prompts), R-3 (FR-779 regression boundary named), R-4 (grounded state-evidence witness, not topic echo alone) folded above. Conditions C-1..C-5 are GATE.
