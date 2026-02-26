# The YAML-First Philosophy: Building Production AI Pipelines with Codified Doctrine

**A framework-level approach to the reproducibility crisis in LLM development**

---

The gap between prototype and production in LLM development remains stubbornly wide. Teams that can spin up a working demo in hours often spend months wrestling with state management, provider abstractions, error propagation, and the kind of implicit knowledge that disappears when engineers change roles.

The root cause is architectural: most LLM pipeline code conflates orchestration logic with business logic, making systems difficult to test, trace, and hand off.

## A Declarative Alternative

YAMLGraph addresses this by inverting the typical approach: **60-80% of AI workflows can be defined entirely in YAML** — graphs, prompts, and schemas — without writing Python code.

No Python classes. No state management boilerplate. No provider-specific code scattered across files.

```yaml
nodes:
  greet:
    type: llm
    prompt: greet
    state_key: greeting

edges:
  - from: START
    to: greet
  - from: greet
    to: END
```

This defines a complete LLM pipeline. Execute with:

```bash
yamlgraph graph run graph.yaml --var name="World"
```

## Beyond the Framework: Codified Doctrine

The more significant contribution is the **development methodology** that surrounds the framework.

When AI agents collaborate with humans on a shared codebase, implicit conventions become liabilities. Agents cannot infer architectural decisions from context alone — they require explicit constraints.

YAMLGraph addresses this with a formal doctrine called **The Scripture** — executable constraints enforced by linters, pre-commit hooks, and automated checks.

**The 10 Commandments of AI Development:**

1. Research before coding — the cheapest code is unwritten code
2. Demonstrate with example — never explain abstractly
3. Keep configuration separate — code is logic, config is truth
4. Honor existing patterns — conform before extending
5. Sanctify outputs with types — no untyped dicts
6. Bear witness of errors — hide nothing from CI
7. Be faithful to TDD — red-green-refactor
8. Kill entropy — split before bloat
9. Define operational truth — measure everything
10. Preserve and improve the doctrine — every failure refines the law

These are not aspirational guidelines — they are enforced at commit time.

## Documentation

The methodology is documented in a 9-chapter eBook:

📚 **"Building AI Development Pipelines with YAMLGraph"**

9 chapters covering:
- The doctrine and why it matters
- Quality toolchain (ruff, vulture, radon, jscpd)
- The 4-agent chaplaincy pipeline
- Reflexion loops and self-improving systems
- Feature request workflow (Plan → Judge → Enforce)
- Requirement traceability from spec to test
- YAMLGraph internals and extension points

Each chapter includes runnable examples from the repository.

## The Development Methodology

The development workflow consists of five phases:

1. **Research** — Let agents explore; distill into constraints
2. **Plan** — Write the feature request before the code
3. **Judge** — Critical review until the path is explicit
4. **Enforce** — Obey the plan; write failing tests first
5. **Distill** — After completion, extract insights for the next cycle

This methodology is intentionally rigid. Rigidity enables reproducibility.

The diary system captures insights from every development session. The chaplaincy pipeline enforces review on every change. The traceability matrix ensures every requirement has a test.

## The Core Value Proposition

LLM-assisted development introduces new failure modes: hallucinated architectures, inconsistent patterns, and undocumented decisions that compound over time.

Codified doctrine addresses these failure modes:
- Agents operate within hard boundaries that prevent hallucinated architectures
- Teams retain guardrails that survive personnel turnover
- Pipelines become reproducible, traceable, and debuggable

## Get Started

The eBook is available in the YAMLGraph repository.

The framework is open source:
- GitHub: github.com/sheikkinen/yamlgraph
- Quick start: `pip install yamlgraph`

Try the hello world demo:
```bash
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" \
  --var style="enthusiastic" \
  --full
```

---

The eBook and framework are open source. Contributions and feedback welcome.

#AI #LLM #SoftwareEngineering #DevOps #Python #YAML #LangGraph #OpenSource #MachineLearning #AIDevelopment

---

## About

YAMLGraph is an open-source YAML-first framework for LLM pipeline orchestration, built on LangGraph with multi-provider support.
