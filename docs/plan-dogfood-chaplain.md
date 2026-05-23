# Plan: Dogfood — Replace Chaplain Copilot Nodes with YAMLGraph Agents

**Date:** 2026-05-22
**Origin:** Skills research reflection — chaplain pipeline as the real skills use case
**Status:** Exploration (phased FR series)

## The Problem

The chaplain pipeline (`.chaplain/config/watcher-pipeline-v2.yaml`) runs 5 LLM-powered steps, all as `type: copilot` black-box nodes with `--allow-all-paths --allow-all-tools`:

| Step | Current type | Model | Needs unrestricted access? |
|------|-------------|-------|---------------------------|
| Plan | `copilot` | gpt-5.3-codex | **Yes** — creates files, runs terminal |
| Judge | `copilot` | claude-sonnet-4.6 | **No** — reads FR + topic, returns verdict |
| Enforce | `copilot` | gpt-5.3-codex | **Yes** — implements code |
| Validate fix | `copilot` | claude-opus-4.6 | Partially — fixes pre-commit issues |
| Sanity check | `copilot` | claude-sonnet-4.6 | **No** — reviews diff, writes diary |

The copilot node is opaque: no tool-call tracing, no structured output, no capability constraints. YAMLGraph orchestrates *when* each step runs but has zero visibility into *what happens inside*.

## The Opportunity

Converting read-only/review steps from copilot to YAMLGraph agent nodes would:

1. **Prove the framework** — YAMLGraph orchestrating its own development pipeline
2. **Create the real skills use case** — shared tool bundles across 3+ pipeline agents
3. **Add observability** — LangSmith traces for every tool call within judge/sanity/inquisitor
4. **Reduce blast radius** — constrained tool sets instead of `--allow-all-tools`
5. **Enable structured output** — Pydantic schemas for verdicts instead of keyword parsing

## Phased Approach

### Phase 1: Judge Node (FR-447)

The judge is the cleanest candidate:
- **Input**: FR file path + topic file path
- **Output**: Structured verdict (APPROVE/AMEND/REJECT/SPLIT) with reasoning
- **Tools needed**: ~6 read-only tools (read files, check architecture, verify tests compile)
- **No side effects** except writing Judge Notes back to FR on AMEND

This is the proof-of-concept. If it works, the pattern extends to phases 2-3.

### Phase 2: Sanity Check Node

Similar profile to judge:
- **Input**: FR path + worktree dir + branch + topic
- **Output**: PASS/WARN with reasoning
- **Tools needed**: git diff, read FR, read diary entries, create diary file
- **One side effect**: creates diary entry and commits it

### Phase 3: Inquisitor as Graph

Currently a raw shell script (`inquisitor.sh`) calling `copilot -p`:
- **Input**: recent commits, CHANGELOG, diary entries
- **Output**: Audit findings + diary entry
- **Tools needed**: git log, read files, create diary, scan FRs
- **Would become**: a proper graph in `.chaplain/graphs/watcher-inquisitor/`

### Out of Scope: Plan & Enforce

Plan and Enforce need unrestricted tool access (terminal, file editing, code search). They're general-purpose coding sessions. Constraining them defeats their purpose.

## Skills That Emerge

Once 3 agents share tools, the reuse pattern becomes concrete:

```yaml
# skills/fr-tools.yaml
name: fr-tools
description: "Read and analyze feature request documents"
tools:
  read_fr:
    type: shell
    command: cat {fr_path}
    description: "Read the feature request document"
  read_topic:
    type: shell
    command: cat {topic_file}
    description: "Read the original topic/proposal"
  parse_acceptance_criteria:
    type: python
    module: .chaplain.tools.fr_tools
    function: parse_acceptance_criteria
    description: "Extract and validate acceptance criteria from FR"
  check_fr_status:
    type: python
    module: .chaplain.tools.fr_tools
    function: check_fr_status
    description: "Get current FR status field"

# skills/git-analysis.yaml
name: git-analysis
description: "Analyze git repository state and diffs"
tools:
  diff_stat:
    type: shell
    command: cd {worktree_dir} && git diff --stat main..HEAD
    description: "Show diff stats vs main branch"
  recent_log:
    type: shell
    command: cd {worktree_dir} && git log --oneline main..HEAD
    description: "Show commits on current branch"

# skills/diary-tools.yaml
name: diary-tools
description: "Create and read diary reflection entries"
tools:
  read_recent_diary:
    type: shell
    command: ls -1t docs/diary/*.md | head -5 | xargs head -20
    description: "Read headers of recent diary entries"
  create_diary:
    type: python
    module: .chaplain.tools.diary_tools
    function: create_diary_entry
    description: "Create a new diary reflection entry"

# skills/code-quality.yaml
name: code-quality
description: "Run code quality checks"
tools:
  verify_tests_compile:
    type: shell
    command: cd {worktree_dir} && python -m pytest --collect-only -q 2>&1 | tail -10
    description: "Verify tests compile and can be collected"
  check_ruff:
    type: shell
    command: cd {worktree_dir} && ruff check --output-format=concise 2>&1 | tail -10
    description: "Run ruff linter"
```

Agent tool selection per phase:

| Agent | Skills |
|-------|--------|
| Judge | `fr-tools`, `git-analysis`, `code-quality` |
| Sanity check | `fr-tools`, `git-analysis`, `diary-tools` |
| Inquisitor | `fr-tools`, `git-analysis`, `code-quality`, `diary-tools` |

## Success Criteria for the Overall Plan

1. Judge runs as `type: agent` with structured Pydantic output — no keyword parsing
2. LangSmith traces show individual tool calls within the judge step
3. Skills reuse validated: same `fr-tools` skill used by judge and sanity check
4. Pipeline pass rate does not regress (judge verdicts remain sound)
5. No `--allow-all-tools` on steps that don't need it

## Dependency

- Skills feature (from `docs/plan-yamlgraph-skills.md`) is a nice-to-have but not a blocker — Phase 1 can use inline tool definitions. Skills become valuable at Phase 2+ when reuse across agents matters.

## Next Steps

1. **FR-447**: Judge node as YAMLGraph agent (this is the first FR)
2. After FR-447 ships and is validated in production pipeline runs, proceed to Phase 2
3. Skills feature can be built in parallel or after Phase 2 proves the reuse need
