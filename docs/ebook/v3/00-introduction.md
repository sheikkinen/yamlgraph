# Chapter 00: Introduction

> *"Build production AI pipelines in minutes, not days."*
> — YAMLGraph README

---

## What is YAMLGraph?

YAMLGraph is a **YAML-first framework** for building LLM pipelines using LangGraph. Its core insight is both simple and radical: **60–80% of AI workflows can be defined entirely in YAML** — graphs, prompts, and schemas — without writing a single line of Python.

```bash
pip install yamlgraph
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="enthusiastic"
```

That's it. A complete LLM pipeline defined in YAML, executed from the command line.

### The YAML-First Philosophy

Traditional LLM pipeline frameworks require developers to write Python classes, wire up state management, configure providers, and handle error propagation — all before the first prompt is sent. YAMLGraph inverts this by making **YAML the primary language** for pipeline definition:

```yaml
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

This design philosophy rests on four pillars, as documented in `ARCHITECTURE.md`:

1. **Separation of concerns** — Pipeline logic lives in YAML; business logic lives in prompts
2. **No Python required** — Non-developers can create and modify pipelines
3. **Version control friendly** — YAML configurations are diff-able and reviewable
4. **Runtime safety** — Schema validation catches errors before execution

### Built on Proven Foundations

YAMLGraph doesn't reinvent the wheel. It builds on a carefully chosen technology stack (`.github/copilot-instructions.md`):

- **LangGraph** — Pipeline orchestration with state management and checkpointing
- **Pydantic v2** — Structured, validated LLM outputs (no untyped dicts allowed)
- **Jinja2** — Advanced template engine for complex prompts
- **Multi-provider LLMs** — Anthropic, Google/Gemini, Mistral, OpenAI, Replicate, xAI, and LM Studio

### The Three-Layer Architecture

Every YAMLGraph application follows a strict separation of concerns (`CLAUDE.md`):

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

The logic layer — where LLM calls, routing decisions, state transitions, and checkpointing happen — is defined entirely in YAML. Python is reserved for what YAML can't express: terminal UI, HTTP routes, and external integrations.

---

## The Development Pipeline Concept

What makes YAMLGraph unique isn't just the framework — it's the **codified development process** that surrounds it.

Most open-source projects have a README, maybe a CONTRIBUTING guide, and some CI checks. YAMLGraph has a **doctrine**: a formal system of laws, rituals, and enforcement mechanisms that govern how code is written, reviewed, and merged. This system is called **the Scripture** (`.github/copilot-instructions.md`), and it is not metaphorical — it is executable.

> *"This document is executable doctrine: violations are defects, not suggestions."*
> — Opening line of the Scripture

### The Chaplain System

At the heart of the development pipeline is the **Sermon of the Chaplain** — a seven-phase workflow that every change must pass through:

1. **Research** — Let agents explore alternatives before writing code. The cheapest code is unwritten code.
2. **Plan** — Write a feature request with objectives, constraints, and acceptance criteria.
3. **Judge** — Critically examine the plan. Resolve contradictions. Eliminate ambiguity. Freeze scope only when the path is explicit and minimal.
4. **Enforce** — Write the failing test first. Make only the smallest sufficient change. Obey the Judgement.
5. **Purge** — Remove invented interfaces, speculative flags, and hypothetical extensibility. If it is not required and not tested, it shall not exist.
6. **Submit** — Bump. Commit. Push. Release. Tag. Let CI judge. *What survives the fire may merge.*
7. **Distill** — Capture lessons learned in the diary. Name the cognitive trap. Extract a heuristic. Plant a seed for future ideas.

This isn't ceremony for ceremony's sake. Each phase exists because the project learned — often painfully — what happens when it's skipped. The diary system (`docs/diary.md`) captures these lessons, and recurring patterns are graduated into the Scripture itself.

### Doctrine-Driven Development

The Scripture contains **10 Commandments** that govern all development:

| # | Commandment | Core Principle |
|---|-------------|----------------|
| 1 | Research before coding | Explore alternatives; the cheapest code is unwritten |
| 2 | Demonstrate with example | Never explain abstractly; show working code |
| 3 | Don't utter code in vain | Keep configuration separate and validated |
| 4 | Honor existing patterns | Conform before extending |
| 5 | Sanctify outputs with types | All data through Pydantic; no untyped dicts |
| 6 | Bear witness of errors | Hide nothing; expose every fault to linters and CI |
| 7 | Be faithful to TDD | Red-Green-Refactor; no fix without a failing test first |
| 8 | Kill all entropy | Split before bloat; delete dead code; measure structural drift |
| 9 | Define operational truth | Measurable objectives; instrument and trace execution |
| 10 | Preserve the doctrine | Every failure refines the law; codify success |

These commandments are enforced by automated tooling: pre-commit hooks, requirement traceability scripts, linters, and CI gates. They are not aspirational guidelines — they are **guardrails with teeth**.

### The Knowledge Graph

Over time, the project's diary entries revealed recurring patterns — cognitive traps that developers fall into repeatedly. These were distilled into what the Scripture calls **The One Law**:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

This single principle, graduated from diary observations, applies across schemas, providers, state management, streaming, and platform boundaries. It is the thread that connects the 10 Commandments into a coherent philosophy.

---

## Book Overview

This book decodes the YAMLGraph development pipeline — not just the framework's features, but the system of practices, tools, and enforcement mechanisms that ensure quality at every stage. Each chapter focuses on one component of the pipeline.

### Table of Contents

| Chapter | Title | What You'll Learn |
|---------|-------|-------------------|
| **00** | **Introduction** | What YAMLGraph is, the development pipeline concept, and who this book is for *(this chapter)* |
| **01** | **Doctrine — The Scripture Decoded** | The 10 Commandments, the Sermon of the Chaplain, and how doctrine drives development |
| **02** | **Pre-commit Gates** | Automated quality checks that run before every commit: linters, formatters, and custom hooks |
| **03** | **The Chaplain Pipeline** | The seven-phase workflow from Research to Distill, with real examples from the project's history |
| **04** | **The Inquisitor** | Critical review processes: how plans are judged, scope is frozen, and authority is granted |
| **05** | **The Diary System** | Metacognitive reflection, cognitive trap identification, and how heuristics graduate to doctrine |
| **06** | **Requirement Traceability Matrix** | ADR-001: linking every test to a requirement, coverage verification, and gap detection |
| **07** | **YAMLGraph Core** | The framework itself: compilation pipeline, node types, state management, and multi-provider LLMs |
| **08** | **The Wizard Behind the Curtain** | How AI agents (Copilot, Claude) are integrated into the development workflow as first-class participants |

### How to Read This Book

The chapters are designed to be read in order, as each builds on concepts from the previous. However, if you're primarily interested in:

- **The framework itself** → Start with Chapter 07 (YAMLGraph Core), then read Chapters 00–01 for context
- **The development process** → Read Chapters 01–06 in sequence
- **AI-assisted development** → Jump to Chapter 08, referring back as needed

---

## Who This Book Is For

### Developers Building AI Pipelines

If you're building LLM-powered applications and find yourself drowning in boilerplate — wiring up providers, managing state, handling errors, formatting prompts — YAMLGraph offers a declarative alternative. This book shows not just how to use the framework, but the architectural thinking behind it.

### Teams Wanting Quality-Enforced Development

The development pipeline documented here — doctrine, pre-commit gates, requirement traceability, the diary system — is transferable to any software project. If your team struggles with inconsistent quality, undocumented decisions, or recurring mistakes, the patterns in Chapters 01–06 provide a concrete, battle-tested model.

### Anyone Interested in YAML-Driven Orchestration

The idea of defining complex workflows in YAML isn't new (think Kubernetes, GitHub Actions, Ansible). But applying it to LLM pipelines — with type-safe outputs, multi-provider support, and streaming — is a frontier worth exploring. This book documents one opinionated approach and the lessons learned along the way.

### What This Book Is NOT

This book is not a LangGraph tutorial or a general introduction to LLMs. It assumes familiarity with:

- Python 3.11+ and basic package management
- Large Language Models and prompt engineering concepts
- YAML syntax
- Git and CI/CD basics

---

## Getting Started

To follow along with examples in this book, you'll need the YAMLGraph repository:

```bash
git clone https://github.com/sheikkinen/yamlgraph.git
cd yamlgraph
pip install -e ".[dev]"
```

Verify your installation:

```bash
yamlgraph graph lint examples/demos/hello/graph.yaml
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" \
  --var style="enthusiastic" \
  --full
```

If you see a greeting, you're ready. Let's begin.

---

*Next: [Chapter 01 — Doctrine: The Scripture Decoded](01-doctrine.md)*
