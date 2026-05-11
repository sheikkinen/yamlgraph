# Diary: scripture-dev Is the Scripture Without the Priest

**Date:** 2026-05-11
**FR:** FR-207 (retrospective)
**Author:** sami / copilot session

---

## What Happened

A cross-reference between `scripture-dev` (the extracted methodology template) and the full yamlgraph `.chaplain/` revealed a structural gap: scripture-dev documents the Chaplain workflow as a "pattern with shell-script reference," but the actual Chaplain — as it exists in yamlgraph — is not a pattern. It is running software.

The actual Chaplain:
- 5 YAMLGraph graphs (`watcher-plan/`, `watcher-enforce/`, `watcher-diary/`, `watcher-forensic/`, `philosopher/`)
- 8 action scripts (~860 lines: `git_commit_action.py`, `validate_gate_action.py`, `yamlgraph_async_action.py`, `precommit_action.py`, etc.)
- 2 configuration files (461 lines: `watcher-dispatcher.yaml`, `watcher-pipeline-v2.yaml`)
- 3 runtime scripts (`start-system.sh` at 294 lines, `pipeline-status.sh`, `clean-worktree.sh`)
- A library (`diary.py`, `worktree.py`, `finalize_lib.sh`)
- A state machine with an event socket, UI port, and inbox FSM

scripture-dev documents: "Plan → Judge → Enforce. This pattern works with any AI coding assistant or human reviewers."

That sentence is true. It is also the difference between describing fire and giving someone a lighter.

---

## The Trap: `detection_without_enforcement`

From the Knowledge Graph: *"Lint without gate = advisory → add CI block or remove claim."*

Applied at the meta-level: *"Document pattern without implementation = advisory → provide runnable system or remove the claim of automation."*

scripture-dev's Chaplain section is advisory. It describes what the workflow does without providing the machinery to run it. A team adopting scripture-dev gets the discipline of the diary, the changelog fragments, the pre-commit hooks — all the gates that measure whether work was done correctly. But they get no automation for *initiating* work, no Plan phase that generates a feature request from an inbox entry, no Judge that returns a verdict, no Enforce phase that opens a PR.

The hooks are the rules. The Chaplain is the enforcement officer. scripture-dev has rules, no officer.

---

## Why This Gap Exists

FR-207 explicitly excluded the Chaplain from Tier 1 and Tier 2:

> **What Does NOT Ship:** No Inquisitor/Philosopher graphs (these require LLM access; document as pattern only)

The rationale was correct at the time: the Chaplain requires LLM access, YAMLGraph as a runtime dependency, a working `.venv`, and a running event socket. These are hard prerequisites for a "zero-install template." The FR's tier structure was right to document rather than extract.

FR-196 (Portable Chaplain) made `.chaplain/` self-contained within yamlgraph — a prerequisite for extraction that FR-207 noted. But FR-196 never went further. It made the Chaplain portable *within yamlgraph*, not portable *to other projects*.

The gap is not a mistake. It is an unfinished journey: FR-196 → FR-207 → (missing FR) → Chaplain as extractable system.

---

## What "Extractable Chaplain" Would Require

The Chaplain has three hard dependencies that prevent naive extraction:

1. **YAMLGraph runtime** — the watcher pipeline graphs use `yamlgraph graph run`. This is not a blocker for extraction; it becomes a declared dependency (`pip install yamlgraph`).

2. **LLM access** — plan, judge, enforce phases all invoke LLMs. This is configurable (provider/model via environment variables). Not a blocker; a documented prerequisite.

3. **Project-specific context** — the judge graph reads the feature request, the enforce graph runs `pytest` and `pre-commit`, the plan graph references `ARCHITECTURE.md`. This context is the hard part. It is not parameterizable with `sed`. It requires the Chaplain to *discover* its host project's conventions.

The third dependency is the real architectural challenge. The Scripture in `.github/copilot-instructions.md` provides agent context. The Chaplain needs the equivalent: a `chaplain.yaml` that tells it where the inbox lives, what the FR template looks like, what the test command is, what the linter is.

In yamlgraph, this is implicit — the Chaplain hardcodes `pytest tests/`, `pre-commit run`, `git -C . log`. In an extracted Chaplain, these become configuration.

---

## The Missing FR

What would make scripture-dev complete:

```
FR-XXX: Extractable Chaplain
- chaplain.yaml: project configuration (inbox path, test cmd, lint cmd, FR template path)
- watcher-dispatcher.yaml and watcher-pipeline-v2.yaml: parameterized via chaplain.yaml
- Action scripts: read chaplain.yaml at runtime instead of hardcoding project paths
- start-system.sh: accepts --config flag pointing to chaplain.yaml
- scripture-dev: includes .chaplain/ as optional add-on requiring yamlgraph + LLM key
```

This FR does not exist yet. It is the bridge between "governance as template" and "governance as running system."

---

## The Asymmetry

scripture-dev is the rules without the referee.
yamlgraph has the referee but keeps it private.

A project adopting scripture-dev today gets:
- ✅ Diary discipline (gates enforce it)
- ✅ Changelog fragments (CI enforces it)
- ✅ Conventional commits (hook enforces it)
- ✅ The Scripture as agent context
- ❌ Automated Plan phase (manual)
- ❌ Automated Judge phase (manual or "ask your AI assistant")
- ❌ Automated Enforce phase (manual PR workflow)
- ❌ Inquisitor drift detection (not extracted)
- ❌ Philosopher challenge nodes (not extracted)

The enforcement apparatus (hooks, CI) is complete. The initiation apparatus (Chaplain) is absent. The team must be the Chaplain themselves.

This is not nothing. Discipline without automation is still discipline. Many teams will never need or want a running FSM daemon. But for teams that do — teams where the volume of FRs and the cadence of AI-assisted development justify it — the path from scripture-dev to a running Chaplain is currently undocumented and unsupported.

---

## Seed

> **The Chaplain is a YAMLGraph application that happens to target its own host repo.** If it were deployed as a separate service — a "governance server" running alongside the project, connected via the inbox directory — would the coupling to the host repo's `.venv` and `pyproject.toml` dissolve? Could a single Chaplain instance govern multiple projects, switching context via `chaplain.yaml` per run?

The answer to that question determines whether the missing FR is "extract Chaplain" or "productize Chaplain."
