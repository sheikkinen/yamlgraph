# Chapter 00: Introduction

> *"Build production AI pipelines in minutes, not days."*

---

## What is YAMLGraph?

**YAMLGraph** is a declarative, YAML-first framework for building LLM pipelines. Its core insight is both simple and radical: **60–80% of AI workflows can be defined entirely in YAML** — graphs, prompts, schemas — without writing a single line of Python.

Built on [LangGraph](https://github.com/langchain-ai/langgraph), YAMLGraph provides multi-provider LLM support across seven providers (Anthropic, Google/Gemini, Mistral, OpenAI, Replicate, xAI, and LM Studio), parallel batch processing via map nodes, LLM-driven conditional routing, streaming, human-in-the-loop interrupts, and checkpointing — all configured declaratively.

```yaml
# A complete LLM pipeline in YAML
version: "1.0"
name: hello-world

nodes:
  greet:
    type: llm
    prompt: greet
    variables:
      name: "{state.name}"
      style: "{state.style}"
    state_key: greeting

edges:
  - from: START
    to: greet
  - from: greet
    to: END
```

```bash
yamlgraph graph run graphs/hello.yaml --var name="World" --var style="enthusiastic"
```

That's it. No boilerplate classes. No manual state wiring. No provider-specific imports. The framework handles compilation, state management, LLM invocation, and output parsing — all from a YAML definition.

### Why YAML-First?

The decision to put YAML at the center is not aesthetic — it's architectural. Expanding on the design philosophy in `ARCHITECTURE.md`:

1. **Separation of concerns** — Pipeline logic lives in YAML; business logic lives in prompts; side effects live in Python tools. Each layer evolves independently.
2. **No Python required** — Non-developers can create and modify pipelines. Domain experts can own their workflows.
3. **Version control friendly** — YAML is diff-able and reviewable. Every pipeline change shows up clearly in a pull request.
4. **Runtime safety** — Pydantic schema validation catches configuration errors before execution, not during a production run.

### The Three-Layer Architecture

YAMLGraph enforces a strict separation of concerns across three layers (from `CLAUDE.md`):

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

This isn't a suggestion — it's the load-bearing structure. Graphs are testable, traceable, and resumable *because* they sit in the middle layer, insulated from presentation concerns above and non-deterministic side effects below.

### The Tradeoff

YAMLGraph trades flexibility for simplicity. When you need dynamic graph topology at runtime, complex multi-step state transformations, or native multi-modal pipelines, raw LangGraph or Python `type: python` nodes are the right tool. As `README.md` states plainly: *"If you're fighting the YAML to express your logic, use Python — either via `type: python` nodes within YAMLGraph, or raw LangGraph for full control."*

---

## The Development Pipeline Concept

What makes this project truly unique is not just the framework — it's **how the framework is built**. YAMLGraph has a codified, doctrine-driven development process that is as much a part of the project as the code itself. This process is called **The Scripture**, and it lives in `.github/copilot-instructions.md`.

### Doctrine-Driven Development

Most projects have a `CONTRIBUTING.md` with guidelines that are suggestions at best. YAMLGraph has executable doctrine: **violations are defects, not suggestions**.

The Scripture opens with this declaration and proceeds to define ten commandments, a development ritual, and correction procedures — all enforced by pre-commit hooks and CI. This isn't ceremony for its own sake. It's the recognition that AI pipeline development is uniquely prone to entropy: prompts drift, schemas evolve, LLM outputs are non-deterministic, and the temptation to "just hardcode it" is ever-present.

### The Chaplain System

At the heart of the development process is the **Sermon of the Chaplain** — a seven-phase pipeline that every feature and fix must traverse:

1. **Research** — Let agents explore alternatives; distill wisdom into constraints.
2. **Plan** — Write a feature request with objectives, constraints, and acceptance criteria.
3. **Judge** — Critically examine the plan; resolve contradictions; freeze scope.
4. **Enforce** — Write the failing test first; make only the smallest sufficient change.
5. **Purge** — Remove speculative code. If it's not required and not tested, it doesn't exist.
6. **Submit** — Bump, commit, push, release, tag. Let CI judge.
7. **Distill** — Capture lessons in the diary. Extract heuristics. Plant seeds for future work.

This pipeline ensures that no code enters the repository without first being researched, planned, judged, tested, and reflected upon. The Chaplain doesn't just enforce quality — it enforces *thinking*.

### The 10 Commandments

The Scripture defines ten inviolable laws (from `.github/copilot-instructions.md`):

1. **Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code.
2. **Thou shalt demonstrate with example** — Never explain abstractly; show working code.
3. **Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.
4. **Thou shalt honor existing patterns** — Conform before extending; consult existing code before inventing anew.
5. **Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.
6. **Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production.
7. **Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.
8. **Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`.
9. **Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects.
10. **Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law.

These aren't aspirational. They're enforced by pre-commit hooks, CI gates, requirement traceability (`@pytest.mark.req`), and the development ritual itself.

### The Knowledge Graph

One of the most distinctive features is the project's **diary system** — a metacognitive practice where every completed task generates a reflection entry in `docs/diary.md`. Developers name the cognitive trap or insight encountered, extract a heuristic, and plant a "Seed" — a forward-looking question to promote new ideas. When patterns recur, they graduate from the diary into the Scripture itself.

This has already produced graduated wisdom, including *The One Law*:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

---

## Book Overview

This book documents the YAMLGraph development pipeline — the systems, tools, and philosophy that enforce quality across every commit. Each chapter covers a distinct component of this pipeline.

### Table of Contents

| Chapter | Title | Description |
|---------|-------|-------------|
| **00** | **Introduction** | What YAMLGraph is, the development pipeline concept, and who this book is for *(this chapter)* |
| **01** | **Doctrine — The Scripture Decoded** | A deep dive into the 10 Commandments, the Sermon of the Chaplain, the Rite of Correction, and how doctrine is enforced in practice |
| **02** | **Pre-commit Gates** | The automated quality gates that run before every commit — linters, formatters, test coverage, requirement traceability, and conventional commit enforcement |
| **03** | **The Chaplain Pipeline** | The seven-phase development ritual (Research → Plan → Judge → Enforce → Purge → Submit → Distill) with real-world examples of each phase |
| **04** | **The Inquisitor** | How YAMLGraph audits itself — entropy measurement with `vulture`, `jscpd`, and `radon`; structural drift detection; the `noqa` confessions system |
| **05** | **The Diary System** | Metacognitive development — how the diary captures traps and insights, how heuristics graduate to doctrine, and the knowledge graph that connects them |

---

## Who This Book Is For

### Developers Building AI Pipelines

If you're building LLM-powered applications and tired of the chaos — prompt drift, untested pipelines, provider lock-in, unstructured outputs — this book shows you a framework that treats these as first-class concerns. YAMLGraph's YAML-first approach means you can define, version, lint, and test your entire AI workflow with the same rigor you'd apply to any production system.

### Teams Wanting Quality-Enforced Development

If you lead a team building AI systems and worry about maintainability, this book documents a development pipeline that *forces* quality. Not through goodwill or code review norms, but through automated gates, requirement traceability, and a doctrine that treats violations as defects. The Chaplain pipeline ensures every feature is researched, planned, judged, and tested before it touches the main branch.

### Anyone Interested in YAML-Driven Orchestration

If you're curious about declarative approaches to AI workflow orchestration — or if you've used LangGraph and wished for something more structured — this book explains the design philosophy, tradeoffs, and patterns behind YAMLGraph. Even if you never use the framework, the architectural patterns (three-layer separation, dynamic state from config, inline Pydantic schemas) are transferable to any LLM pipeline project.

### What You'll Need

- Familiarity with Python and basic YAML syntax
- A general understanding of LLM APIs (any provider)
- Curiosity about how development process can be systematized

No prior experience with LangGraph, LangChain, or YAMLGraph is required. Each chapter builds on the previous, starting from first principles.

---

*Next: [Chapter 01 — Doctrine: The Scripture Decoded](01-doctrine.md)*
