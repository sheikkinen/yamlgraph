# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-17.md](diary-2026-02-17.md) — 10 entries, 10 named traps, one insight: every trap is an unasked verification question.

---

## 2026-02-18: Tool Reflection — When the Hammer Looks for Nails

**Context:** After the diary rotation, asked: "are there tools to propose — either for yamlgraph or metacognition?" Surveyed all ~35 MCP-exposed graphs. Existing meta-tools: `feature-brainstorm` (agent reads codebase, researches web, proposes, prioritizes), `run-analyzer` (post-mortem via LangSmith traces), `code-analysis` (static quality: ruff/radon/vulture/bandit/coverage).

**The inventory of what I almost proposed:**

| Candidate | Verdict | Why not |
|-----------|---------|---------|
| Verification question generator | No | One-line heuristic, not a tool. "Name the verification question" is a mental pause, not an LLM call. |
| Diary trap matcher | No | 10-entry lookup table. A cheat sheet, not a pipeline. |
| FR evidence checker | No | It's `grep`. |
| FR judgment assistant | No | Judgment is the human's job. Automating it defeats the purpose. |
| Metacognitive dashboard | No | Performative meta-recursion. Generates observations about observations. |

**What survived: one new tool, one approved FR to build.**

1. **Pipeline audit** (new graph, built today): Cross-pipeline structural analysis — quality gate coverage, silent fallback census, `on_error:skip` without reporting, shared pattern detection. This is the work I did manually in "The Constraint Shift" (3,000 words, ~2 hours surveying 10 pipelines). The graph does it in one command: `yamlgraph graph run examples/demos/pipeline-audit/graph.yaml`. Three Python tools scan all graph YAMLs and Python nodes, then two LLM nodes analyze and recommend. Smoke test: found 87 graphs, 333 nodes, 18 `on_error:skip`, 32 map nodes, 8 quality gate nodes.

2. **FR-043 Evaluation framework** (already approved, not built): The gap between "generate 81 lessons" and "know if they're good." The diary's constraint shift entry identified this as the primary bottleneck. The pipeline audit tool surfaces *where* evaluation is missing; FR-043 provides *what* to do about it.

**The trap I caught:** **Tool-solution bias.** When you build tools for a living, every insight looks like it needs a tool. But three of the five metacognitive candidates were heuristics (one-liners), one was a lookup table, and one was `grep`. The verification question — "does this need to be a pipeline, or is it a sentence?" — killed 5 of 7 candidates.

**The useful distinction:** A tool is justified when the work is (a) tedious to do manually, (b) needs to be repeated, and (c) benefits from LLM analysis beyond what `grep` provides. The pipeline audit passes all three: manually surveying 87 graphs for structural patterns took hours; it needs re-running as the ecosystem grows; pattern detection across graphs is genuinely analytical. The metacognitive candidates fail (b) — you name the trap once and remember it.

**What the audit graph covers:**
- `scan_graphs_tool`: parses all graph YAMLs, extracts node types, edges, `on_error` settings, quality gate presence, loops
- `scan_python_nodes_tool`: scans Python node/tool files for silent fallbacks (`bare except`, `or []`), inline `model_dump`, manual `.get('result')`
- `count_patterns_tool`: aggregate counts across all graphs (18 skip, 32 map, 8 quality gates, etc.)
- LLM analyze: structural issues, gap analysis, risk rating
- LLM recommend: prioritized, actionable improvements grouped by effort

**Heuristic:** Before proposing a tool, ask: "Is this a pipeline or a sentence?" If the insight fits in one line of documentation, it's a heuristic, not a tool. If it requires scanning N files and synthesizing patterns, it's a tool.

**Meta-heuristic:** The existing meta-tools (feature-brainstorm, run-analyzer, code-analysis) cover ideation, post-mortem, and static quality. The pipeline audit fills the structural health gap — the space between "does the code pass lint" and "does the pipeline architecture make sense." FR-043 will fill the output quality gap — "is what the pipeline produces any good." After that, the meta-tool inventory is complete. Further proposals should clear a high bar.
