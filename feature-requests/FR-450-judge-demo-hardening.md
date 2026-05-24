# Feature Request: FR-450 Promote Judge Demo to Real Judge

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-05-24

## Summary

The standalone judge demo (`examples/demos/judge/`) renders verdicts on 6% of the architecture and cannot run tests. Promote it from a demo with facade tools to a **real, usable judge** with task-shaped tools, test execution, and adequate evidence coverage. Target: replace the Chaplain's copilot-based judge for lightweight, scriptable FR evaluation.

## Value Statement

A scriptable judge that produces trustworthy structured verdicts from genuine investigation — usable in CI, pre-merge gates, and ad-hoc review — without requiring the full Chaplain pipeline.

## Problem

### Core Problem: Ritual vs Investigation

The judge's 8 evaluation criteria require specific evidence. The current tools provide facades:

| Criterion | Evidence needed | Current tool | Coverage |
|---|---|---|---|
| 1. Scope clear & minimal | Read FR, count files | `cat` / `head -100` | Partial |
| 2. Contradictions | Read FR text | `cat` ✓ | OK |
| 3. Measurable criteria | See test patterns | **none** | **0%** |
| 4. Feasible implementation | Read code being changed | `head -100` | **14-100%** |
| 5. Architecture alignment | Search REQs, check layers | 30 of 498 lines | **6%** |
| 6. Single responsibility | Analyze FR | Pure reasoning ✓ | OK |
| 7. Strategic classification | Count use cases, existing abstractions | 10 of 428 FRs | **2.3%** |
| **8. Tests compile & fail** | **Run the tests** | **nothing** | **0%** |

Criterion #8 is the most important and the one the judge **cannot do at all**. The Scripture says *"Code that has not been run must not be demoed"* — but the judge renders a verdict on tests it has never executed.

The demo-output.log confirms: 14 tool calls, 6 redundant, agent renders confident 8/8 "all passed" verdict having seen 6% of the architecture and 0% of test execution. This is the **plausible_wrong_answer** trap: structurally correct output from an incomplete evidence base.

### Secondary Issues

1. **Redundant `read_fr` tool** — overlaps with `read_file`, wastes iterations.
2. **Static `check_architecture`** — same 30 lines regardless of FR.
3. **`max_iterations: 8`** — too tight for genuine investigation.
4. **Temperature bug** — split to FR-451 (framework bug, not demo-scoped).

## Proposed Solution

### New Toolset: 5 Task-Shaped Tools

Replace 4 facade tools with 5 tools mapped to what a judge actually investigates:

```yaml
tools:
  read_file:
    type: shell
    command: cat {file}
    description: "Read a project file in full."
    parse: text

  search:
    type: shell
    command: rg -n --glob "{glob}" "{pattern}" .
    description: "Search files matching a glob pattern. Examples: --glob 'ARCHITECTURE.md', --glob 'feature-requests/*.md', --glob 'yamlgraph/**/*.py', --glob 'tests/**/*.py', --glob 'capabilities/*.yaml'."
    parse: text

  list_dir:
    type: shell
    command: ls {dir}
    description: "List contents of a directory."
    parse: text

  git_log:
    type: shell
    command: git log --oneline --all --grep="{pattern}"
    description: "Search git history for commits mentioning a pattern. Find prior attempts, related FRs, rejected work."
    parse: text

  run_tests:
    type: shell
    command: pytest {test_file} -v --no-cov --tb=short 2>&1 | tail -40
    description: "Run a specific test file. Verify acceptance tests fail for the right reasons (criterion 8)."
    parse: text
```

Tool design rationale:

| Tool | Replaces | Why |
|---|---|---|
| `read_file` | `read_fr` + `read_file` | One tool, `cat`, full file. No truncation. |
| `search` | `check_architecture` + `search_existing_frs` | One `rg --glob` replaces 3 static tools. Agent picks scope. |
| `list_dir` | *new* | Explore project structure. See scale (428 FRs, 134 CAPs). |
| `git_log` | *new* | Was this tried before? Was it rejected? What changed recently? |
| `run_tests` | *new* | **The critical addition.** Without this, criterion #8 is guesswork. |

