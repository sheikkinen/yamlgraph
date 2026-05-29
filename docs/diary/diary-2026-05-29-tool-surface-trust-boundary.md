# Diary: Tool Surface as Trust Boundary

**Date:** 2026-05-29
**FR:** FR-463 (Enforcer Demo Safety Hardening)
**Trap:** `downstream_fix` — guard added where symptom manifests, not at entry boundary

## Observation

Reviewing the plan→judge→enforce trilogy tools revealed a clean capability escalation ladder: judge is read-only (5 tools), planner adds write (5 tools), enforcer adds test+commit (6 tools). The tool surface *is* the trust boundary.

But the security analysis showed the boundary is illusory. Every shell tool has path traversal — `cat {file}` can read `/etc/shadow`, `ls {dir}` can list `/root/`. Shell injection is blocked by `shlex.quote()` in the framework, but path validation doesn't exist at any layer. The `write_file` Python tool has no project-root restriction. And `git add -A` compounds everything by committing whatever pollution the agent creates.

FR-463 proposes fixing `write_file` path validation and `git add .` — both at the demo level. But this is a `downstream_fix`. The real boundary is the shell tool executor in `yamlgraph/tools/shell.py`. Every graph that uses `cat {file}` has the same traversal risk. Fixing two demo files doesn't fix the pattern.

The trap: I wrote the FR to fix the symptom (enforcer writes outside project root) rather than the cause (no path validation in the tool execution layer). The demo fix is still worth doing — defense in depth — but it's not the root cause fix.

## Heuristic

**Tools are trust boundaries, not convenience wrappers.** When a tool grants filesystem access to an LLM agent, the tool definition *is* the security perimeter. Validate paths at the tool executor level (the entry boundary), not in individual tool implementations (downstream). Each demo-level fix is a confession that the framework lacks a gate.

## Insight: Shared tools drift

The trilogy copies `read_file`, `search`, and `list_dir` definitions identically across three graphs. The descriptions already drift (different glob examples). When FR-463 adds path validation to `write_file`, it creates two copies of security-critical code. This is a `false_duplicate` waiting to diverge. A shared tool library (graph-level `imports` or `tool_packs`) would normalize at the boundary.

## Seed

Should YAMLGraph support a `working_dir` constraint on shell tools — a declarative sandbox that restricts all path arguments to a subtree? This would move path validation from per-tool Python code to the framework's tool executor, fixing the root cause once for all graphs.
