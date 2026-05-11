# Diary: Monorepo Identity — Three Systems, One Repo

**Date:** 2026-05-10
**FR:** (none — architectural reflection)
**Author:** sami / copilot session

---

## What Happened

A full monorepo orientation was performed, not to implement a feature, but to name what the repository has become. The observation: this repo contains three distinct systems with different lifecycles, stakeholders, and deployment targets — cohabiting without an explicit contract about separation.

---

## The Three Systems

**1. The Framework** (`yamlgraph/`, `prompts/`, `graphs/`, `capabilities/`)

A publishable Python library. Has version (`0.5.0`), 140+ capability definitions, 304 test files, CI gates, import-linter enforcing architectural boundaries. This is the part that could be `pip install yamlgraph` for any external team.

**2. The IDE** (`.chaplain/`, Watcher2, Inquisitor, Philosopher daemons)

An autonomous development loop: inbox → plan → judge → enforce → merge. Watcher2 opens PRs. The Inquisitor detects drift and auto-proposes FRs. The Philosopher challenges architecture decisions. The whole system runs as an FSM with an event socket, UI port, and action scripts — a self-hosted AI development environment that happens to live inside the repo it governs.

**3. The Applications** (`projects/ninchat_voice/`, `projects/outcaller/`, `projects/incaller/`, etc.)

Production deployments. `ninchat_voice` alone has its own Dockerfile, `fly.toml`, deploy scripts, `pyproject.toml`, pre-commit config, 15+ e2e test suites, STT/TTS services, and a full FSM voice coordinator for Finnish healthcare (medical triage, eldercare, prescription callbacks). This is a product — a separate repository living as a guest.

---

## The Trap: `working_system_inertia`

From the Knowledge Graph: *"'It works' blocks seeing it clearly → inventory fit, not function."*

The repo works. CI is green. PRs merge. The Chaplain governs. But the question isn't "does it work?" — it's "is this the right container?" The answer was never explicitly asked because the growth happened incrementally: one project added, one daemon added, one action script added. Each step was locally justified. The aggregate shape was never evaluated.

The `ninchat_voice` project is the clearest signal. It has all the hallmarks of an independent repo: its own deployment target (Fly.io), its own domain model (voice FSM, STT/TTS, IEC 62304-adjacent healthcare concerns), its own test suite with NC-prefixed ticket numbers that correspond to a separate issue tracker. It depends *on* the yamlgraph framework but is not *part of* it.

---

## The Mixed-Concern Problem

The Chaplain is the sharpest case. It is simultaneously:
- A **commit author** (Watcher2 opens PRs)
- A **CI system** (Inquisitor blocks merges on drift)
- A **product** of the framework (built on YAMLGraph graphs and nodes)
- A **governance layer** of the framework (enforces the Scripture it was built with)

When the IDE lives inside the repo it governs, it creates a recursive dependency: framework bugs block the IDE that fixes framework bugs. Watcher2 remediation loops that crash (FR-281, FR-284) halt the entire development pipeline — not just governance, but also `ninchat_voice` feature work that flows through the same Chaplain inbox.

The applications compound this: `ninchat_voice` CI failures are surfaced in the same GitHub Actions run as `yamlgraph` unit tests. A broken healthcare voice flow and a broken YAML parser appear as peers in the same check suite.

---

## What the "AI Development IDE" Framing Reveals

The Chaplain is genuinely novel — a governance loop that manages its own host framework. But an IDE that ships as a commit in the project it edits has a stability coupling problem. The IDE and the framework are not the same release unit; they should not share a version number.

The `framework_costume` trap from the Knowledge Graph applies at the repo level: *"FSM wearing DAG costume → if <50% nodes use core features, wrong tool."* Here the inversion: the monorepo wearing a framework costume, when the dominant ongoing development is IDE infrastructure and a production voice application.

---

## What This Is Not

This is not a call to immediately extract or refactor. The current arrangement carries known advantages:
- Shared pre-commit hooks and linting across all three systems
- Framework dog-fooding: `ninchat_voice` is the highest-fidelity user of `yamlgraph`
- Chaplain changes and framework changes share atomic commits — no version skew between governance scripts and the framework they invoke

These are real benefits. The cost is the coupling. The question is whether the coupling is load-bearing or incidental.

---

## Seed

> **What would it take to extract the Chaplain as a standalone tool?** A repo that any YAMLGraph project could install as a dev dependency — pointed at its own inbox directory, using its own event socket, governing its own CI — without inheriting the framework codebase or the `ninchat_voice` production deployment.

The answer to that question reveals whether the current coupling is architectural necessity or accumulated inertia. If the Chaplain can be described as "a YAMLGraph application that happens to target the YAMLGraph repo as its working directory," extraction becomes a deployment choice rather than an architectural overhaul.

The heuristic to graduate: **"When a system within a monorepo has its own deploy target, its own issue tracker prefix, and its own release lifecycle — treat it as a separate repo until proven otherwise."**
