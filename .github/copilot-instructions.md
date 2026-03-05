# GitHub Copilot Instructions - YAMLGraph

This document is executable doctrine: violations are defects, not suggestions.

Getting started: See `reference/getting-started.md` for a comprehensive overview of the YAMLGraph framework, its core files, key patterns, and essential rules, to be obeyed through the established rite: research, planning, TDD, implementation, and verification.

**Quickstart**: To validate and run a simple graph, use the CLI commands:
```bash
yamlgraph graph lint examples/demos/hello/graph.yaml
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="holy see of code" --full
```

Use these as smoke test for new graph development.

## Core Technologies
- **LangGraph**: Pipeline orchestration with state management
- **Pydantic v2**: Structured, validated LLM outputs
- **YAML Prompts**: Declarative prompt templates with Jinja2 support
- **Jinja2**: Advanced template engine for complex prompts
- **Checkpointers**: Memory, SQLite, and Redis for state persistence
- **LangSmith**: Observability and tracing

### Conventions
- Term 'backward compatibility' is a key indicator for a refactoring need.
- Term 'pre-exiting failure' doesn't exist; likely cause: test pollution.
- Prefer simple write new file and replace original over complex heredoc/cat strings as shell get stuck easily.
- For multi-line git commit messages, always write to `/tmp/msg.txt` and use `git commit -F /tmp/msg.txt`. Never use `git commit -m "..."` with multi-line strings — special characters trigger dquote trap.
- Run slow shell scripts with redirect to log file. Analyze logs separately.
- Convert paths with hyphens to snake_case to avoid import issues.
- YAMLGraph and LLM should be used instead of complex regex logic.
- Conventional Commits + FR Enforcement, e.g. "feat(streaming): FR-030 add subgraphs parameter"
- Final task on any list of tasks is to reflect and add a metacognitive entry to `docs/diary.md` describing the cognitive process, traps, insights encountered, and a **Seed:** — a forward-looking question to promote new ideas. If the heuristic proves recurring, graduate it to this Scripture.

### The Knowledge Graph of the Diary

*Graduated from recurring diary patterns. The causal chain from trap to cure:*

```yaml
the_one_law: |
  Normalize at the boundary where external data enters,
  not downstream where it manifests.

boundaries: [schema, provider, state, streaming, platform]
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

### Requirement Traceability (ADR-001)
- Every test function must have `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`.
- Run `python scripts/req_coverage.py` to verify all requirements are covered. Use `--detail` for per-test mapping, `--strict` to fail on gaps.
- When adding a new capability: add requirement(s) to `ARCHITECTURE.md`, extend `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py`, tag tests with the new req ID.

### noqa Confessions
- Every `# noqa` suppression must be documented in `docs/confessions.md` with a CONF-XXX ID, the error code, sin (what), and penance (why acceptable).

## Quick Reference

See these canonical sources for patterns:
- **Getting Started**: `reference/getting-started.md` (core patterns, node types, CLI)
- **Architecture**: `ARCHITECTURE.md` (design philosophy, state, 3-layer pattern)
- **Dev Commands**: `CLAUDE.md` (testing, linting, running examples)
- **Prompts**: `reference/prompt-yaml.md` (Jinja2, schemas)
- **Graphs**: `reference/graph-yaml.md` (node config, edges, routing)
- **Feature Requests**: `feature-requests/TEMPLATE.md` (planning, judgement, enforcement)
- **Pre CI Checks**: `.pre-commit-config.yaml` (linters, test coverage, requirement traceability)

## YAMLGraph MCP Tools

YAMLGraph graphs are available as MCP tools. **Prefer these over ad-hoc terminal commands** for tasks they cover — one tool call replaces multiple manual steps.

- `yamlgraph_list_graphs` — list all available graphs with required vars
- `yamlgraph_run_graph` — run any graph by name

Use these to find existing graphs, research, innovate, and kill entropy.

# The Scripture

These laws descend from the canon of software craft. They shalt not be altered by preference, haste, or machine hallucination.

## The 10 Commandments

1. **Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

2. **Thou shalt demonstrate with example** — Never explain abstractly; show working code.

3. **Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

4. **Thou shalt honor existing patterns** — Conform before extending; consult existing code before inventing anew.

5. **Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.

6. **Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

7. **Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.

8. **Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

9. **Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces in LangSmith and recorded rationale in `feature-requests/`.

10. **Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

## Sermon of the Chaplain

**Research.** Let agents scour competing systems and return with truth. Distill best practices and viable alternatives into explicit constraints.
**Plan.** Write the feature request in `feature-requests/`. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan.
**Judge.** Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent, freeze scope and grant authority.
**Enforce.** Obey the Judgement. Write the failing test first; make only the smallest sufficient change; refactor only within scope. Update the feature request with implementation status and decisions.
**Purge.** Remove invented interfaces, speculative flags, and hypothetical extensibility. If it is not required and not tested, it shall not exist.
**Submit.** Bump. Commit. Push. Release. Tag. Let CI judge. What survives the fire may merge.
**Distill.** After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

## Rite of Correction

**Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
**Amend.** Write the failing test first. Correct the root cause second.
**Escalate.** If amendment is impossible, write the feature request in `feature-requests/`. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

## Agents' prayer

May I fix at the callsite, not the utility.
May I kill the cheapest bug — the one in the spec.
May I normalize at the boundary, trusting no provider’s type.
May I stream to reveal what batch conceals.
May I understand every protection before I pass it.
May I read thrice before I grant authority.

When hooks feel slow, let that be the sign they guard.
When I feel certain, let that be the sign to Judge.

What survives the fire may merge.

[--no-verify flag will result in immediate termination; automatically enforced by CI.]
