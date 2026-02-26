# Chapter 00: Introduction

> *"Build production AI pipelines in minutes, not days."*
> — YAMLGraph README

---

## What is YAMLGraph?

YAMLGraph is a **YAML-first framework** for building LLM pipelines using LangGraph. Its founding insight is deceptively simple: **60–80% of AI workflows can be defined entirely in YAML** — graphs, prompts, and schemas — without writing a single line of Python.

Built on LangGraph with multi-provider LLM support (Anthropic, Google/Gemini, Mistral, OpenAI, Replicate, xAI, LM Studio), YAMLGraph trades some flexibility for dramatically faster prototyping, easier maintenance, and built-in best practices. A pipeline that might take days to wire up in raw Python can be defined, validated, and running in minutes:

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

```bash
yamlgraph graph run graphs/hello.yaml --var name="World" --var style="enthusiastic"
```

That's a complete, runnable AI pipeline. No boilerplate. Version-controlled. Observable via LangSmith. Lintable. Diff-able in code review.

### The Design Philosophy

YAMLGraph enforces a strict **separation of concerns** through what the project calls the Three-Layer Pattern (*source: `CLAUDE.md`, §Three-Layer Pattern*):

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

The four reasons YAML comes first (*source: `ARCHITECTURE.md`, §Why YAML-First?*):

1. **Separation of concerns** — Pipeline logic in YAML, business logic in prompts
2. **No Python required** — Non-developers can create/modify pipelines
3. **Version control friendly** — Diff-able, reviewable configuration
4. **Runtime safety** — Schema validation catches errors before execution

### What It Includes

The framework ships with a rich set of capabilities (*source: `README.md`*):

- **Declarative graph configuration** with schema validation
- **YAML prompt templates** with Jinja2 support
- **Pydantic v2** structured LLM outputs — inline in YAML or as Python models
- **Multi-provider LLMs** — seven providers, switchable at runtime
- **LangGraph orchestration** with parallel map nodes, conditional routing, and loops
- **Human-in-the-loop** interrupt nodes for user input
- **Token streaming** at both prompt and graph level
- **Async support** for FastAPI integration
- **Checkpointers** — Memory, SQLite, and Redis for state persistence
- **LangSmith observability** and tracing

### When Not to Use It

YAMLGraph is honest about its tradeoffs (*source: `README.md`, §When NOT to Use YAMLGraph*). Consider raw LangGraph when you need dynamic graph topology at runtime, complex multi-step state transformations, custom node types per-invoke, or native multi-modal pipelines. The rule of thumb: **if you're fighting the YAML to express your logic, use Python.**

---

## The Development Pipeline Concept

What makes YAMLGraph unique among AI frameworks is not just what it builds, but **how it's built**. The project codifies its entire development process into an executable doctrine called **The Scripture** (*source: `.github/copilot-instructions.md`*).

This document opens with a declaration that sets the tone:

> *"This document is executable doctrine: violations are defects, not suggestions."*

### Doctrine-Driven Development

Most projects have a `CONTRIBUTING.md` that suggests conventions. YAMLGraph has a **living covenant** that is enforced by pre-commit hooks, CI pipelines, and AI agents. The doctrine is organized into three layers:

**The 10 Commandments** define inviolable laws. A few examples (*source: `.github/copilot-instructions.md`, §The 10 Commandments*):

- *"Thou shalt research before coding"* — Explore alternatives before writing a line
- *"Thou shalt be faithful to TDD"* — Red-Green-Refactor; no bug fixed without a failing test first
- *"Thou shalt sanctify thy outputs with types"* — All data through Pydantic; no untyped dicts
- *"Thou shalt kill all entropy and false idols"* — Split modules before they bloat; delete dead code

**The Sermon of the Chaplain** defines the development workflow as a ritual (*source: `.github/copilot-instructions.md`, §Sermon of the Chaplain*):

1. **Research** — Let agents scour competing systems and return with truth
2. **Plan** — Write the feature request; define objectives, constraints, acceptance criteria
3. **Judge** — Critically examine; resolve contradictions; freeze scope
4. **Enforce** — Write the failing test first; make the smallest sufficient change
5. **Purge** — Remove speculative code; if it's not required and not tested, it shall not exist
6. **Submit** — Bump, commit, push, release, tag; let CI judge
7. **Distill** — Capture lessons in the diary; extract heuristics; plant seeds for future work

**The Rite of Correction** provides a structured approach to fixing things when they break: Inspect, Amend, Escalate.

### The Chaplain System

The Chaplain is not a metaphor — it's an **automated pipeline** that enforces the doctrine at every commit. Through pre-commit hooks, linters, requirement traceability scripts, and CI checks, the Chaplain ensures:

- Every test links to a requirement via `@pytest.mark.req("REQ-YG-XXX")`
- Every `# noqa` suppression is documented with a confession ID
- Every module stays under the line-count ceiling
- Every commit message follows Conventional Commits with feature request tracing

The development process is itself a pipeline — a meta-pipeline that builds the framework that builds pipelines.

### The Knowledge Graph

Lessons learned don't disappear. They follow a graduation path (*source: `.github/copilot-instructions.md`, §The Knowledge Graph of the Diary*):

1. **Diary entry** — A metacognitive reflection after each task
2. **Recurring pattern** — When a heuristic appears multiple times
3. **Scripture graduation** — Promoted to a permanent commandment

The core insight that graduated from the diary:

> *"Normalize at the boundary where external data enters, not downstream where it manifests."*

This single law — the One Law — governs how the project handles schemas, providers, state, streaming, and platform boundaries.

---

## Book Overview

This book documents the **YAMLGraph Development Pipeline** — the systems, rituals, and automation that enforce quality across the project. Each chapter examines one layer of this pipeline in depth.

### Table of Contents

| Chapter | Title | What You'll Learn |
|---------|-------|-------------------|
| **00** | **Introduction** *(this chapter)* | What YAMLGraph is, why the development pipeline matters, and who this book is for |
| **01** | **Doctrine — The Scripture Decoded** | Deep dive into the 10 Commandments, the Sermon, and how doctrine shapes every decision |
| **02** | **Pre-commit Gates** | The automated checks that run before every commit — linters, formatters, requirement traceability, and confession tracking |
| **03** | **The Chaplain Pipeline** | How the Research → Plan → Judge → Enforce → Purge → Submit → Distill workflow operates in practice |
| **04** | **The Inquisitor** | Automated code quality enforcement — entropy measurement, dead code detection, duplication hunting, and module health |
| **05** | **The Diary System** | Metacognitive reflection as a development practice — how lessons graduate from diary entries to permanent doctrine |
| **06** | **Requirement Traceability Matrix** | How every test maps to a requirement, how coverage gaps are detected, and how the matrix evolves with the codebase |

---

## Who This Book Is For

### Developers Building AI Pipelines

If you're using LangChain, LangGraph, or similar frameworks to build LLM-powered applications, this book shows you a **declarative alternative** that eliminates boilerplate. You'll learn how YAMLGraph's YAML-first approach lets you define complex workflows — routing, loops, agents, human-in-the-loop — without the ceremony of full-code frameworks. Even if you don't adopt YAMLGraph, the patterns here (structured outputs, provider abstraction, state management) transfer to any AI pipeline work.

### Teams Wanting Quality-Enforced Development

The development pipeline documented in this book solves a problem every team faces: **how do you maintain quality as a codebase grows?** YAMLGraph's answer — codified doctrine, automated enforcement, requirement traceability, and metacognitive reflection — provides a template you can adapt. The Chaplain system, pre-commit gates, and diary practice are patterns that work regardless of whether you're building AI pipelines or traditional software.

### Anyone Interested in YAML-Driven Orchestration

YAML as a configuration language is everywhere. YAML as an **orchestration language** for AI is still novel. This book explores what happens when you push YAML beyond configuration into the territory of workflow definition — where templates become programs, schemas become contracts, and graphs become the primary unit of composition. If you're curious about declarative approaches to complex systems, this book is for you.

### How to Read This Book

The chapters are designed to be read in order, as each builds on concepts from the previous. However, if you're primarily interested in specific topics:

- **For the philosophy**: Start with Chapter 01 (Doctrine)
- **For the tooling**: Jump to Chapter 02 (Pre-commit Gates) and Chapter 04 (The Inquisitor)
- **For the process**: Read Chapter 03 (The Chaplain Pipeline)
- **For the culture**: Read Chapter 05 (The Diary System)
- **For the engineering rigor**: Read Chapter 06 (Requirement Traceability)

---

## A Note on Sources

This book draws directly from the YAMLGraph repository's living documentation:

| Source File | Role |
|-------------|------|
| `README.md` | Project overview and public-facing documentation |
| `ARCHITECTURE.md` | Design philosophy, module architecture, and requirements |
| `CLAUDE.md` | Development commands and critical rules |
| `.github/copilot-instructions.md` | The Scripture — executable doctrine |
| `docs/diary.md` | Metacognitive development journal |
| `feature-requests/` | Planning documents and acceptance criteria |
| `scripts/req_coverage.py` | Requirement traceability automation |

These are not static documents. They evolve with the codebase, refined by the very processes they describe. The doctrine improves the code; the code validates the doctrine. This feedback loop — where **every failure refines the law** — is the heartbeat of YAMLGraph's development pipeline.

---

*Next: [Chapter 01 — Doctrine: The Scripture Decoded](01-doctrine.md)*
