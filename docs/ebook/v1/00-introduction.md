# Chapter 00: Introduction

> *"Build production AI pipelines in minutes, not days."*
> — YAMLGraph README

---

## What is YAMLGraph?

YAMLGraph is a **YAML-first framework** for building LLM pipelines. The core insight is disarmingly simple: **60–80% of AI workflows can be defined entirely in YAML** — graphs, prompts, schemas — without writing a single line of Python.

Built on [LangGraph](https://github.com/langchain-ai/langgraph), YAMLGraph provides a declarative orchestration layer that supports multi-provider LLMs (Anthropic, Google/Gemini, Mistral, OpenAI, Replicate, xAI, LM Studio), parallel batch processing via map nodes, LLM-driven conditional routing, streaming, human-in-the-loop interrupts, and checkpointing — all from YAML configuration.

```yaml
# A complete pipeline in YAML
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

That's it. No boilerplate classes, no manual state management, no provider-specific imports. The framework handles compilation, state generation, LLM invocation, and output parsing.

### Why YAML-First?

The design philosophy, as documented in `ARCHITECTURE.md`, rests on four pillars:

1. **Separation of concerns** — Pipeline logic lives in YAML; business logic lives in prompts.
2. **No Python required** — Non-developers can create and modify pipelines.
3. **Version control friendly** — YAML is diff-able and reviewable.
4. **Runtime safety** — Pydantic schema validation catches errors before execution.

The tradeoff is explicit: YAMLGraph sacrifices some flexibility for dramatically faster prototyping, easier maintenance, and built-in best practices. When you find yourself fighting the YAML to express complex logic, you reach for `type: python` nodes within YAMLGraph, or drop to raw LangGraph for full control.
*(Source: `README.md`, "When NOT to Use YAMLGraph")*

### The Three-Layer Architecture

Every YAMLGraph application follows a strict separation of concerns:

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

Graphs are testable, traceable, and resumable. Python handles UX where YAML can't. Tools isolate non-deterministic operations. Each layer evolves independently.
*(Source: `CLAUDE.md`, "Three-Layer Pattern")*

---

## The Development Pipeline Concept

This book is not primarily about YAMLGraph's runtime capabilities. It is about something rarer and more valuable: the **codified development process** that produces and maintains the framework.

Most software projects have informal processes — a CONTRIBUTING.md, maybe some CI checks, a code review culture that varies by reviewer. YAMLGraph takes a different approach. Its development process is **executable doctrine** — a system of interlocking tools, checks, and rituals that enforce quality not through goodwill, but through automation.

### The Scripture

At the heart of this system is a document called **The Scripture** (`.github/copilot-instructions.md`). It opens with an unambiguous declaration:

> *"This document is executable doctrine: violations are defects, not suggestions."*

The Scripture codifies ten commandments for development — from "Thou shalt research before coding" to "Thou shalt preserve and improve the doctrine." These are not aspirational guidelines. They are enforced by pre-commit hooks, CI gates, and automated review pipelines.
*(Source: `.github/copilot-instructions.md`, "The 10 Commandments")*

### The Chaplain System

The Scripture defines a ritual called the **Sermon of the Chaplain** — a seven-step development pipeline:

1. **Research** — Let agents explore alternatives and return with truth.
2. **Plan** — Write the feature request with objectives, constraints, and acceptance criteria.
3. **Judge** — Critically examine the plan; resolve contradictions; freeze scope.
4. **Enforce** — TDD. Write the failing test first; make only the smallest sufficient change.
5. **Purge** — Remove speculative code. If it isn't required and tested, it doesn't exist.
6. **Submit** — Bump, commit, push, release, tag. Let CI judge.
7. **Distill** — Add a metacognitive diary entry. Name the cognitive trap. Plant a seed.

This pipeline is not metaphor. It is the actual development workflow, enforced by tooling that includes a pre-commit Chaplain pipeline, an Inquisitor code review system, requirement traceability matrices, and a reflective diary system.
*(Source: `.github/copilot-instructions.md`, "Sermon of the Chaplain")*

### Doctrine-Driven Development

What makes this approach distinctive is its self-improving nature. The tenth commandment states:

> *"Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word."*

The doctrine evolves. Recurring diary patterns get "graduated" into The Scripture itself. The Knowledge Graph captures causal chains from trap to cure. The system learns from its mistakes and encodes those lessons as automated checks, not tribal knowledge.

This is **doctrine-driven development**: a process where the development methodology itself is versioned, tested, and continuously improved — just like the code it produces.

---

## Book Overview

This book dissects the YAMLGraph development pipeline, chapter by chapter. Each chapter examines one layer of the system, from the philosophical foundations to the practical tooling.

### Table of Contents

| Chapter | Title | Description |
|---------|-------|-------------|
| **00** | **Introduction** | What YAMLGraph is, why the development pipeline matters, and how this book is organized. *(You are here.)* |
| **01** | **Doctrine — The Scripture Decoded** | A deep reading of the 10 Commandments, the Sermon of the Chaplain, the Rite of Correction, and how doctrine shapes every commit. |
| **02** | **Pre-commit Gates** | The automated quality gates that run before every commit — linters, formatters, test coverage, requirement traceability, and the `--no-verify` death sentence. |
| **03** | **The Chaplain Pipeline** | How the seven-step Chaplain workflow (Research → Plan → Judge → Enforce → Purge → Submit → Distill) operates in practice with real feature requests. |
| **04** | **The Inquisitor** | The automated code review system that enforces doctrine compliance, catches anti-patterns, and ensures every change aligns with The Scripture. |
| **05** | **The Diary System** | How metacognitive reflection is built into the development process — traps, insights, seeds, and the graduation of heuristics into doctrine. |
| **06** | **Requirement Traceability Matrix** | ADR-001 in action: how every test maps to a requirement, how `req_coverage.py` enforces coverage, and how the `noqa` confession system handles exceptions. |
| **07** | **YAMLGraph Core** | The runtime framework itself — the compilation pipeline, node factory, executor, dynamic state, multi-provider LLM support, and the graph YAML specification. |
| **08** | **The Wizard Behind the Curtain** | How AI agents (GitHub Copilot, Claude) operate within the doctrine — constrained by The Scripture, guided by conventions, and held accountable by the same CI gates as human developers. |

Each chapter is self-contained but builds on the concepts introduced in earlier chapters. Chapters 01–06 focus on the development pipeline. Chapter 07 covers the framework itself. Chapter 08 reveals how AI-assisted development works within a doctrine-driven system.

---

## Who This Book Is For

### Developers Building AI Pipelines

If you're building LLM-powered applications and tired of rewriting boilerplate orchestration code, YAMLGraph offers a declarative alternative. Chapter 07 gives you the technical deep-dive into the framework. But the surrounding chapters show you something more valuable: how to build AI pipelines with a quality process that scales beyond "it works on my machine."

### Teams Wanting Quality-Enforced Development

If your team struggles with inconsistent code quality, informal processes, or "it depends on who reviews it" culture, this book offers a concrete alternative. The YAMLGraph development pipeline demonstrates how to encode quality standards as automated checks — not as wiki pages that nobody reads. Chapters 02–06 are your playbook.

### Anyone Interested in YAML-Driven Orchestration

If the idea of defining complex AI workflows — routing, loops, agents, human-in-the-loop — in declarative YAML intrigues you, start with Chapter 07 for the technical details, then read Chapter 01 to understand the philosophy that shaped those design decisions.

### AI-Augmented Development Teams

If you're using AI coding assistants (GitHub Copilot, Claude, or similar) and wondering how to keep them aligned with your team's standards, Chapter 08 shows how YAMLGraph constrains AI agents with the same doctrine that governs human developers. The Scripture doesn't care whether the commit came from a human or a machine.

---

## A Note on Tone

You'll notice that YAMLGraph's documentation uses religious metaphor — Scripture, Commandments, Chaplain, Inquisitor, Confessions. This is deliberate. The language is chosen to convey that these are not suggestions. They are **laws** — enforced by automation, refined by experience, and violated only at the cost of a failed build.

The metaphor also captures something true about software craft: quality is a discipline, not a talent. It requires rituals (TDD, code review, reflection) practiced consistently, not brilliance applied sporadically.

> *"What survives the fire may merge."*
> — The Scripture, closing line

Let's begin.

---

*Next: [Chapter 01 — Doctrine: The Scripture Decoded](01-doctrine.md)*