Tools considered and cut:
- `lint_graph` (`yamlgraph graph lint`) — <10% of FRs involve graph changes. Agent can use `search` to find graph YAML issues.
- `count_lines` (`wc -l`) — trivial; agent can infer from `read_file` output. Not worth an iteration budget slot.

### Node Configuration

```yaml
nodes:
  judge:
    type: agent
    prompt: judge
    model: claude-sonnet-4-6
    temperature: 0
    tools: [read_file, search, list_dir, git_log, run_tests]
    max_iterations: 12
    state_key: verdict
```

- `max_iterations: 12` — genuine investigation with 5 tools needs room. Not 15 (over-tooled), not 8 (too tight).
- `temperature: 0` — deterministic verdicts. Depends on FR-451 fix.

### Prompt Update

Update prompt to:
1. Read the FR first (unchanged)
2. Search for specific REQ/CAP IDs found in the FR (not static grep)
3. Check git history for prior attempts
4. **Run acceptance tests if they exist** — report pass/fail/error
5. Assess evidence coverage — "how many related FRs exist? Did you check enough?"
6. Count lines of files being modified — flag modules approaching 400-line limit

## Acceptance Criteria

- [ ] No tool uses `| head -N` truncation (except `run_tests` tail-40 for output sanity)
- [ ] Graph has 5 tools: `read_file`, `search`, `list_dir`, `git_log`, `run_tests`
- [ ] `search` uses `rg` with `--glob` for scoped pattern search across any project directory
- [ ] `run_tests` can execute pytest on a specific test file and report results
- [ ] `max_iterations` set to 12
- [ ] Demo runs successfully against a real FR (new `demo-output.log`)
- [ ] Agent verdict includes evidence from: architecture search, FR landscape, git history, and test execution
- [ ] `demo.sh` updated to output structured `judgement.json`
- [ ] Prompt updated: search specific REQ/CAP IDs, check git history, run tests if they exist

## Alternatives Considered

- **Keep as demo with facade tools** — Rejected. A judge that makes verdicts on 6% of evidence and 0% test execution is worse than no judge. "Demo" is not an excuse for dishonest tools.
- **Use `type: copilot` instead** — The Chaplain judge uses copilot with full tool access. But a copilot node requires the VS Code agent runtime. An agent node with shell tools is **portable** — runs in CI, scripts, cron. That's the value proposition.
- **Add summarization step before judge** — Considered for future: a pre-processing node that reads the FR and extracts REQ/CAP references, then feeds them to the judge as variables. Would reduce iteration waste. Out of scope for this FR.

## Related

- FR-447 — Judge agent node (created the demo)
- FR-449 — Agent structured output Anthropic bugfix
- FR-451 — Agent temperature zero bug (split from this FR)
- `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` — Chaplain copilot judge (the benchmark)
- `examples/demos/judge/` — target directory
- Scripture: `gate_checks_shape_not_substance`, `plausible_wrong_answer`, `demo_vs_test`

## Notes

- Shell injection is not an issue: agent shell tools go through `execute_shell_tool()` → `sanitize_variables()` → `shlex.quote()`.
- `run_tests` with `| tail -40` is the one justified truncation: pytest verbose output can be thousands of lines. The verdict needs pass/fail + failure message, not full trace.
- `rg --glob` with `shlex.quote()` verified working: `shlex.quote('feature-requests/*.md')` produces `'feature-requests/*.md'`, and `rg` handles its own glob expansion.

## Judgement

**Verdict:** AMEND → APPROVE (after split)

**Date:** 2026-05-24

The original FR bundled two orthogonal concerns: demo tool hardening (graph-level) and agent temperature resolution (framework-level). Split temperature bug to FR-451.

After split, FR-450 is single-responsibility: replace facade tools with task-shaped tools in one graph file + one prompt file + one shell script. No framework changes.

Trimmed from 7 to 5 tools: dropped `count_lines` (trivial, not worth iteration budget) and `lint_graph` (<10% of FRs involve graph changes). Each remaining tool earns its place against a specific evaluation criterion.

**Classification:** contrib_example — portable judge for ad-hoc FR review and potential CI gate. Not a framework primitive (that's the Chaplain pipeline).
