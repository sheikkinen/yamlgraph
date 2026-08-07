# Feature Request: Research-Agent Toolbelt Conversion — Fourth Shell-Manifest Consumer

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
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

**Sequencing:** enforce after FR-779 lands — both FRs touch the same graph file; FR-779's binding/routing changes are the base. RED-before-authoring per FR-779's R-3 precedent.

## Acceptance Criteria

- [ ] AC-1 RED: failing test asserting research-agent declares read_file/search/list_dir/git_log solely by toolbelt manifest ref.
- [ ] AC-2 GREEN via author.sh; lint + validate + authoring report evidence.
- [ ] AC-3 Effective-config equivalence test (command, description, parse, timeout == 30) for the four converted tools; `count_lines` remains inline.
- [ ] AC-4 Prompts reference canonical tool names; no orphan references to `search_code`/`list_files` remain anywhere in the demo.
- [ ] AC-5 Regenerated grounded `demo-output.log` with non-empty findings; no fatal markers; topic echo visible.
- [ ] AC-6 Tests carry `@pytest.mark.req` markers (extend REQ-YG-579/CAP-220 with the fourth consumer, or add a REQ if the judge prefers); `req_coverage --strict` green.
- [ ] AC-7 Changelog fragment, FR fold, diary entry; no `yamlgraph/` changes.

## Alternatives Considered

- **Raise `max_iterations` instead:** treats the symptom — the agent would still read 80-line fragments; cap increases without tool fidelity are cost without grounding.
- **Widen the inline variants in place (cat/rg inline):** re-creates the byte-duplication FR-777 just eliminated; four consumers of the same contract belong on the manifest.
- **Convert `count_lines` too:** no second consumer exists; the fit boundary says demo-local variants stay inline.

## Related

- feature-requests/FR-777-shared-shell-toolbelt-manifests.md — toolbelt + fit boundary
- feature-requests/FR-779-research-agent-demo-rot.md — same graph, bindings + synthesis gate (base for this FR)
- examples/shared/toolbelt/ — the four manifests
- feature-requests/FR-215-research-agent-demo.md — created the demo

## Judgement (pending)

**Verdict:** —
